from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sr_olthad.framework.schema import InstructLm, InstructLmMessage, LmStreamHandler


class OpenAIInstructLm(InstructLm):
    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo"):
        super().__init__()

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(
        self,
        messages: list[InstructLmMessage],
        stream_handler: LmStreamHandler | None = None,
        **kwargs,
        # E.g., temperature, max_tokens, top_p, presence_penalty, frequency_penalty...
    ) -> str:
        if stream_handler is not None:
            response_generator = await self.client.chat.completions.create(
                model=self.model, messages=messages, stream=True, **kwargs
            )
            full_response = ""
            async for chunk in response_generator:
                chunk: ChatCompletionChunk
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    chunk_text = chunk.choices[0].delta.content
                    stream_handler(chunk_text)
                    full_response += chunk_text
            return full_response
        else:  # No need to stream
            chat_completion: ChatCompletion = await self.client.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            )
            return chat_completion.choices[0].message.content
