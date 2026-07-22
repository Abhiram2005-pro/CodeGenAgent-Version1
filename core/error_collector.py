from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class ErrorInfo:
    error_type: str
    message: str
    file: str | None = None
    line: int | None = None
    traceback: str | None = None


class ErrorCollector:

    def collect(self, stderr: str) -> ErrorInfo:

        stderr = (stderr or "").strip()

        if not stderr:
            return ErrorInfo(
                error_type="Unknown",
                message="No error output.",
                traceback=""
            )

        error_type = "Unknown"
        message = stderr.splitlines()[-1]

        patterns = [
            r"(ModuleNotFoundError): (.+)",
            r"(ImportError): (.+)",
            r"(SyntaxError): (.+)",
            r"(NameError): (.+)",
            r"(TypeError): (.+)",
            r"(AttributeError): (.+)",
            r"(AssertionError): ?(.*)",
            r"(ValueError): (.+)",
            r"(IndexError): (.+)",
            r"(KeyError): (.+)",
            r"(FileNotFoundError): (.+)"
        ]

        for pattern in patterns:

            match = re.search(pattern, stderr)

            if match:
                error_type = match.group(1)
                message = match.group(2).strip()
                break

        file = None
        line = None

        file_matches = re.findall(
            r'File "(.+?)", line (\d+)',
            stderr
        )

        if file_matches:
            file = file_matches[-1][0]
            line = int(file_matches[-1][1])

        return ErrorInfo(
            error_type=error_type,
            message=message,
            file=file,
            line=line,
            traceback=stderr
        )