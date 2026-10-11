import hashlib
import json
import logging
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text
from qdrant_client import QdrantClient
from .catalog import CATALOG, BY_CODE, COUNTRIES
from .config import settings
from .models import Query, Clarification
from .planner import plan_query
from .eurostat import fetch_observations, demo_observations, SourceError
from .retrieval import retrieve, collection_name, retrieval_method
from .storage import engine, Document
from sqlalchemy import select, func
from sqlalchemy.orm import Session

app = FastAPI(title='Leumur: data to plots', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[settings.cors_origin], allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
cache = Redis.from_url(settings.redis_url, decode_responses=True)
logger = logging.getLogger(__name__)

@app.get('/api/catalog')
def catalog():
    return {'datasets': CATALOG, 'countries': COUNTRIES}

@app.get('/api/health')
async def health():
    components = {}
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        components['postgres'] = True
    except Exception:
        components['postgres'] = False
    try:
        components['redis'] = await cache.ping()
    except Exception:
        components['redis'] = False
    try:
        client = QdrantClient(url=settings.qdrant_url, trust_env=False)
        client.get_collections()
        components['qdrant'] = True
        components['context_index'] = client.collection_exists(collection_name())
    except Exception:
        components['qdrant'] = False
        components['context_index'] = False
    article_chunks = 0
    if components.get('postgres'):
        try:
            with Session(engine) as session:
                article_chunks = session.scalar(select(func.count()).select_from(Document).where(Document.kind == 'article'))
        except Exception:
            pass
    return {'ready': all(components.values()), 'components': components, 'article_chunks': article_chunks, 'retrieval': retrieval_method(), 'planner': 'llm_structured' if settings.llm_api_key else 'deterministic'}

@app.post('/api/chart')
async def chart(query: Query):
    key = 'chart:v1:' + hashlib.sha256((query.mode + query.question + settings.llm_model + collection_name()).encode()).hexdigest()
    try:
        cached = await cache.get(key)
        if cached:
            result = json.loads(cached)
            result['cached'] = True
            return result
    except Exception:
        logger.warning('Cache unavailable; continuing without cache')
    try:
        context = await retrieve(query.question)
        plan, planner = await plan_query(query.question, context)
        item = BY_CODE[plan.dataset]
        if query.mode == 'demo':
            points, source_url, updated = demo_observations(plan), None, None
        else:
            points, source_url, updated = await fetch_observations(plan)
    except Clarification as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except SourceError as exc:
        raise HTTPException(502, detail=str(exc)) from exc
    except (RuntimeError, httpx.HTTPError) as exc:
        raise HTTPException(503, detail='Retrieval or model service unavailable. Check context ingestion, network policy, and configured credentials.') from exc
    except Exception as exc:
        logger.exception('Chart request failed')
        raise HTTPException(503, detail='A required service is unavailable. Check the health endpoint and backend logs.') from exc
    result = {
        'plan': plan.model_dump(), 'title': f"{item['measure']} · {COUNTRIES[plan.geo]}",
        'unit': item['unit'], 'points': points, 'mode': query.mode, 'cached': False,
        'interpretation': f"{item['description']} {COUNTRIES[plan.geo]}; {plan.years} {'complete calendar years' if plan.time_basis == 'calendar_years' else 'years ending at the latest available observation'}. Missing values remain gaps.",
        'provenance': {'dataset': plan.dataset, 'filters': dict(item['filters'], geo=plan.geo), 'source_url': source_url, 'article_url': item['article'], 'article_relationship': item['article_relationship'], 'source_updated': updated, 'retrieved_at': datetime.now(timezone.utc).isoformat()},
        'retrieval': {'method': retrieval_method(), 'planner': planner, 'context': context},
        'warnings': (['SYNTHETIC DEMO DATA — these values are not Eurostat observations.'] if query.mode == 'demo' else []) + (['Some observations are missing.'] if any(point['value'] is None for point in points) else []),
    }
    try:
        await cache.setex(key, settings.cache_seconds, json.dumps(result))
    except Exception:
        logger.warning('Could not cache chart')
    return result
