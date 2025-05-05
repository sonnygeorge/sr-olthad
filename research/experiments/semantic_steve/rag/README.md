# rag

This directory contains a basic implementation of vectory-similarity retrieval of few-shot examples for the sr-OLTHAD system.

Here are the important files/directories to know about::

```python
...
 ┃ 📂 examples # The few-shot examples that are retrieved
 ┃  ┗ ...
 ┣ 📂 rag # This directory
 ┃  ┣ 📜 create_db.py  # Creates persistent vector db from ../examples
 ┃  ┣ 📜 embed.py  # Code for embedding documents
 ┃  ┣ 📜 retrieve.py  # Function that retrieve examples from db based on vector similarity
 ┃  ...
 ┣ 📜 get_prompt_input.py # Strategy passed to sr-OLTHAD to feed in SemanticSteve-specific information into the sr-OLTHAD prompts dynamically
...
```
