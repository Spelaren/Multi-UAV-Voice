
import json
import time
import urllib.request


class SLMEngine:

    def __init__(self):
        self.api_url = (
            "http://127.0.0.1:1234/v1/chat/completions"
        )

        self.model_name = "qwen3-4b-instruct-2507"

        self.system_prompt = """
You are a command parser for a multi-UAV warehouse system.

Convert spoken English commands into structured JSON.

Return ONLY a valid JSON object in this format:

{
  "missions": [
    {
      "uav_id": "2",
      "task": "inspect_zone",
      "location": "B"
    }
  ]
}

Rules:
1. Return only JSON.
2. The top-level object must contain exactly "missions".
3. Each mission must contain exactly:
   "uav_id", "task", "location".
4. UAV IDs must be strings.
5. Allowed tasks are "inspect_zone" and "inspect_pallet".
6. Zone locations use letters A to F.
7. Pallet locations use IDs such as P05.
8. Preserve every explicitly spoken UAV assignment.
9. Never invent UAV IDs, tasks, or locations.
10. If any field is missing, use null.
11. Never guess missing information.
12. Do not approve or execute missions.
"""

    def parse_command(self, transcription):

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ],
            "temperature": 0,
            "stream": False
        }

        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        start = time.perf_counter()

        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:
            result = json.load(response)

        elapsed = time.perf_counter() - start

        model_output = (
            result["choices"][0]["message"]["content"]
        )

        return model_output, elapsed
