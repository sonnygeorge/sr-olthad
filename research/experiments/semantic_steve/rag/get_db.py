import functools
import os

from chromadb import Collection, PersistentClient

from research.experiments.semantic_steve.rag.constants import (
    PATH_TO_VECTOR_DB,
)
from research.experiments.semantic_steve.rag.create_db import create_vector_db
from research.utils import to_lower_snake_case
from sr_olthad import LmAgentName


@functools.cache
def get_collections() -> dict[LmAgentName, Collection]:
    """
    Get all collections from the vector database.
    """
    if not os.path.exists(PATH_TO_VECTOR_DB):
        create_vector_db()
    chroma_client = PersistentClient(path=PATH_TO_VECTOR_DB)
    collections = {}
    for agent_name in LmAgentName:
        agent_name_lower_snake = to_lower_snake_case(agent_name)
        collections[agent_name] = chroma_client.get_or_create_collection(
            name=agent_name_lower_snake
        )
    return collections


if __name__ == "__main__":
    collections = get_collections()
    for agent_name, collection in collections.items():
        print(f"Collection for {agent_name}:")
        print(f"  Name: {collection.name}")
        print(f"  Count: {collection.count()}")
        print(f"  Metadata: {collection.metadata}")
