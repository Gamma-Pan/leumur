"""Local semantic embeddings from FastEmbed's published MiniLM ONNX artifact."""
from functools import lru_cache
from pathlib import Path
import httpx
from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType
from .config import settings

@lru_cache(maxsize=1)
def model():
    if not (Path(settings.model_cache) / 'fast-all-MiniLM-L6-v2').exists():
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                response = client.head('https://storage.googleapis.com/qdrant-fastembed/sentence-transformers-all-MiniLM-L6-v2.tar.gz')
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError('Local semantic model download is unavailable. Allow storage.googleapis.com or explicitly use EMBEDDING_BACKEND=lexical for diagnostics.') from exc
    # Use the official FastEmbed HTTPS artifact directly; no Hugging Face account needed.
    TextEmbedding.add_custom_model(
        model='leumur/all-MiniLM-L6-v2', pooling=PoolingType.MEAN, normalization=True,
        sources=ModelSource(url='https://storage.googleapis.com/qdrant-fastembed/sentence-transformers-all-MiniLM-L6-v2.tar.gz', _deprecated_tar_struct=True),
        dim=384, model_file='model.onnx', license='apache-2.0',
        description='FastEmbed distribution of all-MiniLM-L6-v2',
    )
    return TextEmbedding(model_name='leumur/all-MiniLM-L6-v2', cache_dir=settings.model_cache, threads=2)
