"""
Tests for SpoonOS agent utilities.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_utils import (
    llm_call,
    generate_deal_memo,
    render_memo_html,
    html_to_pdf,
    upload_to_ipfs,
    submit_to_backend
)


@patch('agent_utils.requests.post')
def test_llm_call_openai(mock_post):
    """Test LLM call with OpenAI provider."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    mock_post.return_value = mock_response
    
    with patch.dict('os.environ', {
        'LLM_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key',
        'LLM_MODEL': 'gpt-4'
    }):
        result = llm_call("Test prompt")
        assert result == "Test response"
        mock_post.assert_called_once()


def test_llm_call_simulation():
    """Test LLM call falls back to simulation when no API key."""
    with patch.dict('os.environ', {}, clear=True):
        result = llm_call("Test prompt")
        # Should return simulated JSON response
        assert isinstance(result, str)
        # Parse to verify it's valid JSON
        data = json.loads(result)
        assert "executive_summary" in data
        assert "swot" in data


def test_generate_deal_memo():
    """Test deal memo generation with mocked LLM."""
    startup_data = {
        "name": "TestCo",
        "sector": "Tech",
        "stage": "Seed",
        "description": "A test company"
    }
    
    with patch('agent_utils.llm_call') as mock_llm:
        mock_llm.return_value = json.dumps({
            "executive_summary": "Test summary",
            "investment_thesis": "Test thesis",
            "swot": {
                "strengths": ["Strong team"],
                "weaknesses": ["Early stage"],
                "opportunities": ["Large market"],
                "threats": ["Competition"]
            },
            "risks": [{"category": "Market", "description": "Test", "severity": "Low", "mitigation": "Test"}],
            "risk_score": 50,
            "confidence_score": 75,
            "recommendation": "Test recommendation",
            "key_metrics_to_track": ["Metric 1"]
        })
        
        result = generate_deal_memo(startup_data)
        
        assert isinstance(result, dict)
        assert "executive_summary" in result
        assert "swot" in result
        assert result["confidence_score"] == 75
        mock_llm.assert_called_once()


def test_render_memo_html():
    """Test HTML rendering from memo content."""
    memo_content = {
        "executive_summary": "Test summary",
        "investment_thesis": "Test thesis",
        "swot": {
            "strengths": ["S1", "S2"],
            "weaknesses": ["W1"],
            "opportunities": ["O1", "O2"],
            "threats": ["T1"]
        },
        "risks": [
            {
                "category": "Market",
                "description": "Test risk",
                "severity": "Medium",
                "mitigation": "Test mitigation"
            }
        ],
        "risk_score": 55,
        "confidence_score": 80,
        "recommendation": "INVEST",
        "key_metrics_to_track": ["Metric 1", "Metric 2"]
    }
    
    startup_data = {
        "name": "TestCo",
        "sector": "Tech",
        "stage": "Series A",
        "description": "Test description"
    }
    
    html = render_memo_html(memo_content, startup_data)
    
    assert isinstance(html, str)
    assert "TestCo" in html
    assert "Test summary" in html
    assert "SWOT Analysis" in html
    assert "Investment Memorandum" in html


def test_html_to_pdf_fallback():
    """Test PDF generation with fallback when WeasyPrint unavailable."""
    html = "<html><body><h1>Test</h1></body></html>"
    
    # WeasyPrint might not be installed in test environment
    result = html_to_pdf(html)
    
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_upload_to_ipfs_simulation():
    """Test IPFS upload in simulation mode."""
    test_data = b"Test file content"
    
    with patch.dict('os.environ', {'DEMO_MODE': 'true'}):
        cid = upload_to_ipfs(test_data, "test.pdf")
        
        assert isinstance(cid, str)
        assert cid.startswith("bafybei")
        assert len(cid) > 10


@patch('agent_utils.requests.post')
def test_upload_to_ipfs_real(mock_post):
    """Test IPFS upload with web3.storage API."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"cid": "bafytest123"}
    mock_post.return_value = mock_response
    
    test_data = b"Test file content"
    
    with patch.dict('os.environ', {
        'WEB3_STORAGE_KEY': 'test-token',
        'DEMO_MODE': 'false'
    }):
        cid = upload_to_ipfs(test_data, "test.pdf")
        
        assert cid == "bafytest123"
        mock_post.assert_called_once()


@patch('agent_utils.requests.post')
def test_submit_to_backend_success(mock_post):
    """Test successful backend submission."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": 1,
        "status": "active",
        "title": "Test Proposal"
    }
    mock_post.return_value = mock_response
    
    submission_data = {
        "title": "Test Proposal",
        "summary": "Test summary",
        "cid": "bafytest",
        "confidence": 75,
        "metadata": {}
    }
    
    result = submit_to_backend(submission_data)
    
    assert result["id"] == 1
    assert result["status"] == "active"
    mock_post.assert_called_once()


@patch('agent_utils.requests.post')
def test_submit_to_backend_connection_error(mock_post):
    """Test backend submission handles connection errors."""
    mock_post.side_effect = Exception("Connection refused")
    
    submission_data = {
        "title": "Test",
        "summary": "Test",
        "cid": "test",
        "confidence": 75,
        "metadata": {}
    }
    
    # Should not raise exception, should return simulated response
    result = submit_to_backend(submission_data)
    
    assert "id" in result
    # Should indicate failure or simulation
    assert "status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

