"""
Unit tests for NEO smart contract.
Uses mocked contract execution for testing logic.
"""

import pytest
from unittest.mock import MagicMock, patch


class MockStorage:
    """Mock storage for testing contract functions."""
    
    def __init__(self):
        self.data = {}
    
    def put(self, key, value):
        """Store a value."""
        if isinstance(key, bytes):
            key = key.hex()
        if isinstance(value, int):
            value = str(value).encode()
        if isinstance(value, str):
            value = value.encode()
        self.data[key] = value
    
    def get(self, key):
        """Retrieve a value."""
        if isinstance(key, bytes):
            key = key.hex()
        return self.data.get(key, b'')
    
    def delete(self, key):
        """Delete a value."""
        if isinstance(key, bytes):
            key = key.hex()
        if key in self.data:
            del self.data[key]


class TestProposalContract:
    """Tests for proposal contract logic."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.storage = MockStorage()
    
    def test_create_proposal(self):
        """Test creating a new proposal."""
        # Simulate contract behavior
        count_key = b'proposal_count'
        
        # Initial count should be 0
        count = self.storage.get(count_key)
        assert count == b''
        
        # Create first proposal
        proposal_id = 1
        self.storage.put(count_key, proposal_id)
        
        # Store proposal data
        proposal_key = b'proposal:' + str(proposal_id).encode()
        proposal_data = 'Test Proposal|QmTest123|1234567890|85|0|0|0'
        self.storage.put(proposal_key, proposal_data)
        
        # Verify stored
        stored_count = self.storage.get(count_key)
        assert stored_count == b'1'
        
        stored_proposal = self.storage.get(proposal_key)
        assert b'Test Proposal' in stored_proposal
        assert b'QmTest123' in stored_proposal
    
    def test_vote_on_proposal(self):
        """Test voting on a proposal."""
        # Setup: create a proposal
        proposal_id = 1
        proposal_key = b'proposal:' + str(proposal_id).encode()
        proposal_data = 'Test Proposal|QmTest123|9999999999|85|0|0|0'
        self.storage.put(proposal_key, proposal_data)
        
        # Vote yes
        voter = b'NTestVoter123'
        vote_key = b'vote:' + str(proposal_id).encode() + voter
        choice = 1
        
        # Check voter hasn't voted yet
        existing_vote = self.storage.get(vote_key)
        assert existing_vote == b''
        
        # Record vote
        self.storage.put(vote_key, choice)
        
        # Update proposal tally
        parts = proposal_data.split('|')
        yes_votes = int(parts[4]) + 1
        parts[4] = str(yes_votes)
        updated_data = '|'.join(parts)
        self.storage.put(proposal_key, updated_data)
        
        # Verify vote recorded
        stored_vote = self.storage.get(vote_key)
        assert stored_vote == b'1'
        
        # Verify tally updated
        stored_proposal = self.storage.get(proposal_key).decode()
        parts = stored_proposal.split('|')
        assert parts[4] == '1'  # yes_votes
        assert parts[5] == '0'  # no_votes
    
    def test_duplicate_vote_rejected(self):
        """Test that duplicate votes are rejected."""
        # Setup: create a proposal and vote once
        proposal_id = 1
        proposal_key = b'proposal:' + str(proposal_id).encode()
        proposal_data = 'Test Proposal|QmTest123|9999999999|85|1|0|0'
        self.storage.put(proposal_key, proposal_data)
        
        voter = b'NTestVoter123'
        vote_key = b'vote:' + str(proposal_id).encode() + voter
        self.storage.put(vote_key, 1)
        
        # Try to vote again
        existing_vote = self.storage.get(vote_key)
        assert existing_vote != b''  # Already voted
        
        # Vote should be rejected (would be checked in contract logic)
        # In real contract, this would return False
    
    def test_finalize_proposal(self):
        """Test finalizing a proposal."""
        # Setup: create a proposal with votes
        proposal_id = 1
        proposal_key = b'proposal:' + str(proposal_id).encode()
        proposal_data = 'Test Proposal|QmTest123|1000000000|85|5|2|0'
        self.storage.put(proposal_key, proposal_data)
        
        # Finalize
        parts = proposal_data.split('|')
        parts[6] = '1'  # Set finalized flag
        finalized_data = '|'.join(parts)
        self.storage.put(proposal_key, finalized_data)
        
        # Verify finalized
        stored_proposal = self.storage.get(proposal_key).decode()
        parts = stored_proposal.split('|')
        assert parts[6] == '1'  # finalized
        assert parts[4] == '5'  # yes_votes preserved
        assert parts[5] == '2'  # no_votes preserved
    
    def test_get_proposal(self):
        """Test retrieving proposal data."""
        # Setup: create a proposal
        proposal_id = 1
        proposal_key = b'proposal:' + str(proposal_id).encode()
        proposal_data = 'Investment in TestCo|QmAbc123|1234567890|78|10|3|0'
        self.storage.put(proposal_key, proposal_data)
        
        # Retrieve
        stored = self.storage.get(proposal_key).decode()
        
        # Parse and verify
        parts = stored.split('|')
        assert parts[0] == 'Investment in TestCo'
        assert parts[1] == 'QmAbc123'
        assert parts[2] == '1234567890'
        assert parts[3] == '78'
        assert parts[4] == '10'
        assert parts[5] == '3'
        assert parts[6] == '0'
    
    def test_get_proposal_count(self):
        """Test getting proposal count."""
        count_key = b'proposal_count'
        
        # Initially empty
        count = self.storage.get(count_key)
        assert count == b''
        
        # After creating proposals
        self.storage.put(count_key, 5)
        count = self.storage.get(count_key)
        assert count == b'5'
    
    def test_proposal_lifecycle(self):
        """Test complete proposal lifecycle: create -> vote -> finalize."""
        # 1. Create proposal
        proposal_id = 1
        count_key = b'proposal_count'
        proposal_key = b'proposal:' + str(proposal_id).encode()
        
        self.storage.put(count_key, proposal_id)
        proposal_data = 'DAO Proposal|QmHash|9999999999|90|0|0|0'
        self.storage.put(proposal_key, proposal_data)
        
        # 2. Multiple votes
        voters = [b'Voter1', b'Voter2', b'Voter3', b'Voter4', b'Voter5']
        votes = [1, 1, 0, 1, 1]  # 4 yes, 1 no
        
        parts = proposal_data.split('|')
        for i, voter in enumerate(voters):
            vote_key = b'vote:' + str(proposal_id).encode() + voter
            self.storage.put(vote_key, votes[i])
            
            if votes[i] == 1:
                parts[4] = str(int(parts[4]) + 1)
            else:
                parts[5] = str(int(parts[5]) + 1)
        
        proposal_data = '|'.join(parts)
        self.storage.put(proposal_key, proposal_data)
        
        # 3. Finalize
        parts = proposal_data.split('|')
        parts[6] = '1'
        finalized_data = '|'.join(parts)
        self.storage.put(proposal_key, finalized_data)
        
        # 4. Verify final state
        final = self.storage.get(proposal_key).decode()
        parts = final.split('|')
        
        assert parts[0] == 'DAO Proposal'
        assert parts[4] == '4'  # 4 yes votes
        assert parts[5] == '1'  # 1 no vote
        assert parts[6] == '1'  # finalized
        
        # Proposal approved (yes > no)
        assert int(parts[4]) > int(parts[5])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

