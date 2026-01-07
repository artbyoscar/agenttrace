"""
Tests for audit verification system.
"""

import pytest
from datetime import datetime, date, timezone, timedelta

from ..models.audit import (
    AuditEvent,
    ActorType,
    EventCategory,
    Action,
    Severity
)
from ..models.audit_verification import (
    VerificationStatus,
    TamperingType
)
from ..services.audit_verification import (
    AuditChain,
    AuditMerkleTree,
    TimestampAuthority,
    AuditCheckpoint
)


@pytest.fixture
def audit_chain():
    """Create AuditChain instance."""
    return AuditChain()


@pytest.fixture
def merkle_tree():
    """Create AuditMerkleTree instance."""
    return AuditMerkleTree()


@pytest.fixture
def timestamp_authority():
    """Create TimestampAuthority instance."""
    return TimestampAuthority()


@pytest.fixture
def sample_events():
    """Create a chain of sample events."""
    events = []
    previous_hash = ""

    for i in range(5):
        event = AuditEvent(
            event_id=f"event-{i}",
            timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            organization_id="org-123",
            actor_type=ActorType.USER,
            actor_id=f"user-{i}",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}",
            previous_hash=previous_hash
        )
        events.append(event)
        previous_hash = event.hash

    return events


# AuditChain Tests

def test_compute_event_hash(audit_chain):
    """Test hash computation for an event."""
    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        request_id="req-123"
    )

    hash_value = audit_chain.compute_event_hash(event)

    # Hash should be 64 character hex string (SHA-256)
    assert len(hash_value) == 64
    assert all(c in '0123456789abcdef' for c in hash_value)

    # Computing hash again should give same result (deterministic)
    hash_value2 = audit_chain.compute_event_hash(event)
    assert hash_value == hash_value2


def test_compute_event_hash_different_events(audit_chain):
    """Test that different events have different hashes."""
    event1 = AuditEvent(
        event_id="test-1",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-1",
        action=Action.CREATE,
        request_id="req-1"
    )

    event2 = AuditEvent(
        event_id="test-2",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-2",  # Different resource
        action=Action.CREATE,
        request_id="req-2"
    )

    hash1 = audit_chain.compute_event_hash(event1)
    hash2 = audit_chain.compute_event_hash(event2)

    assert hash1 != hash2


def test_link_to_chain_first_event(audit_chain):
    """Test linking first event (no previous event)."""
    event = AuditEvent(
        event_id="test-1",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-1",
        action=Action.CREATE,
        request_id="req-1"
    )

    previous_hash = audit_chain.link_to_chain(event, None)

    assert previous_hash == ""


def test_link_to_chain_second_event(audit_chain):
    """Test linking second event to first."""
    event1 = AuditEvent(
        event_id="test-1",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-1",
        action=Action.CREATE,
        request_id="req-1"
    )

    event2 = AuditEvent(
        event_id="test-2",
        timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-2",
        action=Action.CREATE,
        request_id="req-2"
    )

    previous_hash = audit_chain.link_to_chain(event2, event1)

    assert previous_hash == event1.hash


def test_verify_chain_valid(audit_chain, sample_events):
    """Test verification of valid event chain."""
    result = audit_chain.verify_chain(sample_events)

    assert result.status == VerificationStatus.VALID
    assert result.total_events == 5
    assert result.valid_events == 5
    assert result.invalid_events == 0
    assert len(result.broken_links) == 0
    assert len(result.hash_mismatches) == 0


def test_verify_chain_empty(audit_chain):
    """Test verification of empty chain."""
    result = audit_chain.verify_chain([])

    assert result.status == VerificationStatus.VALID
    assert result.total_events == 0


def test_verify_chain_hash_mismatch(audit_chain, sample_events):
    """Test verification detects hash mismatches."""
    # Tamper with an event's hash
    sample_events[2].hash = "tampered_hash"

    result = audit_chain.verify_chain(sample_events)

    assert result.status == VerificationStatus.INCOMPLETE
    assert result.invalid_events > 0
    assert "event-2" in result.hash_mismatches


