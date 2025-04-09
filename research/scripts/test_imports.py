"""Tests imports w/ the current the project structure."""

import openai

import research.eval_harness
import research.experiments
import research.other_methods
from sr_olthad import SrOlthad

print(openai, research.experiments, research.eval_harness, research.other_methods, SrOlthad)
