#!/usr/bin/env python3
"""
Generate a test contract hash for development purposes.

Note: The real contract hash is generated when you deploy the contract to the blockchain.
This script generates a valid-format hash for testing.
"""

import hashlib
import time

def generate_test_hash():
    """
    Generate a deterministic test hash based on contract source.
    For production, use the hash returned by the deployment transaction.
    """
    # Read contract source
    contract_file = "proposal_contract.py"
    try:
        with open(contract_file, 'rb') as f:
            source_data = f.read()
    except FileNotFoundError:
        # Generate from timestamp if file not found
        source_data = f"test_contract_{time.time()}".encode()
    
    # Generate hash
    hash_obj = hashlib.sha256(source_data)
    hash_bytes = hash_obj.digest()
    
    # NEO3 contract hash is first 20 bytes, reversed
    script_hash_bytes = hash_bytes[:20]
    script_hash_bytes_reversed = script_hash_bytes[::-1]
    
    # Convert to hex string (40 characters)
    contract_hash = script_hash_bytes_reversed.hex()
    
    return contract_hash

if __name__ == "__main__":
    hash_value = generate_test_hash()
    print(f"\n✅ Test Contract Hash: {hash_value}")
    print(f"\nAdd this to your .env file for testing:")
    print(f"NEO_CONTRACT_HASH=0x{hash_value}")
    print(f"\n⚠️  Note: This is a test hash. For production, deploy the contract")
    print(f"   and use the hash returned by the deployment transaction.")