def test_verify_chain_broken_link(audit_chain, sample_events):
    """Test verification detects broken chain links."""
    # Break the chain
    sample_events[2].previous_hash = "wrong_hash"

    result = audit_chain.verify_chain(sample_events)

    assert result.status == VerificationStatus.INCOMPLETE
    assert result.invalid_events > 0
    assert "event-2" in result.broken_links


def test_find_tampering_none(audit_chain, sample_events):
    """Test tampering detection with valid events."""
    indicators = audit_chain.find_tampering(sample_events)

    assert len(indicators) == 0


def test_find_tampering_hash_mismatch(audit_chain, sample_events):
    """Test tampering detection finds hash mismatches."""
    # Tamper with event
    sample_events[2].hash = "tampered_hash"

    indicators = audit_chain.find_tampering(sample_events)

    assert len(indicators) > 0
    assert any(i.tampering_type == TamperingType.HASH_MISMATCH for i in indicators)
    assert any(i.event_id == "event-2" for i in indicators)


def test_find_tampering_chain_break(audit_chain, sample_events):
    """Test tampering detection finds chain breaks."""
    # Break the chain
    sample_events[2].previous_hash = "wrong_hash"

    indicators = audit_chain.find_tampering(sample_events)

    assert len(indicators) > 0
    assert any(i.tampering_type == TamperingType.CHAIN_BREAK for i in indicators)


def test_find_tampering_timestamp_anomaly(audit_chain, sample_events):
    """Test tampering detection finds timestamp anomalies."""
    # Make an event timestamp before the previous one
    sample_events[2].timestamp = sample_events[1].timestamp - timedelta(hours=1)

    indicators = audit_chain.find_tampering(sample_events)

    assert len(indicators) > 0
    assert any(i.tampering_type == TamperingType.TIMESTAMP_ANOMALY for i in indicators)


# AuditMerkleTree Tests

def test_build_tree_empty(merkle_tree):
    """Test building Merkle tree with no events."""
    root = merkle_tree.build_tree([])

    assert root.event_count == 0
    assert root.root_hash is not None


def test_build_tree_single_event(merkle_tree, sample_events):
    """Test building Merkle tree with single event."""
    root = merkle_tree.build_tree([sample_events[0]])

    assert root.event_count == 1
    assert root.root_hash == sample_events[0].hash


def test_build_tree_multiple_events(merkle_tree, sample_events):
    """Test building Merkle tree with multiple events."""
    root = merkle_tree.build_tree(sample_events)

    assert root.event_count == 5
    assert root.root_hash is not None
    assert len(root.root_hash) == 64  # SHA-256 hex


def test_build_tree_deterministic(merkle_tree, sample_events):
    """Test that building tree is deterministic."""
    root1 = merkle_tree.build_tree(sample_events)
    root2 = merkle_tree.build_tree(sample_events)

    assert root1.root_hash == root2.root_hash


def test_generate_proof(merkle_tree, sample_events):
    """Test generating Merkle proof for an event."""
    root = merkle_tree.build_tree(sample_events)

    # Generate proof for middle event
    proof = merkle_tree.generate_proof(sample_events[2], root)

    assert proof is not None
    assert proof.event_id == "event-2"
    assert proof.event_hash == sample_events[2].hash
    assert proof.root_hash == root.root_hash
    assert len(proof.proof_hashes) > 0


def test_generate_proof_not_in_tree(merkle_tree, sample_events):
    """Test generating proof for event not in tree."""
    root = merkle_tree.build_tree(sample_events[:3])

    # Try to generate proof for event not in tree
    proof = merkle_tree.generate_proof(sample_events[4], root)

    assert proof is None


def test_verify_proof_valid(merkle_tree, sample_events):
    """Test verifying valid Merkle proof."""
    root = merkle_tree.build_tree(sample_events)
    proof = merkle_tree.generate_proof(sample_events[2], root)

    is_valid = merkle_tree.verify_proof(sample_events[2], proof, root)

    assert is_valid is True


