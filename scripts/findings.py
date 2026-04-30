"""Shared finding/issue records for Autobahn validators.

Validators are read-only. They emit `Issue` records describing what is wrong
and, where the architecture's hierarchy determines the answer, a `verdict`
naming the winner. Whoever consumes the output (an LLM, a human, CI) reads
the verdict line to decide whether to act mechanically or escalate.

Verdict semantics:
  - `verdict` set     → hierarchy resolved the conflict; the verdict states
                        what the file should look like. The next operation
                        is determined.
  - `verdict` is None → no parent in the hierarchy can arbitrate. Human
                        engagement required.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    """A single validator finding for one file.

    error    - what is wrong, in plain prose.
    verdict  - what the file should be, when the architecture's hierarchy
               determines the answer. None when the conflict cannot be
               resolved without human input.
    """
    error: str
    verdict: str | None = None

    @property
    def kind(self) -> str:
        return "determined" if self.verdict else "human"
