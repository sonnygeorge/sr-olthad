from research.experiments.semantic_steve.rag.schema import PlannerExample
from sr_olthad import UserPromptInputData
from sr_olthad.olthad import TaskNode, TaskStatus
from sr_olthad.prompts import PlannerLmResponseOutputData

ENV_STATE = """{
    "envState": {
        "playerCoordinates": [42.5, 70, 131.4],
        "health": "20/20",
        "hunger": "20/20",
        "inventory": [{"name": "oak_log", "count": 4}, {"name": "stick", "count": 16}, {"name": "wooden_axe", "count": 1}, {"name": "birch_planks", "count": 2}, {"name": "crafting_table", "count": 1}, {"name": "oak_planks", "count": 6}, {"name": "wooden_pickaxe", "count": 1, "durabilityRemaining": "98%"}],
        "equipped": {
            "hand": "birch_planks",
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
                    "oak_leaves": [...],
                    "birch_leaves": [...],
                },
                "visibleBiomes": ["swamp", "windswept_forest", "taiga", "forest"],
                "visibleItems": {}
            },
            "distantSurroundings": {
                "up": {
                    "visibleBlockCounts": {
                        "oak_leaves": 15,
                        "birch_leaves": 5
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "down": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": ["windswept_forest", "swamp", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "north": {
                    "visibleBlockCounts": {
                        "oak_leaves": 31,
                        "grass_block": 80,
                        "spruce_leaves": 32,
                        "dirt": 6
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "northeast": {
                    "visibleBlockCounts": {
                        "oak_leaves": 6,
                        "grass_block": 50
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "east": {
                    "visibleBlockCounts": {
                        "oak_leaves": 9,
                        "birch_leaves": 6,
                        "grass_block": 8
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "forest", "taiga"],
                    "visibleItemCounts": {}
                },
                "southeast": {
                    "visibleBlockCounts": {
                        "birch_leaves": 15,
                        "oak_leaves": 1
                    },
                    "visibleBiomes": ["windswept_forest", "swamp", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "south": {
                    "visibleBlockCounts": {
                        "oak_leaves": 3,
                        "grass_block": 1
                    },
                    "visibleBiomes": ["windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                },
                "southwest": {
                    "visibleBlockCounts": {
                        "oak_leaves": 27,
                        "birch_leaves": 6,
                        "grass_block": 5
                    },
                    "visibleBiomes": ["windswept_forest", "swamp", "forest", "taiga"],
                    "visibleItemCounts": {}
                },
                "west": {
                    "visibleBlockCounts": {
                        "grass_block": 75,
                        "dirt": 29,
                        "oak_leaves": 20
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "forest", "taiga"],
                    "visibleItemCounts": {}
                },
                "northwest": {
                    "visibleBlockCounts": {
                        "grass_block": 159,
                        "dirt": 7
                    },
                    "visibleBiomes": ["swamp", "windswept_forest", "taiga", "forest"],
                    "visibleItemCounts": {}
                }
            }
        }
    },
    "skillInvocationResults": ...,
    "inventoryChanges": {...}
}"""


TASK_IN_QUESTION = TaskNode(
    _id="1.2.1",
    _task="Dig down to obtain cobblestone for a stone pickaxe.",
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
        TaskNode(
            _id="1.1",
            _task="Obtain wood and necessary wood tools.",
            _status=TaskStatus.SUCCESS,
            _retrospective="I obtained a small supply of wood as well as a wooden axe and pickaxe.",
            _parent_id=None,
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
        TaskNode(
            _id="1.2",
            _task="Obtain 9 iron bars.",
            _status=TaskStatus.IN_PROGRESS,
            _retrospective=None,
            _parent_id=None,
            _non_planned_subtasks=[
                TASK_IN_QUESTION,
            ],
            _planned_subtasks=[],
        ),
    ],
    _planned_subtasks=[
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

NEW_PLANNED_SUBTASKS = [
    "pathfindToCoordinates([48.5, 64, 131.4], ['stone', 'coal_ore', 'iron_ore'])"
]

OUTPUT = PlannerLmResponseOutputData(new_planned_subtasks=NEW_PLANNED_SUBTASKS)

REASONING = """The task in question is "Dig down to obtain cobblestone for a stone pickaxe". I am currently at [42.5, 70, 131.4] and have a wooden pickaxe with 98% durability remaining.
With SemanticSteve skill functions, the best way to to dig down is to pathfind to coordinates that are below me ()'pathfindToCoordinates' will dig through the impeding block)s.
In Minecraft, digging down is safest when moving downward at a diagonal (avoiding digging straight down). Therefore, I will add 6 to my x-coordinate and subtract 6 from the y-coordinate to get target coordinates of [48.5, 64, 131.4] that will create a diagonally downward pathfinding trajectory.
Let's pathfinding to these coordinates, stopping early if I uncover stone, coal ore, or iron ore.
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
