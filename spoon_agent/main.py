#!/usr/bin/env python3
"""
SpoonOS Agent for AI Investment Scout DAO
Generates investment memos using LLM, creates PDF, uploads to IPFS, and submits to backend.

This agent can run standalone or via spoon-cli.
"""

import os
import sys
import json
import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root or current directory
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to current directory

from agent_utils import (
    generate_deal_memo,
    render_memo_html,
    html_to_pdf,
    upload_to_ipfs,
    submit_to_backend
)


# Configure logging to stderr so stdout is clean for JSON output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr, keep stdout clean for JSON
)
logger = logging.getLogger(__name__)


def _derive_category(sector: str) -> str:
    """Map arbitrary sector strings to UI categories."""
    if not sector:
        return None
    s = sector.lower()
    if "ai" in s or "ml" in s:
        return "AI & ML"
    if "health" in s or "bio" in s or "med" in s:
        return "Healthcare"
    if "clean" in s or "climate" in s or "energy" in s or "green" in s:
        return "CleanTech"
    if "web3" in s or "blockchain" in s or "crypto" in s or "defi" in s:
        return "Web3"
    if "fintech" in s or "finance" in s or "payment" in s or "bank" in s:
        return "FinTech"
    return None


def process_startup_data(startup_data: dict, submit_callback=None) -> dict:
    """
    Process startup data and generate investment memo.

    Args:
        startup_data: Dict containing startup information
        submit_callback: Optional callback function for direct database submission.
                        If provided, bypasses HTTP and calls this function directly.
                        Should accept: title, summary, cid, confidence, metadata

    Returns:
        Dict with generated memo, CID, and metadata
    """
    logger.info(f"Processing startup: {startup_data.get('name', 'Unknown')}")

    # Step 1: Generate deal memo using LLM
    logger.info("Generating deal memo with LLM...")
    memo_content = generate_deal_memo(startup_data)

    # Step 2: Render HTML from template
    logger.info("Rendering HTML memo...")
    html_content = render_memo_html(memo_content, startup_data)

    # Step 3: Convert HTML to PDF
    logger.info("Converting to PDF...")
    pdf_bytes = html_to_pdf(html_content)

    # Step 4: Upload to IPFS
    logger.info("Uploading to IPFS...")
    ipfs_cid = upload_to_ipfs(
        pdf_bytes, f"{startup_data.get('name', 'memo')}.pdf")

    # Step 5: Prepare submission data (add category/tags for frontend filters)
    sector = startup_data.get("sector", "unknown")
    stage = startup_data.get("stage", "unknown")
    category = _derive_category(sector) or sector
    tags = {t for t in [category, sector, stage] if t}

    # Get current Storacha space for tagging
    storacha_space = None
    try:
        storacha_cmd = os.getenv("STORACHA_CLI", "storacha")
        if shutil.which(storacha_cmd):
            result = subprocess.run(
                [storacha_cmd, "space", "current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                space_name = result.stdout.strip()
                if space_name and space_name != "none":
                    storacha_space = space_name
    except Exception:
        pass  # Fail silently, space tagging is optional

    submission = {
        "title": f"Investment Memo: {startup_data.get('name')}",
        "summary": memo_content.get("executive_summary", "")[:500],
        "cid": ipfs_cid,
        "confidence": memo_content.get("confidence_score", 75),
        "metadata": {
            "startup_name": startup_data.get("name"),
            "sector": sector,
            "stage": stage,
            "category": category,
            "tags": sorted(tags),
            "risk_score": memo_content.get("risk_score", 50),
            "swot_summary": {
                "strengths": len(memo_content.get("swot", {}).get("strengths", [])),
                "weaknesses": len(memo_content.get("swot", {}).get("weaknesses", [])),
                "opportunities": len(memo_content.get("swot", {}).get("opportunities", [])),
                "threats": len(memo_content.get("swot", {}).get("threats", []))
            }
        }
    }
    
    # Add source field to metadata (for frontend filtering)
    source = startup_data.get("source")
    if source:
        submission["metadata"]["source"] = source
    
    # Add Storacha space to metadata if available
    if storacha_space:
        submission["metadata"]["storacha_space"] = storacha_space

    # Step 6: Submit to backend
    logger.info("Submitting to DAO backend...")

    # Use direct callback if provided (for direct call mode), otherwise use HTTP
    if submit_callback:
        logger.info("Using direct database submission (bypassing HTTP)...")
        try:
            response = submit_callback(
                title=submission["title"],
                summary=submission["summary"],
                cid=submission["cid"],
                confidence=submission["confidence"],
                metadata=submission["metadata"]
            )
            logger.info(
                f"✅ Direct submission successful! Proposal ID: {response.get('id')}")
        except Exception as e:
            logger.error(f"❌ Direct submission failed: {e}")
            logger.warning("Falling back to HTTP submission...")
            response = submit_to_backend(submission)
    else:
        response = submit_to_backend(submission)

    logger.info(
        f"✅ Memo submitted successfully! Proposal ID: {response.get('id')}")
    logger.info(f"   IPFS CID: {ipfs_cid}")
    logger.info(f"   View at: https://storacha.link/ipfs/{ipfs_cid}")

    return {
        "proposal_id": response.get("id"),
        "ipfs_cid": ipfs_cid,
        "memo_content": memo_content,
        "submission": submission
    }


def demo_mode():
    """Run agent in demo mode with sample data."""
    logger.info("Running in DEMO mode with sample startup data")

    sample_startup = {
        "name": "NexGenAI",
        "sector": "Artificial Intelligence",
        "stage": "Series A",
        "description": "NexGenAI is building next-generation AI models for enterprise automation. The company has developed proprietary algorithms that reduce training time by 70% while maintaining accuracy.",
        "team": [
            {"name": "Jane Doe", "role": "CEO",
                "background": "Ex-Google AI Research"},
            {"name": "John Smith", "role": "CTO",
                "background": "PhD MIT, former OpenAI"}
        ],
        "metrics": {
            "mrr": 50000,
            "growth_rate": 15,
            "customers": 12,
            "runway_months": 18
        },
        "ask": {
            "amount": 5000000,
            "valuation": 20000000,
            "use_of_funds": "Product development (60%), Sales & Marketing (30%), Operations (10%)"
        },
        "market": {
            "size": "Enterprise AI automation market estimated at $15B by 2027",
            "competition": "Competing with UiPath, Automation Anywhere, but differentiated by AI-first approach"
        }
    }

    result = process_startup_data(sample_startup)

    # Save result to file
    output_file = Path("demo_output.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Demo results saved to {output_file}")
    return result


def main():
    """Main entry point for the agent."""
    parser = argparse.ArgumentParser(
        description="AI Investment Scout DAO - SpoonOS Agent"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to JSON file containing startup data"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with sample data"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path to save output JSON"
    )

    args = parser.parse_args()

    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    demo_mode_enabled = os.getenv("DEMO_MODE", "true").lower() == "true"

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars and not args.demo:
        logger.warning(
            f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning(
            "Running with simulated operations. Set DEMO_MODE=false for real operations.")

    if not demo_mode_enabled and not shutil.which(os.getenv("STORACHA_CLI", "storacha")):
        logger.warning(
            "Storacha CLI not found. Install @storacha/cli to enable real uploads.")

    try:
        if args.demo or (not args.input):
            # Run demo mode
            result = demo_mode()
            # Print result as JSON to stdout for subprocess communication
            # Flush stderr first to ensure logs are written, then print clean JSON to stdout
            sys.stderr.flush()
            print(json.dumps(result, indent=2), flush=True)
        else:
            # Load startup data from file
            input_path = Path(args.input)
            if not input_path.exists():
                logger.error(f"Input file not found: {args.input}")
                sys.exit(1)

            with open(input_path, "r") as f:
                startup_data = json.load(f)

            result = process_startup_data(startup_data)

            # Save output if specified
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Results saved to {args.output}")

            # IMPORTANT: Print result as JSON to stdout for subprocess communication
            # This allows the backend to parse the output when running as subprocess
            # Flush stderr first to ensure logs are written, then print clean JSON to stdout
            sys.stderr.flush()
            print(json.dumps(result, indent=2), flush=True)

        logger.info("Agent execution completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
