from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import subprocess
import time
import sys
import os

# ==========================================================
# Execution Result
# ==========================================================

@dataclass
class ExecutionResult:
    success: bool = False
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    execution_time: float = 0.0


# ==========================================================
# Executor
# ==========================================================

class Executor:

    def __init__(self):

        self.workspace = Path("workspace")
        self.projects_root = Path("generated_projects")

        self.plan = None
        self.project_root = None

        self.language = None
        self.framework = None
        self.entry_point = None
        self.last_result = None

    # ======================================================
    # Execute (Main Entry)
    # ======================================================

    def execute(self):

        self.load_project()

        self.analyze_project()

        self.print_summary()

        # ------------------------------------------------------
        # Install Dependencies
        # ------------------------------------------------------

        result = self.install_dependencies()

        self.print_result(result)

        self.last_result = result

        if not result.success:
            return result

        # ------------------------------------------------------
        # Run Tests
        # ------------------------------------------------------

        result = self.run_tests()

        self.print_result(result)

        self.last_result = result

        if not result.success:
            return result

        # ------------------------------------------------------
        # Run Application
        # ------------------------------------------------------

        result = self.run_application()

        self.print_result(result)

        self.last_result = result

        return result
    # ======================================================
    # Load Project
    # ======================================================

    def load_project(self):

        plan_path = self.workspace / "project_plan.json"

        if not plan_path.exists():
            raise FileNotFoundError(
                "workspace/project_plan.json not found."
            )

        with open(plan_path, "r", encoding="utf-8") as f:
            self.plan = json.load(f)

        project_name = self.plan["project_name"]

        self.project_root = self.projects_root / project_name

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project folder '{project_name}' not found."
            )

    # ======================================================
    # Analyze Project
    # ======================================================

    def analyze_project(self):

        self.detect_language()

        self.detect_framework()

        self.detect_entry_point()

    # ======================================================
    # Detect Language
    # ======================================================

    def detect_language(self):

        files = self.plan.get("files", [])

        extensions = set()

        for file in files:

            ext = Path(file["path"]).suffix.lower()

            extensions.add(ext)

        if ".py" in extensions:

            self.language = "Python"

        elif ".java" in extensions:

            self.language = "Java"

        elif ".js" in extensions:

            self.language = "JavaScript"

        elif ".cpp" in extensions or ".cc" in extensions:

            self.language = "C++"

        elif ".c" in extensions:

            self.language = "C"

        elif ".go" in extensions:

            self.language = "Go"

        elif ".rs" in extensions:

            self.language = "Rust"

        else:

            self.language = "Unknown"

    # ======================================================
    # Detect Framework
    # ======================================================

    def detect_framework(self):

        if (self.project_root / "pom.xml").exists():

            self.framework = "Maven"

            return

        if (self.project_root / "build.gradle").exists():

            self.framework = "Gradle"

            return

        if (self.project_root / "package.json").exists():

            self.framework = "Node"

            return

        if (self.project_root / "requirements.txt").exists():

            self.framework = "Python"

            return

        self.framework = "None"

    # ======================================================
    # Detect Entry Point
    # ======================================================

    def detect_entry_point(self):

        candidates = [
            "main.py",
            "app.py",
            "run.py",
            "manage.py",
            "server.py",
            "src/main.py",
            "src/app.py",
            "src/run.py",
            "src/server.py",
            "Main.java",
            "src/Main.java",
            "index.js",
            "server.js"
        ]

        for file in candidates:
            path = self.project_root / file
            if path.exists():
                self.entry_point = path
                return

        if self.language == "Python":

            py_files = list(self.project_root.rglob("*.py"))

            py_files = [
                f for f in py_files
                if "__init__" not in f.name
                and "test" not in f.name.lower()
            ]

            if len(py_files) == 1:
                self.entry_point = py_files[0]
                return

        self.entry_point = None

    # ======================================================
    # Getters
    # ======================================================

    def get_language(self):

        return self.language

    def get_framework(self):

        return self.framework

    def get_entry_point(self):

        return self.entry_point

    # ======================================================
    # Print Summary
    # ======================================================

    def print_summary(self):

        print("\n====================================")
        print("        PROJECT ANALYSIS")
        print("====================================")

        print(f"Project   : {self.plan['project_name']}")
        print(f"Language  : {self.language}")
        print(f"Framework : {self.framework}")

        if self.entry_point:

            print(f"Entry     : {self.entry_point.relative_to(self.project_root)}")

        else:

            print("Entry     : Not Found")

        print("====================================\n")
        # ======================================================
