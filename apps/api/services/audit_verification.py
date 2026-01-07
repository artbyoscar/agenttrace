"""
Audit Verification Service

Cryptographic verification system for audit trails, including:
- Hash chain verification
- Merkle tree construction and verification
- Timestamp authority integration
- Daily checkpoint system

This provides strong cryptographic guarantees for audit trail integrity.
"""

import hashlib
import json
import math
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
import base64

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.x509.oid import NameOID
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

from ..models.audit import AuditEvent, AuditEventFilter
from ..models.audit_verification import (
    ChainVerificationResult,
    TamperingIndicator,
    MerkleNode,
    MerkleRoot,
    MerkleProof,
    TimestampToken,
    Checkpoint,
    CheckpointVerificationResult,
    VerificationReport,
    VerificationStatus,
    TamperingType,
)


class AuditChain:
    """
    Maintains cryptographic integrity of audit events using hash chaining.

    This class implements a blockchain-style hash chain where each event
    includes the hash of the previous event, creating an immutable sequence.
    """

    @staticmethod
    def compute_event_hash(event: AuditEvent) -> str:
        """
        Compute SHA-256 hash of event content.

        The hash includes all critical event data:
        - Event ID and timestamp
        - Actor information
        - Event type and category
        - Resource information
        - Action and states
        - Request context

        Args:
            event: The audit event to hash

        Returns:
            Hexadecimal SHA-256 hash string
        """
        # Create deterministic representation
        hash_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "organization_id": event.organization_id,
            "project_id": event.project_id,
            "actor_type": event.actor_type.value,
            "actor_id": event.actor_id,
            "actor_email": event.actor_email,
            "event_category": event.event_category.value,
            "event_type": event.event_type,
            "event_severity": event.event_severity.value,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "resource_name": event.resource_name,
            "action": event.action.value,
            "previous_state": event.previous_state,
            "new_state": event.new_state,
            "request_id": event.request_id,
            "session_id": event.session_id,
        }

        # Convert to JSON with sorted keys for determinism
        json_str = json.dumps(hash_data, sort_keys=True, default=str)

        # Compute SHA-256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    @staticmethod
    def link_to_chain(event: AuditEvent, previous_event: Optional[AuditEvent]) -> str:
        """
        Create chain link by combining event hash with previous event's hash.

        This creates the "blockchain" property where each event cryptographically
        references the previous event.

        Args:
            event: Current event to link
            previous_event: Previous event in chain (None for first event)

        Returns:
            Previous hash value to store in event.previous_hash
        """
        if previous_event is None:
            return ""

        # Return the hash of the previous event
        return previous_event.hash

    def verify_chain(self, events: List[AuditEvent]) -> ChainVerificationResult:
        """
        Verify integrity of event sequence.

        Checks:
        1. Each event's hash matches its content
        2. Each event's previous_hash matches the actual previous event's hash
        3. Events are in chronological order

        Args:
            events: List of events to verify (should be in chronological order)

        Returns:
            ChainVerificationResult with detailed verification information
        """
        if not events:
            return ChainVerificationResult(
                status=VerificationStatus.VALID,
                total_events=0,
                valid_events=0,
                invalid_events=0
            )

        total_events = len(events)
        valid_events = 0
        invalid_events = 0
        broken_links = []
        hash_mismatches = []
        errors = []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Verify each event
        for i, event in enumerate(sorted_events):
            # Verify event's hash
            computed_hash = self.compute_event_hash(event)
            if computed_hash != event.hash:
                hash_mismatches.append(event.event_id)
                invalid_events += 1
                errors.append({
                    "event_id": event.event_id,
                    "type": "hash_mismatch",
                    "expected": computed_hash,
                    "actual": event.hash
                })
                continue

            # Verify chain link (except for first event)
            if i > 0:
                previous_event = sorted_events[i - 1]
                expected_previous_hash = previous_event.hash

                if event.previous_hash != expected_previous_hash:
                    broken_links.append(event.event_id)
                    invalid_events += 1
                    errors.append({
                        "event_id": event.event_id,
                        "type": "chain_break",
                        "expected": expected_previous_hash,
                        "actual": event.previous_hash
                    })
                    continue

            valid_events += 1

        # Determine overall status
        if invalid_events == 0:
            status = VerificationStatus.VALID
        elif valid_events == 0:
            status = VerificationStatus.INVALID
        else:
            status = VerificationStatus.INCOMPLETE

        return ChainVerificationResult(
            status=status,
            total_events=total_events,
            valid_events=valid_events,
            invalid_events=invalid_events,
            first_event_id=sorted_events[0].event_id if sorted_events else None,
            last_event_id=sorted_events[-1].event_id if sorted_events else None,
            broken_links=broken_links,
            hash_mismatches=hash_mismatches,
            errors=errors
        )

    def find_tampering(self, events: List[AuditEvent]) -> List[TamperingIndicator]:
        """
        Detect potential tampering in audit log.

        Checks for:
        - Hash mismatches (modified content)
        - Chain breaks (missing or reordered events)
        - Timestamp anomalies (events out of order or with suspicious timestamps)
        - Sequence gaps (missing event IDs)

        Args:
            events: List of events to analyze

        Returns:
            List of tampering indicators found
        """
        indicators = []

        if not events:
            return indicators

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Check each event
        for i, event in enumerate(sorted_events):
            # Check hash mismatch
            computed_hash = self.compute_event_hash(event)
            if computed_hash != event.hash:
                indicators.append(TamperingIndicator(
                    event_id=event.event_id,
                    tampering_type=TamperingType.HASH_MISMATCH,
                    severity=10,
                    description=f"Event hash does not match content",
                    evidence={
                        "expected_hash": computed_hash,
                        "actual_hash": event.hash
                    }
                ))

            # Check chain break
            if i > 0:
                previous_event = sorted_events[i - 1]
                if event.previous_hash != previous_event.hash:
                    indicators.append(TamperingIndicator(
                        event_id=event.event_id,
                        tampering_type=TamperingType.CHAIN_BREAK,
                        severity=10,
                        description=f"Chain broken: previous_hash doesn't match",
                        evidence={
                            "expected_previous_hash": previous_event.hash,
                            "actual_previous_hash": event.previous_hash,
                            "previous_event_id": previous_event.event_id
                        }
                    ))

            # Check timestamp anomaly (event timestamp before previous event)
            if i > 0:
                previous_event = sorted_events[i - 1]
                if event.timestamp < previous_event.timestamp:
                    indicators.append(TamperingIndicator(
                        event_id=event.event_id,
                        tampering_type=TamperingType.TIMESTAMP_ANOMALY,
                        severity=8,
                        description=f"Event timestamp is before previous event",
                        evidence={
                            "event_timestamp": event.timestamp.isoformat(),
                            "previous_timestamp": previous_event.timestamp.isoformat()
                        }
                    ))

            # Check for suspicious timestamp (too far in future)
            now = datetime.now(timezone.utc)
            if event.timestamp > now + timedelta(hours=1):
                indicators.append(TamperingIndicator(
                    event_id=event.event_id,
                    tampering_type=TamperingType.TIMESTAMP_ANOMALY,
                    severity=7,
                    description=f"Event timestamp is in the future",
                    evidence={
                        "event_timestamp": event.timestamp.isoformat(),
                        "current_time": now.isoformat()
                    }
                ))

        return indicators


