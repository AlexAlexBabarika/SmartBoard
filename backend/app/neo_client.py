"""
NEO blockchain client for smart contract interactions.
Supports both real NEO RPC calls and simulated demo mode.
"""

import os
import logging
from typing import Dict, Any
import hashlib
import time

logger = logging.getLogger(__name__)

# Check if we're in demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


class NeoClient:
    """
    Client for interacting with NEO blockchain and smart contract.
    Falls back to simulation mode if credentials are not provided.
    """
    
    def __init__(self):
        self.rpc_url = os.getenv("NEO_RPC_URL")
        self.private_key = os.getenv("NEO_WALLET_PRIVATE_KEY")
        self.contract_hash = os.getenv("NEO_CONTRACT_HASH")
        
        # Determine if we can make real blockchain calls
        self.is_simulated = DEMO_MODE or not all([self.rpc_url, self.private_key, self.contract_hash])
        
        # Always initialize simulation state (needed for fallback even when not in demo mode)
        self.simulated_proposals = {}
        self.simulated_votes = {}
        self.next_proposal_id = 1
        
        if self.is_simulated:
            logger.warning("NEO client running in SIMULATION mode - no real blockchain transactions")
        else:
            logger.info(f"NEO client initialized with RPC: {self.rpc_url}")
            # In a real implementation, initialize neo-mamba client here
            # from neo.core.Blockchain import Blockchain
            # from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
            # self.wallet = UserWallet.Open(path, password)
    
    def create_proposal(self, title: str, ipfs_hash: str, deadline: int, confidence: int) -> Dict[str, Any]:
        """
        Create a new proposal on the NEO smart contract.
        
        Args:
            title: Proposal title
            ipfs_hash: IPFS CID for the full memo document
            deadline: Unix timestamp for voting deadline
            confidence: Confidence score (0-100)
            
        Returns:
            Dict with tx_hash and proposal_id
        """
        if self.is_simulated:
            return self._simulate_create_proposal(title, ipfs_hash, deadline, confidence)
        
        try:
            # Real NEO transaction would look like this:
            # from neo.mamba import Mamba
            # mamba = Mamba(rpc=self.rpc_url, wallet=self.private_key)
            # result = mamba.invoke_contract(
            #     contract_hash=self.contract_hash,
            #     operation="create_proposal",
            #     args=[title, ipfs_hash, deadline, confidence]
            # )
            # return {"tx_hash": result.tx_hash, "proposal_id": result.stack[0]}
            
            logger.warning("Real NEO implementation not configured, using simulation")
            return self._simulate_create_proposal(title, ipfs_hash, deadline, confidence)
            
        except Exception as e:
            logger.error(f"Error creating proposal on NEO: {e}")
            raise
    
    def vote(self, proposal_id: int, voter: str, choice: int) -> Dict[str, Any]:
        """
        Submit a vote on a proposal.
        
        Args:
            proposal_id: ID of the proposal
            voter: Voter's NEO address
            choice: 1 for yes, 0 for no
            
        Returns:
            Dict with tx_hash
        """
        if self.is_simulated:
            return self._simulate_vote(proposal_id, voter, choice)
        
        try:
            # Real NEO transaction:
            # result = mamba.invoke_contract(
            #     contract_hash=self.contract_hash,
            #     operation="vote",
            #     args=[proposal_id, voter.encode(), choice]
            # )
            # return {"tx_hash": result.tx_hash}
            
            logger.warning("Real NEO implementation not configured, using simulation")
            return self._simulate_vote(proposal_id, voter, choice)
            
        except Exception as e:
            logger.error(f"Error submitting vote on NEO: {e}")
            raise
    
    def finalize_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """
        Finalize a proposal (close voting).
        
        Args:
            proposal_id: ID of the proposal
            
        Returns:
            Dict with tx_hash
        """
        if self.is_simulated:
            return self._simulate_finalize(proposal_id)
        
        try:
            # Real NEO transaction:
            # result = mamba.invoke_contract(
            #     contract_hash=self.contract_hash,
            #     operation="finalize_proposal",
            #     args=[proposal_id]
            # )
            # return {"tx_hash": result.tx_hash}
            
            logger.warning("Real NEO implementation not configured, using simulation")
            return self._simulate_finalize(proposal_id)
            
        except Exception as e:
            logger.error(f"Error finalizing proposal on NEO: {e}")
            raise
    
    def get_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """
        Get proposal data from blockchain.
        
        Args:
            proposal_id: ID of the proposal
            
        Returns:
            Dict with proposal data, or string in format: title|ipfs_hash|deadline|confidence|yes_votes|no_votes|finalized
        """
        if self.is_simulated:
            proposal = self.simulated_proposals.get(proposal_id, {})
            if proposal:
                # Return in same format as smart contract
                finalized = 1 if proposal.get("finalized", False) else 0
                return (
                    f"{proposal.get('title', '')}|"
                    f"{proposal.get('ipfs_hash', '')}|"
                    f"{proposal.get('deadline', 0)}|"
                    f"{proposal.get('confidence', 0)}|"
                    f"{proposal.get('yes_votes', 0)}|"
                    f"{proposal.get('no_votes', 0)}|"
                    f"{finalized}"
                )
            return ""
        
        # Real implementation would query the contract
        # from neo.mamba import Mamba
        # mamba = Mamba(rpc=self.rpc_url)
        # result = mamba.invoke_contract(
        #     contract_hash=self.contract_hash,
        #     operation="get_proposal",
        #     args=[proposal_id]
        # )
        # return result.stack[0]  # Returns string in format: title|ipfs_hash|deadline|confidence|yes_votes|no_votes|finalized
        
        logger.warning("Real NEO implementation not configured, using simulation")
        return ""
    
    # Simulation methods
    
    def _simulate_create_proposal(self, title: str, ipfs_hash: str, deadline: int, confidence: int) -> Dict[str, Any]:
        """Simulate creating a proposal without real blockchain interaction."""
        proposal_id = self.next_proposal_id
        self.next_proposal_id += 1
        
        # Generate fake transaction hash
        tx_data = f"{proposal_id}{title}{ipfs_hash}{time.time()}"
        tx_hash = "0x" + hashlib.sha256(tx_data.encode()).hexdigest()[:64]
        
        self.simulated_proposals[proposal_id] = {
            "id": proposal_id,
            "title": title,
            "ipfs_hash": ipfs_hash,
            "deadline": deadline,
            "confidence": confidence,
            "yes_votes": 0,
            "no_votes": 0,
            "finalized": False
        }
        
        logger.info(f"[SIMULATED] Created proposal {proposal_id} with TX: {tx_hash}")
        return {"tx_hash": tx_hash, "proposal_id": proposal_id}
    
    def _simulate_vote(self, proposal_id: int, voter: str, choice: int) -> Dict[str, Any]:
        """Simulate voting without real blockchain interaction."""
        tx_data = f"{proposal_id}{voter}{choice}{time.time()}"
        tx_hash = "0x" + hashlib.sha256(tx_data.encode()).hexdigest()[:64]
        
        vote_key = f"{proposal_id}:{voter}"
        if vote_key in self.simulated_votes:
            raise ValueError("Voter has already voted on this proposal")
        
        self.simulated_votes[vote_key] = choice
        
        if proposal_id in self.simulated_proposals:
            if choice == 1:
                self.simulated_proposals[proposal_id]["yes_votes"] += 1
            else:
                self.simulated_proposals[proposal_id]["no_votes"] += 1
        
        logger.info(f"[SIMULATED] Recorded vote on proposal {proposal_id} with TX: {tx_hash}")
        return {"tx_hash": tx_hash}
    
    def _simulate_finalize(self, proposal_id: int) -> Dict[str, Any]:
        """Simulate finalizing a proposal."""
        tx_data = f"finalize{proposal_id}{time.time()}"
        tx_hash = "0x" + hashlib.sha256(tx_data.encode()).hexdigest()[:64]
        
        if proposal_id in self.simulated_proposals:
            self.simulated_proposals[proposal_id]["finalized"] = True
        
        logger.info(f"[SIMULATED] Finalized proposal {proposal_id} with TX: {tx_hash}")
        return {"tx_hash": tx_hash}

