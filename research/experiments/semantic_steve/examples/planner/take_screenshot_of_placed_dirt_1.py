from research.experiments.semantic_steve.rag.schema import PlannerExample
from sr_olthad import UserPromptInputData
from sr_olthad.olthad import TaskNode, TaskStatus
from sr_olthad.prompts import PlannerLmResponseOutputData

ENV_STATE = """{
    "envState": {
        "playerCoordinates": [...],
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
                "visibleBlocks": {...},
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
    "inventoryChanges": ...
}"""

OLTHAD = TaskNode(
    _id="1",
    _task="Take a screenshot of some dirt that you placed.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _parent_id=None,
    _non_planned_subtasks=[],
    _planned_subtasks=[],
)

TASK_IN_QUESTION = OLTHAD

NEW_PLANNED_SUBTASKS = ["Place some dirt", "Take a screenshot of the placed dirt"]

OUTPUT = PlannerLmResponseOutputData(new_planned_subtasks=NEW_PLANNED_SUBTASKS)

REASONING = """The task "Take a screenshot of some dirt that you placed" is the highest level task with id "1". Therefore, it is user-requested.
Considering this aspect, that a human user is requesting this of me, I will consider what necessary immediate steps would best fulfill what my user is wanting.
Another important aspect to consider is that there are no subtasks planned, so this will be the first time I am considering potential subtasks for this task.
It is clear that the user wants me to place dirt, and then take a screenshot of it. Given that these two things must occur to complete the task, it best to plan them as the subtasks.
Then, in future planning steps, I can break down and work on these subtasks further."""

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
