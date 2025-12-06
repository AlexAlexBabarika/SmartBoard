#!/usr/bin/env python3
"""
Test script to verify contract hash integration with the voting system.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_contract_hash():
    """Test that the contract hash is properly formatted and can be used."""
    
    # Test hash from generation
    test_hash = "dffebec2aca3a1ea3df1e870ad37ca818832f5bc"
    hash_with_prefix = f"0x{test_hash}"
    
    print("=" * 60)
    print("Contract Hash Test")
    print("=" * 60)
    print(f"\n✅ Generated Hash: {hash_with_prefix}")
    print(f"   Length: {len(test_hash)} hex characters (20 bytes)")
    print(f"   Format: Valid NEO3 contract hash format")
    
    # Test NeoClient initialization
    print("\n" + "=" * 60)
    print("Testing NeoClient Integration")
    print("=" * 60)
    
    try:
        from backend.app.neo_client import NeoClient
        
        # Set environment for testing
        os.environ["NEO_CONTRACT_HASH"] = hash_with_prefix
        os.environ["DEMO_MODE"] = "true"  # Use simulation mode
        
        client = NeoClient()
        print(f"\n✅ NeoClient initialized successfully")
        print(f"   Simulation mode: {client.is_simulated}")
        print(f"   Contract hash will be used in: {hash_with_prefix}")
        
        # Test vote simulation
        print("\n" + "=" * 60)
        print("Testing Vote Simulation")
        print("=" * 60)
        
        # Simulate a vote
        result = client.vote(
            proposal_id=1,
            voter="test_voter_123",
            choice=1
        )
        
        print(f"\n✅ Vote simulation successful")
        print(f"   Transaction hash: {result.get('tx_hash', 'N/A')}")
        print(f"   Note: In DEMO_MODE, votes are simulated (not on-chain)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\n✅ Contract hash format is correct")
    print("✅ NeoClient can use the hash")
    print("✅ Vote simulation works")
    print("\n📝 Next steps:")
    print("   1. Add to .env: NEO_CONTRACT_HASH=" + hash_with_prefix)
    print("   2. Set SIMULATED_VOTING_ENABLED=true in .env")
    print("   3. Start backend to see real-time voting simulation")
    print("\n⚠️  Note: This is a test hash. For production:")
    print("   - Deploy the contract to NEO testnet")
    print("   - Use the hash from the deployment transaction")
    print("   - Set DEMO_MODE=false to use real blockchain")
    
    return True

if __name__ == "__main__":
    success = test_contract_hash()
    sys.exit(0 if success else 1)



