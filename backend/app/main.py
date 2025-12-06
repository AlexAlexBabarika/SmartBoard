"""
FastAPI Backend for AI Investment Scout DAO
Main application entry point with all API endpoints.
"""

import os
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
import logging

from .db import get_db, init_db
from .models import Proposal as DBProposal, Vote as DBVote
from .neo_client import NeoClient

# Load environment variables from project root or current directory
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to current directory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Investment Scout DAO API",
    description="Backend API for decentralized investment proposal evaluation",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NEO client
neo_client = NeoClient()

# Initialize database on startup


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Backend started successfully")


# Pydantic models for request/response
class SubmitMemoRequest(BaseModel):
    title: str
    summary: str
    cid: str
    confidence: int  # 0-100
    metadata: Optional[dict] = {}


class ProposalResponse(BaseModel):
    id: int
    title: str
    summary: str
    ipfs_cid: str
    confidence: int
    status: str
    yes_votes: int
    no_votes: int
    created_at: str
    deadline: Optional[int] = None
    metadata: Optional[dict] = {}

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    proposal_id: int
    voter_address: str
    vote: int  # 1 for yes, 0 for no


class FinalizeRequest(BaseModel):
    proposal_id: int


# API Endpoints

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Investment Scout DAO Backend",
        "demo_mode": os.getenv("DEMO_MODE", "true") == "true"
    }


@app.post("/submit-memo", response_model=ProposalResponse)
async def submit_memo(request: SubmitMemoRequest, db: Session = Depends(get_db)):
    """
    Submit a new investment memo proposal.
    Stores in database and submits on-chain transaction.
    """
    logger.info(f"Submitting memo: {request.title}")

    try:
        # Calculate deadline (7 days from now, in block timestamp)
        import time
        deadline = int(time.time()) + (7 * 24 * 60 * 60)

        # Submit to NEO blockchain
        tx_result = neo_client.create_proposal(
            title=request.title,
            ipfs_hash=request.cid,
            deadline=deadline,
            confidence=request.confidence
        )

        # Store in local database
        db_proposal = DBProposal(
            title=request.title,
            summary=request.summary,
            ipfs_cid=request.cid,
            confidence=request.confidence,
            status="active",
            yes_votes=0,
            no_votes=0,
            proposal_metadata=request.metadata,
            tx_hash=tx_result.get("tx_hash"),
            on_chain_id=tx_result.get("proposal_id"),
            deadline=deadline
        )

        db.add(db_proposal)
        db.commit()
        db.refresh(db_proposal)

        logger.info(
            f"Proposal created: ID={db_proposal.id}, TX={tx_result.get('tx_hash')}")

        return ProposalResponse(
            id=db_proposal.id,
            title=db_proposal.title,
            summary=db_proposal.summary,
            ipfs_cid=db_proposal.ipfs_cid,
            confidence=db_proposal.confidence,
            status=db_proposal.status,
            yes_votes=db_proposal.yes_votes,
            no_votes=db_proposal.no_votes,
            created_at=db_proposal.created_at.isoformat(),
            deadline=db_proposal.deadline,
            metadata=db_proposal.proposal_metadata
        )

    except Exception as e:
        logger.error(f"Error submitting memo: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit proposal: {str(e)}")


@app.get("/proposals", response_model=List[ProposalResponse])
async def get_proposals(db: Session = Depends(get_db)):
    """Get list of all proposals with on-chain status."""
    proposals = db.query(DBProposal).order_by(
        DBProposal.created_at.desc()).all()

    return [
        ProposalResponse(
            id=p.id,
            title=p.title,
            summary=p.summary,
            ipfs_cid=p.ipfs_cid,
            confidence=p.confidence,
            status=p.status,
            yes_votes=p.yes_votes,
            no_votes=p.no_votes,
            created_at=p.created_at.isoformat(),
            deadline=p.deadline,
            metadata=p.proposal_metadata
        )
        for p in proposals
    ]


@app.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific proposal."""
    proposal = db.query(DBProposal).filter(
        DBProposal.id == proposal_id).first()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return ProposalResponse(
        id=proposal.id,
        title=proposal.title,
        summary=proposal.summary,
        ipfs_cid=proposal.ipfs_cid,
        confidence=proposal.confidence,
        status=proposal.status,
        yes_votes=proposal.yes_votes,
        no_votes=proposal.no_votes,
        created_at=proposal.created_at.isoformat(),
        deadline=proposal.deadline,
        metadata=proposal.proposal_metadata
    )


@app.post("/vote")
async def vote(request: VoteRequest, db: Session = Depends(get_db)):
    """
    Submit a vote on a proposal.
    Records vote on-chain and updates local tally.
    """
    logger.info(
        f"Processing vote: proposal={request.proposal_id}, voter={request.voter_address}, vote={request.vote}")

    # Validate proposal exists
    proposal = db.query(DBProposal).filter(
        DBProposal.id == request.proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "active":
        raise HTTPException(status_code=400, detail="Proposal is not active")

    # Check if voter already voted
    existing_vote = db.query(DBVote).filter(
        DBVote.proposal_id == request.proposal_id,
        DBVote.voter_address == request.voter_address
    ).first()

    if existing_vote:
        raise HTTPException(
            status_code=400, detail="Voter has already voted on this proposal")

    try:
        # Submit vote to blockchain
        tx_result = neo_client.vote(
            proposal_id=proposal.on_chain_id or request.proposal_id,
            voter=request.voter_address,
            choice=request.vote
        )

        # Record vote in database
        db_vote = DBVote(
            proposal_id=request.proposal_id,
            voter_address=request.voter_address,
            vote=request.vote,
            tx_hash=tx_result.get("tx_hash")
        )
        db.add(db_vote)

        # Update vote tally
        if request.vote == 1:
            proposal.yes_votes += 1
        else:
            proposal.no_votes += 1

        db.commit()

        logger.info(f"Vote recorded: TX={tx_result.get('tx_hash')}")

        return {
            "success": True,
            "tx_hash": tx_result.get("tx_hash"),
            "yes_votes": proposal.yes_votes,
            "no_votes": proposal.no_votes
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing vote: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process vote: {str(e)}")


@app.post("/finalize")
async def finalize(request: FinalizeRequest, db: Session = Depends(get_db)):
    """
    Finalize a proposal (close voting and determine outcome).
    """
    logger.info(f"Finalizing proposal: {request.proposal_id}")

    proposal = db.query(DBProposal).filter(
        DBProposal.id == request.proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "active":
        raise HTTPException(status_code=400, detail="Proposal is not active")

    try:
        # Finalize on blockchain
        tx_result = neo_client.finalize_proposal(
            proposal_id=proposal.on_chain_id or request.proposal_id
        )

        # Determine outcome
        if proposal.yes_votes > proposal.no_votes:
            proposal.status = "approved"
        else:
            proposal.status = "rejected"

        db.commit()

        logger.info(
            f"Proposal finalized: ID={request.proposal_id}, status={proposal.status}")

        return {
            "success": True,
            "proposal_id": proposal.id,
            "status": proposal.status,
            "tx_hash": tx_result.get("tx_hash"),
            "yes_votes": proposal.yes_votes,
            "no_votes": proposal.no_votes
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error finalizing proposal: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to finalize proposal: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
