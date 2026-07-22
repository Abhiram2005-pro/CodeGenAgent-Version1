import json
import re
from pathlib import Path


class Generator:

    def __init__(self, engine):

        self.engine = engine

        self.workspace = Path("workspace")

        self.projects_root = Path("generated_projects")

        self.projects_root.mkdir(exist_ok=True)

        self.plan = None

        self.project_root = None

    # ==========================================================
    # Main Entry
    # ==========================================================

    def generate_project(self) -> bool:

        print("\nLoading project plan...")

        if not self.load_plan():
            return False

        print("\nCreating project...")

        self.create_project()

        print("\nCreating folders...")

        self.create_folders()

        print("\nGenerating files...")

        self.generate_all_files()

        print("\n====================================")
        print("Project Generated Successfully!")
        print(f"Location : {self.project_root}")
        print("====================================")

        return True

    # ==========================================================
    # Load JSON
    # ==========================================================

    def load_plan(self) -> bool:

        plan_file = self.workspace / "project_plan.json"

        if not plan_file.exists():

            print("project_plan.json not found.")

            return False

        try:

            with open(plan_file, "r", encoding="utf-8") as f:

                self.plan = json.load(f)

            return True

        except Exception as e:

            print("Failed to load project plan.")

            print(e)

            return False

    # ==========================================================
    # Create Project Directory
    # ==========================================================

    def create_project(self) ->None:

        project_name = self.plan["project_name"]

        self.project_root = self.projects_root / project_name

        self.project_root.mkdir(parents=True, exist_ok=True)

    # ==========================================================
    # Create Folder Structure
    # ==========================================================

    def create_folders(self) -> None:

        folders = self.plan.get("folders", [])

        for folder in folders:

            folder_path = self.project_root / folder

            folder_path.mkdir(
                parents=True,
                exist_ok=True
            )

            print(f"Created Folder : {folder}")
    # ==========================================================
    # Generate Every File
    # ==========================================================

    def generate_all_files(self) -> None:

        files = self.plan.get("files", [])

        if not files:
            print("No files found in project plan.")
            return

        total = len(files)

        for index, file_info in enumerate(files, start=1):

            print(f"\n[{index}/{total}] {file_info['path']}")

            self.generate_single_file(file_info)

    # ==========================================================
    # Generate One File
    # ==========================================================

    def generate_single_file(self, file_info) -> None:

        file_path = file_info["path"]

        language = file_info["language"]

        purpose = file_info["purpose"]

        project_name = self.plan["project_name"]

        description = self.plan["description"]

        full_path = self.project_root / file_path

        full_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        print("Generating...")

        prompt = f"""
    You are an expert {language} software engineer.

    Generate ONLY the requested file.

    Project Name:
    {project_name}

    Project Description:
    {description}

    Project Structure:

    Folders:
    {json.dumps(self.plan.get("folders", []), indent=4)}

    Files:
    {json.dumps(self.plan.get("files", []), indent=4)}

    Current File:
    {file_path}

    Purpose:
    {purpose}

    Rules:

    1. Generate ONLY this file.
    2. Do NOT explain anything.
    3. Do NOT use markdown.
    4. Do NOT wrap code inside ``` blocks.
    5. Return ONLY the file contents.
    6. Produce production-quality code.
    7. Assume every listed file will exist.
    8. Import modules using the generated project structure.
    9. If generating tests, use correct imports.
    10. If generating main.py, make it executable.
    11. If generating __init__.py, return only what is necessary.
    12. If generating requirements.txt, include only required packages.
    13. Do not invent additional files.
    14. Keep the code consistent with the other planned files.
    15. The generated project must run without manual modification.
    """
        response = self.engine.generate(
            prompt=prompt,
            max_new_tokens=768,
            do_sample=False
        )

        code = self.clean_code(response)

        self.save_file(
            full_path,
            code
        )
    # ==========================================================
    # Clean Generated Code
    # ==========================================================

    def clean_code(self, response) -> str:

        if response is None:
            return ""

        code = response.strip()

        # Remove Markdown fences
        code = re.sub(r"```[a-zA-Z0-9_+-]*", "", code)
        code = code.replace("```", "")
        code = code.strip()

        # Remove accidental leading/trailing whitespace
        code = code.strip()

        return code

    # ==========================================================
    # Save File
    # ==========================================================

    def save_file(self, file_path, code) -> None:

        try:

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            print(f"Saved : {file_path.relative_to(self.project_root)}")

        except Exception as e:

            print(f"Failed to save {file_path}")
            print(e)
    def get_project_root(self) -> Path:
        return self.project_root