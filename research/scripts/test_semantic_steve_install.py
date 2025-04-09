"""
Tests that semantic-steve was installed into site-packages and runs.
"""

import asyncio

from semantic_steve import SemanticSteve, run_as_cli

ss = SemanticSteve(should_rebuild_typescript=True, debug=True)
asyncio.run(run_as_cli(ss))