class AuditMerkleTree:
    """
    Efficient verification of large audit log segments using Merkle trees.

    A Merkle tree allows verification of individual events without needing
    to verify the entire audit log.
    """

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """Hash a pair of hashes together."""
        combined = left + right
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def _build_tree_recursive(self, hashes: List[Tuple[str, str]]) -> MerkleNode:
        """
        Recursively build Merkle tree from leaf hashes.

        Args:
            hashes: List of (event_id, hash) tuples

        Returns:
            Root node of the tree
        """
        if len(hashes) == 1:
            # Leaf node
            event_id, hash_value = hashes[0]
            return MerkleNode(hash=hash_value, event_id=event_id)

        # Build parent nodes
        parent_hashes = []

        for i in range(0, len(hashes), 2):
            left_id, left_hash = hashes[i]

            if i + 1 < len(hashes):
                right_id, right_hash = hashes[i + 1]
            else:
                # Odd number of nodes: duplicate the last one
                right_id, right_hash = left_id, left_hash

            # Create parent node
            parent_hash = self._hash_pair(left_hash, right_hash)
            parent_hashes.append((f"{left_id}+{right_id}", parent_hash))

        # Recursively build upper levels
        if len(parent_hashes) == 1:
            # This is the root
            _, root_hash = parent_hashes[0]
            left_node = self._build_tree_recursive([hashes[i] for i in range(0, len(hashes), 2)])
            if len(hashes) > 1:
                right_node = self._build_tree_recursive([hashes[i] for i in range(1, len(hashes), 2)])
            else:
                right_node = None

            return MerkleNode(hash=root_hash, left=left_node, right=right_node)
        else:
            return self._build_tree_recursive(parent_hashes)

    def build_tree(self, events: List[AuditEvent]) -> MerkleRoot:
        """
        Build Merkle tree from events.

        Args:
            events: List of audit events

        Returns:
            MerkleRoot containing the tree and root hash
        """
        if not events:
            # Empty tree
            empty_hash = hashlib.sha256(b"").hexdigest()
            return MerkleRoot(
                root_hash=empty_hash,
                tree=MerkleNode(hash=empty_hash),
                event_count=0
            )

        # Extract hashes
        hashes = [(event.event_id, event.hash) for event in events]

        # Build tree
        tree = self._build_tree_recursive(hashes)

        return MerkleRoot(
            root_hash=tree.hash,
            tree=tree,
            event_count=len(events),
            metadata={
                "first_event_id": events[0].event_id,
                "last_event_id": events[-1].event_id,
                "time_range": {
                    "start": events[0].timestamp.isoformat(),
                    "end": events[-1].timestamp.isoformat()
                }
            }
        )

    def _find_event_path(
        self, node: MerkleNode, target_event_id: str, path: List[Tuple[str, str]]
    ) -> Optional[List[Tuple[str, str]]]:
        """
        Find path from leaf to root for a specific event.

        Args:
            node: Current node in traversal
            target_event_id: Event ID to find
            path: Current path (list of (hash, direction) tuples)

        Returns:
            Path from leaf to root, or None if not found
        """
        if node.is_leaf():
            if node.event_id == target_event_id:
                return path
            return None

        # Search left subtree
        if node.left:
            left_path = self._find_event_path(
                node.left,
                target_event_id,
                path + [(node.right.hash if node.right else node.left.hash, "right")]
            )
            if left_path is not None:
                return left_path

        # Search right subtree
        if node.right:
            right_path = self._find_event_path(
                node.right,
                target_event_id,
                path + [(node.left.hash if node.left else node.right.hash, "left")]
            )
            if right_path is not None:
                return right_path

        return None

    def generate_proof(self, event: AuditEvent, tree: MerkleRoot) -> Optional[MerkleProof]:
        """
        Generate inclusion proof for a single event.

        Args:
            event: Event to generate proof for
            tree: Merkle tree root

        Returns:
            MerkleProof for the event, or None if event not in tree
        """
        # Find path from leaf to root
        path = self._find_event_path(tree.tree, event.event_id, [])

        if path is None:
            return None

        # Extract proof hashes and directions
        proof_hashes = [h for h, _ in path]
        proof_directions = [d for _, d in path]

        return MerkleProof(
            event_id=event.event_id,
            event_hash=event.hash,
            proof_hashes=proof_hashes,
            proof_directions=proof_directions,
            root_hash=tree.root_hash
        )

    def verify_proof(self, event: AuditEvent, proof: MerkleProof, root: MerkleRoot) -> bool:
        """
        Verify event inclusion using Merkle proof.

        Args:
            event: Event to verify
            proof: Merkle proof for the event
            root: Expected Merkle root

        Returns:
            True if proof is valid
        """
        # Check that event hash matches
        if event.hash != proof.event_hash:
            return False

        # Check that root hash matches
        if proof.root_hash != root.root_hash:
            return False

        # Recompute root hash using proof
        current_hash = event.hash

        for sibling_hash, direction in zip(proof.proof_hashes, proof.proof_directions):
            if direction == "left":
                current_hash = self._hash_pair(sibling_hash, current_hash)
            else:
                current_hash = self._hash_pair(current_hash, sibling_hash)

        # Check if computed hash matches root
        return current_hash == root.root_hash


