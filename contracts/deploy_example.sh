#!/bin/bash

# NEO Smart Contract Deployment Script (Example)
# Demonstrates how to deploy the contract to NEO testnet

set -e  # Exit on error

echo "🚀 NEO Smart Contract Deployment Guide"
echo "========================================"
echo ""

# Load environment variables if .env exists
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check for required environment variables
if [ -z "$NEO_RPC_URL" ]; then
    echo "⚠️  NEO_RPC_URL not set in .env"
    NEO_RPC_URL="https://testnet1.neo.org:443"
    echo "   Using default: $NEO_RPC_URL"
fi

if [ -z "$NEO_WALLET_PRIVATE_KEY" ]; then
    echo ""
    echo "❌ NEO_WALLET_PRIVATE_KEY not set in .env"
    echo ""
    echo "To deploy the contract, you need:"
    echo "1. A NEO testnet wallet with GAS for deployment fees"
    echo "2. The wallet's private key"
    echo "3. Set NEO_WALLET_PRIVATE_KEY in .env"
    echo ""
    echo "To get testnet GAS:"
    echo "- Visit: https://neowish.ngd.network/"
    echo "- Enter your testnet address"
    echo "- Request test GAS (typically 100 GAS)"
    echo ""
    echo "Deployment cost: ~10-15 GAS for contract deployment + invocation fees"
    echo ""
    echo "SECURITY WARNING: NEVER use mainnet private keys! Testnet only!"
    echo ""
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Contract files
NEF_FILE="$SCRIPT_DIR/proposal_contract.nef"
MANIFEST_FILE="$SCRIPT_DIR/proposal_contract.manifest.json"

if [ ! -f "$NEF_FILE" ]; then
    echo "❌ Contract not compiled. Run ./compile_contract.sh first"
    exit 1
fi

echo "Contract files found:"
echo "  NEF: $NEF_FILE"
echo "  Manifest: $MANIFEST_FILE"
echo ""

echo "Deployment Configuration:"
echo "  RPC URL: $NEO_RPC_URL"
echo "  Wallet: ${NEO_WALLET_PRIVATE_KEY:0:10}..."
echo ""

# Check if neo-mamba is installed
if ! python -c "import neo.mamba" 2>/dev/null; then
    echo "⚠️  neo-mamba not installed (required for deployment)"
    echo ""
    echo "To deploy using neo-mamba:"
    echo "  pip install neo-mamba"
    echo ""
    echo "Alternative deployment methods:"
    echo "1. Use neo-cli:"
    echo "   neo> deploy $NEF_FILE"
    echo ""
    echo "2. Use neo-express:"
    echo "   neoxp contract deploy $NEF_FILE"
    echo ""
    echo "3. Use online deployment tools:"
    echo "   https://neo.org/deploy"
    echo ""
    exit 1
fi

echo "🔄 Deploying contract to NEO testnet..."
echo ""

# Python deployment script using neo-mamba
python3 << DEPLOY_SCRIPT
import sys
import os
from pathlib import Path

try:
    # Note: This is example code structure
    # Actual neo-mamba API may vary based on version
    print("Connecting to NEO RPC...")
    
    rpc_url = "$NEO_RPC_URL"
    private_key = "$NEO_WALLET_PRIVATE_KEY"
    nef_file = "$NEF_FILE"
    manifest_file = "$MANIFEST_FILE"
    
    print(f"RPC: {rpc_url}")
    print(f"NEF: {nef_file}")
    print("")
    
    # Load NEF and manifest
    with open(nef_file, 'rb') as f:
        nef_bytes = f.read()
    
    with open(manifest_file, 'r') as f:
        manifest_json = f.read()
    
    print(f"NEF size: {len(nef_bytes)} bytes")
    print("")
    
    # TODO: Actual deployment using neo-mamba
    # This is a placeholder - update based on neo-mamba API
    
    print("⚠️  SIMULATION MODE")
    print("")
    print("To actually deploy, use neo-mamba or neo-cli:")
    print("")
    print("Example with neo-mamba (pseudocode):")
    print("  from neo.mamba import Wallet, ContractManagement")
    print("  wallet = Wallet.from_private_key(private_key)")
    print("  tx = ContractManagement.deploy(nef_bytes, manifest_json)")
    print("  result = wallet.sign_and_send(tx)")
    print("  contract_hash = result.contract_hash")
    print("")
    print("After deployment:")
    print("1. Save the contract hash")
    print("2. Update .env: NEO_CONTRACT_HASH=0x...")
    print("3. Wait for transaction confirmation (1-2 blocks)")
    print("4. Test contract invocation")
    print("")
    print("Example contract hash: 0x1234567890abcdef1234567890abcdef12345678")
    
except Exception as e:
    print(f"❌ Deployment error: {e}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Common issues:", file=sys.stderr)
    print("- Insufficient GAS balance", file=sys.stderr)
    print("- Invalid private key format", file=sys.stderr)
    print("- RPC endpoint not responding", file=sys.stderr)
    print("- Contract size too large (> 1MB)", file=sys.stderr)
    sys.exit(1)

DEPLOY_SCRIPT

echo ""
echo "📋 Post-Deployment Checklist:"
echo ""
echo "✓ Save the contract hash to .env"
echo "✓ Verify deployment on testnet explorer:"
echo "  https://testnet.neotube.io/"
echo "✓ Test contract invocation:"
echo "  python test_contract_invocation.py"
echo "✓ Initialize contract if needed (set permissions, etc.)"
echo ""
echo "Contract Methods Available:"
echo "  - create_proposal(title, ipfs_hash, deadline, confidence)"
echo "  - vote(proposal_id, voter, choice)"
echo "  - finalize_proposal(proposal_id)"
echo "  - get_proposal(proposal_id)"
echo "  - get_proposal_count()"
echo ""
echo "Happy deploying! 🎉"

