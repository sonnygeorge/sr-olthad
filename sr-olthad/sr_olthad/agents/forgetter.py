from sr_olthad.framework.schema import LmStreamsHandler
from sr_olthad.lm_step import LmStepTemplate
from sr_olthad.olthad import OlthadTraversal


class Forgetter:
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

    async def run(self, env_state: str) -> None:
        raise NotImplementedError
