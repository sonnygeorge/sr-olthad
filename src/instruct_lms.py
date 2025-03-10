from typing import List

from transformers import AutoModelForCausalLM, AutoTokenizer

from types_and_models import InstructLm, InstructLmMessage


class LocalInstructLm(InstructLm):
    def __init__(self, model_name: str, device: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

    async def generate(
        self, messages: List[InstructLmMessage], **kwargs
    ) -> List[InstructLmMessage]:
        prompt = self._messages_to_prompt(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_length=kwargs.get("max_tokens", 100),
            temperature=kwargs.get("temperature", 0.7),
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return messages + [{"role": "assistant", "content": response}]


# TODO
class OpenAIInstructLm(InstructLm):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(
        self, messages: List[InstructLmMessage], **kwargs
    ) -> List[InstructLmMessage]:
        pass
