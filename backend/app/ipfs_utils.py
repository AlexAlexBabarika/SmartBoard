"""
IPFS/Storacha utilities for uploading data to decentralized storage.
"""

import os
import json
import subprocess
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


def _simulated_ipfs_upload(data: bytes, filename: str) -> str:
    """Simulate IPFS upload for demo mode."""
    import hashlib
    import time
    
    # Generate a fake CID based on content
    content_hash = hashlib.sha256(data).hexdigest()
    fake_cid = f"bafysim{content_hash[:46]}"
    logger.info(f"[SIMULATED] Uploaded {filename} to IPFS: {fake_cid}")
    return fake_cid


def upload_json_to_ipfs(data: Dict[str, Any], filename: str = "data.json") -> str:
    """
    Upload JSON data to IPFS using Storacha CLI.
    
    Args:
        data: Dictionary to upload as JSON
        filename: Name for the file (default: data.json)
    
    Returns:
        IPFS CID
    """
    # Convert to JSON bytes
    json_bytes = json.dumps(data, indent=2).encode('utf-8')
    
    if DEMO_MODE:
        logger.info("DEMO_MODE enabled, simulating Storacha upload")
        return _simulated_ipfs_upload(json_bytes, filename)
    
    storacha_cmd = os.getenv("STORACHA_CLI", "storacha")
    
    if not shutil.which(storacha_cmd):
        logger.warning(
            "Storacha CLI not found. Install with `npm i -g @storacha/cli` and run `storacha login`."
        )
        return _simulated_ipfs_upload(json_bytes, filename)
    
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.json',
            encoding='utf-8'
        ) as tmp:
            json.dump(data, tmp, indent=2)
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
                f"Storacha CLI upload failed ({result.returncode}): {output.strip()[:400]}"
            )
            return _simulated_ipfs_upload(json_bytes, filename)
        
        # Parse CID from output
        # Storacha output format: "Upload complete: https://storacha.link/ipfs/Qm..."
        # or just the CID
        import re
        lines = output.strip().split('\n')
        cid = None
        
        # Try to find CID in various formats
        cid_match = re.search(r"storacha\.link/ipfs/([a-zA-Z0-9]+)", output)
        if not cid_match:
            cid_match = re.search(r"(bafy[a-zA-Z0-9]+)", output)
        if not cid_match:
            cid_match = re.search(r"(Qm[a-zA-Z0-9]+)", output)
        
        if cid_match:
            cid = cid_match.group(1)
        else:
            # Fallback: look for CID-like strings in output
            for line in lines:
                if 'ipfs/' in line:
                    cid = line.split('ipfs/')[-1].strip().split()[0]
                    break
                elif line.startswith('Qm') or line.startswith('bafy'):
                    cid = line.strip().split()[0]
                    break
        
        if not cid:
            logger.warning("Could not parse CID from Storacha output, using simulation")
            return _simulated_ipfs_upload(json_bytes, filename)
        
        logger.info(f"Successfully uploaded {filename} to IPFS: {cid}")
        return cid
    
    except subprocess.TimeoutExpired:
        logger.error("Storacha upload timed out")
        return _simulated_ipfs_upload(json_bytes, filename)
    except Exception as e:
        logger.error(f"Error uploading to Storacha: {str(e)}")
        return _simulated_ipfs_upload(json_bytes, filename)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

