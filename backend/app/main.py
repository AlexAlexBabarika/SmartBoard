"""
FastAPI Backend for AI Investment Scout DAO
Main application entry point with all API endpoints.
"""

# Load environment variables FIRST, before importing modules that read env vars
import io
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Optional
from concurrent.futures import TimeoutError as FuturesTimeout
from concurrent.futures import ThreadPoolExecutor
import logging
import asyncio
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .db import get_db, init_db, SessionLocal
from .models import Proposal as DBProposal, Vote as DBVote, User as DBUser, Organization as DBOrganization
from .neo_client import NeoClient
from .startup_discovery import (
    discover_startups,
    discover_and_process_startups,
    AUTO_SEARCH_ENABLED,
    SEARCH_INTERVAL_HOURS
)
from .storacha_sync import (
    sync_from_manifest,
    sync_from_cids,
    get_existing_cids,
    AUTO_SYNC_ENABLED,
    SYNC_INTERVAL_HOURS,
    periodic_storacha_sync
)
from .manifest_manager import (
    schedule_manifest_refresh,
    get_manifest_cid
)
from .utils import clean_cid, get_current_storacha_space
from .research_pipeline_adapter import run_research_pipeline
from .vote_service import process_vote
from .email_service import send_congratulations_email as send_email, send_proposal_outcome_email
from .blockchain_listener import BlockchainListener
from .ipfs_utils import upload_json_to_ipfs

env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to current directory

# Configure logger after imports
logger = logging.getLogger(__name__)
if env_path.exists():
    logger.debug(f"Loaded .env from: {env_path}")
else:
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

# Thread pool executor for Storacha sync (separate to avoid blocking)
storacha_executor = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="storacha_sync")

# Fetch-time Storacha sync configuration
STORACHA_SYNC_ON_FETCH = os.getenv(
    "STORACHA_SYNC_ON_FETCH", "true").lower() == "true"
STORACHA_SYNC_ON_FETCH_TIMEOUT = float(
    os.getenv("STORACHA_SYNC_ON_FETCH_TIMEOUT", "3.0"))

# Simulated voting configuration
SIMULATED_VOTING_ENABLED = os.getenv(
    "SIMULATED_VOTING_ENABLED", "false").lower() == "true"
SIMULATED_VOTING_INTERVAL_SECONDS = float(
    os.getenv("SIMULATED_VOTING_INTERVAL_SECONDS", "2.0"))
SIMULATED_VOTING_MAX_VOTES_PER_PROPOSAL = int(
    os.getenv("SIMULATED_VOTING_MAX_VOTES_PER_PROPOSAL", "200"))
SIMULATED_VOTING_YES_PROBABILITY = float(
    os.getenv("SIMULATED_VOTING_YES_PROBABILITY", "0.65"))

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
simulated_voting_agent = None


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

    # Start background Storacha sync task if enabled
    if AUTO_SYNC_ENABLED:
        logger.info("Starting automatic Storacha sync background task...")
        logger.info(f"Sync interval: {SYNC_INTERVAL_HOURS} hours")
        # Run in thread pool since it's a blocking function
        storacha_executor.submit(periodic_storacha_sync)
    else:
        logger.info("Automatic Storacha sync is disabled")
        logger.info(f"To enable, set STORACHA_AUTO_SYNC=true in .env file")

    # Start simulated voting agent (demo/automation)
    if SIMULATED_VOTING_ENABLED:
        try:
            from .vote_simulation_agent import SimulatedVotingAgent
            global simulated_voting_agent
            simulated_voting_agent = SimulatedVotingAgent(
                interval_seconds=SIMULATED_VOTING_INTERVAL_SECONDS,
                max_votes_per_proposal=SIMULATED_VOTING_MAX_VOTES_PER_PROPOSAL,
                yes_probability=SIMULATED_VOTING_YES_PROBABILITY,
                db_factory=SessionLocal
            )
            simulated_voting_agent.start()
            logger.info(
                "Simulated voting agent started",
                extra={
                    "interval_seconds": SIMULATED_VOTING_INTERVAL_SECONDS,
                    "max_votes_per_proposal": SIMULATED_VOTING_MAX_VOTES_PER_PROPOSAL,
                    "yes_probability": SIMULATED_VOTING_YES_PROBABILITY
                }
            )
        except Exception as exc:
            logger.error(f"Failed to start simulated voting agent: {exc}")

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
    logger.info("Shutting down thread pool executors...")
    executor.shutdown(wait=True)
    storacha_executor.shutdown(wait=True)
    if simulated_voting_agent:
        simulated_voting_agent.stop()
    logger.info("Shutdown complete")


