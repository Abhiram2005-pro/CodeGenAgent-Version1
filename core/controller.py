from __future__ import annotations

from core.engine import QwenEngine
from core.planner import Planner
from core.generator import Generator
from core.executor import Executor
from core.error_collector import ErrorCollector
from core.context_builder import ContextBuilder
from core.debugger import Debugger


class Controller:

    MAX_RETRIES = 5

    def __init__(self, engine: QwenEngine):

        self.engine = engine

        self.planner = Planner(engine)

        self.generator = Generator(engine)

        self.executor = Executor()

        self.error_collector = ErrorCollector()

        self.context_builder = ContextBuilder()

        self.debugger = Debugger(engine)

    # ==========================================================
    # Main Entry
    # ==========================================================

    def run(
        self,
        user_request: str
    ) -> bool:

        print("\n========================================")
        print("Generating Project Plan...")
        print("========================================")

        plan = self.planner.create_plan(user_request)

        if plan is None:

            print("\nFailed to generate project plan.")

            return False

        print("\n========================================")
        print("Generating Project...")
        print("========================================")

        success = self.generator.generate_project()

        if not success:

            print("\nProject generation failed.")

            return False

        print("\n========================================")
        print("Project Generated Successfully")
        print("========================================")

        return self.execute_pipeline()

    # ==========================================================
    # Execute + Debug Loop
    # ==========================================================

    def execute_pipeline(self) -> bool:

        retries = 0

        while retries <= self.MAX_RETRIES:

            print("\n========================================")
            print(f"Execution Attempt {retries + 1}")
            print("========================================")

            try:

                result = self.executor.execute()

            except Exception as e:

                print(f"\nExecutor crashed: {e}")

                return False

            if result.success:

                print("\n========================================")
                print("PROJECT EXECUTED SUCCESSFULLY")
                print("========================================")

                return True

            print("\nExecution failed.")
            print("Collecting debugging information...")

            try:

                error = self.error_collector.collect(
                    result.stderr
                )

            except Exception as e:

                print(f"\nFailed to collect error: {e}")

                return False

            try:

                context = self.context_builder.build(
                    self.generator.get_project_root(),
                    error
                )

            except Exception as e:

                print(f"\nFailed to build debug context: {e}")

                return False

            print("\n========================================")
            print("Invoking AI Debugger...")
            print("========================================")

            repaired = self.debugger.repair(context)

            if not repaired:

                print("\nAI Debugger could not repair the project.")

                return False

            retries += 1

        print("\n========================================")
        print("Maximum retry limit reached.")
        print("========================================")

        return False