"""Strategy contract for digitizing physical-photo captures.

The interface takes a *list* of PIL images even though the single-shot MVP
always passes exactly one. That keeps the contract forward-compatible with
multi-shot capture (glare removal / super-resolution from several frames)
without any interface change — swap the strategy, not the plumbing.
"""
from typing import Protocol, runtime_checkable, Optional
from dataclasses import dataclass
from PIL import Image


@dataclass
class DigitizeResult:
    image: Image.Image
    was_digitized: bool
    confidence: float
    corners: Optional[list[tuple[int, int]]] = None
    strategy: str = "single_shot"


@runtime_checkable
class DigitizeStrategy(Protocol):
    name: str

    def execute(self, images: list[Image.Image]) -> DigitizeResult:
        """Rectify one or more captures of the same physical photo into a
        single clean image. Single-shot: len(images) == 1."""
        ...
