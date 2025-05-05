## TODO

### Planner

- Place onto ____ -> walk through the calculation of what position in onto _____.
- When the agent is by the oak leaves of a tree but view is cut off of oak logs inside leaves -> clear the leaves (`mineBlocks("oak_leaves", 12)`)

```text
{
    "envState": {
        "playerCoordinates": [188.5, 64, 302.5],
        "health": "20/20",
        "hunger": "20/20",
        "inventory": [{"name": "cobblestone", "count": 2}, {"name": "stone_pickaxe",
"count": 1}, {"name": "wooden_pickaxe", "count": 1, "durabilityRemaining": "76%"},
{"name": "birch_planks", "count": 3}, {"name": "crafting_table", "count": 1},
{"name": "dirt", "count": 3}],
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
                    "oak_leaves": [[185, 65, 301], [185, 66, 301], [186, 67, 300],
[186, 65, 301], [186, 66, 301], [187, 67, 300], [187, 68, 300], [187, 65, 301],
[187, 66, 301], [188, 67, 299], [188, 65, 301], [188, 66, 301], [189, 65, 298],
[189, 66, 298], [189, 65, 299], [189, 66, 299], [189, 65, 300], [189, 66, 300]],
                    "grass_block": [[189, 63, 301], [188, 63, 302], [186, 63, 302]]
                },
                "visibleBiomes": ["plains", "forest"],
                "visibleItems": {}
            },
            "distantSurroundings": {
                "up": {
                    "visibleBlockCounts": {
                        "oak_leaves": 3
                    },
                    "visibleBiomes": ["plains", "forest"],
                    "visibleItemCounts": {}
                },
                "down": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": ["plains", "forest"],
                    "visibleItemCounts": {}
                },
                "north": {
                    "visibleBlockCounts": {
                        "grass_block": 4,
                        "oak_leaves": 10
                    },
                    "visibleBiomes": ["plains", "forest"],
                    "visibleItemCounts": {}
                },
                "northeast": {
                    "visibleBlockCounts": {
                        "grass_block": 62,
                        "netherrack": 2
                    },
                    "visibleBiomes": ["plains"],
                    "visibleItemCounts": {}
                },
                "east": {
                    "visibleBlockCounts": {
                        "grass_block": 219
                    },
                    "visibleBiomes": ["plains"],
                    "visibleItemCounts": {}
                },
                "southeast": {
                    "visibleBlockCounts": {
                        "grass_block": 44
                    },
                    "visibleBiomes": ["plains"],
                    "visibleItemCounts": {}
                },
                "south": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": ["plains"],
                    "visibleItemCounts": {}
                },
                "southwest": {
                    "visibleBlockCounts": {
                        "grass_block": 3
                    },
                    "visibleBiomes": ["plains", "forest"],
                    "visibleItemCounts": {}
                },
                "west": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": ["plains", "forest"],
                    "visibleItemCounts": {}
                },
                "northwest": {
                    "visibleBlockCounts": {},
                    "visibleBiomes": ["plains", "forest"],
                    "visibleItemCounts": {}
                }
            }
        }
    },
    "skillInvocationResults": "You successfully placed 'oak_sapling' at coordinates
'186, 64, 302'.",
    "inventoryChanges": {
        "itemsAcquired": {},
        "itemsLostOrConsumed": {
            "oak_sapling": 1
        }
    }
}
```

- Always go to a clear area before placing tasks?
- pathfind to a clear area if struggling to place things on top of each other

