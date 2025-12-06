"""
Blockchain event listener for monitoring smart contract events.
Listens for proposal finalization events and triggers email notifications.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Check if we're in demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


class BlockchainListener:
    """
    Listens for blockchain events and triggers appropriate actions.
    Monitors the smart contract for proposal finalization events.
    """
    
    def __init__(self, neo_client, db_session_factory):
        """
        Initialize the blockchain listener.
        
        Args:
            neo_client: NeoClient instance for blockchain interactions
            db_session_factory: Function to create database sessions
        """
        self.neo_client = neo_client
        self.db_session_factory = db_session_factory
        self.is_running = False
        self.poll_interval = int(os.getenv("BLOCKCHAIN_POLL_INTERVAL", "30"))  # seconds
        
    async def start(self):
        """Start listening for blockchain events."""
        if self.is_running:
            logger.warning("Blockchain listener already running")
            return
        
        self.is_running = True
        logger.info(f"Starting blockchain event listener (poll interval: {self.poll_interval}s)")
        
        while self.is_running:
            try:
                await self._check_for_finalized_proposals()
            except Exception as e:
                logger.error(f"Error in blockchain listener: {str(e)}")
            
            await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop listening for blockchain events."""
        self.is_running = False
        logger.info("Stopping blockchain event listener")
    
    async def _check_for_finalized_proposals(self):
        """
        Check the blockchain for newly finalized proposals.
        Compares on-chain state with database state and triggers emails if needed.
        """
        if self.neo_client.is_simulated:
            # In simulation mode, we rely on API endpoints
            return
        
        db = self.db_session_factory()
        try:
            from .models import Proposal as DBProposal
            
            # Get all active proposals from database
            active_proposals = db.query(DBProposal).filter(
                DBProposal.status == "active"
            ).all()
            
            for proposal in active_proposals:
                try:
                    # Check on-chain status
                    on_chain_data = self.neo_client.get_proposal(
                        proposal.on_chain_id or proposal.id
                    )
                    
                    if not on_chain_data:
                        continue
                    
                    # Parse on-chain proposal data
                    # Format: title|ipfs_hash|deadline|confidence|yes_votes|no_votes|finalized
                    if isinstance(on_chain_data, str):
                        parts = on_chain_data.split('|')
                        if len(parts) >= 7:
                            finalized = int(parts[6])
                            
                            if finalized == 1:
                                # Proposal is finalized on-chain
                                # Determine outcome
                                yes_votes = int(parts[4])
                                no_votes = int(parts[5])
                                
                                if yes_votes > no_votes:
                                    status = "approved"
                                else:
                                    status = "rejected"
                                
                                # Update database if not already updated
                                if proposal.status == "active":
                                    proposal.status = status
                                    db.commit()
                                    logger.info(
                                        f"Proposal {proposal.id} finalized on-chain: {status}"
                                    )
                                
                                # Trigger email notifications
                                await self._trigger_proposal_outcome_emails(
                                    proposal.id,
                                    proposal.title,
                                    status,
                                    yes_votes,
                                    no_votes
                                )
                
                except Exception as e:
                    logger.error(
                        f"Error checking proposal {proposal.id} on-chain: {str(e)}"
                    )
                    continue
        
        finally:
            db.close()
    
    async def _trigger_proposal_outcome_emails(
        self,
        proposal_id: int,
        proposal_title: str,
        status: str,
        yes_votes: int,
        no_votes: int
    ):
        """
        Trigger email notifications for a finalized proposal.
        This is called when a proposal is finalized on the blockchain.
        """
        try:
            from .email_service import send_proposal_outcome_email
            from .models import Vote as DBVote, User as DBUser
            
            db = self.db_session_factory()
            try:
                # Get all votes for this proposal
                votes = db.query(DBVote).filter(
                    DBVote.proposal_id == proposal_id
                ).all()
                
                if not votes:
                    logger.info(
                        f"No votes found for proposal {proposal_id}, skipping email notifications"
                    )
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
                                f"Failed to send outcome email to {user.email}: {str(e)}"
                            )
                
                logger.info(
                    f"Sent proposal outcome emails to {emails_sent} voters for proposal {proposal_id} ({status}) - triggered by blockchain event"
                )
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Failed to trigger proposal outcome emails: {str(e)}")

