"""
Storacha/IPFS proposal synchronization module.

This module provides functionality to:
1. Load proposals from Storacha/IPFS
2. Check if they already exist in the database (by IPFS CID)
3. Add only unique proposals that aren't already present

Supports multiple methods:
- Sync from a manifest.json file stored on Storacha
- Sync from a list of CIDs
- Sync by downloading and parsing PDFs from IPFS
"""

import os
import json
import re
import subprocess
import shutil
import logging
import requests
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import tempfile

from .db import SessionLocal
from .models import Proposal as DBProposal

logger = logging.getLogger(__name__)

# Storacha gateway URLs
STORACHA_GATEWAY = "https://storacha.link/ipfs"
IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs",
    "https://dweb.link/ipfs",
    "https://gateway.pinata.cloud/ipfs",
    "https://cloudflare-ipfs.com/ipfs",
]


def get_storacha_cli() -> Optional[str]:
    """Get Storacha CLI command path."""
    storacha_cmd = os.getenv("STORACHA_CLI", "storacha")
    if shutil.which(storacha_cmd):
        return storacha_cmd
    return None


def download_from_ipfs(cid: str, timeout: int = 30) -> Optional[bytes]:
    """
    Download file from IPFS using various gateways.
    
    Args:
        cid: IPFS CID
        timeout: Request timeout in seconds
        
    Returns:
        File content as bytes, or None if download fails
    """
    # Clean CID (remove gateway prefix if present)
    clean_cid = cid.replace("https://", "").replace("http://", "")
    clean_cid = re.sub(r"^[^/]+/ipfs/", "", clean_cid)
    clean_cid = clean_cid.replace("ipfs://", "")
    
    # Try Storacha gateway first
    gateways = [STORACHA_GATEWAY] + IPFS_GATEWAYS
    
    for gateway in gateways:
        try:
            url = f"{gateway}/{clean_cid}"
            logger.debug(f"Trying to download from {url}")
            response = requests.get(url, timeout=timeout, stream=True)
            
            if response.status_code == 200:
                content = response.content
                logger.info(f"Successfully downloaded CID {clean_cid} from {gateway}")
                return content
        except Exception as e:
            logger.debug(f"Failed to download from {gateway}: {e}")
            continue
    
    logger.warning(f"Failed to download CID {clean_cid} from all gateways")
    return None


