import os

from research.utils import to_lower_snake_case
from sr_olthad import LmAgentName

EMBEDDING_WEIGHTS = {
    "env_state": 0.5,
    "olthad": 0.3,
    "task_in_question": 0.2,
}
PATH_TO_HERE = os.path.dirname(os.path.abspath(__file__))
PATH_TO_EXAMPLES_DIR = os.path.join(PATH_TO_HERE, "../", "examples")
PATHS_TO_EXAMPLE_DIRS_BY_AGENT = {
    name: os.path.join(PATH_TO_EXAMPLES_DIR, to_lower_snake_case(name))
    for name in LmAgentName
}
PATH_TO_VECTOR_DB = os.path.join(PATH_TO_EXAMPLES_DIR, "vector_db")
