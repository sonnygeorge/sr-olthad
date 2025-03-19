<!--
TODO: Solve problem of LM Response Text Boxes Not clearing on GUI reject + update top right & bottom right labels
TODO: Get rid of Agent ABC (bruh there's no point lol)
TODO: Make prepare messages be a util and make SingleTurnChatAgent take a user message (and make other contexts render their own templates)
TODO: Rename "GUI" to "dashboard"?
TODO: Add m-coding style logging
TODO: Build a GUI app to step through sr-OLTHAD LM-calls w/ a "next" button (w/ a more human-readable plan string?) (and simulate environment)
TODO: Ranking of multiple async "Planner" outputs?
TODO: Annotation GUI?
TODO: RAG of SemanticSteve tutorials?
-->

# sr-OLTHAD

Structured Reasoning with Open-Language Hierarchies of Any Depth

```python
📦sr-olthad
 ┣ 📂src
 ┃ ┣ 📂agent_framework # Package for generic agent framework
 ┃ ┃ ┣ 📂agents # Package for generic plug-and-play agents
 ┃ ┃ ┃ ┗ 📜single_turn_chat.py
 ┃ ┃ ┣ 📜lms.py # Module (soon-to-be package) for a variety of LMs
 ┃ ┃ ┣ 📜schema.py
 ┃ ┃ ┗ 📜utils.py
 ┃ ┣ 📂gui
 ┃ ┗ 📂sr_olthad # Package for sr-OLTHAD
 ┃   ┣ 📂agents # Package for the 4(?) main agents of sr-OLTHAD
 ┃   ┃ ┣ 📂attempt_summarizer
 ┃   ┃ ┃ ┗ ...
 ┃   ┃ ┣ 📂backtracker
 ┃   ┃ ┃ ┗ ...
 ┃   ┃ ┣ 📂forgetter
 ┃   ┃ ┃ ┗ ...
 ┃   ┃ ┣ 📂planner
 ┃   ┃ ┃ ┗ ...
 ┃   ┃ ┗ ...
 ┃   ┣ 📜config.py
 ┃   ┣ 📜schema.py
 ┃   ┣ 📜sr_olthad.py # Main sr-OLTHAD class that outer contexts import
 ┃   ┣ 📜task_node.py
 ┃   ┗ 📜utils.py
 ┣ 📜quick_tests.py # Ad-hoc testing scripts
 ┣ 📜run_gui.py
 ┗ 📜requirements.txt
```
