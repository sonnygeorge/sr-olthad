import numpy as np
from sentence_transformers import SentenceTransformer

from research.experiments.semantic_steve.rag.constants import EMBEDDING_WEIGHTS
from sr_olthad import UserPromptInputData


def get_embed_inputs(prompt_input_data: UserPromptInputData) -> UserPromptInputData:
    # NOTE: Just a placeholder for now
    return prompt_input_data


def embed(prompt_input_data: UserPromptInputData) -> np.ndarray:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [
        prompt_input_data.env_state,
        prompt_input_data.olthad,
        prompt_input_data.task_in_question,
    ]
    # start_time = time.time()
    embeddings = model.encode(texts)
    # elapsed_time = time.time() - start_time
    # print(f"Embedded {len(texts)} texts in {elapsed_time:.2f} seconds")
    # print(f"Average time per text: {elapsed_time/len(texts):.4f} seconds")
    weights = np.array([EMBEDDING_WEIGHTS.get(key, 1) for key in texts])
    return np.sum(embeddings * weights[:, np.newaxis], axis=0)
