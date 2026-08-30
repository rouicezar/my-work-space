"""Conservative macOS resource evidence for local inference routing."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


PAGE_SIZE = re.compile(r"page size of ([0-9]+) bytes")
PAGE_LINE = re.compile(r'^Pages (free|inactive|speculative):\s+([0-9]+)\.$')


@dataclass(frozen=True)
class MemoryEvidence:
    available_memory_mb: int
    verified: bool
    code: str


def parse_vm_stat(output: str) -> MemoryEvidence:
    header = PAGE_SIZE.search(output)
    if header is None:
        return MemoryEvidence(0, False, "AVAILABLE_MEMORY_UNKNOWN")
    page_size = int(header.group(1))
    pages: dict[str, int] = {}
    for line in output.splitlines():
        match = PAGE_LINE.fullmatch(line.strip())
        if match:
            pages[match.group(1)] = int(match.group(2))
    if page_size <= 0 or set(pages) != {"free", "inactive", "speculative"}:
        return MemoryEvidence(0, False, "AVAILABLE_MEMORY_UNKNOWN")
    available = sum(pages.values()) * page_size // (1024 * 1024)
    if available <= 0:
        return MemoryEvidence(0, False, "AVAILABLE_MEMORY_UNKNOWN")
    return MemoryEvidence(available, True, "AVAILABLE_MEMORY_MEASURED")


def measure_available_memory() -> MemoryEvidence:
    try:
        result = subprocess.run(
            ["/usr/bin/vm_stat"], capture_output=True, text=True,
            check=False, timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return MemoryEvidence(0, False, "AVAILABLE_MEMORY_UNKNOWN")
    if result.returncode != 0:
        return MemoryEvidence(0, False, "AVAILABLE_MEMORY_UNKNOWN")
    return parse_vm_stat(result.stdout)
