<!--
TODO: Finish basic implementation of sr-OLTHAD
TODO: Add m-coding style logging
TODO: Build a GUI app to step through sr-OLTHAD LM-calls w/ a "next" button (w/ a more human-readable plan string?) (and simulate environment)
TODO: Ranking of multiple async "Planner" outputs?
TODO: Annotation GUI?
TODO: RAG of SemanticSteve tutorials?
-->

```python
📦sr-olthad
 ┣ 📂src
 ┃ ┣ 📂agent_framework # Package for generic agent framework
 ┃ ┃ ┣ 📂agents # Package for generic plug-and-play agents
 ┃ ┃ ┃ ┗ 📜single_turn_chat.py
 ┃ ┃ ┣ 📜lms.py # Module (soon-to-be package) for a variety of LMs
 ┃ ┃ ┣ 📜schema.py
 ┃ ┃ ┗ 📜utils.py
 ┃ ┗ 📂sr_olthad # Package sr-OLTHAD
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
 ┃   ┣ 📂olthad # Package for OLTHAD stuff: TaskNode, traversal, etc.
 ┃   ┃ ┃ ┗ ...
 ┃   ┣ 📜config.py
 ┃   ┣ 📜schema.py
 ┃   ┣ 📜sr_olthad.py # Main sr-OLTHAD class imported externally
 ┃   ┗ 📜utils.py
 ┣ 📜quick_tests.py  # Ad-hoc testing scripts
 ┗ 📜requirements.txt
 ```