```
{
     "id": "1",
     "task": "Take a screenshot of 2 different varieties of wood planks stacked on top of each other",
     "status": "In progress",
     "retrospective": null,
     "subtasks": [
        {
           "id": "1.1",
           "task": "Arrange two different varieties of wood planks stacked on top of each other",
           "status": "In progress",
           "retrospective": null,
           "subtasks": [
              {
                 "id": "1.1.1",
                 "task": "placeBlock('oak_planks')",
                 "status": "Attempted (success)",
                 "retrospective": "The oak plank block was successfully placed at coordinates [157, 71, 167]. The block appears in the immediate surroundings, and one oak plank was correctly consumed from inventory. This sets up the base for stacking the second type of wood on top. No problems encountered.",
                 "subtasks": null
              },
              {
                 "id": "1.1.2",
                 "task": "placeBlock('birch_planks')",
                 "status": "Attempted (success)",
                 "retrospective": "The birch plank block was successfully placed at coordinates [157, 71, 169], and the block appears in the immediate surroundings at that location. One birch plank was correctly consumed from inventory. Note that, while the placement succeeded, the birch plank is not directly stacked on top of the previously placed oak plank (which is at [157, 71, 167]), so further adjustment may be required in future steps to achieve a vertical stack.",
                 "subtasks": null
              },
              {
                 "id": "1.1.3",
                 "task": "Remove any incorrectly placed plank blocks to clear vertical space for stacking",
                 "status": "Attempted (success)",
                 "retrospective": "The required birch plank block was successfully removed to clear vertical space for stacking. No incorrectly placed plank blocks remain in the relevant area, and inventory increased by one birch plank.",
                 "subtasks": null
              },
              {
                 "id": "1.1.4",
                 "task": "Place two wood planks of different varieties so that one is directly stacked on top of the other",
                 "status": "In progress",
                 "retrospective": null,
                 "subtasks": [
                    {
                       "id": "1.1.4.1",
                       "task": "placeBlock('oak_planks')",
                       "status": "Attempted (success)",
                       "retrospective": "The oak plank block was successfully placed at coordinates [156, 71, 168], and one was consumed from inventory. However, there is a birch_log directly above at [156, 72, 168], which blocks immediate placement of another plank on top for stacking. For stacking two wood plank varieties vertically at this location, the birch_log will need to be removed before placing the second plank.",
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.2",
                       "task": "mineBlocks('birch_log', 1)",
                       "status": "Attempted (success)",
                       "retrospective": "The birch log above the placed oak plank at [156, 71, 168] was successfully mined and removed, as confirmed by its absence in the immediate surroundings and the addition of two birch logs to inventory. A single stick and a piece of dirt were also acquired/lost, likely as incidental drops/blocks during the process. The vertical space at [156, 72, 168] now appears clear and ready for stacking the birch plank as intended.",
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.3",
                       "task": "placeBlock('birch_planks', [156, 72, 168])",
                       "status": "Attempted (failure)",
                       "retrospective": "The attempt to place a birch plank at [156, 72, 168] failed with a SkillInvocationError: 'The coordinates 156, 72, 168 are not placeable. Please call getPlaceableCoordinates and try again with placeable coordinates.' No birch planks were consumed, and the block was not placed. This suggests the target location was not valid for placement\u2014possibly due to environmental constraints or Minecraft's rules for block support. In the future, ensure that the target coordinates are placeable (e.g., use getPlaceableCoordinates) before attempting to stack blocks.",
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.4",
                       "task": "getPlaceableCoordinates()",
                       "status": "Attempted (success)",
                       "retrospective": "Successfully retrieved the coordinates at which a block can currently be placed. The following placeable coordinates were returned: [[157, 70, 169], [158, 70, 168], [158, 70, 167], [158, 70, 169], [158, 71, 170], [159, 70, 168], [159, 70, 167], [159, 70, 169], [158, 70, 171], [159, 70, 170]]. This information will allow selection of an appropriate location for stacking the birch plank above the oak plank. No issues encountered.",
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.5",
                       "task": "placeBlock('birch_planks', [best_valid_coordinate_for_stack])",
                       "status": "Attempted (failure)",
                       "retrospective": "The attempt to place a birch plank block failed due to a SkillRuntimeError: the placement coordinates provided were not integers, which caused the function to reject the action ('Cubed meter coords must be integers'). As a result, the birch plank was not placed, no inventory was consumed, and no progress was made towards stacking wood planks. For future attempts, always ensure the coordinates provided for block placement are valid integers and correspond to a location where stacking is physically possible (use getPlaceableCoordinates and carefully select a valid spot directly above the first plank).",
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.6",
                       "task": "Determine valid coordinates for stacking by retrieving placeable coordinates and filtering for vertically-adjacent pairs where stacking is possible",
                       "status": "In progress",
                       "retrospective": null,
                       "subtasks": [
                          {
                             "id": "1.1.4.6.1",
                             "task": "Identify a pair of vertically adjacent placeable coordinates for stacking blocks",
                             "status": "In progress",
                             "retrospective": null,
                             "subtasks": [
                                {
                                   "id": "1.1.4.6.1.1",
                                   "task": "Analyze the list of available placeable coordinates to find a pair of integer locations where one is directly above the other",
                                   "status": "In progress",
                                   "retrospective": null,
                                   "subtasks": [
                                      {
                                         "id": "1.1.4.6.1.1.1",
                                         "task": "Identify a pair of vertically adjacent placeable coordinates suitable for stacking blocks",
                                         "status": "In progress",
                                         "retrospective": null,
                                         "subtasks": null
                                      }
                                   ]
                                }
                             ]
                          }
                       ]
                    },
                    {
                       "id": "1.1.4.7",
                       "task": "placeBlock('oak_planks', [lower_valid_coordinate])",
                       "status": "Tentatively planned",
                       "retrospective": null,
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.8",
                       "task": "Retrieve placeable coordinates again and placeBlock('birch_planks', [upper_valid_coordinate_directly_above])",
                       "status": "Tentatively planned",
                       "retrospective": null,
                       "subtasks": null
                    },
                    {
                       "id": "1.1.4.9",
                       "task": "Repeat the coordinate selection and block placement process with other pairs if stacking fails",
                       "status": "Tentatively planned",
                       "retrospective": null,
                       "subtasks": null
                    }
                 ]
              }
           ]
        },
        {
           "id": "1.2",
           "task": "Take a screenshot of the stacked wood planks",
           "status": "Tentatively planned",
           "retrospective": null,
           "subtasks": null
        }
     ]
  }
```

