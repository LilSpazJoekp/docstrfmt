"""Exceptions for docstrfmt."""

from __future__ import annotations

from collections.abc import Sized
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class DocstrfmtError(Exception):
    """Base exception class for docstrfmt."""


class InvalidRstError(ValueError):
    """An error that occurred while parsing RST."""

    @property
    def error_message(self) -> str:
        """Return a formatted error message."""
        return (
            f"{self.level}: File"
            f' "{self.file}"{f", line {self.line}" if self.line else ""}:\n{self.message}'
        )

    def __init__(self, file: Path | str, level: str, line: int, message: str) -> None:
        """Initialize an invalid RST error.

        :param file: The file where the error occurred.
        :param level: The severity level of the error.
        :param line: The line number where the error occurred.
        :param message: The error message.

        """
        self.file = file
        self.level = level

        self.line = line
        self.message = message

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return self.error_message


class InvalidRstErrors(DocstrfmtError, Sized):
    """Container for multiple invalid RST errors."""

    def __len__(self) -> int:  # pragma: no cover
        """Return the number of errors."""
        return len(self.errors)

    def __init__(self, errors: list[InvalidRstError]) -> None:
        """Initialize the error container with a list of errors.

        :param errors: List of InvalidRstError instances.

        """
        self.errors = errors

    def __str__(self) -> str:
        """Return a string representation of the errors."""
        return "\n".join([str(error) for error in self.errors])
