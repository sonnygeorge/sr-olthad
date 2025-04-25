import asyncio
import os

import google.generativeai as genai
from deepseek import DeepSeekAPI
from groq import AsyncGroq

# from openai.types.chat import ChatCompletion , ChatCompletionChunk
from groq.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

from sr_olthad.framework.schema import (
    InstructLm,
    InstructLmChatRole,
    InstructLmMessage,
    LmStreamHandler,
)

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


class GeminiInstructLm(InstructLm):
    # NOTE: Rate limits @ https://ai.google.dev/gemini-api/docs/rate-limits
    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        super().__init__()
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = model
        self.genai_model = genai.GenerativeModel(model_name=model)

    async def generate(
        self,
        messages: list[InstructLmMessage],
        stream_handler: LmStreamHandler | None = None,
        **kwargs,
    ) -> str:
        gemini_messages = self._convert_to_gemini_format(messages)
        if stream_handler is not None:
            return await self._generate_streaming(gemini_messages, stream_handler, **kwargs)
        else:
            response = await self._generate_non_streaming(gemini_messages, **kwargs)
            return response

    def _convert_to_gemini_format(self, messages: list[InstructLmMessage]) -> list:
        gemini_messages = []
        for msg in messages:
            if msg["role"] == InstructLmChatRole.USER:
                gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == InstructLmChatRole.ASSISTANT:
                gemini_messages.append(
                    {"role": "model", "parts": [{"text": msg["content"]}]}
                )
            elif msg["role"] == InstructLmChatRole.SYS:
                # Gemini doesn't have a direct system message equivalent
                # Prepend to the first user message or add as a user message if none exists
                system_content = msg["content"]
                if not gemini_messages:
                    gemini_messages.append(
                        {
                            "role": "user",
                            "parts": [{"text": f"[System Instruction] {system_content}"}],
                        }
                    )
                elif gemini_messages and gemini_messages[0]["role"] == "user":
                    gemini_messages[0]["parts"][0]["text"] = (
                        f"[System Instruction] {system_content}\n\n"
                        + gemini_messages[0]["parts"][0]["text"]
                    )
                else:
                    # Insert system message as a user message at the beginning
                    gemini_messages.insert(
                        0,
                        {
                            "role": "user",
                            "parts": [{"text": f"[System Instruction] {system_content}"}],
                        },
                    )
        return gemini_messages

    async def _generate_streaming(
        self, gemini_messages: list, stream_handler: LmStreamHandler, **kwargs
    ) -> str:
        """Handle streaming generation"""
        chat = self.genai_model.start_chat(history=gemini_messages[:-1])
        last_message = gemini_messages[-1]["parts"][0]["text"] if gemini_messages else ""
        generation_config = {}
        for param in ["temperature", "top_p", "top_k", "max_output_tokens"]:
            if param in kwargs:
                generation_config[param] = kwargs[param]
        response_stream = await chat.send_message_async(
            last_message, generation_config=generation_config, stream=True
        )
        full_response = ""
        async for chunk in response_stream:
            if chunk.text:
                stream_handler(chunk.text)
                full_response += chunk.text
        return full_response

    async def _generate_non_streaming(self, gemini_messages: list, **kwargs) -> str:
        """Handle non-streaming generation"""
        chat = self.genai_model.start_chat(history=gemini_messages[:-1])
        last_message = gemini_messages[-1]["parts"][0]["text"] if gemini_messages else ""
        generation_config = {}
        for param in ["temperature", "top_p", "top_k", "max_output_tokens"]:
            if param in kwargs:
                generation_config[param] = kwargs[param]
        response = await chat.send_message_async(
            last_message, generation_config=generation_config
        )
        return response.text


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
            stream_generator = await async_chat_completion(messages, stream=True, **kwargs)

            async def async_stream_generator():
                for chunk in stream_generator:
                    yield chunk

            full_response = ""
            async for chunk_text in async_stream_generator():
                if chunk_text:
                    stream_handler(chunk_text)
                    full_response += chunk_text

            return full_response
        else:
            response = await async_chat_completion(messages, stream=False, **kwargs)
            return response
