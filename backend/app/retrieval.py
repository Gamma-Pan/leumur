import hashlib
import math
import re
import uuid
import httpx
from qdrant_client import QdrantClient, models
from .catalog import CATALOG
from .config import settings

LOCAL_COLLECTION = 'leumur_context_minilm_v1'
SEMANTIC_COLLECTION = 'leumur_context_semantic_v1'

def local_vector(text):
    vector = [0.0] * 256
    for token in re.findall(r'[a-z0-9]+', text.lower()):
        position = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], 'big') % 256
        vector[position] += 1
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]

async def embed(texts):
    if not settings.llm_api_key:
        if settings.embedding_backend == 'lexical':
            return [local_vector(text) for text in texts]
        from .embeddings import model
        return [vector.tolist() for vector in model().embed(texts)]
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post('https://api.openai.com/v1/embeddings', headers={'Authorization': f'Bearer {settings.llm_api_key}'}, json={'model': settings.embedding_model, 'input': texts, 'dimensions': 1536})
        response.raise_for_status()
        return [item['embedding'] for item in sorted(response.json()['data'], key=lambda item: item['index'])]

def collection_name():
    if settings.llm_api_key:
        return SEMANTIC_COLLECTION + '_' + hashlib.sha256(settings.embedding_model.encode()).hexdigest()[:8]
    return 'leumur_context_lexical_v1' if settings.embedding_backend == 'lexical' else LOCAL_COLLECTION

async def index_documents(documents):
    client = QdrantClient(url=settings.qdrant_url, trust_env=False)
    vectors = []
    for offset in range(0, len(documents), 32):
        vectors.extend(await embed([doc['content'] for doc in documents[offset:offset + 32]]))
    staging = collection_name() + '_' + uuid.uuid4().hex
    client.create_collection(staging, vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE))
    try:
        client.upsert(staging, points=[models.PointStruct(id=doc['id'], vector=vector, payload=doc) for doc, vector in zip(documents, vectors)], wait=True)
        operations = []
        if any(alias.alias_name == collection_name() for alias in client.get_aliases().aliases):
            operations.append(models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=collection_name())))
        operations.append(models.CreateAliasOperation(create_alias=models.CreateAlias(collection_name=staging, alias_name=collection_name())))
        client.update_collection_aliases(operations)
    except Exception:
        client.delete_collection(staging)
        raise
    # Remove obsolete generations only after the new index is active.
    for collection in client.get_collections().collections:
        if collection.name.startswith(collection_name() + '_') and collection.name != staging:
            client.delete_collection(collection.name)

async def retrieve(question):
    vector = (await embed([question]))[0]
    client = QdrantClient(url=settings.qdrant_url, trust_env=False)
    if not client.collection_exists(collection_name()):
        raise RuntimeError('Context index is missing. Run the ingestion command for this embedding mode.')
    hits = []
    # Retrieve metadata separately so long articles cannot displace executable dimensions.
    for kind in ['metadata', 'article']:
        hits.extend(client.query_points(collection_name(), query=vector, query_filter=models.Filter(must=[models.FieldCondition(key='kind', match=models.MatchValue(value=kind))]), limit=3).points)
    return [{'dataset': hit.payload['dataset'], 'kind': hit.payload['kind'], 'source': hit.payload['source'], 'content': hit.payload['content'], 'score': hit.score} for hit in hits]

def metadata_documents():
    return [{'id': str(uuid.uuid5(uuid.NAMESPACE_URL, item['code'])), 'dataset': item['code'], 'kind': 'metadata', 'source': f"https://ec.europa.eu/eurostat/databrowser/view/{item['code']}/default/table?lang=en", 'content': f"{item['title']}. {item['description']} Unit: {item['unit']}. Filters: {item['filters']}."} for item in CATALOG]

def retrieval_method():
    return 'openai_semantic' if settings.llm_api_key else settings.embedding_backend