def load_manifest_from_storacha(manifest_cid: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load a manifest.json file from Storacha/IPFS.
    
    Manifest format:
    [
        {
            "cid": "bafy...",
            "title": "Investment Memo: Startup Name",
            "summary": "Executive summary...",
            "confidence": 85,
            "metadata": {...},
            "created_at": "2024-01-01T00:00:00Z"
        },
        ...
    ]
    
    Args:
        manifest_cid: IPFS CID of the manifest.json file
        
    Returns:
        List of proposal dictionaries, or None if failed
    """
    try:
        manifest_data = download_from_ipfs(manifest_cid)
        if not manifest_data:
            logger.error(f"Failed to download manifest from CID: {manifest_cid}")
            return None
        
        manifest = json.loads(manifest_data.decode('utf-8'))
        if not isinstance(manifest, list):
            logger.error("Manifest is not a list")
            return None
        
        logger.info(f"Loaded manifest with {len(manifest)} proposals")
        return manifest
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading manifest: {e}")
        return None


def extract_metadata_from_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extract basic metadata from PDF file.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        "title": None,
        "summary": None,
        "confidence": 75,  # Default
    }
    
    try:
        # Try to extract text from PDF using PyPDF2 or similar
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract title from metadata
            if pdf_reader.metadata and pdf_reader.metadata.title:
                metadata["title"] = pdf_reader.metadata.title
            
            # Extract first page text as summary
            if len(pdf_reader.pages) > 0:
                first_page_text = pdf_reader.pages[0].extract_text()
                # Use first 500 chars as summary
                metadata["summary"] = first_page_text[:500].strip()
                
                # Try to extract title from first line if not in metadata
                if not metadata["title"]:
                    lines = first_page_text.split('\n')
                    for line in lines[:5]:
                        if line.strip() and len(line.strip()) > 10:
                            metadata["title"] = line.strip()
                            break
        except ImportError:
            logger.warning("PyPDF2 not available, using basic extraction")
        except Exception as e:
            logger.debug(f"PDF extraction error: {e}")
        
        # Fallback: try to find title in filename or basic text search
        if not metadata["title"]:
            # Try to extract from PDF text using regex
            try:
                pdf_text = pdf_bytes.decode('utf-8', errors='ignore')
                # Look for common title patterns
                title_match = re.search(r'Investment Memo[:\s]+([^\n]+)', pdf_text, re.IGNORECASE)
                if title_match:
                    metadata["title"] = title_match.group(1).strip()
            except:
                pass
        
    except Exception as e:
        logger.warning(f"Error extracting PDF metadata: {e}")
    
    return metadata


def check_cid_exists(cid: str, db) -> bool:
    """
    Check if a proposal with the given CID already exists in the database.
    
    Args:
        cid: IPFS CID to check
        db: Database session
        
    Returns:
        True if CID exists, False otherwise
    """
    # Clean CID for comparison
    clean_cid = cid.replace("https://", "").replace("http://", "")
    clean_cid = re.sub(r"^[^/]+/ipfs/", "", clean_cid)
    clean_cid = clean_cid.replace("ipfs://", "")
    
    existing = db.query(DBProposal).filter(
        DBProposal.ipfs_cid == clean_cid
    ).first()
    
    return existing is not None


def _create_proposal_in_db(
    title: str,
    summary: str,
    cid: str,
    confidence: int,
    metadata: dict,
    db
) -> Dict[str, Any]:
    """
    Create a proposal in the database (internal helper).
    
    Args:
        title: Proposal title
        summary: Executive summary
        cid: IPFS CID
        confidence: Confidence score (0-100)
        metadata: Proposal metadata
        db: Database session
        
    Returns:
        Created proposal dictionary
    """
    import time
    from .neo_client import NeoClient
    
    # Calculate deadline (7 days from now)
    deadline = int(time.time()) + (7 * 24 * 60 * 60)
    
    # Submit to NEO blockchain (if configured)
    try:
        neo_client = NeoClient()
        tx_result = neo_client.create_proposal(
            title=title,
            ipfs_hash=cid,
            deadline=deadline,
            confidence=confidence
        )
        tx_hash = tx_result.get("tx_hash")
        on_chain_id = tx_result.get("proposal_id")
    except Exception as e:
        logger.warning(f"Failed to submit to blockchain (continuing anyway): {e}")
        tx_hash = None
        on_chain_id = None
    
    # Store in local database
    db_proposal = DBProposal(
        title=title,
        summary=summary,
        ipfs_cid=cid,
        confidence=confidence,
        status="active",
        yes_votes=0,
        no_votes=0,
        proposal_metadata=metadata,
        tx_hash=tx_hash,
        on_chain_id=on_chain_id,
        deadline=deadline
    )
    
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    
    return {
        "id": db_proposal.id,
        "title": db_proposal.title,
        "summary": db_proposal.summary,
        "ipfs_cid": db_proposal.ipfs_cid,
        "confidence": db_proposal.confidence,
        "status": db_proposal.status,
        "yes_votes": db_proposal.yes_votes,
        "no_votes": db_proposal.no_votes,
        "created_at": db_proposal.created_at.isoformat(),
        "deadline": db_proposal.deadline,
        "metadata": db_proposal.proposal_metadata
    }


def sync_proposal_from_manifest(
    proposal_data: Dict[str, Any],
    db,
    skip_existing: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Sync a single proposal from manifest data.
    
    Args:
        proposal_data: Proposal data from manifest
        db: Database session
        skip_existing: If True, skip proposals that already exist
        
    Returns:
        Created proposal dict, or None if skipped/failed
    """
    cid = proposal_data.get("cid")
    if not cid:
        logger.warning("Proposal data missing CID")
        return None
    
    # Check if already exists
    if skip_existing and check_cid_exists(cid, db):
        logger.info(f"Proposal with CID {cid} already exists, skipping")
        return None
    
    # Extract proposal fields
    title = proposal_data.get("title", f"Investment Memo: {cid[:12]}")
    summary = proposal_data.get("summary", "")
    confidence = proposal_data.get("confidence", 75)
    metadata = proposal_data.get("metadata", {})
    
    # Add source info to metadata
    metadata["synced_from"] = "storacha_manifest"
    metadata["synced_at"] = datetime.utcnow().isoformat()
    
    try:
        # Create proposal in database
        result = _create_proposal_in_db(
            title=title,
            summary=summary,
            cid=cid,
            confidence=confidence,
            metadata=metadata,
            db=db
        )
        
        logger.info(f"✅ Synced proposal: {title} (CID: {cid})")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to sync proposal {cid}: {e}")
        db.rollback()
        return None


def sync_proposal_from_cid(
    cid: str,
    db,
    skip_existing: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Sync a single proposal by downloading PDF from CID and extracting metadata.
    
    Args:
        cid: IPFS CID
        db: Database session
        skip_existing: If True, skip proposals that already exist
        
    Returns:
        Created proposal dict, or None if skipped/failed
    """
    # Check if already exists
    if skip_existing and check_cid_exists(cid, db):
        logger.info(f"Proposal with CID {cid} already exists, skipping")
        return None
    
    # Download PDF
    logger.info(f"Downloading proposal from CID: {cid}")
    pdf_bytes = download_from_ipfs(cid)
    if not pdf_bytes:
        logger.error(f"Failed to download PDF from CID: {cid}")
        return None
    
    # Extract metadata from PDF
    metadata = extract_metadata_from_pdf(pdf_bytes)
    
    # Use extracted or default values
    title = metadata.get("title") or f"Investment Memo: {cid[:12]}"
    summary = metadata.get("summary") or "Investment memo synced from IPFS"
    confidence = metadata.get("confidence", 75)
    
    # Add source info
    proposal_metadata = {
        "synced_from": "storacha_cid",
        "synced_at": datetime.utcnow().isoformat(),
        "source_cid": cid
    }
    
    try:
        # Create proposal in database
        result = _create_proposal_in_db(
            title=title,
            summary=summary,
            cid=cid,
            confidence=confidence,
            metadata=proposal_metadata,
            db=db
        )
        
        logger.info(f"✅ Synced proposal: {title} (CID: {cid})")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to sync proposal {cid}: {e}")
        db.rollback()
        return None


def sync_from_manifest(
    manifest_cid: str,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Sync proposals from a manifest.json file on Storacha/IPFS.
    
    Args:
        manifest_cid: IPFS CID of the manifest.json file
        skip_existing: If True, skip proposals that already exist in database
        
    Returns:
        Dictionary with sync results
    """
    logger.info(f"Starting sync from manifest: {manifest_cid}")
    
    # Load manifest
    proposals = load_manifest_from_storacha(manifest_cid)
    if not proposals:
        return {
            "success": False,
            "error": "Failed to load manifest",
            "synced": 0,
            "skipped": 0,
            "failed": 0
        }
    
    db = SessionLocal()
    synced = 0
    skipped = 0
    failed = 0
    
    try:
        for proposal_data in proposals:
            try:
                result = sync_proposal_from_manifest(proposal_data, db, skip_existing)
                if result:
                    synced += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Error syncing proposal: {e}")
                failed += 1
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error during sync: {e}")
        return {
            "success": False,
            "error": str(e),
            "synced": synced,
            "skipped": skipped,
            "failed": failed
        }
    finally:
        db.close()
    
    logger.info(f"Sync complete: {synced} synced, {skipped} skipped, {failed} failed")
    return {
        "success": True,
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
        "total": len(proposals)
    }


def sync_from_cids(
    cids: List[str],
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Sync proposals from a list of IPFS CIDs.
    
    Args:
        cids: List of IPFS CIDs
        skip_existing: If True, skip proposals that already exist in database
        
    Returns:
        Dictionary with sync results
    """
    logger.info(f"Starting sync from {len(cids)} CIDs")
    
    db = SessionLocal()
    synced = 0
    skipped = 0
    failed = 0
    
    try:
        for cid in cids:
            try:
                result = sync_proposal_from_cid(cid, db, skip_existing)
                if result:
                    synced += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Error syncing CID {cid}: {e}")
                failed += 1
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error during sync: {e}")
        return {
            "success": False,
            "error": str(e),
            "synced": synced,
            "skipped": skipped,
            "failed": failed
        }
    finally:
        db.close()
    
    logger.info(f"Sync complete: {synced} synced, {skipped} skipped, {failed} failed")
    return {
        "success": True,
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
        "total": len(cids)
    }


def get_existing_cids() -> List[str]:
    """
    Get list of all IPFS CIDs currently in the database.
    
    Returns:
        List of CIDs
    """
    db = SessionLocal()
    try:
        proposals = db.query(DBProposal).all()
        return [p.ipfs_cid for p in proposals]
    finally:
        db.close()

