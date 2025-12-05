"""
Utility functions for SpoonOS agent.
Handles LLM calls, PDF generation, IPFS upload, and backend submission.
"""

import os
import json
import logging
import requests
from pathlib import Path
from jinja2 import Template
from typing import Dict, Any
import hashlib
import time

logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


def llm_call(prompt: str, system_prompt: str = None) -> str:
    """
    Call LLM provider (OpenAI, Anthropic, etc.) with the given prompt.
    Abstracted for easy swapping/mocking.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        
    Returns:
        LLM response text
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("LLM_MODEL", "gpt-4")
    
    if not api_key:
        logger.warning("No LLM API key found, using simulated response")
        return _simulated_llm_response(prompt)
    
    try:
        if provider == "openai":
            return _call_openai(prompt, system_prompt, api_key, model)
        elif provider == "anthropic":
            return _call_anthropic(prompt, system_prompt, api_key, model)
        else:
            logger.warning(f"Unknown LLM provider: {provider}, using simulation")
            return _simulated_llm_response(prompt)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        logger.warning("Falling back to simulated response")
        return _simulated_llm_response(prompt)


def _call_openai(prompt: str, system_prompt: str, api_key: str, model: str) -> str:
    """Call OpenAI API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]


def _call_anthropic(prompt: str, system_prompt: str, api_key: str, model: str) -> str:
    """Call Anthropic API."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model if "claude" in model else "claude-3-sonnet-20240229",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    if system_prompt:
        data["system"] = system_prompt
    
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    
    return response.json()["content"][0]["text"]


def _simulated_llm_response(prompt: str) -> str:
    """Generate a simulated LLM response for demo purposes."""
    return json.dumps({
        "executive_summary": "NexGenAI presents a compelling investment opportunity in the rapidly growing enterprise AI automation market. The company's proprietary algorithms offer significant performance advantages, reducing training time by 70% while maintaining accuracy. With a strong founding team from Google AI Research and MIT, along with early traction showing 15% monthly growth, the company is well-positioned to capture market share. However, the competitive landscape is intense, and execution risks remain.",
        
        "investment_thesis": "The enterprise AI automation market is projected to reach $15B by 2027, representing a significant opportunity. NexGenAI's differentiated technology and AI-first approach provide a competitive moat against traditional RPA players. The founding team's deep expertise in AI research and their early customer validation demonstrate strong product-market fit potential. The company's capital efficient growth (15% MRR growth with 18 months runway) indicates prudent management and scalability.",
        
        "swot": {
            "strengths": [
                "Proprietary AI algorithms with 70% efficiency improvement",
                "World-class founding team (ex-Google AI, MIT PhD, ex-OpenAI)",
                "Strong early traction: $50K MRR with 15% monthly growth",
                "AI-first approach vs. traditional RPA incumbents",
                "18-month runway provides adequate time for execution"
            ],
            "weaknesses": [
                "Small customer base (12 customers) indicates early stage",
                "Limited brand recognition in established market",
                "Dependency on AI infrastructure costs",
                "Need to scale sales and marketing capabilities"
            ],
            "opportunities": [
                "Rapidly expanding enterprise AI market ($15B by 2027)",
                "Increasing enterprise adoption of AI automation",
                "Potential for horizontal expansion to adjacent markets",
                "Strategic partnerships with cloud providers",
                "International expansion opportunities"
            ],
            "threats": [
                "Intense competition from well-funded incumbents (UiPath, Automation Anywhere)",
                "Potential market saturation in enterprise automation",
                "Rapid technological change could obsolete current approach",
                "Economic downturn could reduce enterprise AI spending",
                "Regulatory risks around AI usage"
            ]
        },
        
        "risks": [
            {
                "category": "Market Risk",
                "description": "Competition from established players with deeper pockets",
                "severity": "High",
                "mitigation": "Focus on differentiation through AI-first approach and faster iteration"
            },
            {
                "category": "Execution Risk",
                "description": "Ability to scale from 12 to 100+ customers",
                "severity": "Medium",
                "mitigation": "30% of funding allocated to sales & marketing expansion"
            },
            {
                "category": "Technology Risk",
                "description": "Maintaining performance advantage as competitors catch up",
                "severity": "Medium",
                "mitigation": "60% of funding allocated to continued R&D"
            },
            {
                "category": "Team Risk",
                "description": "Need to hire and retain top AI talent",
                "severity": "Medium",
                "mitigation": "Strong employer brand from founder backgrounds"
            }
        ],
        
        "risk_score": 58,
        "confidence_score": 78,
        
        "recommendation": "INVEST with cautious optimism. NexGenAI demonstrates strong technical foundations and promising early traction. The $5M ask at $20M valuation is reasonable given current metrics and market opportunity. However, close monitoring of customer acquisition costs, retention metrics, and competitive positioning is essential. Recommend staged investment with milestones tied to customer growth targets.",
        
        "key_metrics_to_track": [
            "MRR growth rate (target: maintain >10% monthly)",
            "Customer acquisition cost and payback period",
            "Net revenue retention (target: >100%)",
            "Product development velocity",
            "Competitive win/loss analysis"
        ]
    })


def generate_deal_memo(startup_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive investment deal memo using LLM.
    
    Args:
        startup_data: Dict containing startup information
        
    Returns:
        Dict with memo content including SWOT, thesis, risks, scores
    """
    # Load prompt template
    template_path = Path(__file__).parent / "prompt_template.txt"
    with open(template_path, "r") as f:
        prompt_template = f.read()
    
    # Format prompt with startup data
    prompt = prompt_template.format(
        startup_json=json.dumps(startup_data, indent=2)
    )
    
    system_prompt = """You are an expert venture capital analyst specializing in early-stage technology investments. 
Your task is to analyze startups and produce comprehensive investment memos with SWOT analysis, 
investment thesis, risk assessment, and confidence scores. Be thorough, analytical, and balanced 
in your assessments. Output your analysis in JSON format."""
    
    # Call LLM
    response_text = llm_call(prompt, system_prompt)
    
    # Parse JSON response
    try:
        # Try to extract JSON from response (handles cases where LLM adds text before/after)
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            memo_content = json.loads(json_match.group())
        else:
            memo_content = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.warning("Using simulated response instead")
        memo_content = json.loads(_simulated_llm_response(prompt))
    
    return memo_content


