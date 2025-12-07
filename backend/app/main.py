"""
FastAPI Backend for AI Investment Scout DAO
Main application entry point with all API endpoints.
"""

from .startup_discovery import (
    discover_startups,
    discover_and_process_startups,
    AUTO_SEARCH_ENABLED,
    SEARCH_INTERVAL_HOURS
)
from .email_service import send_congratulations_email as send_email, send_proposal_outcome_email
from .neo_client import NeoClient
from .models import Proposal as DBProposal, Vote as DBVote, User as DBUser, Organization as DBOrganization
from .db import get_db, init_db, SessionLocal
from .blockchain_listener import BlockchainListener
from .ipfs_utils import upload_json_to_ipfs
import os
import asyncio
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor

# Load environment variables FIRST, before importing modules that read env vars
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger = logging.getLogger(__name__)
    logger.debug(f"Loaded .env from: {env_path}")
else:
    load_dotenv()  # Fallback to current directory
    logger = logging.getLogger(__name__)
    logger.debug("Loaded .env from current directory")

# Check demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


# Configure logging (if not already configured)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="AI Investment Scout DAO API",
    description="Backend API for decentralized investment proposal evaluation",
    version="1.0.0"
)

# Thread pool executor for CPU-bound or blocking operations
executor = ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="startup_processor")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NEO client (lazy initialization to avoid blocking startup)
neo_client = None


def get_neo_client():
    """Get or initialize NEO client (lazy initialization)."""
    global neo_client
    if neo_client is None:
        neo_client = NeoClient()
    return neo_client


# Initialize database on startup
background_task_running = False


async def periodic_startup_discovery():
    """Background task that periodically discovers and processes startups."""
    global background_task_running

    if not AUTO_SEARCH_ENABLED:
        logger.info(
            "Automatic startup discovery is disabled (AUTO_SEARCH_STARTUPS=false)")
        return

    if background_task_running:
        logger.warning("Background discovery task already running")
        return

    background_task_running = True
    logger.info(
        f"Starting periodic startup discovery (interval: {SEARCH_INTERVAL_HOURS} hours)")

    import time
    while True:
        try:
            logger.info("Running scheduled startup discovery...")
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                executor,
                lambda: discover_and_process_startups(auto_process=True)
            )
            logger.info(
                f"Discovery cycle complete: {results['discovered']} discovered, {results['processed']} processed")
        except Exception as e:
            logger.error(f"Error in periodic discovery: {e}")

        # Wait for the specified interval
        await asyncio.sleep(SEARCH_INTERVAL_HOURS * 3600)


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Backend started successfully")

    # Debug: Check environment variable value
    auto_search_env = os.getenv("AUTO_SEARCH_STARTUPS", "not set")
    logger.info(f"Environment variable AUTO_SEARCH_STARTUPS={auto_search_env}")
    logger.info(
        f"AUTO_SEARCH_ENABLED={AUTO_SEARCH_ENABLED} (type: {type(AUTO_SEARCH_ENABLED)})")

    # Start background discovery task if enabled
    if AUTO_SEARCH_ENABLED:
        logger.info("Starting automatic startup discovery background task...")
        asyncio.create_task(periodic_startup_discovery())
    else:
        logger.info("Automatic startup discovery is disabled")
        logger.info(f"To enable, set AUTO_SEARCH_STARTUPS=true in .env file")

    # Start blockchain event listener for email notifications
    if not DEMO_MODE:
        logger.info(
            "Starting blockchain event listener for proposal finalization...")
        neo_client = get_neo_client()
        listener = BlockchainListener(neo_client, SessionLocal)
        asyncio.create_task(listener.start())
    else:
        logger.info(
            "Blockchain listener disabled in DEMO_MODE - email notifications will be triggered via API endpoints")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down thread pool executor...")
    executor.shutdown(wait=True)
    logger.info("Shutdown complete")


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


class VoteRequestNoId(BaseModel):
    """Vote request without proposal_id (extracted from URL path)"""
    voter_address: str
    vote: int  # 1 for yes, 0 for no


class FinalizeRequest(BaseModel):
    proposal_id: int


class DiscoverStartupsRequest(BaseModel):
    sources: Optional[List[str]] = None
    limit_per_source: int = 5
    auto_process: bool = True


class CreateUserRequest(BaseModel):
    wallet_address: str
    email: Optional[str] = None


