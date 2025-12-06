#!/usr/bin/env python3
"""
Generate NEO3 contract hash from compiled NEF and manifest files.
"""

import sys
import json
import hashlib
from pathlib import Path

def calculate_contract_hash(nef_path: Path, manifest_path: Path) -> str:
    """
    Calculate the contract hash (script hash) from NEF and manifest.
    
    For NEO3, the contract hash is the SHA256 hash of the contract script,
    then take the first 20 bytes (40 hex chars) and reverse the byte order.
    """
    if not nef_path.exists():
        raise FileNotFoundError(f"NEF file not found: {nef_path}")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    # Read NEF file (binary)
    # NEF format: magic(4) + compiler(64) + source(?) + checksum(4) + script
    with open(nef_path, 'rb') as f:
        nef_data = f.read()
    
    # NEF structure (simplified):
    # - Magic: 4 bytes (0x4E454F33 for NEO3)
    # - Compiler: 64 bytes
    # - Source: variable length (null-terminated string)
    # - Reserved: 2 bytes
    # - Checksum: 4 bytes
    # - Script: remaining bytes
    
    # Find script section (after magic + compiler + source + reserved + checksum)
    # Magic (4) + Compiler (64) = 68 bytes
    offset = 68
    
    # Skip source string (null-terminated)
    while offset < len(nef_data) and nef_data[offset] != 0:
        offset += 1
    offset += 1  # Skip null terminator
    
    # Skip reserved (2 bytes) and checksum (4 bytes) = 6 bytes
    offset += 6
    
    # Remaining is the script
    if offset >= len(nef_data):
        raise ValueError("Invalid NEF file structure")
    
    script = nef_data[offset:]
    
    # Compute SHA256 hash of script
    hash_obj = hashlib.sha256(script)
    hash_bytes = hash_obj.digest()
    
    # NEO3 contract hash is first 20 bytes of SHA256, reversed
    script_hash_bytes = hash_bytes[:20]
    script_hash_bytes_reversed = script_hash_bytes[::-1]
    
    # Convert to hex string
    contract_hash = script_hash_bytes_reversed.hex()
    
    return contract_hash

def main():
    script_dir = Path(__file__).parent
    nef_path = script_dir / "proposal_contract.nef"
    manifest_path = script_dir / "proposal_contract.manifest.json"
    
    # Try to compile if files don't exist
    if not nef_path.exists() or not manifest_path.exists():
        print("Compiling contract first...")
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "boa3.boa3", "compile", "proposal_contract.py"],
            cwd=script_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            sys.exit(1)
        print("Compilation successful!")
    
    try:
        contract_hash = calculate_contract_hash(nef_path, manifest_path)
        print(f"\n✅ Contract Hash: {contract_hash}")
        print(f"\nAdd this to your .env file:")
        print(f"NEO_CONTRACT_HASH=0x{contract_hash}")
        return contract_hash
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

