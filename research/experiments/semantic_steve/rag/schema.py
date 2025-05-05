import json

from pydantic import BaseModel

from sr_olthad import UserPromptInputData
from sr_olthad.prompts import PlannerLmResponseOutputData


class PlannerExample(BaseModel):
    prompt_input_data: UserPromptInputData
    example_reasoning: str | None = None
    example_lm_output_data: PlannerLmResponseOutputData

    def stringify_for_prompt_insertion(self):
        # TODO
        out_str = "ENVIRONMENT STATE:\n"
        out_str += f"```json\n{self.prompt_input_data.env_state}\n```\n"
        out_str += "ONGOING PROGRESS/PLANS:\n"
        out_str += f"```json\n{self.prompt_input_data.olthad}\n```\n"
        out_str += "TASK IN QUESTION:\n"
        out_str += f"```json\n{self.prompt_input_data.task_in_question}\n```\n"
        out_str += "RESPONSE:\n"
        out_str += f"{self.example_reasoning}\n"
        out_str += f"```json\n{json.dumps(self.example_lm_output_data.model_dump())}\n```"
        return out_str
