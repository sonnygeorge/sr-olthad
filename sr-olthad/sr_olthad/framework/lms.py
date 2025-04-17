import asyncio
import os

from deepseek import DeepSeekAPI
from groq import AsyncGroq

# from openai.types.chat import ChatCompletion , ChatCompletionChunk
from groq.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

from sr_olthad.framework.schema import InstructLm, InstructLmMessage, LmStreamHandler

# TODO: Split up into separate files


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


class GroqInstructLm(InstructLm):
    def __init__(self, api_key: str | None = None, model: str = "llama-3.1-8b-instant"):
        super().__init__()

        self.client = AsyncGroq(api_key=api_key)
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


class DeepSeekInstructLm(InstructLm):
    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat"):
        super().__init__()

        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

        self.client = DeepSeekAPI(api_key=api_key)
        self.model = model

    async def generate(
        self,
        messages: list[InstructLmMessage],
        stream_handler: LmStreamHandler | None = None,
        **kwargs,
        # E.g., temperature, max_tokens, top_p, presence_penalty, frequency_penalty...
    ) -> str:
        # Create async version of the API methods
        async def async_chat_completion(messages, stream=False, **kwargs):
            """Run DeepSeek's chat_completion method in a thread to make it async-compatible"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.chat_completion(
                    prompt=messages, stream=stream, model=self.model, **kwargs
                ),
            )

        if stream_handler is not None:
            # Handle streaming case
            stream_generator = await async_chat_completion(messages, stream=True, **kwargs)

            # Convert synchronous generator to async generator
            async def async_stream_generator():
                for chunk in stream_generator:
                    yield chunk

            # Process stream
            full_response = ""
            async for chunk_text in async_stream_generator():
                if chunk_text:
                    stream_handler(chunk_text)
                    full_response += chunk_text

            return full_response
        else:
            # Handle non-streaming case
            response = await async_chat_completion(messages, stream=False, **kwargs)
            return response