### Exhaustive Effort Classifier

- False positives on root are deadly! E.g. (classified as exhaustive right before screenshot-taking):

```
  {
     "id": "1",
     "task": "take a screenshot of smooth stone placed on top of a furnace",
-    "status": "In progress",
-    "retrospective": null,
+    "status": "Attempted (failure)",
+    "retrospective": "Although all prerequisites were completed and the structure is built as described, the required screenshot has not been taken. The ultimate goal remains unfulfilled.",
     "subtasks": [
        {
           "id": "1.1",
           "task": "Obtain a furnace",
           "status": "Attempted (success)",
           "retrospective": "A furnace was successfully crafted and now exists in the inventory, as required by the task. Previous setbacks were overcome and the final subtask was completed without issue.",
           "subtasks": null
        },
        {
           "id": "1.2",
           "task": "Obtain a furnace",
           "status": "Attempted (success)",
           "retrospective": "A furnace has been crafted and is present in the inventory. The immediate goal of obtaining a furnace is therefore complete.",
           "subtasks": null
        },
        {
           "id": "1.3",
           "task": "Obtain a furnace",
           "status": "Attempted (success)",
           "retrospective": "A furnace has been acquired and is present in the inventory. The task to obtain a furnace is therefore fulfilled.",
           "subtasks": null
        },
        {
           "id": "1.4",
           "task": "Obtain one smooth stone block",
           "status": "Attempted (success)",
           "retrospective": "A smooth stone block has been produced via smelting and is present in the inventory, fulfilling the requirement to obtain one smooth stone block.",
           "subtasks": null
        },
        {
           "id": "1.5",
           "task": "Place the furnace",
           "status": "Attempted (success)",
           "retrospective": "The furnace was successfully placed at the intended coordinates, is now present in the surroundings, and is no longer in the inventory. The requirements of the task have been definitively fulfilled.",
           "subtasks": null
        },
        {
           "id": "1.6",
           "task": "Place smooth stone block on top of the furnace",
           "status": "Attempted (success)",
           "retrospective": "The smooth stone block was successfully placed directly on top of the furnace as specified. The inventory and environment state both confirm correct placement, leaving no remaining requirements for this task.",
           "subtasks": null
        },
        {
           "id": "1.7",
           "task": "Take a screenshot of the placed smooth stone on top of the furnace",
           "status": "Tentatively planned",
           "retrospective": null,
           "subtasks": null
        }
     ]
  }
```
