"""Replication event detection for BFF programs.

This module provides exact replication detection without heuristics or thresholds.
It identifies when programs successfully copy themselves during interaction.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ReplicationEvent:
    """Records the outcome of a program interaction for replication analysis.
    
    Attributes:
        kind: Type of replication detected:
            - "A_exact_replicator": A copied itself to B (A' == A and B' == A)
            - "B_exact_replicator": B copied itself to A (A' == B and B' == B)
            - "none": No exact replication occurred
        A_before: Program A before interaction (64 bytes)
        B_before: Program B before interaction (64 bytes)
        A_after: Program A after interaction (64 bytes)
        B_after: Program B after interaction (64 bytes)
    """
    kind: Literal["A_exact_replicator", "B_exact_replicator", "none"]
    A_before: bytes
    B_before: bytes
    A_after: bytes
    B_after: bytes


def detect_exact_replication(
    A_before: bytes,
    B_before: bytes,
    A_after: bytes,
    B_after: bytes
) -> ReplicationEvent:
    """Detect exact self-replication events using byte-for-byte comparison.
    
    This function identifies two patterns of exact replication:
    - A_exact_replicator: A' == A and B' == A (A copied itself to B's location)
    - B_exact_replicator: A' == B and B' == B (B copied itself to A's location)
    
    No thresholds, similarity scores, or heuristics are used. Only exact
    byte-for-byte matches are considered replication events.
    
    Args:
        A_before: Program A before interaction (must be exactly 64 bytes)
        B_before: Program B before interaction (must be exactly 64 bytes)
        A_after: Program A after interaction (must be exactly 64 bytes)
        B_after: Program B after interaction (must be exactly 64 bytes)
    
    Returns:
        ReplicationEvent with kind indicating the type of replication detected
        and all before/after states recorded.
    
    Raises:
        ValueError: If any program is not exactly 64 bytes.
    """
    # Validate all programs are exactly 64 bytes
    if len(A_before) != 64:
        raise ValueError(f"A_before must be 64 bytes, got {len(A_before)}")
    if len(B_before) != 64:
        raise ValueError(f"B_before must be 64 bytes, got {len(B_before)}")
    if len(A_after) != 64:
        raise ValueError(f"A_after must be 64 bytes, got {len(A_after)}")
    if len(B_after) != 64:
        raise ValueError(f"B_after must be 64 bytes, got {len(B_after)}")
    
    # Check A_exact_replicator pattern: A' == A and B' == A
    # This means A successfully copied itself to B's location
    if A_after == A_before and B_after == A_before:
        return ReplicationEvent(
            kind="A_exact_replicator",
            A_before=A_before,
            B_before=B_before,
            A_after=A_after,
            B_after=B_after
        )
    
    # Check B_exact_replicator pattern: A' == B and B' == B
    # This means B successfully copied itself to A's location
    if A_after == B_before and B_after == B_before:
        return ReplicationEvent(
            kind="B_exact_replicator",
            A_before=A_before,
            B_before=B_before,
            A_after=A_after,
            B_after=B_after
        )
    
    # No exact replication pattern matched
    return ReplicationEvent(
        kind="none",
        A_before=A_before,
        B_before=B_before,
        A_after=A_after,
        B_after=B_after
    )
