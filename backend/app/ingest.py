"""Run `python -m app.ingest --articles` for live article ingestion."""
import argparse
import asyncio
import json
import uuid
import httpx
from redis import Redis
from .config import settings
from bs4 import BeautifulSoup
from .catalog import CATALOG
from .retrieval import metadata_documents, index_documents
from .storage import initialize, save_documents


def chunk_text(text, size=1800, overlap=200):
    if size <= overlap or overlap < 0:
        raise ValueError('Chunk size must exceed overlap.')
    return [text[start:start + size] for start in range(0, len(text), size - overlap) if text[start:start + size].strip()]

async def ingest(articles=False):
    documents = metadata_documents()
    if articles:
        async with httpx.AsyncClient(timeout=45, follow_redirects=True, headers={'User-Agent': 'Leumur research prototype (Eurostat article indexing)'}) as client:
            for item in CATALOG:
                response = await client.get(item['article'])
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                body = soup.select_one('.mw-parser-output')
                if not body:
                    raise RuntimeError(f"Article body unavailable: {item['code']}")
                for element in body.select('script, style, nav, .toc, .navbox, .mw-editsection'):
                    element.decompose()
                text = '\n'.join(line.strip() for line in body.get_text('\n').splitlines() if line.strip())
                if len(text) < 500:
                    raise RuntimeError(f"Article body unexpectedly short: {item['code']}")
                # This is a curated association, not an assertion that all article tables use this dataset.
                for i, chunk in enumerate(chunk_text(text)):
                    documents.append({'id': str(uuid.uuid5(uuid.NAMESPACE_URL, item['article'] + str(i))), 'dataset': item['code'], 'kind': 'article', 'source': item['article'], 'content': chunk})
    initialize()
    await index_documents(documents)
    save_documents(documents)
    cache = Redis.from_url(settings.redis_url)
    for key in cache.scan_iter(match='chart:v1:*'):
        cache.delete(key)
    print(json.dumps({'indexed': len(documents), 'article_chunks': sum(doc['kind'] == 'article' for doc in documents), 'mode': 'live_articles' if articles else 'curated_metadata_only'}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--articles', action='store_true')
    args = parser.parse_args()
    asyncio.run(ingest(args.articles))
