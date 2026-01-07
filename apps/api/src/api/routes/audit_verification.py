"""
Audit Verification API Routes

FastAPI endpoints for cryptographic verification of audit trails.
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ....models.audit import AuditEventFilter
from ....models.audit_verification import (
    VerificationStatus,
    VerificationReport
)
from ....services.audit import get_audit_service
from ....services.audit_verification import (
    AuditChain,
    AuditMerkleTree,
    TimestampAuthority,
    AuditCheckpoint
)


router = APIRouter(prefix="/v1/audit", tags=["Audit Verification"])


# Pydantic models for API
class VerifyRequest(BaseModel):
    """Request for audit verification."""
    organization_id: str = Field(..., description="Organization to verify")
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    include_tampering_check: bool = Field(True, description="Check for tampering indicators")


class VerifyResponse(BaseModel):
    """Response from audit verification."""
    status: str
    chain_result: dict
    tampering_indicators: List[dict] = []
    message: str


class CheckpointListResponse(BaseModel):
    """Response listing checkpoints."""
    checkpoints: List[dict]
    total: int


class CheckpointResponse(BaseModel):
    """Response with checkpoint details."""
    checkpoint: dict
    verification: Optional[dict] = None


# Global instances (should be initialized in app startup)
_audit_chain = AuditChain()
_merkle_tree = AuditMerkleTree()
_timestamp_authority = TimestampAuthority()
_checkpoint_service: Optional[AuditCheckpoint] = None


def get_checkpoint_service() -> AuditCheckpoint:
    """Get checkpoint service instance."""
    global _checkpoint_service
    if _checkpoint_service is None:
        audit_service = get_audit_service()
        if audit_service:
            _checkpoint_service = AuditCheckpoint(
                audit_service=audit_service,
                merkle_tree=_merkle_tree,
                timestamp_authority=_timestamp_authority
            )
    return _checkpoint_service


@router.get("/verify", response_model=VerifyResponse)
async def verify_audit_trail(
    organization_id: str = Query(..., description="Organization ID to verify"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO 8601)"),
    include_tampering: bool = Query(True, description="Include tampering analysis")
):
    """
    Verify integrity of audit log for a time range.

    This endpoint performs comprehensive verification including:
    - Hash chain verification
    - Event hash validation
    - Tampering detection (optional)

    Returns a detailed verification report.

    **Example:**
    ```
    GET /v1/audit/verify?organization_id=org-123&start_time=2024-01-01T00:00:00Z
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Default time range: last 30 days
    if not start_time:
        start_time = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_time:
        end_time = datetime.now(timezone.utc)

    # Query events
    filter = AuditEventFilter(
        organization_id=organization_id,
        start_time=start_time,
        end_time=end_time,
        limit=100000
    )

    events = await audit_service.query_events(filter)

    if not events:
        return VerifyResponse(
            status="valid",
            chain_result={
                "status": "valid",
                "total_events": 0,
                "message": "No events found in time range"
            },
            message="No events found to verify"
        )

    # Verify chain
    chain_result = _audit_chain.verify_chain(events)

    # Check for tampering if requested
    tampering_indicators = []
    if include_tampering:
        indicators = _audit_chain.find_tampering(events)
        tampering_indicators = [ind.to_dict() for ind in indicators]

    return VerifyResponse(
        status=chain_result.status.value,
        chain_result=chain_result.to_dict(),
        tampering_indicators=tampering_indicators,
        message=f"Verified {len(events)} events: {chain_result.status.value}"
    )


@router.get("/checkpoints", response_model=CheckpointListResponse)
async def list_checkpoints(
    organization_id: str = Query(..., description="Organization ID"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Maximum number of checkpoints")
):
    """
    List available audit checkpoints.

    Checkpoints are daily snapshots of audit log integrity.

    **Example:**
    ```
    GET /v1/audit/checkpoints?organization_id=org-123&start_date=2024-01-01
    ```
    """
    # TODO: Implement checkpoint storage and retrieval
    # For now, return empty list

    checkpoints = []

    return CheckpointListResponse(
        checkpoints=checkpoints,
        total=len(checkpoints)
    )


@router.get("/checkpoints/{checkpoint_date}", response_model=CheckpointResponse)
async def get_checkpoint(
    checkpoint_date: date,
    organization_id: str = Query(..., description="Organization ID"),
    verify: bool = Query(False, description="Include verification")
):
    """
    Get specific checkpoint with optional verification.

    **Example:**
    ```
    GET /v1/audit/checkpoints/2024-01-15?organization_id=org-123&verify=true
    ```
    """
    checkpoint_service = get_checkpoint_service()
    if not checkpoint_service:
        raise HTTPException(status_code=503, detail="Checkpoint service not available")

    # TODO: Load checkpoint from storage
    # For now, create a new checkpoint

    checkpoint = await checkpoint_service.create_checkpoint(
        organization_id=organization_id,
        checkpoint_date=checkpoint_date
    )

    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for {checkpoint_date}"
        )

    response_data = {
        "checkpoint": checkpoint.to_dict()
    }

    # Verify if requested
    if verify:
        audit_service = get_audit_service()
        if audit_service:
            # Query events for the date
            start_time = datetime.combine(checkpoint_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_time = datetime.combine(checkpoint_date, datetime.max.time()).replace(tzinfo=timezone.utc)

            filter = AuditEventFilter(
                organization_id=organization_id,
                start_time=start_time,
                end_time=end_time,
                limit=100000
            )

            events = await audit_service.query_events(filter)

            verification = await checkpoint_service.verify_checkpoint(checkpoint, events)
            response_data["verification"] = verification.to_dict()

    return CheckpointResponse(**response_data)


@router.post("/checkpoints/{checkpoint_date}/verify", response_model=dict)
async def verify_checkpoint(
    checkpoint_date: date,
    organization_id: str = Query(..., description="Organization ID")
):
    """
    Verify a checkpoint against the current audit log.

    This checks:
    - Checkpoint hash integrity
    - Merkle root validity
    - Timestamp authenticity
    - Chain to previous checkpoint

    **Example:**
    ```
    POST /v1/audit/checkpoints/2024-01-15/verify?organization_id=org-123
    ```
    """
    checkpoint_service = get_checkpoint_service()
    if not checkpoint_service:
        raise HTTPException(status_code=503, detail="Checkpoint service not available")

    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # TODO: Load checkpoint from storage
    checkpoint = await checkpoint_service.create_checkpoint(
        organization_id=organization_id,
        checkpoint_date=checkpoint_date
    )

    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for {checkpoint_date}"
        )

    # Query events
    start_time = datetime.combine(checkpoint_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_time = datetime.combine(checkpoint_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    filter = AuditEventFilter(
        organization_id=organization_id,
        start_time=start_time,
        end_time=end_time,
        limit=100000
    )

    events = await audit_service.query_events(filter)

    # Verify checkpoint
    verification = await checkpoint_service.verify_checkpoint(checkpoint, events)

    return verification.to_dict()


@router.post("/merkle-proof/{event_id}", response_model=dict)
async def generate_merkle_proof(
    event_id: str,
    organization_id: str = Query(..., description="Organization ID"),
    checkpoint_date: Optional[date] = Query(None, description="Checkpoint date for proof")
):
    """
    Generate Merkle proof for a specific event.

    This creates a cryptographic proof that an event is included in the
    audit log without revealing the entire log.

    **Example:**
    ```
    POST /v1/audit/merkle-proof/event-123?organization_id=org-123
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Get the event
    from ....models.audit import AuditEventFilter

    filter = AuditEventFilter(organization_id=organization_id, limit=100000)

    if checkpoint_date:
        start_time = datetime.combine(checkpoint_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_time = datetime.combine(checkpoint_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        filter.start_time = start_time
        filter.end_time = end_time

    events = await audit_service.query_events(filter)

    # Find the specific event
    target_event = None
    for event in events:
        if event.event_id == event_id:
            target_event = event
            break

    if not target_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Build Merkle tree
    merkle_root = _merkle_tree.build_tree(events)

    # Generate proof
    proof = _merkle_tree.generate_proof(target_event, merkle_root)

    if not proof:
        raise HTTPException(status_code=500, detail="Failed to generate proof")

    return {
        "event_id": event_id,
        "proof": proof.to_dict(),
        "merkle_root": merkle_root.to_dict(),
        "message": "Merkle proof generated successfully"
    }


@router.post("/merkle-proof/verify", response_model=dict)
async def verify_merkle_proof(
    event_id: str = Query(..., description="Event ID"),
    organization_id: str = Query(..., description="Organization ID")
):
    """
    Verify a Merkle proof for an event.

    **Example:**
    ```
    POST /v1/audit/merkle-proof/verify?event_id=event-123&organization_id=org-123
    ```
    """
    # This would typically take a proof as input
    # For demonstration, we'll generate and verify

    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Query events
    filter = AuditEventFilter(organization_id=organization_id, limit=100000)
    events = await audit_service.query_events(filter)

    # Find event
    target_event = None
    for event in events:
        if event.event_id == event_id:
            target_event = event
            break

    if not target_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Build tree and generate proof
    merkle_root = _merkle_tree.build_tree(events)
    proof = _merkle_tree.generate_proof(target_event, merkle_root)

    if not proof:
        raise HTTPException(status_code=500, detail="Failed to generate proof")

    # Verify proof
    is_valid = _merkle_tree.verify_proof(target_event, proof, merkle_root)

    return {
        "event_id": event_id,
        "valid": is_valid,
        "message": "Proof verified successfully" if is_valid else "Proof verification failed"
    }


@router.get("/health", response_model=dict)
async def verification_health():
    """
    Health check for verification system.

    Returns status of verification components.
    """
    audit_service = get_audit_service()

    return {
        "status": "healthy",
        "components": {
            "audit_chain": "available",
            "merkle_tree": "available",
            "timestamp_authority": "available",
            "checkpoint_service": "available" if get_checkpoint_service() else "unavailable",
            "audit_service": "available" if audit_service else "unavailable"
        }
    }
