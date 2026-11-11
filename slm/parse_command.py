import json
import time
import urllib.request

API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen3-4b-instruct-2507"

SYSTEM_PROMPT = """
You are a command parser for a multi-UAV warehouse system.

Convert the command into a JSON object.

Rules:
1. Return only valid JSON.
2. Use exactly these three fields:
   "uav_id", "task", "location".
3. The "uav_id" must contain only the drone number
   as a string. Example: "1", not "Drone 1".
4. For zone inspection, use "inspect_zone".
5. The "location" must contain only the zone letter.
6. Do not add information that is not in the command.
"""

command = "Drone 1, inspect zone A"

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": command}
    ],
    "temperature": 0,
    "stream": False
}

request = urllib.request.Request(
    API_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

start_time = time.perf_counter()

with urllib.request.urlopen(request, timeout=120) as response:
    result = json.load(response)

elapsed_time = time.perf_counter() - start_time

model_output = result["choices"][0]["message"]["content"]

print("Input command:", command)
print("SLM output:", model_output)
print(f"SLM response time: {elapsed_time:.2f} seconds")