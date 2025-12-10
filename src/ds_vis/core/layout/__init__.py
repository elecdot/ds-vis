from __future__ import annotations

"""
Layout engine for visual positioning.

The layout layer is responsible for:
  - taking a structural Timeline (no SET_POS ops),
  - computing positions for nodes/edges based on the structure's shape,
  - injecting or updating SET_POS operations to produce a visual Timeline.

This keeps domain models free from rendering coordinates and allows
different renderers (desktop/web) to share common layout logic.
(Specific layout classes can be implemented here or in separate files in the future;
currently, only roles and protocols are defined.)"
"""

from typing import Protocol

from ds_vis.core.ops import Timeline


class LayoutEngine(Protocol):
    """
    Protocol for layout engines.

    Implementations are expected to:
      - read the structural Timeline,
      - compute positions for each step,
      - return a new Timeline that includes SET_POS ops.
    """

    def apply_layout(self, timeline: Timeline) -> Timeline:  # pragma: no cover - protocol
        ...
