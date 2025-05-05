from research.experiments.semantic_steve.rag.schema import PlannerExample
from sr_olthad import UserPromptInputData
from sr_olthad.olthad import TaskNode, TaskStatus
from sr_olthad.prompts import PlannerLmResponseOutputData

ENV_STATE = """{
    "envState": {
        "playerCoordinates": [541, 64, -209.2],
        "health": "20/20",
        "hunger": "20/20",
        "inventory": [...],
        "equipped": {
            "hand": ...,
            "off-hand": ...,
            "feet": ...,
            "legs": ...,
            "torso": ...,
            "head": ...
        },
        "surroundings": {
            "immediateSurroundings": {
                "visibleBlocks": {
                    cobblestone: [[543, 65, -209]],
                    ...
                },
                "visibleBiomes": [...],
                "visibleItems": {...}
            },
            "distantSurroundings": {
                "up": {...},
                "down": {...},
                "north": {...},
                ...
            }
        }
    },
    "skillInvocationResults": ...,
    "inventoryChanges": {...}
}"""

OLTHAD = TaskNode(
    _id="1",
    _task="Take a screenshot of cobblestone that you placed.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _parent_id=None,
    _non_planned_subtasks=[
        TaskNode(
            _id="1.1",
            _task="Place cobblestone",
            _status=TaskStatus.SUCCESS,
            _retrospective="I successfully placed cobblestone at [543, 65, -209].",
            _parent_id="1",
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
    ],
    _planned_subtasks=[
        TaskNode(
            _id="1.2",
            _task="Take a screenshot of the placed cobblestone",
            _status=TaskStatus.PLANNED,
            _retrospective=None,
            _parent_id="1",
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
    ],
)

TASK_IN_QUESTION = OLTHAD

NEW_PLANNED_SUBTASKS = ["takeScreenshot('cobblestone', [543, 65, -209])"]

OUTPUT = PlannerLmResponseOutputData(new_planned_subtasks=NEW_PLANNED_SUBTASKS)

REASONING = """The (user-requested) task we are considering a subtask plan for is "Take a screenshot of cobblestone that you placed". In task 1.1, I successfully placed cobblestone at [543, 65, -209]. This is confirmed by the fact that there is indeed cobblestone visible in the immediate surroundings at these coordinates. Since the placed cobblestone is visible, in the immediate surroundings, and my vantage point from [541, 64, -209.2] should be fine for capturing an adequate screenshot, all preconditions are in place for calling 'takeScreenshotOf'. Therefore, the next planned subtask can be the skill function call."""

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
