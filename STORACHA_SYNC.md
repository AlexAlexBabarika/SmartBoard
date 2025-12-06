# Storacha/IPFS Proposal Synchronization

This feature allows you to sync proposals from Storacha/IPFS storage into your database, automatically checking for duplicates and only adding unique proposals.

## Overview

The sync system supports two methods:

1. **Manifest-based sync**: Sync from a JSON manifest file that lists all proposals with their metadata
2. **CID-based sync**: Sync from a list of IPFS CIDs by downloading and parsing PDFs

## Features

- ✅ Automatic duplicate detection (checks by IPFS CID)
- ✅ Downloads PDFs from multiple IPFS gateways (Storacha, IPFS.io, Cloudflare, etc.)
- ✅ Extracts metadata from PDFs (title, summary, confidence)
- ✅ Background processing support (non-blocking)
- ✅ Comprehensive error handling

## API Endpoints

### 1. Sync from Manifest

Sync proposals from a manifest.json file stored on Storacha/IPFS.

```bash
POST /sync/storacha/manifest
Content-Type: application/json

{
  "manifest_cid": "bafy...",
  "skip_existing": true
}
```

**Query Parameters:**
- `async_mode` (default: `true`): Run sync in background

**Response (async mode):**
```json
{
  "status": "started",
  "message": "Sync from manifest started in background",
  "manifest_cid": "bafy..."
}
```

**Response (sync mode, `async_mode=false`):**
```json
{
  "success": true,
  "synced": 5,
  "skipped": 2,
  "failed": 0,
  "total": 7
}
```

### 2. Sync from CIDs

Sync proposals from a list of IPFS CIDs.

```bash
POST /sync/storacha/cids
Content-Type: application/json

{
  "cids": [
    "bafy...",
    "bafy...",
    "bafy..."
  ],
  "skip_existing": true
}
```

**Query Parameters:**
- `async_mode` (default: `true`): Run sync in background

### 3. Get Existing CIDs

Get list of all IPFS CIDs currently in the database.

```bash
GET /sync/storacha/existing
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "cids": ["bafy...", "bafy...", ...]
}
```

## Manifest File Format

The manifest.json file should be a JSON array of proposal objects:

```json
[
  {
    "cid": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3ylktlsdcasysdy",
    "title": "Investment Memo: Startup Name",
    "summary": "Executive summary of the investment opportunity...",
    "confidence": 85,
    "metadata": {
      "startup_name": "Startup Name",
      "sector": "AI & ML",
      "stage": "Series A",
      "risk_score": 58
    },
    "created_at": "2024-01-01T00:00:00Z",
    "status": "active",
    "yes_votes": 5,
    "no_votes": 2
  },
  ...
]
```

**Required fields:**
- `cid`: IPFS CID of the proposal PDF

**Optional fields:**
- `title`: Proposal title (will be extracted from PDF if not provided)
- `summary`: Executive summary (will be extracted from PDF if not provided)
- `confidence`: Confidence score 0-100 (default: 75)
- `metadata`: Additional metadata dictionary
- `created_at`: ISO timestamp
- `status`: Proposal status
- `yes_votes`, `no_votes`: Vote counts

## Creating a Manifest

Use the helper script to create a manifest from your database:

```bash
# Create manifest from current database
python backend/create_manifest.py

# Create and upload to Storacha
python backend/create_manifest.py --upload

# Custom output file
python backend/create_manifest.py --output my_manifest.json
```

This will:
1. Query all proposals from your database
2. Create a manifest.json file with all proposal metadata
3. Optionally upload it to Storacha and return the CID

## Usage Examples

### Example 1: Sync from Manifest (Python)

```python
import requests

# Sync from manifest
response = requests.post(
    "http://localhost:8000/sync/storacha/manifest",
    json={
        "manifest_cid": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3ylktlsdcasysdy",
        "skip_existing": True
    },
    params={"async_mode": False}  # Wait for completion
)

print(response.json())
# {
#   "success": true,
#   "synced": 5,
#   "skipped": 2,
#   "failed": 0,
#   "total": 7
# }
```

