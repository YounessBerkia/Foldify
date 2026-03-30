"""Core file organization logic."""

from .executor import FileOperation, OperationExecutor
from .organizer import OrganizationResult, Organizer
from .scanner import FileInfo, FileScanner

# note: these are the main public API exports
# everything else should be considered internal
__all__ = [
    "FileInfo",
    "FileOperation",
    "FileScanner",
    "OperationExecutor",
    "Organizer",
    "OrganizationResult",
]
