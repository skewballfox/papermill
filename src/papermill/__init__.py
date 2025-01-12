from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sentence_transformers import SentenceTransformer
from qdrant_client import models, QdrantClient

from papermill.config import Config, dev_config
from papermill.metadata import MetadataHandler
from os import environ

def main() -> int:
    environ["TOKENIZERS_PARALLELISM"] = "false"
    config = dev_config()
    metadata_extractor = MetadataHandler(config)
    client = QdrantClient(config.client_param)

    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    if not (embedding_dims := encoder.get_sentence_embedding_dimension()):
        raise ValueError("embedding_dims is None")

    client.create_collection(
        collection_name="my_books",
        vectors_config=models.VectorParams(
            size=embedding_dims,  # Vector size is defined by used model
            distance=models.Distance.COSINE,
        ),
    )

    client.upload_points(
        collection_name="my_books",
        points=[
            models.PointStruct(
                id=idx,
                vector=encoder.encode(doc.description).tolist(),
                payload=doc.__dict__,
            )
            for idx, doc in enumerate(metadata_extractor.books)
        ],
    )

    hits = client.query_points(
        collection_name="my_books",
        query=encoder.encode("Data Engineering").tolist(),
        limit=3,
    ).points

    for hit in hits:
        print(hit.payload, "score:", hit.score)



    print("Hello from papermill!")
    return 0