# Pydantic models for request/response
class SubmitMemoRequest(BaseModel):
    title: str
    summary: str
    cid: str
    confidence: int  # 0-100
    metadata: dict = Field(default_factory=dict)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v):
        if not v or not v.strip():
            raise ValueError('Summary cannot be empty')
        return v.strip()

    @field_validator('cid')
    @classmethod
    def validate_cid(cls, v):
        if not v or not v.strip():
            raise ValueError('IPFS CID cannot be empty')
        return v.strip()

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not isinstance(v, int) or v < 0 or v > 100:
            raise ValueError('Confidence must be an integer between 0 and 100')
        return v


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
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    proposal_id: int
    voter_address: str
    vote: int  # 1 for yes, 0 for no

    @field_validator('voter_address')
    @classmethod
    def validate_voter_address(cls, v):
        if not v or not v.strip():
            raise ValueError('voter_address cannot be empty')
        return v.strip()

    @field_validator('vote')
    @classmethod
    def validate_vote(cls, v):
        if v not in [0, 1]:
            raise ValueError('vote must be 0 (no) or 1 (yes)')
        return v

    @field_validator('proposal_id')
    @classmethod
    def validate_proposal_id(cls, v):
        if not isinstance(v, int) or v <= 0:
            raise ValueError('proposal_id must be a positive integer')
        return v


class VoteRequestNoId(BaseModel):
    """Vote request without proposal_id (extracted from URL path)"""
    voter_address: str
    vote: int  # 1 for yes, 0 for no

    @field_validator('voter_address')
    @classmethod
    def validate_voter_address(cls, v):
        if not v or not v.strip():
            raise ValueError('voter_address cannot be empty')
        return v.strip()

    @field_validator('vote')
    @classmethod
    def validate_vote(cls, v):
        if v not in [0, 1]:
            raise ValueError('vote must be 0 (no) or 1 (yes)')
        return v


class FinalizeRequest(BaseModel):
    proposal_id: int

    @field_validator('proposal_id')
    @classmethod
    def validate_proposal_id(cls, v):
        if not isinstance(v, int) or v <= 0:
            raise ValueError('proposal_id must be a positive integer')
        return v


class DiscoverStartupsRequest(BaseModel):
    sources: Optional[List[str]] = None
    limit_per_source: int = 5
    auto_process: bool = True


class SyncFromManifestRequest(BaseModel):
    manifest_cid: str
    skip_existing: bool = True


class SyncFromCidsRequest(BaseModel):
    cids: List[str]
    skip_existing: bool = True


class VoiceInteractionRequest(BaseModel):
    # Text transcribed from speech (using Web Speech API on frontend)
    transcribed_text: str

    @field_validator('transcribed_text')
    @classmethod
    def validate_transcribed_text(cls, v):
        if not v or not v.strip():
            raise ValueError('transcribed_text cannot be empty')
        return v.strip()


class CreateUserRequest(BaseModel):
    wallet_address: str
    email: Optional[str] = None


