from research.experiments.semantic_steve.rag.schema import PlannerExample
from sr_olthad import UserPromptInputData
from sr_olthad.olthad import TaskNode, TaskStatus
from sr_olthad.prompts import PlannerLmResponseOutputData

ENV_STATE = """{
    "envState": {
        "playerCoordinates": [30.3, 82, 116.2],
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
                    "grass_block": [...],
                    "dirt": [...],
                },
                "visibleBiomes": ["swamp"],
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
                        "grass_block": 15
                    },
                    "visibleBiomes": ["windswept_forest", "swamp"],
                    "visibleItemCounts": {}
                },
                "north": {
                    "visibleBlockCounts": {
                        "grass_block": 9,
                        "dirt": 4
                    },
                    "visibleBiomes": ["swamp"],
                    "visibleItemCounts": {}
                },
                "northeast": {
                    "visibleBlockCounts": {
                        "dirt": 12,
                        "grass_block": 21,
                        "oak_leaves": 15,
                        "spruce_leaves": 4
                    },
                    "visibleBiomes": ["swamp", "windswept_forest"],
                    "visibleItemCounts": {}
                },
                "east": {
                    "visibleBlockCounts": {
                        "grass_block": 150,
                        "oak_leaves": 54,
                        "oak_log": 3,
                        "spruce_leaves": 7,
                        "dirt": 5
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "forest"],
                    "visibleItemCounts": {}
                },
                "southeast": {
                    "visibleBlockCounts": {
                        "grass_block": 99,
                        "spruce_leaves": 32,
                        "oak_leaves": 40,
                        "birch_leaves": 39,
                        "birch_log": 2,
                        "oak_log": 5
                    },
                    "visibleBiomes": ["windswept_forest", "swamp", "taiga"],
                    "visibleItemCounts": {}
                },
                "south": {
                    "visibleBlockCounts": {
                        "grass_block": 91,
                        "dirt": 4,
                        "oak_leaves": 43,
                        "oak_log": 3,
                        "birch_leaves": 6
                    },
                    "visibleBiomes": ["windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "southwest": {
                    "visibleBlockCounts": {
                        "dirt": 114,
                        "grass_block": 81,
                    },
                    "visibleBiomes": ["windswept_forest", "swamp", "forest"],
                    "visibleItemCounts": {}
                },
                "west": {
                    "visibleBlockCounts": {
                        "grass_block": 91,
                    },
                    "visibleBiomes": ["swamp"],
                    "visibleItemCounts": {}
                },
                "northwest": {
                    "visibleBlockCounts": {
                        "grass_block": 12,
                        "dirt": 18
                    },
                    "visibleBiomes": ["swamp"],
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
    _task="Obtain wood and necessary wood tools.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _parent_id=None,
    _non_planned_subtasks=[],
    _planned_subtasks=[],
)


OLTHAD = TaskNode(
    _id="1",
    _task="Take a screenshot of an iron block.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _parent_id=None,
    _non_planned_subtasks=[
        TASK_IN_QUESTION,
    ],
    _planned_subtasks=[
        TaskNode(
            _id="1.2",
            _task="Obtain 9 iron bars.",
            _status=TaskStatus.PLANNED,
            _retrospective=None,
            _parent_id=None,
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
        TaskNode(
            _id="1.3",
            _task="Craft an iron block.",
            _status=TaskStatus.PLANNED,
            _retrospective=None,
            _parent_id=None,
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
        TaskNode(
            _id="1.4",
            _task="Take a screenshot of the crafted iron block.",
            _status=TaskStatus.PLANNED,
            _retrospective=None,
            _parent_id=None,
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
    ],
)

NEW_PLANNED_SUBTASKS = ["approach('oak_log', 'southeast', ['stone', 'iron_ore'])"]

OUTPUT = PlannerLmResponseOutputData(new_planned_subtasks=NEW_PLANNED_SUBTASKS)

REASONING = """The task in question is, "Obtain wood and necessary wood tools." We can infer based on context that the "necessary wood tools" refers to wood tools that would be necessary or otherwise helpful in the process of obtaining an iron block. Therefore, we can consider this to include at least: logs, sticks, a crafting table, and a wooden pickaxe.
There is neither wood in the inventory or wood that we can collect in the immediate surroundings. However, we can see logs in the east, southeast, and south directions of the distant surroundings, with southeast having the most (5 oak and 2 birch). Regardless of any other plan details, I will always want to approach logs in a promising direction. Therefore, the best next-most skill call is disambiguated and, thus, should be the next planned subtask: approach the oak logs in the southeast direction, stopping if I happen to see a stone or iron ore block, in which case, I will want to make note of this information for stone/iron collection later on.
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
