from research.experiments.semantic_steve.rag.embed import embed, get_embed_inputs
from research.experiments.semantic_steve.rag.get_db import get_collections
from sr_olthad import LmAgentName, UserPromptInputData


def retrieve(
    n: int, user_prompt_input_data: UserPromptInputData, agent_name: LmAgentName
) -> list[str]:
    """
    Retrieve the top n most similar documents from the vector database based on the
    embedding strategy in embed()
    """
    embeddings = embed(get_embed_inputs(user_prompt_input_data))
    collection = get_collections()[agent_name]
    retrieval = collection.query(
        query_embeddings=[embeddings],
        n_results=n,
        include=["documents"],
    )
    documents = retrieval["documents"][0]
    return documents
