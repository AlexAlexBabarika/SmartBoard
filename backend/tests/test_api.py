"""
Tests for FastAPI backend endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from backend.app.main import app, get_db
from backend.app.models import Base
from backend.app.db import get_db as original_get_db

# Create test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@patch("backend.app.main.neo_client.create_proposal")
def test_submit_memo(mock_create_proposal):
    """Test submitting a new memo proposal."""
    # Mock NEO client response
    mock_create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }

    memo_data = {
        "title": "Test Investment Proposal",
        "summary": "A test proposal for unit testing",
        "cid": "QmTest123456789",
        "confidence": 85,
        "metadata": {"sector": "tech", "stage": "series-a"}
    }

    response = client.post("/submit-memo", json=memo_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == memo_data["title"]
    assert data["ipfs_cid"] == memo_data["cid"]
    assert data["confidence"] == memo_data["confidence"]
    assert data["status"] == "active"
    assert data["yes_votes"] == 0
    assert data["no_votes"] == 0

    # Verify NEO client was called
    mock_create_proposal.assert_called_once()


def test_get_proposals_empty():
    """Test getting proposals when none exist."""
    response = client.get("/proposals")
    assert response.status_code == 200
    assert response.json() == []


@patch("backend.app.main.neo_client.create_proposal")
def test_get_proposals(mock_create_proposal):
    """Test getting list of proposals."""
    mock_create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }

    # Create a proposal first
    memo_data = {
        "title": "Test Proposal",
        "summary": "Summary",
        "cid": "QmTest",
        "confidence": 75,
        "metadata": {}
    }
    client.post("/submit-memo", json=memo_data)

    # Get proposals
    response = client.get("/proposals")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == memo_data["title"]


@patch("backend.app.main.neo_client.create_proposal")
def test_get_proposal_by_id(mock_create_proposal):
    """Test getting a specific proposal by ID."""
    mock_create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }

    # Create a proposal
    memo_data = {
        "title": "Specific Proposal",
        "summary": "Detailed summary",
        "cid": "QmSpecific",
        "confidence": 90,
        "metadata": {}
    }
    create_response = client.post("/submit-memo", json=memo_data)
    proposal_id = create_response.json()["id"]

    # Get the specific proposal
    response = client.get(f"/proposals/{proposal_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == proposal_id
    assert data["title"] == memo_data["title"]


def test_get_proposal_not_found():
    """Test getting a non-existent proposal."""
    response = client.get("/proposals/999")
    assert response.status_code == 404


@patch("backend.app.main.neo_client.create_proposal")
@patch("backend.app.main.neo_client.vote")
def test_vote_on_proposal(mock_vote, mock_create_proposal):
    """Test voting on a proposal."""
    mock_create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_vote.return_value = {"tx_hash": "0xvote5678"}

    # Create a proposal
    memo_data = {
        "title": "Voting Test",
        "summary": "Test voting",
        "cid": "QmVote",
        "confidence": 80,
        "metadata": {}
    }
    create_response = client.post("/submit-memo", json=memo_data)
    proposal_id = create_response.json()["id"]

    # Vote yes
    vote_data = {
        "proposal_id": proposal_id,
        "voter_address": "NTestAddress123",
        "vote": 1
    }
    response = client.post("/vote", json=vote_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["yes_votes"] == 1
    assert data["no_votes"] == 0

    # Verify vote was called
    mock_vote.assert_called_once()


@patch("backend.app.main.neo_client.create_proposal")
def test_vote_duplicate_voter(mock_create_proposal):
    """Test that duplicate votes from same voter are rejected."""
    mock_create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }

    # Create proposal
    memo_data = {
        "title": "Duplicate Vote Test",
        "summary": "Test duplicate",
        "cid": "QmDupe",
        "confidence": 70,
        "metadata": {}
    }
    create_response = client.post("/submit-memo", json=memo_data)
    proposal_id = create_response.json()["id"]

    # First vote
    vote_data = {
        "proposal_id": proposal_id,
        "voter_address": "NVoter123",
        "vote": 1
    }
    with patch("app.main.neo_client.vote", return_value={"tx_hash": "0x123"}):
        response1 = client.post("/vote", json=vote_data)
        assert response1.status_code == 200

    # Duplicate vote
    with patch("app.main.neo_client.vote", return_value={"tx_hash": "0x456"}):
        response2 = client.post("/vote", json=vote_data)
        assert response2.status_code == 400


@patch("backend.app.main.neo_client.create_proposal")
@patch("backend.app.main.neo_client.finalize_proposal")
def test_finalize_proposal(mock_finalize, mock_create_proposal):
    """Test finalizing a proposal."""
    mock_create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_finalize.return_value = {"tx_hash": "0xfinalize789"}

    # Create proposal with votes
    memo_data = {
        "title": "Finalize Test",
        "summary": "Test finalization",
        "cid": "QmFinal",
        "confidence": 88,
        "metadata": {}
    }
    create_response = client.post("/submit-memo", json=memo_data)
    proposal_id = create_response.json()["id"]

    # Add some votes
    with patch("app.main.neo_client.vote", return_value={"tx_hash": "0xvote1"}):
        client.post("/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "NVoter1",
            "vote": 1
        })
        client.post("/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "NVoter2",
            "vote": 1
        })
        client.post("/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "NVoter3",
            "vote": 0
        })

    # Finalize
    finalize_data = {"proposal_id": proposal_id}
    response = client.post("/finalize", json=finalize_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["status"] == "approved"  # 2 yes vs 1 no
    assert data["yes_votes"] == 2
    assert data["no_votes"] == 1

    # Verify finalize was called
    mock_finalize.assert_called_once()


def test_finalize_nonexistent_proposal():
    """Test finalizing a non-existent proposal."""
    response = client.post("/finalize", json={"proposal_id": 999})
    assert response.status_code == 404