# Run Command
# ======================================================

    def run_command(
        self,
        command,
        cwd=None,
        timeout=300
    ):

        print("\n----------------------------------------")
        print("Executing Command")
        print("----------------------------------------")

        print(" ".join(command))

        start = time.time()

        try:

            process = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            end = time.time()

            result = ExecutionResult()

            result.success = process.returncode == 0
            result.stdout = process.stdout
            result.stderr = process.stderr
            result.exit_code = process.returncode
            result.execution_time = round(end - start, 2)

            return result

        except subprocess.TimeoutExpired:

            end = time.time()

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds.",
                exit_code=-1,
                execution_time=round(end - start, 2)
            )

        except Exception as e:

            end = time.time()

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=round(end - start, 2)
            )
        # ======================================================
    # Print Execution Result
    # ======================================================

    def print_result(self, result):

        print("\n========================================")
        print("Execution Result")
        print("========================================")

        print(f"Success : {result.success}")
        print(f"Exit    : {result.exit_code}")
        print(f"Time    : {result.execution_time} sec")

        if result.stdout:

            print("\n---------- STDOUT ----------")
            print(result.stdout)

        if result.stderr:

            print("\n---------- STDERR ----------")
            print(result.stderr)

        print("========================================")
    def install_dependencies(self):

        print("\nInstalling Dependencies...")

        if self.language == "Python":

            requirements = self.project_root / "requirements.txt"

            if requirements.exists():

                return self.run_command(
                    [
                        sys.executable,
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test*.py"
                    ],
                    cwd=self.project_root
                )

            return ExecutionResult(
                success=True,
                stdout="No requirements.txt found. Skipping installation."
            )

        return ExecutionResult(
            success=True,
            stdout="No dependency installation required."
        )
    def run_tests(self):

        print("\nRunning Tests...")

        # ---------------------------------------
        # Check if tests exist
        # ---------------------------------------

        tests_dir = self.project_root / "tests"

        if not tests_dir.exists():

            return ExecutionResult(
                success=True,
                stdout="No tests found. Skipping."
            )

        # ---------------------------------------
        # PYTHON
        # ---------------------------------------

        if self.language == "Python":

            # Ensure package initialization files exist
            for init_file in [
                self.project_root / "tests" / "__init__.py",
                self.project_root / "src" / "__init__.py"
            ]:
                if not init_file.exists():
                    init_file.parent.mkdir(parents=True, exist_ok=True)
                    init_file.touch()

            # pytest.ini
            if (self.project_root / "pytest.ini").exists():

                print("Detected pytest.")

                return self.run_command(
                    [sys.executable, "-m", "pytest"],
                    cwd=self.project_root
                )

            # pyproject.toml
            if (self.project_root / "pyproject.toml").exists():

                content = (
                    self.project_root / "pyproject.toml"
                ).read_text(
                    encoding="utf-8",
                    errors="ignore"
                ).lower()

                if "pytest" in content:

                    print("Detected pytest.")

                    return self.run_command(
                        [sys.executable, "-m", "pytest"],
                        cwd=self.project_root
                    )

            # requirements.txt
            req = self.project_root / "requirements.txt"

            if req.exists():

                content = req.read_text(
                    encoding="utf-8",
                    errors="ignore"
                ).lower()

                if "pytest" in content:

                    print("Detected pytest.")

                    return self.run_command(
                        [sys.executable, "-m", "pytest"],
                        cwd=self.project_root
                    )

                if "nose" in content:

                    print("Detected nose.")

                    return self.run_command(
                        [sys.executable, "-m", "nose"],
                        cwd=self.project_root
                    )

            # Default unittest discovery

            print("Detected unittest.")

            return self.run_command(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test*.py"
                ],
                cwd=self.project_root
            )

        # ---------------------------------------
        # JAVA
        # ---------------------------------------

        if self.language == "Java":

            if (self.project_root / "pom.xml").exists():

                print("Running Maven tests.")

                return self.run_command(
                    ["mvn", "test"],
                    cwd=self.project_root
                )

            if (self.project_root / "build.gradle").exists():

                print("Running Gradle tests.")

                return self.run_command(
                    ["gradle", "test"],
                    cwd=self.project_root
                )

        # ---------------------------------------
        # JAVASCRIPT
        # ---------------------------------------

        if self.language == "JavaScript":

            package = self.project_root / "package.json"

            if package.exists():

                return self.run_command(
                    ["npm", "test"],
                    cwd=self.project_root
                )

        # ---------------------------------------
        # Unsupported
        # ---------------------------------------

        return ExecutionResult(
            success=True,
            stdout="Testing not supported for this language."
        )
    def run_application(self):

        print("\nRunning Application...")

        # =====================================================
        # Python
        # =====================================================

        if self.language == "Python":

            candidates = [
                "main.py",
                "app.py",
                "run.py",
                "manage.py",
                "server.py",
                "src/main.py",
                "src/app.py",
                "src/run.py",
                "src/server.py"
            ]

            for file in candidates:

                path = self.project_root / file

                if path.exists():

                    print(f"Launching {file}")

                    return self.run_command(
                        [
                            sys.executable,
                            file
                        ],
                        cwd=self.project_root
                    )
            if self.entry_point:

                relative = self.entry_point.relative_to(self.project_root)

                return self.run_command(
                    [
                        sys.executable,
                        str(relative)
                    ],
                    cwd=self.project_root
                )

            return ExecutionResult(
                success=False,
                stderr=(
                    "No runnable Python entry point found. "
                    "Create main.py or another executable entry point."
                )
            )

        # =====================================================
        # Java
        # =====================================================

        if self.language == "Java":

            if (self.project_root / "pom.xml").exists():

                print("Launching Maven Project")

                return self.run_command(
                    [
                        "mvn",
                        "spring-boot:run"
                    ],
                    cwd=self.project_root
                )

            if (self.project_root / "build.gradle").exists():

                print("Launching Gradle Project")

                return self.run_command(
                    [
                        "gradle",
                        "bootRun"
                    ],
                    cwd=self.project_root
                )

            return ExecutionResult(
                success=False,
                stderr="No runnable Java project found."
            )

        # =====================================================
        # JavaScript / Node
        # =====================================================

        if self.language == "JavaScript":

            package = self.project_root / "package.json"

            if package.exists():

                try:

                    import json

                    with open(package, "r", encoding="utf-8") as f:

                        data = json.load(f)

                    scripts = data.get("scripts", {})

                    if "start" in scripts:

                        print("Running npm start")

                        return self.run_command(
                            [
                                "npm",
                                "start"
                            ],
                            cwd=self.project_root
                        )

                    if "dev" in scripts:

                        print("Running npm run dev")

                        return self.run_command(
                            [
                                "npm",
                                "run",
                                "dev"
                            ],
                            cwd=self.project_root
                        )

                except Exception as e:

                    return ExecutionResult(
                        success=False,
                        stderr=str(e)
                    )

            return ExecutionResult(
                success=False,
                stderr="No runnable Node project found."
            )

        # =====================================================
        # Unsupported
        # =====================================================

        return ExecutionResult(
            success=False,
            stderr=f"{self.language} execution not supported yet."
        )
    def get_last_result(self) -> ExecutionResult:
        return self.last_result