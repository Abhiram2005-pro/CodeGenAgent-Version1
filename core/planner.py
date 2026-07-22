import json
import re
from pathlib import Path


class Planner:

    def __init__(self, engine):
        self.engine = engine
        self.workspace = Path("workspace")
        self.workspace.mkdir(exist_ok=True)

    def create_plan(self, user_request):

        prompt = f"""
You are a Senior Software Architect.

Your ONLY job is to design a complete software project.

Return EXACTLY ONE valid JSON object.

Do NOT generate any source code.
Do NOT explain anything.
Do NOT use markdown.
Do NOT use triple backticks.
Do NOT output any text before or after the JSON.

The JSON MUST follow EXACTLY this schema:

{{
    "project_name": "",
    "description": "",
    "language": "",
    "framework": "",
    "folders": [
        ""
    ],
    "files": [
        {{
            "path": "",
            "language": "",
            "purpose": ""
        }}
    ]
}}

Rules:

1. Return ONLY valid JSON.
2. Every file path must be relative.
3. Use forward slashes (/).
4. Include every required folder.
5. Include every required source file.
6. Include README.md.
7. Do NOT generate file contents.
8. Do NOT invent unnecessary folders.
9. Every file must belong to one of the folders.
10. Every file must have a language.
11. Every file must have a purpose.

Python Project Rules:

12. Every runnable Python application MUST contain:
    - main.py
    - src/__init__.py
    - tests/__init__.py
    - requirements.txt

13. If unit tests exist:
    - create tests/test_<module>.py
    - tests must be executable with unittest discovery.

14. Organize source code inside src/.

15. The generated project must be runnable immediately after generation.

16. Imports must follow the generated folder structure.

17. Do not omit required executable files.

User Request:

{user_request}
"""

        response = self.engine.generate(
            prompt=prompt,
            max_new_tokens=512,
            do_sample=False
        )

        print("\n========== RAW RESPONSE ==========\n")
        print(response)

        cleaned = self.clean_json(response)

        print("\n========== CLEANED JSON ==========\n")
        print(cleaned)

        plan = self.parse_json(cleaned)

        if plan is None:
            return None

        self.save_plan(plan)

        print("\nProject plan saved successfully.")

        return plan

    def clean_json(self, text: str) -> str:

        text = text.strip()

        text = re.sub(
            r"```[a-zA-Z0-9_+-]*",
            "",
            text
        )

        text = text.replace("```", "")

        start = text.find("{")

        if start == -1:
            return ""

        text = text[start:]

        depth = 0
        end = -1

        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end != -1:
            return text[:end + 1]

        return text

    def parse_json(self, cleaned: str):

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            print("\nJSON Parsing Failed")
            print(e)
            return None

    def save_plan(self, plan) -> None:

        output = self.workspace / "project_plan.json"

        with open(output, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4, ensure_ascii=False)