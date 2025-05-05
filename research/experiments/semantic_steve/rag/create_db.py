import importlib
import os
import shutil
import sys

from chromadb import PersistentClient

from research.experiments.semantic_steve.rag.constants import (
    EMBEDDING_WEIGHTS,
    PATH_TO_VECTOR_DB,
    PATHS_TO_EXAMPLE_DIRS_BY_AGENT,
)
from research.experiments.semantic_steve.rag.embed import embed, get_embed_inputs
from research.experiments.semantic_steve.rag.schema import PlannerExample
from research.utils import to_lower_snake_case
from sr_olthad import LmAgentName


def import_examples(agent_name: LmAgentName) -> list[PlannerExample]:
    """
    Import all examples from the specified agent's module.
    """
    directory_path = PATHS_TO_EXAMPLE_DIRS_BY_AGENT[agent_name]
    sys.path.insert(0, os.path.abspath(directory_path))
    examples = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # remove .py
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "EXAMPLE"):
                    examples.append(module.EXAMPLE)
                else:
                    print(f"Module {module_name} does not contain an EXAMPLE object")
            except Exception as e:
                print(f"Error importing {module_name}: {e}")
    return examples


def import_all_examples() -> dict[LmAgentName, list[PlannerExample]]:
    """
    Import all examples from all agent modules.
    """
    all_examples = {}
    for agent_name in PATHS_TO_EXAMPLE_DIRS_BY_AGENT.keys():
        all_examples[agent_name] = import_examples(agent_name)
    return all_examples


def create_vector_db():
    """
    Create a vector database for all agent examples.
    """
    print(f"Creating vector db for in-context examples with weights: {EMBEDDING_WEIGHTS}")
    if os.path.exists(PATH_TO_VECTOR_DB):
        print(f"Deleting existing vector database at {PATH_TO_VECTOR_DB}")
        shutil.rmtree(PATH_TO_VECTOR_DB)
    chroma_client = PersistentClient(path=PATH_TO_VECTOR_DB)
    for agent_name, examples in import_all_examples().items():
        agent_name_lower_snake = to_lower_snake_case(agent_name)
        embeds, docs, ids = [], [], []
        for i, example in enumerate(examples):
            embeds.append(embed(get_embed_inputs(example.prompt_input_data)))
            docs.append(example.stringify_for_prompt_insertion())
            ids.append(f"{agent_name_lower_snake}_{i}")
        if len(docs) == 0:
            print(f"No examples found for {agent_name}. Skipping...")
            continue
        collection = chroma_client.get_or_create_collection(name=agent_name_lower_snake)
        collection.add(embeddings=embeds, documents=docs, ids=ids)
        print(f"Saved {len(docs)} examples to the vector database for {agent_name}")


if __name__ == "__main__":
    create_vector_db()
    print("Vector database created.")