def test_verify_proof_tampered_event(merkle_tree, sample_events):
    """Test verifying proof with tampered event."""
    root = merkle_tree.build_tree(sample_events)
    proof = merkle_tree.generate_proof(sample_events[2], root)

    # Tamper with event
    tampered_event = sample_events[2]
    tampered_event.hash = "tampered_hash"

    is_valid = merkle_tree.verify_proof(tampered_event, proof, root)

    assert is_valid is False


def test_verify_proof_wrong_root(merkle_tree, sample_events):
    """Test verifying proof against wrong root."""
    root1 = merkle_tree.build_tree(sample_events[:3])
    root2 = merkle_tree.build_tree(sample_events[3:])

    proof = merkle_tree.generate_proof(sample_events[1], root1)

    # Verify against wrong root
    is_valid = merkle_tree.verify_proof(sample_events[1], proof, root2)

    assert is_valid is False


# TimestampAuthority Tests

@pytest.mark.asyncio
async def test_get_timestamp_token(timestamp_authority):
    """Test requesting timestamp token."""
    hash_value = "abc123def456"

    token = await timestamp_authority.get_timestamp_token(hash_value)

    assert token is not None
    assert token.message_imprint == hash_value
    assert token.hash_algorithm == "sha256"
    assert token.timestamp is not None


@pytest.mark.asyncio
async def test_verify_timestamp_valid(timestamp_authority):
    """Test verifying valid timestamp."""
    hash_value = "abc123def456"

    token = await timestamp_authority.get_timestamp_token(hash_value)
    is_valid = timestamp_authority.verify_timestamp(token, hash_value)

    assert is_valid is True


@pytest.mark.asyncio
async def test_verify_timestamp_wrong_hash(timestamp_authority):
    """Test verifying timestamp with wrong hash."""
    hash_value = "abc123def456"

    token = await timestamp_authority.get_timestamp_token(hash_value)
    is_valid = timestamp_authority.verify_timestamp(token, "different_hash")

    assert is_valid is False


# Integration Tests

@pytest.mark.asyncio
async def test_full_verification_workflow(audit_chain, merkle_tree, sample_events):
    """Test complete verification workflow."""
    # 1. Verify chain
    chain_result = audit_chain.verify_chain(sample_events)
    assert chain_result.status == VerificationStatus.VALID

    # 2. Check for tampering
    tampering = audit_chain.find_tampering(sample_events)
    assert len(tampering) == 0

    # 3. Build Merkle tree
    root = merkle_tree.build_tree(sample_events)
    assert root.event_count == len(sample_events)

    # 4. Generate and verify proof for each event
    for event in sample_events:
        proof = merkle_tree.generate_proof(event, root)
        assert proof is not None

        is_valid = merkle_tree.verify_proof(event, proof, root)
        assert is_valid is True


@pytest.mark.asyncio
async def test_detect_multiple_tampering_types(audit_chain, sample_events):
    """Test detecting multiple types of tampering."""
    # Introduce multiple tampering types
    sample_events[1].hash = "tampered_hash"  # Hash mismatch
    sample_events[2].previous_hash = "wrong_hash"  # Chain break
    sample_events[3].timestamp = sample_events[2].timestamp - timedelta(hours=1)  # Timestamp anomaly

    indicators = audit_chain.find_tampering(sample_events)

    # Should detect all three types
    types_found = set(i.tampering_type for i in indicators)
    assert TamperingType.HASH_MISMATCH in types_found
    assert TamperingType.CHAIN_BREAK in types_found
    assert TamperingType.TIMESTAMP_ANOMALY in types_found


def test_merkle_tree_with_power_of_two_events(merkle_tree):
    """Test Merkle tree with power of 2 events (perfectly balanced)."""
    events = []
    for i in range(8):  # 2^3 events
        event = AuditEvent(
            event_id=f"event-{i}",
            timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}"
        )
        events.append(event)

    root = merkle_tree.build_tree(events)

    assert root.event_count == 8

    # Verify all events
    for event in events:
        proof = merkle_tree.generate_proof(event, root)
        assert proof is not None
        assert merkle_tree.verify_proof(event, proof, root) is True
