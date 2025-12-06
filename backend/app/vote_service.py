"""
Shared vote handling utilities for API endpoints and simulated agents.
"""

import logging
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import Proposal as DBProposal, Vote as DBVote
from .neo_client import NeoClient

logger = logging.getLogger(__name__)
_neo_client: Optional[NeoClient] = None


def _get_neo_client() -> NeoClient:
    """Lazy Neo client initialization scoped to vote handling."""
    global _neo_client
    if _neo_client is None:
        _neo_client = NeoClient()
    return _neo_client


def process_vote(db: Session, proposal: DBProposal, voter_address: str, vote_value: int) -> dict:
    """
    Persist a vote for a proposal and submit it to the blockchain (or simulation).

    This centralizes the core vote-path logic so it can be used by both HTTP
    routes and background/simulated agents.
    """
    # Prevent duplicate votes from the same address
    existing_vote = db.query(DBVote).filter(
        DBVote.proposal_id == proposal.id,
        DBVote.voter_address == voter_address
    ).first()

    if existing_vote:
        raise HTTPException(
            status_code=400, detail="Voter has already voted on this proposal")

    neo_client = _get_neo_client()

    # Extra guard: verify against on-chain state to avoid double voting when
    # local records are stale or multiple nodes share the contract.
    # In simulation mode, this check is safe and fast. In real mode, failures
    # should not block voting if the check fails (fail-open for availability).
    try:
        already_voted_on_chain = neo_client.has_voted(
            proposal.on_chain_id or proposal.id,
            voter_address
        )
        if already_voted_on_chain:
            raise HTTPException(
                status_code=400,
                detail="Voter has already voted on this proposal (on-chain)")
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for already voted)
        raise
    except Exception as exc:
        # Log but don't block voting if on-chain check fails (fail-open)
        # This ensures availability even if blockchain RPC is temporarily unavailable
        logger.warning(
            "Failed to verify on-chain vote status (continuing anyway): %s",
            exc,
            exc_info=False  # Don't spam logs with full traceback for expected failures
        )
        # Continue with vote - the database check above is sufficient for most cases

    # Submit vote to blockchain (simulation-friendly via NeoClient)
    tx_result = neo_client.vote(
        proposal_id=proposal.on_chain_id or proposal.id,
        voter=voter_address,
        choice=vote_value
    )

    # Record vote in database
    db_vote = DBVote(
        proposal_id=proposal.id,
        voter_address=voter_address,
        vote=vote_value,
        tx_hash=tx_result.get("tx_hash")
    )
    db.add(db_vote)

    # Update tally
    if vote_value == 1:
        proposal.yes_votes += 1
    else:
        proposal.no_votes += 1

    db.commit()

    logger.info(
        "Vote recorded",
        extra={
            "proposal_id": proposal.id,
            "voter": voter_address,
            "vote": vote_value,
            "tx_hash": tx_result.get("tx_hash")
        }
    )

    return {
        "success": True,
        "tx_hash": tx_result.get("tx_hash"),
        "yes_votes": proposal.yes_votes,
        "no_votes": proposal.no_votes
    }