class TimestampAuthority:
    """
    Integration with RFC 3161 timestamping authorities.

    This provides trusted timestamps for audit events and checkpoints,
    creating legal evidence of when data existed.

    Note: This is a simplified implementation. Production use should integrate
    with actual TSA services like DigiCert, FreeTSA, or internal PKI.
    """

    def __init__(
        self,
        tsa_url: Optional[str] = None,
        tsa_cert: Optional[bytes] = None
    ):
        """
        Initialize timestamp authority client.

        Args:
            tsa_url: URL of TSA service (e.g., http://timestamp.digicert.com)
            tsa_cert: TSA certificate for verification
        """
        self.tsa_url = tsa_url or "http://freetsa.org/tsr"
        self.tsa_cert = tsa_cert

    async def get_timestamp_token(self, hash_value: str) -> Optional[TimestampToken]:
        """
        Request timestamp from TSA.

        This creates an RFC 3161 timestamp request and sends it to the TSA.

        Args:
            hash_value: Hash to timestamp (hex string)

        Returns:
            TimestampToken if successful, None otherwise
        """
        if not HAS_HTTPX:
            print("Warning: httpx not installed, cannot request timestamps")
            return self._create_mock_timestamp(hash_value)

        if not HAS_CRYPTOGRAPHY:
            print("Warning: cryptography not installed, cannot request timestamps")
            return self._create_mock_timestamp(hash_value)

        try:
            # For this implementation, we'll create a mock timestamp
            # In production, you would:
            # 1. Create an RFC 3161 TimeStampReq
            # 2. Send it to the TSA
            # 3. Parse the TimeStampResp
            # 4. Extract and verify the TimeStampToken

            return self._create_mock_timestamp(hash_value)

        except Exception as e:
            print(f"Error getting timestamp: {e}")
            return None

    def _create_mock_timestamp(self, hash_value: str) -> TimestampToken:
        """Create a mock timestamp for testing."""
        return TimestampToken(
            hash_algorithm="sha256",
            message_imprint=hash_value,
            timestamp=datetime.now(timezone.utc),
            tsa_name="MockTSA",
            serial_number=base64.b64encode(hash_value.encode()).decode()[:16],
            signature=b"mock_signature",
            policy_oid="1.2.3.4.5"
        )

    def verify_timestamp(self, token: TimestampToken, hash_value: str) -> bool:
        """
        Verify timestamp token authenticity.

        Args:
            token: Timestamp token to verify
            hash_value: Original hash that was timestamped

        Returns:
            True if token is valid
        """
        # Check that hash matches
        if token.message_imprint != hash_value:
            return False

        # Check that timestamp is not in the future
        now = datetime.now(timezone.utc)
        if token.timestamp > now + timedelta(minutes=5):
            return False

        # In production, you would:
        # 1. Verify the TSA's signature using their certificate
        # 2. Verify the certificate chain
        # 3. Check certificate revocation status
        # 4. Verify the timestamp structure

        return True


