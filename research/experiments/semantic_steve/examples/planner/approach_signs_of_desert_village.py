from research.experiments.semantic_steve.rag.schema import PlannerExample
from sr_olthad import UserPromptInputData
from sr_olthad.olthad import TaskNode, TaskStatus
from sr_olthad.prompts import PlannerLmResponseOutputData

ENV_STATE = """{
    "envState": {
        "playerCoordinates": [144.9, 70, 142.7],
        "health": "20/20",
        "hunger": "20/20",
        "inventory": [],
        "equipped": {
            "hand": null,
            "off-hand": null,
            "feet": null,
            "legs": null,
            "torso": null,
            "head": null
        },
        "surroundings": {
            "immediateSurroundings": {
                "visibleBlocks": {
                    "sand": [...],
                },
                "visibleBiomes": ["desert"],
                "visibleItems": {}
            },
            "distantSurroundings": {
                "up": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": [],
                    "visibleItemCounts": {}
                },
                "down": {
                    "visibleBlockCounts": {
                        "sand": 2
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "north": {
                    "visibleBlockCounts": {
                        "sand": 287
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "northeast": {
                    "visibleBlockCounts": {
                        "sand": 204,
                        "cactus": 3,
                        "sandstone": 4
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "east": {
                    "visibleBlockCounts": {
                        "sand": 285,
                        "cactus": 1
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "southeast": {
                    "visibleBlockCounts": {
                        "sand": 200
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "south": {
                    "visibleBlockCounts": {
                        "sand": 72,
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "southwest": {
                    "visibleBlockCounts": {
                        "sand": 9,
                        "terracotta": 7,
                        "smooth_sandstone": 5,
                        "sandstone_slab": 6,
                        "smooth_sandstone_slab": 5
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "west": {
                    "visibleBlockCounts": {
                        "sand": 127
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                },
                "northwest": {
                    "visibleBlockCounts": {
                        "sand": 306
                    },
                    "visibleBiomes": ["desert"],
                    "visibleItemCounts": {}
                }
            }
        }
    },
    "skillInvocationResults": null,
    "inventoryChanges": null
}"""

TASK_IN_QUESTION = TaskNode(
    _id="1.1",
    _task="Explore until a viable food source is identified.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _parent_id="1.1",
    _non_planned_subtasks=[],
    _planned_subtasks=[],
)


OLTHAD = TaskNode(
    _id="1",
    _task="Acquire food.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _parent_id=None,
    _non_planned_subtasks=[
        TASK_IN_QUESTION,
    ],
    _planned_subtasks=[],
)

NEW_PLANNED_SUBTASKS = [
    "approach('smooth_sandstone_slab', 'southwest', ['hay_block', 'chest'])"
]

OUTPUT = PlannerLmResponseOutputData(new_planned_subtasks=NEW_PLANNED_SUBTASKS)

REASONING = """The task in question is, "Explore until a viable food source is identified." In this regard, the southwest direction of the distant surroundings stands out. In this direction, we see blocks like "smooth_sandstone", "sandstone_slab", "smooth_sandstone_slab", and "terracotta". These blocks suggest the existence of a structure, especially the slabs, which wouldn't generate naturally in absence of a structure.
Since this direction could therefore have a village, I will plan to approach one of its "smooth_sandstone_slab" blocks, stopping early if I find a "hay_block" or "chest", which are both potential sources of food in a village.
"""

EXAMPLE = PlannerExample(
    prompt_input_data=UserPromptInputData(
        env_state=ENV_STATE,
        olthad=OLTHAD.stringify(),
        task_in_question=TASK_IN_QUESTION.stringify(),
    ),
    example_reasoning=REASONING,
    example_lm_output_data=OUTPUT,
)

if __name__ == "__main__":
    print(EXAMPLE.stringify_for_prompt_insertion())
