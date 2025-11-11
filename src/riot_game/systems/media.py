"""Media transparency and reputation tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MediaSystem:
    """Maintains transparency and oversight indices."""

    transparency_index: float = 60.0

    def apply_visibility(self, media_visibility: int) -> None:
        self.transparency_index = max(
            0.0, min(100.0, self.transparency_index + media_visibility * 0.8)
        )

    def apply_decision(self, transparency_delta: float) -> None:
        self.transparency_index = max(
            0.0, min(100.0, self.transparency_index + transparency_delta)
        )

    def snapshot(self) -> float:
        return round(self.transparency_index, 2)


__all__ = ["MediaSystem"]
