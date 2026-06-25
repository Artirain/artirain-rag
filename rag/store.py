import uuid
from functools import lru_cache

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .config import Config


@lru_cache(maxsize=4)
def _embedder(model_name: str) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)


def embed(texts, model_name):
    return [vec.tolist() for vec in _embedder(model_name).embed(list(texts))]


class Store:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        url = cfg.qdrant_url
        if url.startswith("http"):
            self.client = QdrantClient(url=url)
        elif url == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(path=url)
        self._dim = None

    @property
    def dim(self):
        if self._dim is None:
            self._dim = len(embed(["dim probe"], self.cfg.embed_model)[0])
        return self._dim

    def reset(self):
        self.client.recreate_collection(
            collection_name=self.cfg.collection,
            vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
        )

    def upsert(self, chunks):
        vectors = embed([c["text"] for c in chunks], self.cfg.embed_model)
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=v, payload=c)
            for v, c in zip(vectors, chunks)
        ]
        self.client.upsert(collection_name=self.cfg.collection, points=points)
        return len(points)

    def search(self, query, top_k=None):
        vec = embed([query], self.cfg.embed_model)[0]
        resp = self.client.query_points(
            collection_name=self.cfg.collection,
            query=vec,
            limit=top_k or self.cfg.top_k,
        )
        return [
            {"score": h.score, "text": h.payload["text"], "source": h.payload["source"]}
            for h in resp.points
        ]