class CreateOrganizationRequest(BaseModel):
    name: str
    sector: Optional[str] = None
    team_members: List[str]  # List of wallet addresses
    creator_wallet: str


# API Endpoints

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Investment Scout DAO Backend",
        "demo_mode": os.getenv("DEMO_MODE", "true") == "true",
        "auto_search_enabled": AUTO_SEARCH_ENABLED,
        "search_interval_hours": SEARCH_INTERVAL_HOURS
    }


@app.post("/discover-startups")
async def discover_startups_endpoint(
    request: DiscoverStartupsRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger startup discovery.
    Can run synchronously or asynchronously in background.
    """
    logger.info(
        f"Manual startup discovery triggered: sources={request.sources}, auto_process={request.auto_process}")

    if request.auto_process:
        # Run in background thread pool to avoid blocking
        async def run_discovery():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                lambda: discover_and_process_startups(
                    sources=request.sources,
                    limit_per_source=request.limit_per_source,
                    auto_process=True
                )
            )

        background_tasks.add_task(run_discovery)
        return {
            "status": "started",
            "message": "Startup discovery and processing started in background",
            "sources": request.sources or ["demo"],
            "limit_per_source": request.limit_per_source
        }
    else:
        # Run synchronously in thread pool (just discovery, no processing)
        loop = asyncio.get_event_loop()
        startups = await loop.run_in_executor(
            executor,
            discover_startups,
            request.sources,
            request.limit_per_source
        )
        return {
            "status": "completed",
            "discovered": len(startups),
            "startups": startups
        }


@app.get("/discover-startups/status")
async def discovery_status():
    """Get status of automatic startup discovery."""
    return {
        "auto_search_enabled": AUTO_SEARCH_ENABLED,
        "search_interval_hours": SEARCH_INTERVAL_HOURS,
        "background_task_running": background_task_running
    }


def submit_proposal_direct(
    title: str,
    summary: str,
    cid: str,
    confidence: int,
    metadata: dict
) -> dict:
    """
    Direct database submission function (bypasses HTTP).
    Can be called from within the same process (e.g., from startup_discovery).

    Returns:
        Dict with proposal id and other fields (same format as HTTP endpoint)
    """
    from .db import SessionLocal
    import time

    logger.info(f"Submitting proposal directly to database: {title}")

    db = SessionLocal()
    try:
        # Calculate deadline (7 days from now, in block timestamp)
        deadline = int(time.time()) + (7 * 24 * 60 * 60)

        # Submit to NEO blockchain
        tx_result = get_neo_client().create_proposal(
            title=title,
            ipfs_hash=cid,
            deadline=deadline,
            confidence=confidence
        )

        # Store in local database
        db_proposal = DBProposal(
            title=title,
            summary=summary,
            ipfs_cid=cid,
            confidence=confidence,
            status="active",
            yes_votes=0,
            no_votes=0,
            proposal_metadata=metadata,
            tx_hash=tx_result.get("tx_hash"),
            on_chain_id=tx_result.get("proposal_id"),
            deadline=deadline
        )

        db.add(db_proposal)
        db.commit()
        db.refresh(db_proposal)

        logger.info(
            f"✅ Proposal created directly: ID={db_proposal.id}, TX={tx_result.get('tx_hash')}")

        return {
            "id": db_proposal.id,
            "title": db_proposal.title,
            "summary": db_proposal.summary,
            "ipfs_cid": db_proposal.ipfs_cid,
            "confidence": db_proposal.confidence,
            "status": db_proposal.status,
            "yes_votes": db_proposal.yes_votes,
            "no_votes": db_proposal.no_votes,
            "created_at": db_proposal.created_at.isoformat(),
            "deadline": db_proposal.deadline,
            "metadata": db_proposal.proposal_metadata
        }
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error submitting proposal directly: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        db.close()


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
        tx_result = get_neo_client().create_proposal(
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
    try:
        logger.info("Fetching proposals from database...")

        # Query database directly (SQLAlchemy handles async properly with check_same_thread=False)
        # No need for thread pool - SQLite with check_same_thread=False works fine
        proposals = db.query(DBProposal).order_by(
            DBProposal.created_at.desc()).all()

        logger.info(f"Found {len(proposals)} proposals in database")

        result = [
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

        logger.info(f"Returning {len(result)} proposals")
        return result
    except Exception as e:
        logger.error(f"Error fetching proposals: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch proposals: {str(e)}"
        )


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
        tx_result = get_neo_client().vote(
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


@app.post("/proposals/{proposal_id}/vote")
async def vote_nested(proposal_id: int, request: VoteRequestNoId, db: Session = Depends(get_db)):
    """
    Submit a vote on a proposal (nested route).
    Records vote on-chain and updates local tally.
    """
    logger.info(
        f"Processing vote: proposal={proposal_id}, voter={request.voter_address}, vote={request.vote}")

    # Validate proposal exists
    proposal = db.query(DBProposal).filter(
        DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "active":
        raise HTTPException(status_code=400, detail="Proposal is not active")

    # Check if voter already voted
    existing_vote = db.query(DBVote).filter(
        DBVote.proposal_id == proposal_id,
        DBVote.voter_address == request.voter_address
    ).first()

    if existing_vote:
        raise HTTPException(
            status_code=400, detail="Voter has already voted on this proposal")

    try:
        # Submit vote to blockchain
        tx_result = get_neo_client().vote(
            proposal_id=proposal.on_chain_id or proposal_id,
            voter=request.voter_address,
            choice=request.vote
        )

        # Record vote in database
        db_vote = DBVote(
            proposal_id=proposal_id,
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
async def finalize(request: FinalizeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Finalize a proposal (close voting and determine outcome).
    Note: In production mode, email notifications are triggered by blockchain events.
    In demo mode, emails are sent via background tasks.
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
        tx_result = get_neo_client().finalize_proposal(
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

        # In demo mode, send emails via API. In production, blockchain listener handles it
        if DEMO_MODE:
            background_tasks.add_task(
                send_proposal_outcome_emails,
                proposal.id,
                proposal.title,
                proposal.status,
                proposal.yes_votes,
                proposal.no_votes
            )
        else:
            logger.info(
                "Email notifications will be triggered by blockchain event listener")

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


@app.post("/proposals/{proposal_id}/finalize")
async def finalize_nested(proposal_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Finalize a proposal (close voting and determine outcome) - nested route.
    Note: In production mode, email notifications are triggered by blockchain events.
    In demo mode, emails are sent via background tasks.
    """
    logger.info(f"Finalizing proposal: {proposal_id}")

    proposal = db.query(DBProposal).filter(
        DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "active":
        raise HTTPException(status_code=400, detail="Proposal is not active")

    try:
        # Finalize on blockchain
        tx_result = get_neo_client().finalize_proposal(
            proposal_id=proposal.on_chain_id or proposal_id
        )

        # Determine outcome
        if proposal.yes_votes > proposal.no_votes:
            proposal.status = "approved"
        else:
            proposal.status = "rejected"

        db.commit()

        logger.info(
            f"Proposal finalized: ID={proposal_id}, status={proposal.status}")

        # In demo mode, send emails via API. In production, blockchain listener handles it
        if DEMO_MODE:
            background_tasks.add_task(
                send_proposal_outcome_emails,
                proposal.id,
                proposal.title,
                proposal.status,
                proposal.yes_votes,
                proposal.no_votes
            )
        else:
            logger.info(
                "Email notifications will be triggered by blockchain event listener")

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


@app.post("/users")
async def create_or_update_user(request: CreateUserRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Create or update a user with wallet address and optional email.
    Sends a congratulations email if email is provided and is new or updated.
    """
    logger.info(
        f"Creating/updating user: wallet={request.wallet_address}, email={request.email}")

    try:
        # Check if user already exists
        existing_user = db.query(DBUser).filter(
            DBUser.wallet_address == request.wallet_address
        ).first()

        email_was_added = False

        if existing_user:
            # Update existing user
            if request.email and request.email != existing_user.email:
                email_was_added = True
                existing_user.email = request.email
                existing_user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_user)
                logger.info(f"Updated user email: {request.wallet_address}")
        else:
            # Create new user
            new_user = DBUser(
                wallet_address=request.wallet_address,
                email=request.email
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            if request.email:
                email_was_added = True
            logger.info(f"Created new user: {request.wallet_address}")

        # Send email in background if email was added
        if email_was_added and request.email:
            background_tasks.add_task(
                send_congratulations_email_task,
                request.wallet_address,
                request.email
            )

        return {
            "success": True,
            "wallet_address": request.wallet_address,
            "email": request.email,
            "email_sent": email_was_added and request.email is not None
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating/updating user: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create/update user: {str(e)}")


@app.post("/organizations")
async def create_organization(
    request: CreateOrganizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new organization and save it to Storacha/IPFS.
    """
    logger.info(
        f"Creating organization: {request.name}, creator: {request.creator_wallet}, members: {len(request.team_members)}"
    )

    try:
        # Prepare organization data for IPFS
        org_data = {
            "name": request.name,
            "sector": request.sector,
            "creator_wallet": request.creator_wallet,
            "team_members": request.team_members,
            "member_count": len(request.team_members),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Upload to Storacha/IPFS
        logger.info("Uploading organization data to Storacha/IPFS...")
        ipfs_cid = upload_json_to_ipfs(org_data, f"organization_{request.name.replace(' ', '_')}.json")

        # Save to database
        organization = DBOrganization(
            name=request.name,
            sector=request.sector,
            ipfs_cid=ipfs_cid,
            creator_wallet=request.creator_wallet,
            team_members=request.team_members,
        )

        db.add(organization)
        db.commit()
        db.refresh(organization)

        logger.info(
            f"Organization created: ID={organization.id}, Name={organization.name}, IPFS CID={ipfs_cid}"
        )

        return {
            "success": True,
            "id": organization.id,
            "name": organization.name,
            "sector": organization.sector,
            "ipfs_cid": organization.ipfs_cid,
            "creator_wallet": organization.creator_wallet,
            "team_members": organization.team_members,
            "member_count": len(organization.team_members),
            "created_at": organization.created_at.isoformat(),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create organization: {str(e)}"
        )


@app.get("/organizations")
async def get_organizations(
    wallet_address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get organizations. If wallet_address is provided, returns organizations where the user is a member.
    """
    try:
        if wallet_address:
            # Get organizations where user is creator or team member
            organizations = db.query(DBOrganization).filter(
                (DBOrganization.creator_wallet == wallet_address) |
                (DBOrganization.team_members.contains([wallet_address]))
            ).all()
        else:
            # Get all organizations
            organizations = db.query(DBOrganization).all()

        return [
            {
                "id": org.id,
                "name": org.name,
                "sector": org.sector,
                "ipfs_cid": org.ipfs_cid,
                "creator_wallet": org.creator_wallet,
                "team_members": org.team_members,
                "member_count": len(org.team_members),
                "created_at": org.created_at.isoformat(),
            }
            for org in organizations
        ]

    except Exception as e:
        logger.error(f"Error fetching organizations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch organizations: {str(e)}"
        )


def send_congratulations_email_task(wallet_address: str, email: str):
    """
    Send a congratulations email to the user when they add their email.
    This function is called as a background task.
    """
    try:
        send_email(wallet_address, email)
        logger.info(
            f"Congratulations email sent to {email} for wallet {wallet_address}")
    except Exception as e:
        logger.error(
            f"Failed to send congratulations email to {email}: {str(e)}")


def send_proposal_outcome_emails(
    proposal_id: int,
    proposal_title: str,
    status: str,
    yes_votes: int,
    no_votes: int
):
    """
    Send email notifications to all users who voted on a proposal when it's finalized.
    This function is called as a background task.
    """
    try:
        from .db import SessionLocal

        db = SessionLocal()
        try:
            # Get all votes for this proposal
            votes = db.query(DBVote).filter(
                DBVote.proposal_id == proposal_id
            ).all()

            if not votes:
                logger.info(
                    f"No votes found for proposal {proposal_id}, skipping email notifications")
                return

            # Get unique voter addresses
            voter_addresses = list(set([vote.voter_address for vote in votes]))

            # Get email addresses for voters
            users = db.query(DBUser).filter(
                DBUser.wallet_address.in_(voter_addresses),
                DBUser.email.isnot(None)
            ).all()

            emails_sent = 0
            for user in users:
                if user.email:
                    try:
                        send_proposal_outcome_email(
                            email=user.email,
                            proposal_title=proposal_title,
                            proposal_id=proposal_id,
                            status=status,
                            yes_votes=yes_votes,
                            no_votes=no_votes
                        )
                        emails_sent += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to send outcome email to {user.email}: {str(e)}")

            logger.info(
                f"Sent proposal outcome emails to {emails_sent} voters for proposal {proposal_id} ({status})"
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to send proposal outcome emails: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
