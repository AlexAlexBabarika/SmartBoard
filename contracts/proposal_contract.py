"""
NEO Smart Contract for AI Investment Scout DAO
Manages investment proposals, voting, and finalization.

Written in Python using neo3-boa compatible syntax.
"""

from typing import Any, cast
from boa3.builtin import NeoMetadata, metadata, public
from boa3.builtin.contract import abort
from boa3.builtin.interop.runtime import check_witness, time, executing_script_hash
from boa3.builtin.interop.storage import delete, get, put
from boa3.builtin.type import UInt160


# Contract metadata
@metadata
def manifest_metadata() -> NeoMetadata:
    meta = NeoMetadata()
    meta.author = "AI Investment Scout DAO"
    meta.description = "Investment proposal voting and governance contract"
    meta.email = "dao@aiinvestmentscout.io"
    return meta


# Storage keys
PROPOSAL_COUNT_KEY = b'proposal_count'
PROPOSAL_PREFIX = b'proposal:'
VOTE_PREFIX = b'vote:'


# Proposal structure (stored as concatenated bytes)
# Format: title_len(2) + title + ipfs_hash_len(2) + ipfs_hash + deadline(4) + confidence(1) + yes_votes(4) + no_votes(4) + finalized(1)


@public
def create_proposal(title: str, ipfs_hash: str, deadline: int, confidence: int) -> int:
    """
    Create a new investment proposal.
    
    Args:
        title: Proposal title
        ipfs_hash: IPFS CID for the full investment memo
        deadline: Unix timestamp when voting ends
        confidence: Confidence score (0-100)
        
    Returns:
        Proposal ID
    """
    # Get next proposal ID
    count = get(PROPOSAL_COUNT_KEY).to_int()
    proposal_id = count + 1
    
    # Store proposal count
    put(PROPOSAL_COUNT_KEY, proposal_id)
    
    # Create proposal key
    proposal_key = PROPOSAL_PREFIX + proposal_id.to_bytes()
    
    # Store proposal data
    # Format: title|ipfs_hash|deadline|confidence|yes_votes|no_votes|finalized
    proposal_data = title + '|' + ipfs_hash + '|' + str(deadline) + '|' + str(confidence) + '|0|0|0'
    put(proposal_key, proposal_data)
    
    return proposal_id


@public
def vote(proposal_id: int, voter: UInt160, choice: int) -> bool:
    """
    Vote on a proposal.
    
    Args:
        proposal_id: ID of the proposal
        voter: Voter's script hash
        choice: 1 for yes, 0 for no
        
    Returns:
        True if vote was recorded successfully
    """
    # Verify the voter is the transaction sender
    if not check_witness(voter):
        abort()
        return False
    
    # Get proposal
    proposal_key = PROPOSAL_PREFIX + proposal_id.to_bytes()
    proposal_data = get(proposal_key)
    
    if len(proposal_data) == 0:
        # Proposal doesn't exist
        return False
    
    # Parse proposal data
    parts = proposal_data.to_str().split('|')
    if len(parts) < 7:
        return False
    
    deadline = int(parts[2])
    finalized = int(parts[6])
    
    # Check if voting is still open
    if time > deadline or finalized == 1:
        return False
    
    # Check if voter has already voted
    vote_key = VOTE_PREFIX + proposal_id.to_bytes() + voter
    if len(get(vote_key)) > 0:
        # Already voted
        return False
    
    # Record vote
    put(vote_key, choice)
    
    # Update vote tally
    yes_votes = int(parts[4])
    no_votes = int(parts[5])
    
    if choice == 1:
        yes_votes += 1
    else:
        no_votes += 1
    
    # Update proposal
    parts[4] = str(yes_votes)
    parts[5] = str(no_votes)
    updated_data = '|'.join(parts)
    put(proposal_key, updated_data)
    
    return True


@public
def finalize_proposal(proposal_id: int) -> bool:
    """
    Finalize a proposal (close voting).
    
    Args:
        proposal_id: ID of the proposal
        
    Returns:
        True if finalized successfully
    """
    # Get proposal
    proposal_key = PROPOSAL_PREFIX + proposal_id.to_bytes()
    proposal_data = get(proposal_key)
    
    if len(proposal_data) == 0:
        return False
    
    # Parse proposal data
    parts = proposal_data.to_str().split('|')
    if len(parts) < 7:
        return False
    
    deadline = int(parts[2])
    finalized = int(parts[6])
    
    # Check if already finalized
    if finalized == 1:
        return False
    
    # Check if deadline has passed
    if time < deadline:
        # Can only finalize after deadline
        return False
    
    # Mark as finalized
    parts[6] = '1'
    updated_data = '|'.join(parts)
    put(proposal_key, updated_data)
    
    return True


@public
def get_proposal(proposal_id: int) -> str:
    """
    Get proposal data.
    
    Args:
        proposal_id: ID of the proposal
        
    Returns:
        Proposal data as string (format: title|ipfs_hash|deadline|confidence|yes_votes|no_votes|finalized)
    """
    proposal_key = PROPOSAL_PREFIX + proposal_id.to_bytes()
    proposal_data = get(proposal_key)
    
    if len(proposal_data) == 0:
        return ''
    
    return proposal_data.to_str()


@public
def get_proposal_count() -> int:
    """
    Get total number of proposals.
    
    Returns:
        Proposal count
    """
    count = get(PROPOSAL_COUNT_KEY)
    if len(count) == 0:
        return 0
    return count.to_int()


@public
def has_voted(proposal_id: int, voter: UInt160) -> bool:
    """
    Check if a voter has voted on a proposal.
    
    Args:
        proposal_id: ID of the proposal
        voter: Voter's script hash
        
    Returns:
        True if the voter has voted
    """
    vote_key = VOTE_PREFIX + proposal_id.to_bytes() + voter
    return len(get(vote_key)) > 0


@public
def get_vote(proposal_id: int, voter: UInt160) -> int:
    """
    Get a voter's vote on a proposal.
    
    Args:
        proposal_id: ID of the proposal
        voter: Voter's script hash
        
    Returns:
        Vote (1 for yes, 0 for no, -1 if not voted)
    """
    vote_key = VOTE_PREFIX + proposal_id.to_bytes() + voter
    vote_data = get(vote_key)
    
    if len(vote_data) == 0:
        return -1
    
    return vote_data.to_int()

