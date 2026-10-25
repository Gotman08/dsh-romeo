"""Checks the endpoint with the official OpenAI SDK: a tool call, then a streamed answer.

    dsh-romeo --run python3 tests/clients/openai_sdk.py      (pip install openai)
"""
import json
import os

from openai import OpenAI

client = OpenAI()   # OPENAI_BASE_URL and OPENAI_API_KEY come from dsh-romeo
model = os.environ["DSH_ROMEO_MODEL"]
tools = [{"type": "function", "function": {
    "name": "get_node_count", "description": "Number of nodes of a partition of the cluster",
    "parameters": {"type": "object", "properties": {"partition": {"type": "string"}}, "required": ["partition"]}}}]
messages = [{"role": "user", "content": "How many nodes does the armgpu partition have? Use the tool."}]

first = client.chat.completions.create(model=model, messages=messages, tools=tools, reasoning_effort="low")
call = first.choices[0].message.tool_calls[0]
print("tool call:", call.function.name, call.function.arguments)
assert call.function.name == "get_node_count" and json.loads(call.function.arguments)["partition"] == "armgpu"

messages += [first.choices[0].message, {"role": "tool", "tool_call_id": call.id, "content": "58"}]
stream = client.chat.completions.create(model=model, messages=messages, tools=tools, stream=True, reasoning_effort="low")
answer = "".join(chunk.choices[0].delta.content or "" for chunk in stream if chunk.choices)
print("streamed answer:", answer.strip())
assert "58" in answer
print("OK")
