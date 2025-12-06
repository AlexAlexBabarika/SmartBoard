#!/bin/bash

# NEO Smart Contract Compilation Script
# Compiles proposal_contract.py using neo3-boa

set -e  # Exit on error

echo "🔨 Compiling NEO Smart Contract..."
echo ""

# Check if neo3-boa is installed
if ! python -c "import boa3" 2>/dev/null; then
    echo "❌ Error: neo3-boa is not installed"
    echo ""
    echo "Please install it with:"
    echo "  pip install neo3-boa"
    echo ""
    echo "Note: neo3-boa requires Python 3.10+"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Contract file
CONTRACT_FILE="$SCRIPT_DIR/proposal_contract.py"

if [ ! -f "$CONTRACT_FILE" ]; then
    echo "❌ Error: Contract file not found: $CONTRACT_FILE"
    exit 1
fi

echo "Contract file: $CONTRACT_FILE"
echo ""

# Compile the contract
echo "Compiling..."
python -m boa3.boa3 compile "$CONTRACT_FILE"

# Check if compilation was successful
if [ -f "${CONTRACT_FILE%.py}.nef" ]; then
    echo ""
    echo "✅ Compilation successful!"
    echo ""
    echo "Generated files:"
    ls -lh "${CONTRACT_FILE%.py}".nef
    ls -lh "${CONTRACT_FILE%.py}".manifest.json
    [ -f "${CONTRACT_FILE%.py}.nefdbgnfo" ] && ls -lh "${CONTRACT_FILE%.py}".nefdbgnfo
    echo ""
    echo "Next steps:"
    echo "1. Review the manifest.json file"
    echo "2. Deploy to testnet using: ./deploy_example.sh"
    echo "3. Update NEO_CONTRACT_HASH in .env with deployed contract hash"
else
    echo ""
    echo "❌ Compilation failed"
    exit 1
fi

