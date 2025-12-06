"""
Tests for FastAPI backend endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from backend.app.main import app, get_db, get_neo_client
from backend.app.models import Base
from backend.app.db import get_db as original_get_db
from backend.app import research_pipeline_adapter as research_adapter

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

# Create a mock NEO client for tests
mock_neo_client = MagicMock()


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


@patch("backend.app.main.get_neo_client")
def test_submit_memo(mock_get_neo_client):
    """Test submitting a new memo proposal."""
    # Mock NEO client response
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_get_neo_client.return_value = mock_client

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
    mock_client.create_proposal.assert_called_once()


def test_get_proposals_empty():
    """Test getting proposals when none exist."""
    response = client.get("/proposals")
    assert response.status_code == 200
    assert response.json() == []


@patch("backend.app.main.get_neo_client")
def test_get_proposals(mock_get_neo_client):
    """Test getting list of proposals."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_get_neo_client.return_value = mock_client

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


@patch("backend.app.main.get_neo_client")
def test_get_proposal_by_id(mock_get_neo_client):
    """Test getting a specific proposal by ID."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_get_neo_client.return_value = mock_client

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


@patch("backend.app.main.get_neo_client")
def test_vote_on_proposal(mock_get_neo_client):
    """Test voting on a proposal."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_client.vote.return_value = {"tx_hash": "0xvote5678"}
    mock_get_neo_client.return_value = mock_client

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
    mock_client.vote.assert_called_once()


@patch("backend.app.main.get_neo_client")
def test_vote_duplicate_voter(mock_get_neo_client):
    """Test that duplicate votes from same voter are rejected."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_client.vote.return_value = {"tx_hash": "0x123"}
    mock_get_neo_client.return_value = mock_client

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
    response1 = client.post("/vote", json=vote_data)
    assert response1.status_code == 200

    # Duplicate vote
    response2 = client.post("/vote", json=vote_data)
    assert response2.status_code == 400


@patch("backend.app.main.get_neo_client")
def test_finalize_proposal(mock_get_neo_client):
    """Test finalizing a proposal."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {
        "tx_hash": "0xabcd1234",
        "proposal_id": 1
    }
    mock_client.vote.return_value = {"tx_hash": "0xvote1"}
    mock_client.finalize_proposal.return_value = {"tx_hash": "0xfinalize789"}
    mock_get_neo_client.return_value = mock_client

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
    mock_client.finalize_proposal.assert_called_once()


def test_finalize_nonexistent_proposal():
    """Test finalizing a non-existent proposal."""
    response = client.post("/finalize", json={"proposal_id": 999})
    assert response.status_code == 404


@patch("backend.app.main.run_research_pipeline")
@patch("backend.app.main.get_neo_client")
def test_submit_memo_runs_research_pipeline(mock_get_neo_client, mock_run_research):
    """Pipeline should be invoked for memo submissions."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {"tx_hash": "0x123", "proposal_id": 42}
    mock_get_neo_client.return_value = mock_client
    mock_run_research.side_effect = lambda payload, source=None: payload

    memo_data = {
        "title": "Pipeline Invocation",
        "summary": "Ensure pipeline runs",
        "cid": "QmPipeline",
        "confidence": 70,
        "metadata": {"source": "test"}
    }

    response = client.post("/submit-memo", json=memo_data)
    assert response.status_code == 200
    mock_run_research.assert_called_once()


@patch("backend.app.main.run_research_pipeline")
@patch("backend.app.main.get_neo_client")
def test_submit_memo_carries_research_metadata(mock_get_neo_client, mock_run_research):
    """Pipeline metadata should be preserved in stored proposal."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {"tx_hash": "0x456", "proposal_id": 99}
    mock_get_neo_client.return_value = mock_client

    def _augment(payload, source=None):
        meta = payload.get("metadata", {}).copy()
        meta["_research"] = {"tag": "research_pipeline_v1", "note": "ok"}
        payload["metadata"] = meta
        return payload

    mock_run_research.side_effect = _augment

    memo_data = {
        "title": "Pipeline Metadata",
        "summary": "Ensure metadata persists",
        "cid": "QmMeta",
        "confidence": 80,
        "metadata": {"sector": "tech"}
    }

    response = client.post("/submit-memo", json=memo_data)
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["_research"]["tag"] == "research_pipeline_v1"


def test_run_research_pipeline_fail_open(monkeypatch):
    """Adapter should fail-open when pipeline raises."""
    payload = {
        "title": "Fail Open",
        "summary": "Keep original",
        "cid": "QmFail",
        "confidence": 60,
        "metadata": {}
    }

    original_process = research_adapter._pipeline_process

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    research_adapter._pipeline_process = _boom
    try:
        result = research_adapter.run_research_pipeline(payload, source="test")
        assert result == payload
    finally:
        research_adapter._pipeline_process = original_process


@patch("backend.app.main.schedule_manifest_refresh")
@patch("backend.app.main.run_research_pipeline")
@patch("backend.app.main.get_neo_client")
def test_submit_memo_refreshes_manifest(mock_get_neo_client, mock_run_research, mock_manifest):
    """Submitting a memo should trigger manifest refresh."""
    mock_client = MagicMock()
    mock_client.create_proposal.return_value = {"tx_hash": "0x789", "proposal_id": 7}
    mock_get_neo_client.return_value = mock_client
    mock_run_research.side_effect = lambda payload, source=None: payload

    memo_data = {
        "title": "Manifest Refresh",
        "summary": "Trigger manifest update",
        "cid": "QmManifest",
        "confidence": 77,
        "metadata": {}
    }

    response = client.post("/submit-memo", json=memo_data)
    assert response.status_code == 200
    mock_manifest.assert_called_once()


@patch("backend.app.main.sync_from_manifest")
@patch("backend.app.main.get_manifest_cid")
def test_get_proposals_syncs_from_manifest(mock_get_manifest_cid, mock_sync_manifest):
    """Fetching proposals should attempt to sync from Storacha manifest when available."""
    mock_get_manifest_cid.return_value = "bafytestcid"
    mock_sync_manifest.return_value = {"success": True, "synced": 0}

    response = client.get("/proposals")
    assert response.status_code == 200
    mock_sync_manifest.assert_called_once()
