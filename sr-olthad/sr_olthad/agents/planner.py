from sr_olthad.config import PlannerCfg as cfg
from sr_olthad.framework.agents import InstructLmAgent, InstructLmAgentOutput
from sr_olthad.framework.schema import LmStreamsHandler
from sr_olthad.lm_step import LmStepTemplate
from sr_olthad.olthad import OlthadTraversal, PendingOlthadUpdate
from sr_olthad.prompts import PlannerLmResponseOutputData
from sr_olthad.schema import (
    LmAgentName,
    UserPromptInputData,
)


class Planner:
    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        lm_step_template: LmStepTemplate,
        streams_handler: LmStreamsHandler | None = None,
    ):
        super().__init__()

        self.traversal = olthad_traversal
        self.lm_step_template = lm_step_template

        self._planner: InstructLmAgent[PlannerLmResponseOutputData] = InstructLmAgent(
            instruct_lm=cfg.INSTRUCT_LM,
            response_json_model=PlannerLmResponseOutputData,
            max_tries_to_get_parsable_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            streams_handler=streams_handler,
        )

    def _process_lm_step_output(
        self,
        output: InstructLmAgentOutput[PlannerLmResponseOutputData],
    ) -> tuple[None, PendingOlthadUpdate]:
        return None, self.traversal.update_planned_subtasks_of_cur_node(
            new_planned_subtasks=output.data.new_planned_subtasks
        )

    async def run(self, env_state) -> None:
        prompt_input_data = UserPromptInputData(
            env_state=env_state,
            olthad=self.traversal.root_node.stringify(
                # TODO: Maybe do this?
                # redact_planned_subtasks_below=self.traversal.cur_node.id
            ),
            task_in_question=self.traversal.cur_node.stringify(
                # TODO: Maybe do this?
                # redact_planned_subtasks_below=self.traversal.cur_node.id
            ),
        )

        lm_step = self.lm_step_template.compose(
            run_step=self._planner.run,
            process_output=self._process_lm_step_output,
            lm_agent_name=LmAgentName.PLANNER,
            cur_node_id=self.traversal.cur_node.id,
            prompt_input_data=prompt_input_data,
        )

        await lm_step()
