#!/usr/bin/env python3
"""
Helper script to create a manifest.json file for Storacha sync.

This script helps you create a manifest file that lists all proposals
with their metadata, which can then be uploaded to Storacha and used
for syncing proposals across different instances.

Usage:
    python create_manifest.py [--output manifest.json] [--upload]
    
Examples:
    # Create manifest from database
    python create_manifest.py
    
    # Create and upload to Storacha
    python create_manifest.py --upload
    
    # Custom output file
    python create_manifest.py --output my_manifest.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.db import SessionLocal
from backend.app.models import Proposal


def create_manifest(output_path: str = "manifest.json") -> str:
    """
    Create a manifest.json file from all proposals in the database.
    
    Args:
        output_path: Path to output manifest file
        
    Returns:
        Path to created manifest file
    """
    db = SessionLocal()
    try:
        proposals = db.query(Proposal).order_by(Proposal.created_at.desc()).all()
        
        manifest = []
        for proposal in proposals:
            manifest_entry = {
                "cid": proposal.ipfs_cid,
                "title": proposal.title,
                "summary": proposal.summary,
                "confidence": proposal.confidence,
                "metadata": proposal.proposal_metadata or {},
                "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
                "status": proposal.status,
                "yes_votes": proposal.yes_votes,
                "no_votes": proposal.no_votes
            }
            manifest.append(manifest_entry)
        
        # Write manifest
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Created manifest with {len(manifest)} proposals")
        print(f"   Output: {output_file.absolute()}")
        
        return str(output_file.absolute())
    finally:
        db.close()


def upload_manifest(manifest_path: str) -> str:
    """
    Upload manifest file to Storacha and return CID.
    
    Args:
        manifest_path: Path to manifest.json file
        
    Returns:
        IPFS CID of uploaded manifest
    """
    import subprocess
    import shutil
    import os
    import re
    
    storacha_cmd = os.getenv("STORACHA_CLI", "storacha")
    if not shutil.which(storacha_cmd):
        print("❌ Storacha CLI not found. Install with: npm i -g @storacha/cli")
        sys.exit(1)
    
    cmd = [storacha_cmd, "up", manifest_path]
    if os.getenv("STORACHA_NO_WRAP", "true").lower() == "true":
        cmd.append("--no-wrap")
    
    print(f"Uploading manifest to Storacha...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        print(f"❌ Upload failed: {result.stderr}")
        sys.exit(1)
    
    output = f"{result.stdout}\n{result.stderr}"
    cid_match = re.search(r"storacha\.link/ipfs/([a-zA-Z0-9]+)", output)
    if not cid_match:
        cid_match = re.search(r"(bafy[a-zA-Z0-9]+)", output)
    
    if cid_match:
        cid = cid_match.group(1)
        print(f"✅ Manifest uploaded: {cid}")
        print(f"   URL: https://storacha.link/ipfs/{cid}")
        return cid
    else:
        print(f"❌ Could not parse CID from output: {output[:200]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create a manifest.json file for Storacha sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--output",
        default="manifest.json",
        help="Output manifest file path (default: manifest.json)"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload manifest to Storacha after creation"
    )
    
    args = parser.parse_args()
    
    # Create manifest
    manifest_path = create_manifest(args.output)
    
    # Upload if requested
    if args.upload:
        cid = upload_manifest(manifest_path)
        print(f"\n📋 Use this CID to sync proposals:")
        print(f"   POST /sync/storacha/manifest")
        print(f'   {{"manifest_cid": "{cid}", "skip_existing": true}}')


if __name__ == "__main__":
    main()

