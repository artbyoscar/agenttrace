"""Models package for AgentTrace API."""

from .audit import (
    ActorType,
    EventCategory,
    Severity,
    Action,
    AuditEvent,
    AuditEventFilter,
)

from .audit_verification import (
    VerificationStatus,
    TamperingType,
    ChainVerificationResult,
    TamperingIndicator,
    MerkleNode,
    MerkleRoot,
    MerkleProof,
    TimestampToken,
    Checkpoint,
    CheckpointVerificationResult,
    VerificationReport,
)

__all__ = [
    # Audit models
    "ActorType",
    "EventCategory",
    "Severity",
    "Action",
    "AuditEvent",
    "AuditEventFilter",
    # Verification models
    "VerificationStatus",
    "TamperingType",
    "ChainVerificationResult",
    "TamperingIndicator",
    "MerkleNode",
    "MerkleRoot",
    "MerkleProof",
    "TimestampToken",
    "Checkpoint",
    "CheckpointVerificationResult",
    "VerificationReport",
]
