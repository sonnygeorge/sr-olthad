import base64
import os
import re

import openai
from tenacity import retry, stop_after_attempt

MODEL = "gpt-4.1-2025-04-14"
TEMPERATURE = 0.6
PROMPT = """
Here is a screenshot taken by a Minecraft player who was asked to perform the task: '{task}'.
Your job is to consider the degree to which the screenshot evidences that the player fulfilled this task.
First, think step-by-step about the screenshot:
1. Describe the key elements visible in the screenshot.
2. Explain how these elements relate to the task.
3. Assess how the elements do or do not provide evidence for the fulfillment of the task.
After your step-by-step reasoning, provide your final answer as a single word or phrase, indicating your level of agreement with the statement:
"The screenshot evidences that the player fulfilled the task, '{task}.'"
IMPORTANT! YOUR FINAL UTTERANCE MUST BE ONE OF THE FOLLOWING OPTIONS:
- agree
- somewhat agree
- neutral
- somewhat disagree
- disagree
"""
SCORE_MAP = {
    "disagree": 0.0,
    "somewhat disagree": 0.25,
    "neutral": 0.5,
    "somewhat agree": 0.75,
    "agree": 1.0,
}


def extract_final_answer_from_response(response: str) -> str | None:
    """Extracts the last answer match (case insensitive) from the response."""
    pattern = r"(" + "|".join(map(re.escape, list(SCORE_MAP.keys()))) + ")"
    matches = re.findall(pattern, response, re.IGNORECASE)
    final_answer = str(matches[-1]).lower() if matches else None
    return final_answer


@retry(stop=stop_after_attempt(8))
def get_task_score(screenshot_fpath: str, task: str) -> float:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    client = openai.OpenAI(api_key=api_key)
    with open(screenshot_fpath, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    formatted_prompt = PROMPT.format(task=task).strip()
    img_url = f"data:image/jpeg;base64,{encoded_image}"
    text_content = {"type": "text", "text": formatted_prompt}
    image_content = {"type": "image_url", "image_url": {"url": img_url}}
    messages = [{"role": "user", "content": [text_content, image_content]}]
    response = client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=15_000, temperature=TEMPERATURE
    )
    final_answer = extract_final_answer_from_response(response.choices[0].message.content)
    if final_answer is None:
        raise ValueError(f"Invalid response '{final_answer}'.")
    return SCORE_MAP[final_answer]
