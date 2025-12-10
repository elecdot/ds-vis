from __future__ import annotations

"""
Domain models for data structures.

Each model encapsulates the logical state and exposes operations that
return structural Timelines (no coordinates), which are later passed
through the layout engine.

Contract:
      - All mutating operations (insert/delete/rotate/etc.) MUST:
        1) update the internal tree structure,
        2) produce a structural Timeline that is consistent with the new state.
"""