### Example 2: Sync from CIDs (cURL)

```bash
curl -X POST "http://localhost:8000/sync/storacha/cids?async_mode=false" \
  -H "Content-Type: application/json" \
  -d '{
    "cids": [
      "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3ylktlsdcasysdy",
      "bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxwvybicm"
    ],
    "skip_existing": true
  }'
```

### Example 3: Check Existing CIDs

```bash
curl "http://localhost:8000/sync/storacha/existing"
```

### Example 4: Frontend Integration

```javascript
// Sync from manifest
async function syncFromManifest(manifestCid) {
  const response = await fetch(
    `/sync/storacha/manifest?async_mode=false`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        manifest_cid: manifestCid,
        skip_existing: true
      })
    }
  );
  
  const result = await response.json();
  console.log(`Synced: ${result.synced}, Skipped: ${result.skipped}`);
  return result;
}

// Sync from CIDs
async function syncFromCids(cids) {
  const response = await fetch(
    `/sync/storacha/cids?async_mode=false`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cids: cids,
        skip_existing: true
      })
    }
  );
  
  return await response.json();
}
```

## How It Works

### Manifest Sync Flow

1. Download manifest.json from Storacha/IPFS
2. Parse JSON array of proposals
3. For each proposal:
   - Check if CID already exists in database
   - If not, create proposal with metadata from manifest
   - If yes and `skip_existing=true`, skip it

### CID Sync Flow

1. For each CID in the list:
   - Check if CID already exists in database
   - If not:
     - Download PDF from IPFS (tries multiple gateways)
     - Extract metadata from PDF (title, summary, confidence)
     - Create proposal in database
   - If yes and `skip_existing=true`, skip it

### PDF Metadata Extraction

The system attempts to extract metadata from PDFs using:

1. **PDF Metadata**: Title from PDF document properties
2. **First Page Text**: Summary from first page content
3. **Pattern Matching**: Looks for "Investment Memo: ..." patterns
4. **Fallbacks**: Uses default values if extraction fails

**Note**: For best results, use manifest-based sync which includes full metadata.

## IPFS Gateway Fallback

The system tries multiple IPFS gateways in order:

1. Storacha (`https://storacha.link/ipfs/`)
2. IPFS.io (`https://ipfs.io/ipfs/`)
3. dweb.link (`https://dweb.link/ipfs/`)
4. Pinata (`https://gateway.pinata.cloud/ipfs/`)
5. Cloudflare (`https://cloudflare-ipfs.com/ipfs/`)

This ensures high availability even if one gateway is down.

## Error Handling

- **Failed downloads**: Logged and skipped, doesn't stop entire sync
- **Invalid PDFs**: Uses fallback metadata, proposal still created
- **Database errors**: Transaction rolled back, error logged
- **Duplicate CIDs**: Skipped (if `skip_existing=true`)

## Best Practices

1. **Use manifest-based sync** when possible for better metadata
2. **Set `skip_existing=true`** to avoid duplicates
3. **Use async mode** for large syncs to avoid timeouts
4. **Check existing CIDs first** to see what's already synced
5. **Keep manifest updated** by regenerating it periodically

## Troubleshooting

### "Failed to download from all gateways"

- Check if CID is valid
- Verify IPFS gateway availability
- Try syncing individual CIDs to identify problematic ones

### "PyPDF2 not available"

- Install PyPDF2: `pip install PyPDF2`
- Or use manifest-based sync which doesn't require PDF parsing

### "Storacha CLI not found"

- Install Storacha CLI: `npm i -g @storacha/cli`
- Or use CID-based sync which doesn't require Storacha CLI

### Sync is slow

- Use async mode (`async_mode=true`) for background processing
- Sync in smaller batches
- Use manifest-based sync (faster than downloading PDFs)

## Security Considerations

- CIDs are validated before processing
- Database transactions ensure data consistency
- Background tasks are isolated from main request handling
- No sensitive data is logged

