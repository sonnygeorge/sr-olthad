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


if __name__ == "__main__":
    import re

    from sr_olthad.olthad import TaskNode, TaskStatus

    dummy_task = TaskNode(
        _id="1",
        _task="Dig down through grass and dirt until stone is exposed.",
        _status=TaskStatus.IN_PROGRESS,
        _retrospective=None,
        _parent_id=None,
        _non_planned_subtasks=[],
        _planned_subtasks=[],
    )

    dummy_env_state = """{
    "envState": {
        "playerCoordinates": [43.5, 68, 133.6],
        "health": "20/20",
        "hunger": "20/20",
        "inventory": [{"name": "oak_planks", "count": 2}, {"name": "stick", "count":
2}, {"name": "crafting_table", "count": 1}, {"name": "wooden_pickaxe", "count": 1,
"durabilityRemaining": "98%"}, {"name": "dirt", "count": 3}, {"name":
"birch_planks", "count": 1}],
        "equipped": {
            "hand": "oak_planks",
            "off-hand": null,
            "feet": null,
            "legs": null,
            "torso": null,
            "head": null
        },
        "surroundings": {
            "immediateSurroundings": {
                "visibleBlocks": {
                    "grass_block": [[39, 69, 132], [40, 69, 131], [41, 69, 131],
[41, 68, 132], [42, 69, 130], [42, 68, 131], [42, 67, 132], [42, 68, 133], [42, 68,
137], [43, 69, 130], [43, 68, 132], [43, 67, 133], [43, 68, 134], [44, 69, 130],
[44, 68, 133], [45, 69, 130], [46, 69, 130], [47, 68, 131], [48, 68, 132], [48, 68,
133]],
                    "birch_leaves": [[41, 72, 132], [41, 72, 133], [42, 72, 132],
[42, 72, 133], [43, 72, 133], [44, 72, 132], [44, 72, 133], [44, 72, 134], [45, 72,
132], [45, 72, 133]],
                    "oak_leaves": [[41, 72, 134], [41, 72, 135], [42, 72, 134], [42,
72, 135], [43, 71, 130], [43, 72, 131], [43, 72, 134], [43, 72, 135], [43, 72, 136],
[44, 71, 130], [44, 71, 131], [44, 72, 135], [44, 72, 136], [45, 72, 131], [46, 71,
131]],
                    "oak_log": [[42, 71, 136]],
                    "birch_log": [[43, 72, 132]]
                },
                "visibleBiomes": ["forest"],
                "visibleItems": {}
            },
            "distantSurroundings": {
                "up": {
                    "visibleBlockCounts": {
                        "oak_leaves": 17,
                        "birch_leaves": 5,
                        "grass_block": 1
                    },
                    "visibleBiomes": ["forest"],
                    "visibleItemCounts": {}
                },
                "down": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": [],
                    "visibleItemCounts": {}
                },
                "north": {
                    "visibleBlockCounts": {
                        "oak_leaves": 4,
                        "grass_block": 11,
                        "spruce_leaves": 9,
                        "dirt": 1,
                        "spruce_log": 1
                    },
                    "visibleBiomes": ["forest", "swamp", "windswept_forest",
"taiga"],
                    "visibleItemCounts": {}
                },
                "northeast": {
                    "visibleBlockCounts": {
                        "oak_leaves": 30,
                        "grass_block": 62,
                        "birch_leaves": 4,
                        "dirt": 11,
                        "oak_log": 1
                    },
                    "visibleBiomes": ["forest", "windswept_forest",
"windswept_hills"],
                    "visibleItemCounts": {}
                },
                "east": {
                    "visibleBlockCounts": {
                        "grass_block": 98,
                        "birch_leaves": 57,
                        "birch_log": 10,
                        "oak_leaves": 74,
                        "oak_log": 12
                    },
                    "visibleBiomes": ["forest"],
                    "visibleItemCounts": {}
                },
                "southeast": {
                    "visibleBlockCounts": {
                        "oak_leaves": 58,
                        "birch_leaves": 63,
                        "grass_block": 45,
                        "birch_log": 8,
                        "oak_log": 4
                    },
                    "visibleBiomes": ["forest"],
                    "visibleItemCounts": {}
                },
                "south": {
                    "visibleBlockCounts": {
                        "oak_leaves": 85,
                        "grass_block": 25,
                        "oak_log": 7,
                        "birch_leaves": 8,
                        "birch_log": 3,
                        "dirt": 2
                    },
                    "visibleBiomes": ["forest"],
                    "visibleItemCounts": {}
                },
                "southwest": {
                    "visibleBlockCounts": {
                        "oak_leaves": 84,
                        "birch_leaves": 18,
                        "birch_log": 3,
                        "grass_block": 2,
                        "oak_log": 2,
                        "dirt": 1
                    },
                    "visibleBiomes": ["forest"],
                    "visibleItemCounts": {}
                },
                "west": {
                    "visibleBlockCounts": {
                        "grass_block": 30,
                        "dirt": 11,
                        "oak_leaves": 32,
                        "oak_log": 3
                    },
                    "visibleBiomes": ["windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "northwest": {
                    "visibleBlockCounts": {
                        "grass_block": 106,
                        "oak_leaves": 2,
                        "dirt": 23,
                        "stone": 1
                    },
                    "visibleBiomes": ["windswept_forest", "taiga", "forest",
"swamp"],
                    "visibleItemCounts": {}
                }
            }
        }
    },
    "skillInvocationResults": null,
    "inventoryChanges": null
}"""

    user_prompt_input_data = UserPromptInputData(
        env_state=dummy_env_state,
        olthad=dummy_task.stringify(),
        task_in_question=dummy_task.stringify(),
    )

    docs = retrieve(3, user_prompt_input_data, LmAgentName.PLANNER)

    def extract_task(text):
        match = re.search(r'"task":\s*"([^"]*)"', text)
        if match:
            return match.group(1)
        else:
            return None

    print("Retrieved documents:")
    for doc in docs:
        doc = doc[doc.find("TASK IN QUESTION") :]
        print(f"Task: {extract_task(doc)}")
