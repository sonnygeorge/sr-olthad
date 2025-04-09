from sr_olthad.config import PlannerCfg as cfg
from sr_olthad.framework.agents import InstructLmAgent
from sr_olthad.framework.schema import LmStreamsHandler
from sr_olthad.lm_step import LmStepTemplate
from sr_olthad.olthad import OlthadTraversal
from sr_olthad.prompts import PlannerLmResponseOutputData


class Planner:
    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        lm_step_template: LmStepTemplate,
        streams_handler: LmStreamsHandler | None = None,
    ):
        super().__init__()

        self.traversal = olthad_traversal
        self.streams_handler = streams_handler
        self.lm_step_template = lm_step_template

        self._planner: InstructLmAgent[PlannerLmResponseOutputData] = InstructLmAgent(
            instruct_lm=cfg.INSTRUCT_LM,
            response_json_model=PlannerLmResponseOutputData,
            max_tries_to_get_parsable_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
        )

    async def run(self, env_state) -> None:
        raise NotImplementedError