class CreateOrganizationRequest(BaseModel):
    name: str
    sector: Optional[str] = None
    team_members: List[str] = Field(default_factory=list)  # List of wallet addresses
    creator_wallet: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip()

    @field_validator('creator_wallet')
    @classmethod
    def validate_creator_wallet(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('creator_wallet cannot be empty')
        v_clean = v.strip()
        if not v_clean.startswith('N'):
            raise ValueError(f'Invalid NEO wallet address: {v_clean} (must start with \"N\")')
        return v_clean

    @field_validator('team_members')
    @classmethod
    def validate_team_members(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('team_members must contain at least one wallet address')
        cleaned = []
        for addr in v:
            if not addr or not addr.strip():
                raise ValueError('team_members cannot contain empty addresses')
            addr_clean = addr.strip()
            if not addr_clean.startswith('N'):
                raise ValueError(f'Invalid NEO wallet address: {addr_clean} (must start with \"N\")')
            cleaned.append(addr_clean)
        return cleaned


# API Endpoints

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    current_space = get_current_storacha_space()
    return {
        "status": "healthy",
        "service": "AI Investment Scout DAO Backend",
        "demo_mode": os.getenv("DEMO_MODE", "true") == "true",
        "auto_search_enabled": AUTO_SEARCH_ENABLED,
        "search_interval_hours": SEARCH_INTERVAL_HOURS,
        "storacha_auto_sync_enabled": AUTO_SYNC_ENABLED,
        "storacha_sync_interval_hours": SYNC_INTERVAL_HOURS,
        "storacha_space": current_space or "not set"
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


@app.get("/sync/storacha/status")
async def storacha_sync_status():
    """Get status of automatic Storacha sync."""
    manifest_cid = get_manifest_cid()

    return {
        "auto_sync_enabled": AUTO_SYNC_ENABLED,
        "sync_interval_hours": SYNC_INTERVAL_HOURS,
        "manifest_cid": manifest_cid,
        "skip_existing": os.getenv("STORACHA_SYNC_SKIP_EXISTING", "true").lower() == "true",
        "existing_cids_count": len(get_existing_cids())
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
        # Deduplicate by CID or title
        existing = db.query(DBProposal).filter(
            (DBProposal.ipfs_cid == clean_cid(cid)) | (DBProposal.title == title)
        ).first()
        if existing:
            logger.info(
                "Duplicate proposal detected; returning existing record (direct submit)")
            return {
                "id": existing.id,
                "title": existing.title,
                "summary": existing.summary,
                "ipfs_cid": existing.ipfs_cid,
                "confidence": existing.confidence,
                "status": existing.status,
                "yes_votes": existing.yes_votes,
                "no_votes": existing.no_votes,
                "created_at": existing.created_at.isoformat(),
                "deadline": existing.deadline,
                "metadata": existing.proposal_metadata
            }

        proposal_payload = {
            "title": title,
            "summary": summary,
            "cid": cid,
            "confidence": confidence,
            "metadata": metadata or {}
        }
        proposal_payload = run_research_pipeline(
            proposal_payload, source="submit_proposal_direct")
        title = proposal_payload.get("title", title)
        summary = proposal_payload.get("summary", summary)
        cid = proposal_payload.get("cid", cid)
        confidence = proposal_payload.get("confidence", confidence)
        metadata = proposal_payload.get("metadata", metadata or {})

        # Add current Storacha space to metadata for filtering
        current_space = get_current_storacha_space()
        if current_space:
            metadata["storacha_space"] = current_space
            logger.debug(
                f"Tagged proposal with Storacha space: {current_space}")

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

        # Refresh Storacha manifest in background (fail-open)
        schedule_manifest_refresh(source="submit_proposal_direct")

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
        proposal_payload = {
            "title": request.title,
            "summary": request.summary,
            "cid": request.cid,
            "confidence": request.confidence,
            "metadata": request.metadata
        }
        proposal_payload = run_research_pipeline(
            proposal_payload, source="submit_memo")
        title = proposal_payload.get("title", request.title)
        summary = proposal_payload.get("summary", request.summary)
        cid = proposal_payload.get("cid", request.cid)
        confidence = proposal_payload.get("confidence", request.confidence)
        metadata = proposal_payload.get("metadata", request.metadata)

        # Add current Storacha space to metadata for filtering
        current_space = get_current_storacha_space()
        if current_space:
            metadata["storacha_space"] = current_space
            logger.debug(
                f"Tagged proposal with Storacha space: {current_space}")

        # Deduplicate by CID or title
        existing = db.query(DBProposal).filter(
            (DBProposal.ipfs_cid == clean_cid(cid)) | (DBProposal.title == title)
        ).first()
        if existing:
            logger.info(
                "Duplicate proposal detected; returning existing record (HTTP submit)")
            return ProposalResponse(
                id=existing.id,
                title=existing.title,
                summary=existing.summary,
                ipfs_cid=existing.ipfs_cid,
                confidence=existing.confidence,
                status=existing.status,
                yes_votes=existing.yes_votes,
                no_votes=existing.no_votes,
                created_at=existing.created_at.isoformat(),
                deadline=existing.deadline,
                metadata=existing.proposal_metadata or {}
            )

        # Calculate deadline (7 days from now, in block timestamp)
        import time
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

        # Refresh Storacha manifest in background (fail-open)
        schedule_manifest_refresh(source="submit_memo")

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
            metadata=db_proposal.proposal_metadata or {}
        )

    except Exception as e:
        logger.error(f"Error submitting memo: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit proposal: {str(e)}")


@app.get("/proposals", response_model=List[ProposalResponse])
async def get_proposals(db: Session = Depends(get_db)):
    """Get list of all proposals with on-chain status."""
    try:
        if STORACHA_SYNC_ON_FETCH:
            manifest_cid = get_manifest_cid()
            if manifest_cid:
                try:
                    future = storacha_executor.submit(
                        sync_from_manifest, manifest_cid, True)
                    future.result(timeout=STORACHA_SYNC_ON_FETCH_TIMEOUT)
                except FuturesTimeout:
                    logger.warning(
                        "Manifest sync on fetch timed out; continuing without blocking",
                        extra={"timeout_s": STORACHA_SYNC_ON_FETCH_TIMEOUT}
                    )
                except Exception as sync_exc:
                    logger.debug(
                        "Manifest sync skipped due to error: %s", sync_exc)

        logger.info("Fetching proposals from database...")

        # Get current Storacha space and filter proposals
        current_space = get_current_storacha_space()
        query = db.query(DBProposal)

        if current_space:
            # Filter by current space: include proposals with matching space or no space (legacy)
            # SQLite JSON filtering: use JSON_EXTRACT or manual filtering
            from sqlalchemy import or_, func
            import json

            # For SQLite, we need to handle JSON differently
            # Filter: space matches OR space is null/missing
            def space_matches(proposal):
                meta = proposal.proposal_metadata or {}
                space = meta.get("storacha_space")
                return space is None or space == current_space

            # We'll filter in Python for SQLite compatibility
            logger.info(
                f"Filtering proposals by Storacha space: {current_space}")
        else:
            # If no space is set, show all proposals (backward compatibility)
            logger.info("No Storacha space detected, showing all proposals")

        # Query database directly (SQLAlchemy handles async properly with check_same_thread=False)
        # No need for thread pool - SQLite with check_same_thread=False works fine
        proposals = query.order_by(DBProposal.created_at.desc()).all()

        # Filter by space in Python (SQLite JSON support varies)
        if current_space:
            filtered_proposals = []
            for proposal in proposals:
                meta = proposal.proposal_metadata or {}
                space = meta.get("storacha_space")
                # Include if space matches or is missing (legacy proposals)
                if space is None or space == current_space:
                    filtered_proposals.append(proposal)
            proposals = filtered_proposals

        logger.info(
            f"Found {len(proposals)} proposals in database (after space filtering)")

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
            metadata=p.proposal_metadata or {}
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
        metadata=proposal.proposal_metadata or {}
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
        return process_vote(
            db=db,
            proposal=proposal,
            voter_address=request.voter_address,
            vote_value=request.vote
        )
    except HTTPException:
        db.rollback()
        raise
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
    # Validate inputs
    if not request.voter_address or not request.voter_address.strip():
        raise HTTPException(
            status_code=400, detail="voter_address is required and cannot be empty")

    if request.vote not in [0, 1]:
        raise HTTPException(
            status_code=400, detail="vote must be 0 (no) or 1 (yes)")

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
        return process_vote(
            db=db,
            proposal=proposal,
            voter_address=request.voter_address,
            vote_value=request.vote
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing vote: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process vote: {str(e)}")


@app.get("/proposals/{proposal_id}/has-voted/{voter_address}")
async def has_voted(proposal_id: int, voter_address: str, db: Session = Depends(get_db)):
    """
    Check on-chain whether a voter has already cast a vote for a proposal.

    Uses the smart contract has_voted method to avoid duplicate voting UI.
    """
    proposal = db.query(DBProposal).filter(
        DBProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    try:
        result = get_neo_client().has_voted(
            proposal.on_chain_id or proposal_id,
            voter_address
        )
        return {
            "proposal_id": proposal_id,
            "voter_address": voter_address,
            "has_voted": bool(result)
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error checking on-chain vote status: %s",
                     exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to check on-chain vote status"
        )


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


@app.post("/sync/storacha/manifest")
async def sync_from_manifest_endpoint(
    request: SyncFromManifestRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(True, description="Run sync in background")
):
    """
    Sync proposals from a manifest.json file stored on Storacha/IPFS.

    The manifest should be a JSON array of proposal objects with:
    - cid: IPFS CID
    - title: Proposal title
    - summary: Executive summary
    - confidence: Confidence score (0-100)
    - metadata: Optional metadata dict

    Args:
        async_mode: If True, run in background. If False, wait for completion.
    """
    logger.info(f"Syncing from manifest: {request.manifest_cid}")

    if async_mode:
        # Run in background to avoid blocking
        def run_sync():
            return sync_from_manifest(
                manifest_cid=request.manifest_cid,
                skip_existing=request.skip_existing
            )

        background_tasks.add_task(run_sync)

        return {
            "status": "started",
            "message": "Sync from manifest started in background",
            "manifest_cid": request.manifest_cid
        }
    else:
        # Run synchronously
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            lambda: sync_from_manifest(
                manifest_cid=request.manifest_cid,
                skip_existing=request.skip_existing
            )
        )
        return result


@app.post("/sync/storacha/cids")
async def sync_from_cids_endpoint(
    request: SyncFromCidsRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(True, description="Run sync in background")
):
    """
    Sync proposals from a list of IPFS CIDs.

    For each CID, the system will:
    1. Download the PDF from IPFS
    2. Extract metadata (title, summary, confidence)
    3. Check if CID already exists in database
    4. Add only if not already present (if skip_existing=True)

    Args:
        async_mode: If True, run in background. If False, wait for completion.
    """
    logger.info(f"Syncing from {len(request.cids)} CIDs")

    if async_mode:
        # Run in background to avoid blocking
        def run_sync():
            return sync_from_cids(
                cids=request.cids,
                skip_existing=request.skip_existing
            )

        background_tasks.add_task(run_sync)

        return {
            "status": "started",
            "message": "Sync from CIDs started in background",
            "cid_count": len(request.cids)
        }
    else:
        # Run synchronously
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            lambda: sync_from_cids(
                cids=request.cids,
                skip_existing=request.skip_existing
            )
        )
        return result


@app.get("/sync/storacha/existing")
async def get_existing_cids_endpoint():
    """
    Get list of all IPFS CIDs currently in the database.
    Useful for checking what's already synced.
    """
    try:
        cids = get_existing_cids()
        return {
            "success": True,
            "count": len(cids),
            "cids": cids
        }
    except Exception as e:
        logger.error(f"Error getting existing CIDs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get existing CIDs: {str(e)}"
        )


@app.delete("/proposals/clear-old-space")
async def clear_old_space_proposals(
    space_name: str = Query(...,
                            description="Space name to clear proposals from"),
    db: Session = Depends(get_db)
):
    """
    Clear proposals from a specific Storacha space.
    Useful when switching spaces and wanting to remove old proposals.

    WARNING: This permanently deletes proposals from the database.
    """
    try:
        current_space = get_current_storacha_space()
        if space_name == current_space:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot clear proposals from current active space: {space_name}"
            )

        # Find proposals from the specified space
        all_proposals = db.query(DBProposal).all()
        to_delete = []
        for proposal in all_proposals:
            meta = proposal.proposal_metadata or {}
            if meta.get("storacha_space") == space_name:
                to_delete.append(proposal)

        count = len(to_delete)
        if count == 0:
            return {
                "success": True,
                "message": f"No proposals found for space: {space_name}",
                "deleted_count": 0
            }

        # Delete proposals
        for proposal in to_delete:
            db.delete(proposal)
        db.commit()

        logger.info(f"Cleared {count} proposals from space: {space_name}")

        return {
            "success": True,
            "message": f"Cleared {count} proposals from space: {space_name}",
            "deleted_count": count
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing old space proposals: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear proposals: {str(e)}"
        )


@app.get("/proposals/spaces")
async def get_proposal_spaces(db: Session = Depends(get_db)):
    """
    Get list of all Storacha spaces that have proposals in the database.
    Useful for seeing which spaces have data.
    """
    try:
        all_proposals = db.query(DBProposal).all()
        spaces = {}
        no_space_count = 0

        for proposal in all_proposals:
            meta = proposal.proposal_metadata or {}
            space = meta.get("storacha_space")
            if space:
                spaces[space] = spaces.get(space, 0) + 1
            else:
                no_space_count += 1

        current_space = get_current_storacha_space()

        return {
            "success": True,
            "current_space": current_space,
            "spaces": spaces,
            "no_space_count": no_space_count,
            "total_proposals": len(all_proposals)
        }
    except Exception as e:
        logger.error(f"Error getting proposal spaces: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get proposal spaces: {str(e)}"
        )


@app.post("/proposals/{proposal_id}/voice-interaction")
async def voice_interaction(proposal_id: int, request: VoiceInteractionRequest, db: Session = Depends(get_db)):
    """
    Voice interaction endpoint:
    1. Receives transcribed text from frontend (using Web Speech API)
    2. Sends transcribed text + company summary to ChatGPT
    3. Uses ElevenLabs text-to-speech to generate audio response
    4. Returns audio response
    """
    logger.info(
        f"[Voice] Voice interaction request received - Proposal ID: {proposal_id}")
    logger.debug(
        f"[Voice] Request body: transcribed_text='{request.transcribed_text[:50]}...'")

    try:
        # Get proposal
        logger.debug(f"[Voice] Querying database for proposal {proposal_id}")
        proposal = db.query(DBProposal).filter(
            DBProposal.id == proposal_id).first()
        if not proposal:
            logger.warning(f"[Voice] Proposal {proposal_id} not found")
            raise HTTPException(status_code=404, detail="Proposal not found")

        logger.info(f"[Voice] Found proposal: {proposal.title}")

        transcribed_text = request.transcribed_text.strip()
        logger.info(f"[Voice] Transcribed text: '{transcribed_text}'")

        if not transcribed_text:
            logger.warning("[Voice] Transcribed text is empty")
            raise HTTPException(
                status_code=400, detail="Transcribed text cannot be empty")

        # Check for ElevenLabs API key
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            logger.error("[Voice] ElevenLabs API key not configured")
            raise HTTPException(
                status_code=500,
                detail="ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file"
            )
        logger.debug("[Voice] ElevenLabs API key found")

        # Check for OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("[Voice] OpenAI API key not configured")
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file"
            )
        logger.debug("[Voice] OpenAI API key found")

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Send to ChatGPT with company summary
            llm_model = os.getenv("LLM_MODEL", "gpt-4")
            logger.info(
                f"[Voice] Sending request to ChatGPT (model: {llm_model})")
            logger.debug(
                f"[Voice] Company summary length: {len(proposal.summary)} characters")

            chatgpt_prompt = f"Company Summary:\n{proposal.summary}\n\nUser Question: {transcribed_text}\n\nPlease provide a helpful answer about this company based on the summary above."
            logger.debug(
                f"[Voice] ChatGPT prompt length: {len(chatgpt_prompt)} characters")

            chatgpt_response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions about investment proposals. Provide clear, concise answers based on the company summary provided."
                        },
                        {
                            "role": "user",
                            "content": chatgpt_prompt
                        }
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )

            logger.info(
                f"[Voice] ChatGPT response status: {chatgpt_response.status_code}")
            if chatgpt_response.status_code != 200:
                logger.error(
                    f"[Voice] ChatGPT error: {chatgpt_response.status_code} - {chatgpt_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"ChatGPT API failed: {chatgpt_response.text}"
                )

            chatgpt_result = chatgpt_response.json()
            answer_text = chatgpt_result["choices"][0]["message"]["content"]
            logger.info(
                f"[Voice] ChatGPT answer received ({len(answer_text)} characters): {answer_text[:100]}...")

            # Step 2: Text-to-speech using ElevenLabs
            # Get default voice ID (or use a specific one)
            voice_id = os.getenv("ELEVENLABS_VOICE_ID",
                                 "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel

            # Use a newer model available on free tier
            # Options: eleven_turbo_v2_5 (fast, free tier), eleven_multilingual_v2 (multilingual, free tier)
            tts_model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")

            logger.info(
                f"[Voice] Sending request to ElevenLabs TTS (voice_id: {voice_id}, model: {tts_model})")
            logger.debug(
                f"[Voice] Text to convert to speech ({len(answer_text)} characters): {answer_text[:100]}...")

            tts_response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": elevenlabs_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": answer_text,
                    "model_id": tts_model,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
            )

            logger.info(
                f"[Voice] ElevenLabs TTS response status: {tts_response.status_code}")
            if tts_response.status_code != 200:
                logger.error(
                    f"[Voice] ElevenLabs TTS error: {tts_response.status_code} - {tts_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Text-to-speech failed: {tts_response.text}"
                )

            # Return audio response
            audio_bytes = tts_response.content
            logger.info(
                f"[Voice] Audio response generated: {len(audio_bytes)} bytes")
            logger.debug(
                f"[Voice] Audio content type: {tts_response.headers.get('content-type', 'unknown')}")

            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'attachment; filename="response.mp3"'
                }
            )

    except HTTPException:
        logger.error(
            f"[Voice] HTTPException raised for proposal {proposal_id}")
        raise
    except Exception as e:
        logger.error(
            f"[Voice] Unexpected error in voice interaction for proposal {proposal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Voice interaction failed: {str(e)}"
        )


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
        # Normalize and deduplicate team members (preserve order)
        normalized_members: List[str] = []
        seen = set()
        # ensure creator is part of the org
        candidate_members = [*request.team_members, request.creator_wallet]
        for member in candidate_members:
            member_clean = member.strip()
            if not member_clean:
                continue
            if not member_clean.startswith("N"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid NEO wallet address: {member_clean} (must start with 'N')"
                )
            if member_clean not in seen:
                seen.add(member_clean)
                normalized_members.append(member_clean)

        if not normalized_members:
            raise HTTPException(
                status_code=400,
                detail="At least one valid team member wallet address is required"
            )

        # Check for duplicate organization name to avoid accidental collision
        existing = db.query(DBOrganization).filter(
            DBOrganization.name == request.name.strip()
        ).first()
        if existing:
            logger.warning(f"Organization with name '{request.name}' already exists")
            return {
                "success": True,
                "id": existing.id,
                "name": existing.name,
                "sector": existing.sector,
                "ipfs_cid": existing.ipfs_cid,
                "creator_wallet": existing.creator_wallet,
                "team_members": existing.team_members or [],
                "member_count": len(existing.team_members or []),
                "created_at": existing.created_at.isoformat(),
            }

        # Prepare organization data for IPFS
        org_data = {
            "name": request.name.strip(),
            "sector": request.sector.strip() if request.sector else None,
            "creator_wallet": request.creator_wallet.strip(),
            "team_members": normalized_members,
            "member_count": len(normalized_members),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Upload to Storacha/IPFS (fail closed to avoid dangling DB records without storage)
        logger.info("Uploading organization data to Storacha/IPFS...")
        safe_filename = request.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        ipfs_cid = upload_json_to_ipfs(
            org_data, f"organization_{safe_filename}.json"
        )
        if not ipfs_cid:
            raise HTTPException(
                status_code=502,
                detail="Failed to persist organization to IPFS/Storacha"
            )

        # Save to database
        organization = DBOrganization(
            name=request.name.strip(),
            sector=request.sector.strip() if request.sector else None,
            ipfs_cid=ipfs_cid,
            creator_wallet=request.creator_wallet.strip(),
            team_members=normalized_members,  # Store as JSON array
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
            "team_members": organization.team_members or [],
            "member_count": len(organization.team_members or []),
            "created_at": organization.created_at.isoformat(),
        }

    except ValueError as e:
        db.rollback()
        logger.error(f"Validation error creating organization: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Invalid request: {str(e)}"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating organization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to create organization: {str(e)}"
        )


@app.get("/organizations")
async def get_organizations(
    wallet_address: Optional[str] = Query(None, description="Filter by wallet address"),
    db: Session = Depends(get_db)
):
    """
    Get organizations. If wallet_address is provided, returns organizations where the user is a member.
    """
    try:
        if wallet_address:
            # Get all organizations and filter in Python (SQLite JSON support varies)
            all_orgs = db.query(DBOrganization).all()
            organizations = []
            for org in all_orgs:
                # Check if user is creator
                if org.creator_wallet == wallet_address:
                    organizations.append(org)
                # Check if user is in team_members (JSON array)
                elif org.team_members and isinstance(org.team_members, list):
                    if wallet_address in org.team_members:
                        organizations.append(org)
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
                "team_members": org.team_members or [],
                "member_count": len(org.team_members) if org.team_members else 0,
                "created_at": org.created_at.isoformat(),
            }
            for org in organizations
        ]

    except Exception as e:
        logger.error(f"Error fetching organizations: {str(e)}", exc_info=True)
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
