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
import re
import shutil
import subprocess
import tempfile
import base64

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
            logger.warning(
                f"Unknown LLM provider: {provider}, using simulation")
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
    """
    Generate a simulated LLM response for demo purposes.
    Varies confidence_score based on startup data if available.
    """
    # Try to extract startup info from prompt to vary the response
    confidence = 78  # Default
    risk_score = 58  # Default
    
    try:
        # Try to find startup data in prompt
        import re
        startup_match = re.search(r'"name"\s*:\s*"([^"]+)"', prompt)
        if startup_match:
            startup_name = startup_match.group(1)
            # Vary confidence based on startup name hash (deterministic but varied)
            name_hash = hash(startup_name) % 100
            confidence = 60 + (name_hash % 30)  # Range: 60-89
            risk_score = 100 - confidence + 20  # Inverse relationship
            logger.debug(f"Simulated confidence for {startup_name}: {confidence}")
    except Exception:
        pass  # Use defaults if extraction fails
    
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

        "risk_score": risk_score,
        "confidence_score": confidence,

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
        
        # Validate and extract confidence_score with multiple fallback strategies
        confidence_score = None
        
        # Strategy 1: Direct field
        if "confidence_score" in memo_content:
            confidence_score = memo_content["confidence_score"]
        # Strategy 2: Alternative field names
        elif "confidence" in memo_content:
            confidence_score = memo_content["confidence"]
        elif "confidenceScore" in memo_content:
            confidence_score = memo_content["confidenceScore"]
        # Strategy 3: Calculate from risk_score (inverse relationship)
        elif "risk_score" in memo_content:
            risk = memo_content.get("risk_score", 50)
            # Scale: 0-100 risk -> 20-100 confidence (lower risk = higher confidence)
            confidence_score = max(0, min(100, 100 - risk + 20))
            logger.info(f"Calculated confidence_score from risk_score: {confidence_score}")
        # Strategy 4: Extract from recommendation text
        elif "recommendation" in memo_content:
            rec_text = str(memo_content.get("recommendation", "")).upper()
            if "INVEST" in rec_text and "STRONG" in rec_text:
                confidence_score = 85
            elif "INVEST" in rec_text:
                confidence_score = 75
            elif "WATCH" in rec_text:
                confidence_score = 60
            elif "PASS" in rec_text or "REJECT" in rec_text:
                confidence_score = 40
            else:
                confidence_score = 70
            logger.info(f"Derived confidence_score from recommendation text: {confidence_score}")
        
        # Validate and set confidence_score
        if confidence_score is None:
            logger.warning("Could not determine confidence_score, using default: 75")
            confidence_score = 75
        
        # Ensure it's a valid integer in range
        try:
            conf = int(float(confidence_score))  # Handle string numbers
            confidence_score = max(0, min(100, conf))  # Clamp to 0-100
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid confidence_score format: {confidence_score}, using 75. Error: {e}")
            confidence_score = 75
        
        memo_content["confidence_score"] = confidence_score
        logger.info(f"Final confidence_score: {confidence_score}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response text (first 500 chars): {response_text[:500]}")
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
    Convert HTML to PDF using reportlab (pure Python, no system dependencies).

    Args:
        html_content: HTML string

    Returns:
        PDF bytes
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        from html.parser import HTMLParser
        import io
        import re
        
        # Enhanced HTML parser to extract structure
        class HTMLToPDFParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.elements = []
                self.current_tag = None
                self.current_text = []
                self.in_header = False
                self.in_paragraph = False
                self.in_list = False
                self.list_items = []
                self.in_div = False
                self.div_class = None
                self.tag_stack = []
                
            def handle_starttag(self, tag, attrs):
                self.tag_stack.append(tag)
                attrs_dict = dict(attrs)
                
                if tag in ['h1', 'h2', 'h3', 'h4']:
                    self.in_header = True
                    self.current_tag = tag
                    self.current_text = []
                elif tag == 'p':
                    self.in_paragraph = True
                    self.current_text = []
                elif tag in ['ul', 'ol']:
                    self.in_list = True
                    self.list_items = []
                elif tag == 'li':
                    self.current_text = []
                elif tag == 'div':
                    self.in_div = True
                    self.div_class = attrs_dict.get('class', '')
                    self.current_text = []
            
            def handle_endtag(self, tag):
                if tag in self.tag_stack:
                    self.tag_stack.remove(tag)
                
                if tag in ['h1', 'h2', 'h3', 'h4']:
                    if self.current_text:
                        text = ' '.join(self.current_text).strip()
                        if text:
                            self.elements.append(('heading', tag, text))
                    self.in_header = False
                    self.current_tag = None
                    self.current_text = []
                elif tag == 'p':
                    if self.current_text:
                        text = ' '.join(self.current_text).strip()
                        if text:
                            self.elements.append(('paragraph', text))
                    self.in_paragraph = False
                    self.current_text = []
                elif tag in ['ul', 'ol']:
                    if self.list_items:
                        self.elements.append(('list', self.list_items))
                    self.in_list = False
                    self.list_items = []
                elif tag == 'li':
                    if self.current_text:
                        text = ' '.join(self.current_text).strip()
                        if text:
                            self.list_items.append(text)
                    self.current_text = []
                elif tag == 'div':
                    if self.current_text:
                        text = ' '.join(self.current_text).strip()
                        if text:
                            # Handle special div classes
                            if 'executive-summary' in self.div_class:
                                self.elements.append(('paragraph', text))
                            elif 'startup-info' in self.div_class or 'metadata' in self.div_class:
                                # Skip metadata divs as they're handled separately
                                pass
                            elif 'recommendation' in self.div_class:
                                self.elements.append(('paragraph', text))
                            elif 'risk-item' in self.div_class:
                                self.elements.append(('paragraph', text))
                            elif 'swot-box' in self.div_class:
                                # SWOT items are handled as lists
                                pass
                            else:
                                # Generic div content
                                self.elements.append(('paragraph', text))
                    self.in_div = False
                    self.div_class = None
                    self.current_text = []
            
            def handle_data(self, data):
                text = data.strip()
                if text and text not in ['•', '-', '*']:  # Skip standalone bullet chars
                    self.current_text.append(text)
        
        # Parse HTML
        parser = HTMLToPDFParser()
        parser.feed(html_content)
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        # Define custom styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            leading=14,
            alignment=TA_JUSTIFY
        )
        
        # Build PDF content
        story = []
        
        for element_type, *args in parser.elements:
            if element_type == 'heading':
                tag, text = args
                if tag == 'h1':
                    story.append(Paragraph(text, title_style))
                    story.append(Spacer(1, 0.3*inch))
                elif tag == 'h2':
                    story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph(text, heading1_style))
                elif tag == 'h3':
                    story.append(Paragraph(text, heading2_style))
            elif element_type == 'paragraph':
                text = args[0]
                # Clean up text
                text = re.sub(r'\s+', ' ', text)
                if text:
                    story.append(Paragraph(text, normal_style))
                    story.append(Spacer(1, 0.1*inch))
            elif element_type == 'list':
                items = args[0]
                for item in items:
                    # Use bullet points
                    story.append(Paragraph(f"• {item}", normal_style))
                    story.append(Spacer(1, 0.05*inch))
                story.append(Spacer(1, 0.1*inch))
        
        # If no structured content found, fall back to simple text extraction
        if not story:
            logger.warning("Could not parse HTML structure, using simple text extraction")
            # Simple fallback: extract all text
            class SimpleStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                
                def handle_data(self, data):
                    if data.strip():
                        self.text.append(data.strip())
                
                def get_text(self):
                    return '\n\n'.join(self.text)
            
            stripper = SimpleStripper()
            stripper.feed(html_content)
            text_content = stripper.get_text()
            
            for para in text_content.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), normal_style))
                    story.append(Spacer(1, 0.15*inch))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        logger.info(f"Generated PDF using reportlab: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except ImportError:
        logger.error("reportlab not installed. Install with: pip install reportlab")
        logger.warning("Falling back to HTML format")
        return html_content.encode('utf-8')
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        logger.warning("Falling back to HTML format")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return html_content.encode('utf-8')


def upload_to_ipfs(file_bytes: bytes, filename: str) -> str:
    """
    Upload file to IPFS using Storacha CLI (no API token required).

    Args:
        file_bytes: File content as bytes
        filename: Name for the file

    Returns:
        IPFS CID
    """
    if DEMO_MODE:
        logger.warning(
            "DEMO_MODE enabled, simulating Storacha upload")
        return _simulated_ipfs_upload(file_bytes, filename)

    storacha_cmd = os.getenv("STORACHA_CLI", "storacha")

    if not shutil.which(storacha_cmd):
        logger.warning(
            "Storacha CLI not found. Install with `npm i -g @storacha/cli` and run `storacha login`.")
        return _simulated_ipfs_upload(file_bytes, filename)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            tmp_path = tmp.name

        cmd = [storacha_cmd, "up", tmp_path]

        if os.getenv("STORACHA_NO_WRAP", "true").lower() == "true":
            cmd.append("--no-wrap")

        logger.info(f"Uploading to Storacha via CLI: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240
        )

        output = f"{result.stdout}\n{result.stderr}"

        if result.returncode != 0:
            logger.error(
                f"Storacha CLI upload failed ({result.returncode}): {output.strip()[:400]}")
            return _simulated_ipfs_upload(file_bytes, filename)

        cid_match = re.search(
            r"storacha\.link/ipfs/([a-zA-Z0-9]+)", output)
        if not cid_match:
            cid_match = re.search(r"(bafy[a-zA-Z0-9]+)", output)

        if cid_match:
            cid = cid_match.group(1)
            logger.info(f"Uploaded to Storacha/IPFS: {cid}")
            return cid

        logger.error(
            f"Could not parse CID from Storacha CLI output: {output.strip()[:400]}")
        return _simulated_ipfs_upload(file_bytes, filename)

    except FileNotFoundError:
        logger.warning(
            "Storacha CLI executable not found. Falling back to simulated CID.")
        return _simulated_ipfs_upload(file_bytes, filename)
    except subprocess.TimeoutExpired:
        logger.error("Storacha CLI upload timed out.")
        return _simulated_ipfs_upload(file_bytes, filename)
    except Exception as e:
        logger.error(f"Storacha upload failed: {e}")
        logger.warning("Falling back to simulated CID")
        return _simulated_ipfs_upload(file_bytes, filename)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                logger.debug(f"Could not remove temp file {tmp_path}")


def _simulated_ipfs_upload(file_bytes: bytes, filename: str) -> str:
    """Generate a simulated IPFS CID for demo purposes."""
    # Generate base32-encoded hash to avoid non-base32 characters
    content_hash = hashlib.sha256(file_bytes + filename.encode()).digest()
    base32_hash = base64.b32encode(content_hash).decode("utf-8").lower().rstrip("=")
    # Use a distinct prefix so UI can still detect demo CIDs
    cid = f"bafysim{base32_hash[:52]}"
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

    logger.info(f"Submitting to backend: {endpoint}")
    logger.debug(f"Submission data keys: {list(submission_data.keys())}")

    try:
        response = requests.post(
            endpoint,
            json=submission_data,
            timeout=30
        )
        
        logger.debug(f"Backend response status: {response.status_code}")
        
        if not response.ok:
            error_text = response.text[:500]
            logger.error(f"Backend returned error {response.status_code}: {error_text}")
            raise requests.exceptions.HTTPError(f"Backend error {response.status_code}: {error_text}")
        
        response.raise_for_status()

        result = response.json()
        proposal_id = result.get('id')
        logger.info(f"✅ Successfully submitted to backend: Proposal ID {proposal_id}")
        logger.debug(f"Full response: {result}")
        
        if not proposal_id or proposal_id == 1:
            logger.warning(f"⚠️  Received proposal_id={proposal_id}, might be simulated response")
        
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Could not connect to backend at {backend_url}: {e}")
        logger.warning(
            "Make sure the backend is running: uvicorn backend.app.main:app --reload")
        # Return simulated response for demo
        simulated = {
            "id": 1,
            "status": "simulated - backend not available",
            **submission_data
        }
        logger.warning(f"⚠️  Returning simulated response: {simulated}")
        return simulated
    except requests.exceptions.Timeout:
        logger.error(f"❌ Backend request timed out after 30 seconds")
        return {
            "id": 1,
            "status": "failed - timeout",
            "error": "Backend request timed out"
        }
    except Exception as e:
        logger.error(f"❌ Backend submission failed: {type(e).__name__}: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {
            "id": 1,
            "status": "failed",
            "error": str(e)
        }
