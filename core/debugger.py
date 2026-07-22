from __future__ import annotations
from pathlib import Path
from typing import List
from dataclasses import dataclass
import ast
import re
import shutil

from core.engine import QwenEngine
from core.context_builder import DebugContext


@dataclass
class FilePatch:
    path: str
    content: str
class Debugger:

    def __init__(self, engine: QwenEngine):

        self.engine = engine

    # ==========================================================
    # PUBLIC
    # ==========================================================

    def debug(
        self,
        context: DebugContext
        ) -> List[FilePatch]:
        """
        Main entry point.

        Returns raw LLM response.
        """

        prompt = self.build_prompt(context)

        print("\n========== DEBUG PROMPT ==========\n")
        print(prompt[:2000])      # Prevent huge console output
        print("\n==================================\n")

        response = self.ask_llm(prompt)

        patches = self.parse_response(response)

        if not self.validate_patches(patches):

            print("No valid patches generated.")

            return []

        self.print_patch_summary(patches)

        return patches

    # ==========================================================
    # PROMPT
    # ==========================================================

    def build_prompt(self, context: DebugContext) -> str:

        related = self.build_related_files(context)

        prompt = f"""
You are an expert software engineer.

A generated project failed during execution.

Your job is to FIX the project.

===========================
ERROR TYPE
===========================

{context.error_type}

===========================
ERROR MESSAGE
===========================

{context.error_message}

===========================
TRACEBACK
===========================

{context.traceback}

===========================
PROJECT TREE
===========================

{context.project_tree}

===========================
FAILING FILE
===========================

{context.failing_file}

===========================
FAILING LINE
===========================

{context.failing_line}

===========================
FAILING FILE CONTENT
===========================

{context.failing_file_content}

===========================
RELATED FILES
===========================

{related}

RULES

Fix ONLY the files required to solve the error.

You MAY create new files if necessary.

Examples:
- main.py
- __init__.py
- requirements.txt

You MAY modify multiple files.

Preserve working code whenever possible.

Do not rewrite unrelated files.

Return every corrected file exactly in this format:

===== FILE: relative/path =====
<complete corrected file>
===== END FILE =====

Do not explain.

Do not use markdown.

Output only corrected files.
"""

        return prompt

    # ==========================================================
    # RELATED FILES
    # ==========================================================

    def build_related_files(self, context: DebugContext) -> str:

        output = []

        for file in context.related_files:

            output.append(
                f"""
==========================
FILE : {file.path}
==========================

{file.content}
"""
            )

        return "\n".join(output)

    # ==========================================================
    # LLM
    # ==========================================================

    def ask_llm(self, prompt: str) -> str:

        response = self.engine.generate(
            prompt=prompt,
            max_new_tokens=1024,
            do_sample=False
        )

        return response
    # ==========================================================
    # RESPONSE PARSER
    # ==========================================================

    def parse_response(self, response: str) -> List[FilePatch]:
        """
        Parse Qwen response into file patches.

        Expected format:

        ===== FILE: src/main.py =====
        ...
        ===== END FILE =====
        """
        response = re.sub(
            r"```[a-zA-Z0-9_+-]*",
            "",
            response
        )

        response = response.replace("```", "")

        pattern = (
            r"=+\s*FILE:\s*(.*?)\s*=+\s*"
            r"(.*?)"
            r"=+\s*END FILE\s*=+"
        )

        matches = re.findall(
            pattern,
            response,
            flags=re.DOTALL
        )

        patches = []

        for path, content in matches:

            patches.append(

                FilePatch(

                    path=path.strip(),

                    content=content.strip()

                )

            )

        return patches

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_patches(
        self,
        patches: List[FilePatch]
    ) -> bool:

        if not patches:
            return False

        for patch in patches:

            if not patch.path:
                return False

            if not patch.content:
                return False

        return True
    def validate_python_file(
        self,
        path: str,
        content: str
    ) -> bool:
        """
        Validate Python syntax before applying a patch.
        Non-Python files are accepted automatically.
        """

        if not path.endswith(".py"):
            return True

        try:
            ast.parse(content)
            return True

        except SyntaxError as e:
            print(f"Syntax error in generated file {path}: {e}")
            return False
    # ==========================================================
    # SUMMARY
    # ==========================================================

    def print_patch_summary(
        self,
        patches: List[FilePatch]
    ):

        print("\n========== PATCH SUMMARY ==========\n")

        print(f"Total Files : {len(patches)}")

        for patch in patches:

            print(f"✓ {patch.path}")

        print("\n===================================\n")
        # ==========================================================
    # APPLY PATCHES
    # ==========================================================

    def apply_patches(
        self,
        project_root: Path,
        patches: List[FilePatch]
    ) -> bool:

        # Resolve the project root only once
        project_root = Path(project_root).resolve()

        backups = []

        try:

            for patch in patches:

                # Build the absolute target path
                target = (project_root / patch.path).resolve()

                # Prevent writing outside the project directory
                if not str(target).startswith(str(project_root)):
                    raise ValueError(
                        f"Unsafe patch path: {patch.path}"
                    )

                # Create parent directories if needed
                target.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                backup = None

                # Backup the existing file
                if target.exists():

                    backup = target.with_suffix(
                        target.suffix + ".bak"
                    )

                    shutil.copy2(
                        target,
                        backup
                    )

                backups.append((target, backup))
                if not self.validate_python_file(
                    patch.path,
                    patch.content
                ):
                    raise ValueError(
                        f"Generated invalid Python: {patch.path}"
                    )

                # Write the new file
                target.write_text(
                    patch.content,
                    encoding="utf-8"
                )

            # Everything succeeded
            self.delete_backups(backups)

            print("\nPatches successfully applied.\n")

            return True

        except Exception as e:

            print(f"\nPatch failed: {e}")

            # Restore original files
            self.restore_backups(backups)

            return False
    # ==========================================================
    # RESTORE
    # ==========================================================

    def restore_backups(
        self,
        backups
    ):

        for target, backup in backups:

            try:

                if backup and backup.exists():

                    shutil.copy2(
                        backup,
                        target
                    )

                    backup.unlink()

            except Exception:

                pass

    # ==========================================================
    # DELETE BACKUPS
    # ==========================================================

    def delete_backups(
        self,
        backups
    ):

        for _, backup in backups:

            try:

                if backup and backup.exists():

                    backup.unlink()

            except Exception:

                pass

    # ==========================================================
    # COMPLETE DEBUG PIPELINE
    # ==========================================================

    def repair(
        self,
        context: DebugContext
    ) -> bool:

        patches = self.debug(context)

        if not patches:

            return False

        success = self.apply_patches(

            context.project_root,

            patches

        )

        return success