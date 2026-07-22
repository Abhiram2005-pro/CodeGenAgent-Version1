from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import os

from core.error_collector import ErrorInfo


@dataclass
class RelatedFile:
    path: str
    content: str


@dataclass
class DebugContext:

    project_root: Path
    project_tree: str

    error_type: str
    error_message: str
    traceback: str

    failing_file: str | None
    failing_line: int | None
    failing_file_content: str | None

    related_files: List[RelatedFile]


class ContextBuilder:

    EXCLUDED_DIRS = {
        "__pycache__",
        ".git",
        ".idea",
        ".vscode",
        "venv",
        ".venv",
        "env",
        "node_modules",
        "target",
        "build",
        ".pytest_cache"
    }

    SOURCE_EXTENSIONS = {
        ".py",
        ".java",
        ".js",
        ".ts",
        ".json",
        ".xml",
        ".gradle",
        ".properties",
        ".txt",
        ".md"
    }

    def __init__(self):

        pass

    # =======================================================

    def build(
        self,
        project_root: Path,
        error: ErrorInfo
    ) -> DebugContext:

        self.project_root = Path(project_root)

        return DebugContext(

            project_root=self.project_root,

            project_tree=self._build_tree(),

            error_type=error.error_type,

            error_message=error.message,

            traceback=error.traceback or "",

            failing_file=error.file,

            failing_line=error.line,

            failing_file_content=self._read_failing_file(error.file),

            related_files=self._find_related_files(error)
        )

    # =======================================================

    def _build_tree(self) -> str:

        lines = []

        for root, dirs, files in os.walk(self.project_root):

            dirs[:] = [
                d for d in dirs
                if d not in self.EXCLUDED_DIRS
            ]

            level = len(Path(root).relative_to(self.project_root).parts)

            indent = "    " * level

            lines.append(f"{indent}{Path(root).name}/")

            for file in sorted(files):

                lines.append(f"{indent}    {file}")

        return "\n".join(lines)

    # =======================================================

    def _read_failing_file(
        self,
        file_path: str | None
    ) -> str | None:

        if not file_path:
            return None

        path = Path(file_path)

        if not path.is_absolute():
            path = self.project_root / file_path

        try:

            return path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        except Exception:

            return None

    # =======================================================

    def _find_related_files(
        self,
        error: ErrorInfo
    ) -> List[RelatedFile]:

        related = []

        keywords = []

        if error.file:

            keywords.append(
                Path(error.file).stem.lower()
            )

        if "No module named" in error.message:

            try:

                module = error.message.split("'")[1]

                keywords.append(module.lower())

            except Exception:

                pass

        for file in self.project_root.rglob("*"):

            if not file.is_file():
                continue

            if file.suffix not in self.SOURCE_EXTENSIONS:
                continue

            relative = str(
                file.relative_to(self.project_root)
            )

            include = any(
                keyword in relative.lower()
                for keyword in keywords
            )

            if not include:
                continue

            try:

                related.append(

                    RelatedFile(

                        path=relative,

                        content=file.read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )

                    )

                )

            except Exception:

                pass

        if error.file:

            if not any(
                r.path == error.file
                for r in related
            ):

                content = self._read_failing_file(
                    error.file
                )

                if content:

                    related.insert(

                        0,

                        RelatedFile(

                            path=error.file,

                            content=content

                        )

                    )

        return related

    # =======================================================

    def summarize(
        self,
        context: DebugContext
    ) -> None:

        print("\n========== DEBUG CONTEXT ==========\n")

        print(f"Error Type : {context.error_type}")
        print(f"Message    : {context.error_message}")
        print(f"File       : {context.failing_file}")
        print(f"Line       : {context.failing_line}")

        print("\nRelated Files:")

        for file in context.related_files:

            print(f" - {file.path}")

        print("\n===================================\n")