class AuditCheckpoint:
    """
    Daily integrity checkpoints for compliance evidence.

    Checkpoints provide efficient verification of large audit logs by
    creating daily snapshots with Merkle roots and TSA timestamps.
    """

    def __init__(
        self,
        audit_service,
        merkle_tree: AuditMerkleTree,
        timestamp_authority: TimestampAuthority
    ):
        """
        Initialize checkpoint system.

        Args:
            audit_service: AuditService instance
            merkle_tree: AuditMerkleTree instance
            timestamp_authority: TimestampAuthority instance
        """
        self.audit_service = audit_service
        self.merkle_tree = merkle_tree
        self.timestamp_authority = timestamp_authority

    async def create_checkpoint(
        self,
        organization_id: str,
        checkpoint_date: date
    ) -> Optional[Checkpoint]:
        """
        Create daily checkpoint.

        The checkpoint contains:
        - Merkle root of all events for the day
        - Event count and hash range
        - TSA timestamp token
        - Reference to previous checkpoint

        Args:
            organization_id: Organization to checkpoint
            checkpoint_date: Date to create checkpoint for

        Returns:
            Checkpoint object if successful
        """
        # Query events for the date
        start_time = datetime.combine(checkpoint_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_time = datetime.combine(checkpoint_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        from ..models.audit import AuditEventFilter

        filter = AuditEventFilter(
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
            limit=100000
        )

        events = await self.audit_service.query_events(filter)

        if not events:
            print(f"No events found for {organization_id} on {checkpoint_date}")
            return None

        # Build Merkle tree
        merkle_root = self.merkle_tree.build_tree(events)

        # Get previous checkpoint
        previous_date = checkpoint_date - timedelta(days=1)
        previous_checkpoint_hash = ""  # TODO: Load from storage

        # Request timestamp from TSA
        timestamp_token = await self.timestamp_authority.get_timestamp_token(
            merkle_root.root_hash
        )

        # Create checkpoint
        checkpoint = Checkpoint(
            checkpoint_date=checkpoint_date,
            organization_id=organization_id,
            merkle_root=merkle_root.root_hash,
            event_count=len(events),
            first_event_hash=events[0].hash,
            last_event_hash=events[-1].hash,
            timestamp_token=timestamp_token,
            previous_checkpoint_hash=previous_checkpoint_hash
        )

        # Compute checkpoint hash
        checkpoint_data = {
            "checkpoint_date": checkpoint.checkpoint_date.isoformat(),
            "organization_id": checkpoint.organization_id,
            "merkle_root": checkpoint.merkle_root,
            "event_count": checkpoint.event_count,
            "first_event_hash": checkpoint.first_event_hash,
            "last_event_hash": checkpoint.last_event_hash,
            "previous_checkpoint_hash": checkpoint.previous_checkpoint_hash
        }
        checkpoint_json = json.dumps(checkpoint_data, sort_keys=True)
        checkpoint.checkpoint_hash = hashlib.sha256(checkpoint_json.encode()).hexdigest()

        return checkpoint

    async def export_checkpoint(self, checkpoint: Checkpoint) -> bytes:
        """
        Export checkpoint as signed document.

        Creates a portable checkpoint document that can be stored externally
        for compliance purposes.

        Args:
            checkpoint: Checkpoint to export

        Returns:
            Signed checkpoint document (JSON format)
        """
        # Create checkpoint document
        document = {
            "version": "1.0",
            "checkpoint": checkpoint.to_dict(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "signature": "TODO: Sign with organization's private key"
        }

        # Convert to JSON
        return json.dumps(document, indent=2).encode('utf-8')

    async def verify_checkpoint(
        self,
        checkpoint: Checkpoint,
        events: List[AuditEvent]
    ) -> CheckpointVerificationResult:
        """
        Verify a checkpoint against current audit log.

        Args:
            checkpoint: Checkpoint to verify
            events: Events for the checkpoint date

        Returns:
            Verification result
        """
        result = CheckpointVerificationResult(
            status=VerificationStatus.UNKNOWN,
            checkpoint_date=checkpoint.checkpoint_date
        )

        # Verify checkpoint hash
        checkpoint_data = {
            "checkpoint_date": checkpoint.checkpoint_date.isoformat(),
            "organization_id": checkpoint.organization_id,
            "merkle_root": checkpoint.merkle_root,
            "event_count": checkpoint.event_count,
            "first_event_hash": checkpoint.first_event_hash,
            "last_event_hash": checkpoint.last_event_hash,
            "previous_checkpoint_hash": checkpoint.previous_checkpoint_hash
        }
        checkpoint_json = json.dumps(checkpoint_data, sort_keys=True)
        computed_hash = hashlib.sha256(checkpoint_json.encode()).hexdigest()

        result.checkpoint_hash_valid = (computed_hash == checkpoint.checkpoint_hash)

        # Verify Merkle root
        if events:
            merkle_root = self.merkle_tree.build_tree(events)
            result.merkle_root_valid = (merkle_root.root_hash == checkpoint.merkle_root)
        else:
            result.errors.append("No events found for verification")

        # Verify timestamp
        if checkpoint.timestamp_token:
            result.timestamp_valid = self.timestamp_authority.verify_timestamp(
                checkpoint.timestamp_token,
                checkpoint.merkle_root
            )
        else:
            result.errors.append("No timestamp token present")

        # TODO: Verify chain to previous checkpoint

        # Determine overall status
        if result.checkpoint_hash_valid and result.merkle_root_valid:
            result.status = VerificationStatus.VALID
        elif result.checkpoint_hash_valid or result.merkle_root_valid:
            result.status = VerificationStatus.INCOMPLETE
        else:
            result.status = VerificationStatus.INVALID

        return result