def render_memo_html(memo_content: Dict[str, Any], startup_data: Dict[str, Any]) -> str:
    """
    Render investment memo as HTML using Jinja2 template.
    
    Args:
        memo_content: Generated memo content from LLM
        startup_data: Original startup data
        
    Returns:
        HTML string
    """
    template_path = Path(__file__).parent / "memo_template.html"
    with open(template_path, "r") as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    html = template.render(
        startup=startup_data,
        memo=memo_content,
        generated_date=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    )
    
    return html


def html_to_pdf(html_content: str) -> bytes:
    """
    Convert HTML to PDF using WeasyPrint.
    
    Args:
        html_content: HTML string
        
    Returns:
        PDF bytes
    """
    try:
        from weasyprint import HTML, CSS
        
        # Custom CSS for better PDF rendering
        css = CSS(string="""
            @page {
                size: letter;
                margin: 1in;
            }
            body {
                font-family: 'Georgia', serif;
                line-height: 1.6;
                color: #333;
            }
            h1, h2, h3 {
                color: #1a202c;
            }
        """)
        
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css])
        logger.info(f"Generated PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except ImportError:
        logger.error("WeasyPrint not available, using fallback")
        # Fallback: return HTML as bytes (for demo)
        return html_content.encode('utf-8')
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return html_content.encode('utf-8')


def upload_to_ipfs(file_bytes: bytes, filename: str) -> str:
    """
    Upload file to IPFS using web3.storage API.
    
    Args:
        file_bytes: File content as bytes
        filename: Name for the file
        
    Returns:
        IPFS CID
    """
    api_token = os.getenv("WEB3_STORAGE_KEY")
    
    if not api_token or DEMO_MODE:
        logger.warning("No web3.storage key or DEMO_MODE enabled, simulating IPFS upload")
        return _simulated_ipfs_upload(file_bytes, filename)
    
    try:
        url = "https://api.web3.storage/upload"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "X-NAME": filename
        }
        
        response = requests.post(
            url,
            headers=headers,
            data=file_bytes,
            timeout=120
        )
        response.raise_for_status()
        
        cid = response.json()["cid"]
        logger.info(f"Uploaded to IPFS: {cid}")
        return cid
        
    except Exception as e:
        logger.error(f"IPFS upload failed: {e}")
        logger.warning("Falling back to simulated CID")
        return _simulated_ipfs_upload(file_bytes, filename)


def _simulated_ipfs_upload(file_bytes: bytes, filename: str) -> str:
    """Generate a simulated IPFS CID for demo purposes."""
    # Generate a realistic-looking CID based on content hash
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    # CIDv1 format: bafybei... (base32)
    cid = f"bafybei{content_hash[:52]}"
    logger.info(f"[SIMULATED] Generated IPFS CID: {cid}")
    return cid


def submit_to_backend(submission_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit memo to backend API.
    
    Args:
        submission_data: Dict with title, summary, cid, confidence, metadata
        
    Returns:
        Backend response
    """
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    endpoint = f"{backend_url}/submit-memo"
    
    try:
        response = requests.post(
            endpoint,
            json=submission_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Submitted to backend: Proposal ID {result.get('id')}")
        return result
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to backend at {backend_url}")
        logger.warning("Make sure the backend is running: uvicorn app.main:app --reload")
        # Return simulated response for demo
        return {
            "id": 1,
            "status": "simulated - backend not available",
            **submission_data
        }
    except Exception as e:
        logger.error(f"Backend submission failed: {e}")
        return {
            "id": 1,
            "status": "failed",
            "error": str(e)
        }

