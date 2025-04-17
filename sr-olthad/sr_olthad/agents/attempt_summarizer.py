from sr_olthad.config import AttemptSummarizerCfg as cfg
from sr_olthad.framework.agents import InstructLmAgent, InstructLmAgentOutput
from sr_olthad.framework.schema import LmStreamsHandler
from sr_olthad.lm_step import LmStepTemplate
from sr_olthad.olthad import OlthadTraversal, PendingOlthadUpdate
from sr_olthad.prompts import AttemptSummarizerLmResponseOutputData
from sr_olthad.schema import (
    LmAgentName,
    UserPromptInputData,
)


class AttemptSummarizer:
    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        lm_step_template: LmStepTemplate,
        streams_handler: LmStreamsHandler | None = None,
    ):
        super().__init__()

        self.traversal = olthad_traversal
        self.lm_step_template = lm_step_template

        self._attempt_summarizer: InstructLmAgent[AttemptSummarizerLmResponseOutputData] = (
            InstructLmAgent(
                instruct_lm=cfg.INSTRUCT_LM,
                response_json_model=AttemptSummarizerLmResponseOutputData,
                max_tries_to_get_parsable_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
                streams_handler=streams_handler,
            )
        )

    def _process_lm_step_output(
        self, output: InstructLmAgentOutput[AttemptSummarizerLmResponseOutputData]
    ) -> tuple[None, PendingOlthadUpdate]:
        return None, self.traversal.update_status_and_retrospective_of(
            node=self.traversal.cur_node.in_progress_subtask,
            new_status=output.data.status_to_assign,
            new_retrospective=output.data.retrospective_to_assign,
        )

    async def run(self, env_state: str) -> None:
        prompt_input_data = UserPromptInputData(
            env_state=env_state,
            olthad=self.traversal.root_node.stringify(
                obfuscate_status_of=self.traversal.cur_node.in_progress_subtask.id
            ),
            task_in_question=self.traversal.cur_node.in_progress_subtask.stringify(
                obfuscate_status_of=self.traversal.cur_node.in_progress_subtask.id
            ),
        )

        lm_step = self.lm_step_template.compose(
            run_step=self._attempt_summarizer.run,
            process_output=self._process_lm_step_output,
            lm_agent_name=LmAgentName.ATTEMPT_SUMMARIZER,
            cur_node_id=self.traversal.cur_node.id,
            prompt_input_data=prompt_input_data,
        )

        await lm_step()
