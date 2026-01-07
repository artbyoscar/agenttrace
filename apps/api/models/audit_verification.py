"""
Audit Verification Models

Data structures for cryptographic verification of audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum


class VerificationStatus(str, Enum):
    """Status of verification result."""
    VALID = "valid"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"


class TamperingType(str, Enum):
    """Type of tampering detected."""
    HASH_MISMATCH = "hash_mismatch"
    CHAIN_BREAK = "chain_break"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"
    SEQUENCE_GAP = "sequence_gap"
    MISSING_EVENT = "missing_event"
    DUPLICATE_EVENT = "duplicate_event"


@dataclass
class ChainVerificationResult:
    """
    Result of hash chain verification.

    Attributes:
        status: Overall verification status
        total_events: Total number of events verified
        valid_events: Number of events that passed verification
        invalid_events: Number of events that failed verification
        first_event_id: ID of first event in chain
        last_event_id: ID of last event in chain
        broken_links: List of event IDs where chain breaks occur
        hash_mismatches: List of event IDs with hash mismatches
        errors: Detailed error information
        verified_at: Timestamp when verification was performed
    """
    status: VerificationStatus
    total_events: int
    valid_events: int
    invalid_events: int
    first_event_id: Optional[str] = None
    last_event_id: Optional[str] = None
    broken_links: List[str] = field(default_factory=list)
    hash_mismatches: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    verified_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "total_events": self.total_events,
            "valid_events": self.valid_events,
            "invalid_events": self.invalid_events,
            "first_event_id": self.first_event_id,
            "last_event_id": self.last_event_id,
            "broken_links": self.broken_links,
            "hash_mismatches": self.hash_mismatches,
            "errors": self.errors,
            "verified_at": self.verified_at.isoformat()
        }


@dataclass
class TamperingIndicator:
    """
    Indicator of potential tampering.

    Attributes:
        event_id: ID of affected event
        tampering_type: Type of tampering detected
        severity: Severity level (1-10)
        description: Human-readable description
        evidence: Supporting evidence
        detected_at: When tampering was detected
    """
    event_id: str
    tampering_type: TamperingType
    severity: int
    description: str
    evidence: Dict[str, Any]
    detected_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "tampering_type": self.tampering_type.value,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class MerkleNode:
    """
    Node in Merkle tree.

    Attributes:
        hash: Hash value of this node
        left: Left child node
        right: Right child node
        event_id: Associated event ID (for leaf nodes)
    """
    hash: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    event_id: Optional[str] = None

    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return self.left is None and self.right is None


@dataclass
class MerkleRoot:
    """
    Root of Merkle tree.

    Attributes:
        root_hash: Hash of root node
        tree: Root node of tree
        event_count: Number of events in tree
        created_at: When tree was created
        metadata: Additional metadata
    """
    root_hash: str
    tree: MerkleNode
    event_count: int
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root_hash": self.root_hash,
            "event_count": self.event_count,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class MerkleProof:
    """
    Merkle proof for event inclusion.

    Attributes:
        event_id: ID of event being proved
        event_hash: Hash of the event
        proof_hashes: List of sibling hashes in path to root
        proof_directions: List of directions (left/right) for each hash
        root_hash: Expected root hash
    """
    event_id: str
    event_hash: str
    proof_hashes: List[str]
    proof_directions: List[str]  # "left" or "right"
    root_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_hash": self.event_hash,
            "proof_hashes": self.proof_hashes,
            "proof_directions": self.proof_directions,
            "root_hash": self.root_hash
        }


@dataclass
class TimestampToken:
    """
    RFC 3161 timestamp token.

    Attributes:
        hash_algorithm: Algorithm used (e.g., "sha256")
        message_imprint: Hash value that was timestamped
        timestamp: Time from TSA
        tsa_name: Name of timestamp authority
        serial_number: Token serial number
        signature: Digital signature from TSA
        certificate_chain: X.509 certificates for verification
        policy_oid: TSA policy OID
    """
    hash_algorithm: str
    message_imprint: str
    timestamp: datetime
    tsa_name: str
    serial_number: str
    signature: bytes
    certificate_chain: List[bytes] = field(default_factory=list)
    policy_oid: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hash_algorithm": self.hash_algorithm,
            "message_imprint": self.message_imprint,
            "timestamp": self.timestamp.isoformat(),
            "tsa_name": self.tsa_name,
            "serial_number": self.serial_number,
            "policy_oid": self.policy_oid
        }


@dataclass
class Checkpoint:
    """
    Daily audit checkpoint.

    Attributes:
        checkpoint_date: Date of checkpoint
        organization_id: Organization identifier
        merkle_root: Merkle root of day's events
        event_count: Number of events in checkpoint
        first_event_hash: Hash of first event
        last_event_hash: Hash of last event
        timestamp_token: TSA timestamp token
        previous_checkpoint_hash: Hash of previous checkpoint
        checkpoint_hash: Hash of this checkpoint
        created_at: When checkpoint was created
        metadata: Additional metadata
    """
    checkpoint_date: date
    organization_id: str
    merkle_root: str
    event_count: int
    first_event_hash: str
    last_event_hash: str
    timestamp_token: Optional[TimestampToken] = None
    previous_checkpoint_hash: str = ""
    checkpoint_hash: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_date": self.checkpoint_date.isoformat(),
            "organization_id": self.organization_id,
            "merkle_root": self.merkle_root,
            "event_count": self.event_count,
            "first_event_hash": self.first_event_hash,
            "last_event_hash": self.last_event_hash,
            "timestamp_token": self.timestamp_token.to_dict() if self.timestamp_token else None,
            "previous_checkpoint_hash": self.previous_checkpoint_hash,
            "checkpoint_hash": self.checkpoint_hash,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class CheckpointVerificationResult:
    """
    Result of checkpoint verification.

    Attributes:
        status: Verification status
        checkpoint_date: Date of checkpoint
        checkpoint_hash_valid: Whether checkpoint hash is valid
        merkle_root_valid: Whether Merkle root is valid
        timestamp_valid: Whether timestamp is valid
        chain_valid: Whether chain to previous checkpoint is valid
        errors: Any errors encountered
        verified_at: When verification was performed
    """
    status: VerificationStatus
    checkpoint_date: date
    checkpoint_hash_valid: bool = False
    merkle_root_valid: bool = False
    timestamp_valid: bool = False
    chain_valid: bool = False
    errors: List[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "checkpoint_date": self.checkpoint_date.isoformat(),
            "checkpoint_hash_valid": self.checkpoint_hash_valid,
            "merkle_root_valid": self.merkle_root_valid,
            "timestamp_valid": self.timestamp_valid,
            "chain_valid": self.chain_valid,
            "errors": self.errors,
            "verified_at": self.verified_at.isoformat()
        }


@dataclass
class VerificationReport:
    """
    Comprehensive verification report.

    Attributes:
        organization_id: Organization verified
        time_range: Time range of verification
        chain_result: Hash chain verification result
        tampering_indicators: List of tampering indicators
        checkpoints_verified: List of checkpoint verification results
        overall_status: Overall verification status
        generated_at: When report was generated
    """
    organization_id: str
    time_range: Dict[str, datetime]
    chain_result: ChainVerificationResult
    tampering_indicators: List[TamperingIndicator] = field(default_factory=list)
    checkpoints_verified: List[CheckpointVerificationResult] = field(default_factory=list)
    overall_status: VerificationStatus = VerificationStatus.UNKNOWN
    generated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "organization_id": self.organization_id,
            "time_range": {
                "start": self.time_range["start"].isoformat(),
                "end": self.time_range["end"].isoformat()
            },
            "chain_result": self.chain_result.to_dict(),
            "tampering_indicators": [ti.to_dict() for ti in self.tampering_indicators],
            "checkpoints_verified": [cv.to_dict() for cv in self.checkpoints_verified],
            "overall_status": self.overall_status.value,
            "generated_at": self.generated_at.isoformat()
        }
