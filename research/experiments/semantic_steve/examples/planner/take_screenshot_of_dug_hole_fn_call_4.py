from research.experiments.semantic_steve.rag.schema import PlannerExample
from sr_olthad import UserPromptInputData
from sr_olthad.olthad import TaskNode, TaskStatus
from sr_olthad.prompts import PlannerLmResponseOutputData

ENV_STATE = """{
    "envState": {
        "playerCoordinates": [22.3, 64, 166.3],
        "health": "20/20",
        "hunger": "20/20",
        "inventory": [{"name": "dirt", "count": 1}],
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
                    "grass_block": [[18, 63, 164], [18, 63, 165], [18, 63, 166], [18, 63, 167], [18, 63, 168], [19, 63, 163], [19, 63, 164], [19, 63, 165], [19, 63, 166], [19, 63, 167], [19, 63, 168], [19, 63, 169], [20, 63, 162], [20, 63, 163], [20, 63, 164], [20, 63, 165], [20, 63, 166], [20, 63, 167], [20, 63, 168], [20, 63, 169], [20, 63, 170], [21, 63, 162], [21, 63, 163], [21, 63, 164], [21, 63, 166], [21, 63, 167], [21, 63, 168], [21, 63, 169], [21, 63, 170], [22, 63, 162], [22, 63, 163], [22, 63, 164], [22, 63, 165], [22, 63, 166], [22, 63, 167], [22, 63, 168], [22, 63, 169], [22, 63, 170], [22, 63, 171], [23, 63, 162], [23, 63, 163], [23, 63, 164], [23, 63, 165], [23, 63, 166], [23, 63, 167], [23, 63, 168], [23, 63, 169], [23, 63, 170], [24, 63, 162], [24, 63, 163], [24, 63, 164], [24, 63, 165], [24, 63, 166], [24, 63, 167], [24, 63, 168], [24, 63, 169], [24, 63, 170], [25, 63, 163], [25, 63, 164], [25, 63, 165], [25, 63, 166], [25, 63, 167], [25, 63, 168], [25, 63, 169], [25, 63, 170], [26, 63, 164], [26, 63, 165], [26, 63, 166], [26, 63, 167], [26, 63, 168], [26, 63, 169], [27, 63, 166], [21, 62, 165]]
                },
                "visibleBiomes": [...],
                "visibleItems": {}
            },
            "distantSurroundings": {
                "up": {...},
                "down": {...},
                "north": {...},
                ...
            }
        }
    },
    "skillInvocationResults": "You were able to successfully pathfind to or near [22, 64, 166] such that these coordinates are now in your immediate surroundings.",
    "inventoryChanges": {...}
}"""


OLTHAD = TaskNode(
    _id="1",
    _task="Take a screenshot of a hole that you dug out of the ground.",
    _status="In progress",
    _retrospective=None,
    _parent_id=None,
    _non_planned_subtasks=[
        TaskNode(
            _id="1.1",
            _task="Navigate to a flat area to allow my dug hole to visually stand out from an otherwise topologically flat backdrop.",
            _status=TaskStatus.SUCCESS,
            _retrospective="After navigating around for some time, I reached [21, 64, 165.3] and verified that where I was standing was indeed flat, since all visible blocks in the immediate surroundings were at the same y-level of 63.",
            _parent_id="1.1",
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
        TaskNode(
            _id="1.2",
            _task='mineBlocks("grass_block", 1)',
            _status=TaskStatus.SUCCESS,
            _retrospective="I successfully mined 1 grass block and am now at [21.5, 63, 165.5]. Since I was previously at [21, 64, 165.3], it appears I am now a block lower than before, suggesting that I may be inside the resulting 1-block hole.",
            _parent_id="1.2",
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
        TaskNode(
            _id="1.3",
            _task="Pathfind to a vantage point that will allow me to confirm the location of the hole and take a top-down screenshot of it.",
            _status=TaskStatus.SUCCESS,
            _retrospective="Hoping to go east by one block and up by one block (and presumably arrive at the rim of the hole), I attempted to pathfind to [22, 64, 166] and wound up at [22.3, 64, 166.3]. From here, all visible blocks in the immediate surroundings are at y-level 63 except for the block at [21, 62, 165].",
            _parent_id="1",
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        ),
    ],
    _planned_subtasks=[],
)

TASK_IN_QUESTION = OLTHAD

NEW_PLANNED_SUBTASKS = ["takeScreenshotOf('grass_block', [21, 62, 165])"]

OUTPUT = PlannerLmResponseOutputData(new_planned_subtasks=NEW_PLANNED_SUBTASKS)

REASONING = """The task in question is the highest-level (user-requested) task, "Take a screenshot of a hole that you dug out of the ground". Given previous tasks 1.1 and 1.2, I know that I removed a single grass block in an otherwise flat area. In task 1.3, I pathfound to where I am now at [22.3, 64, 166.3], which is presumably near the rim of the hole left by my removal of the single grass block.
Since all visible blocks in the immediate surroundings are at y-level 63 except for the block at [21, 62, 165], the 'grass_block' at [21, 62, 165] can be described as the block at the bottom of a 1-block hole where the walls are the 'grass_block's at [21, 63, 164] (north wall), [22, 63, 165] (east wall), [21, 63, 166] (south wall), and [20, 63, 165] (west wall).
Since, (1) before mining the grass block in task 1.2, the area was observed to be flat such that all visible blocks in the immediate surroundings were at y-level 63, and, (2) after mining the grass block in task 1.2, this continues to be true except for the block at [21, 62, 165], I can conclude that this hole, whose bottom block is at [21, 62, 165], was dug by me.
Since I know this, the next logical step is to try and take a screenshot of the hole. Since I am standing at [22.3, 64, 166.3], and can see down into the hole's bottom at [21, 62, 165], I am in a good position to take a top-down screenshot of the hole (looking down into it).
The skill function 'takeScreenshotOf' exists and allows me to, from my vantage point, take a screenshot of something at specified coordinates, assuming the thing exists and is visible in the immediate surroundings. Since the bottom of the hole I dug is visible in the immediate surroundings ('grass_block' at [21, 62, 165]), I can take a screenshot of it and, since my vantage point (position at [22.3, 64, 166.3]) is from above, doing so should result in a screenshot that is a top-down view of (into) the hole.
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
