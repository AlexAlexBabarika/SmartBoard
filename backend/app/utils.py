import re
import os
import subprocess
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_cid(cid: str) -> str:
    """Normalize CID to a bare hash for duplicate checks."""
    if not cid:
        return cid
    clean = cid.replace("https://", "").replace("http://", "")
    clean = re.sub(r"^[^/]+/ipfs/", "", clean)
    clean = clean.replace("ipfs://", "")
    return clean


def get_current_storacha_space() -> Optional[str]:
    """
    Get the current active Storacha space name.
    
    Returns:
        Space name if available, None otherwise.
        Falls back to STORACHA_SPACE env var if CLI query fails.
    """
    # First check environment variable (explicit override)
    env_space = os.getenv("STORACHA_SPACE")
    if env_space:
        return env_space
    
    # Try to get from CLI
    storacha_cmd = os.getenv("STORACHA_CLI", "storacha")
    if not shutil.which(storacha_cmd):
        logger.debug("Storacha CLI not found, cannot determine current space")
        return None
    
    try:
        # Method 1: Try `storacha space info` (shows current space name)
        result = subprocess.run(
            [storacha_cmd, "space", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse "Name: <space_name>" from output
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Name:'):
                    space_name = line.split(':', 1)[1].strip()
                    if space_name:
                        logger.debug(f"Current Storacha space (from space info): {space_name}")
                        return space_name
        
        # Method 2: Fallback to `storacha space ls` and find the one with asterisk
        result = subprocess.run(
            [storacha_cmd, "space", "ls"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Find line with asterisk (*) which indicates current space
            for line in result.stdout.split('\n'):
                if line.strip().startswith('*'):
                    # Format: "* did:key:... <space_name>"
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        space_name = parts[-1]  # Last part is the space name
                        if space_name:
                            logger.debug(f"Current Storacha space (from space ls): {space_name}")
                            return space_name
        
        logger.debug("No active Storacha space found")
        return None
    except Exception as e:
        logger.debug(f"Failed to get Storacha space: {e}")
        return None

