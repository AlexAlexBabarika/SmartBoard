"""
Storacha manifest refresh helper.

Responsibilities:
- Generate manifest.json from current proposals
- Upload manifest to Storacha/IPFS (optional)
- Keep the latest manifest CID in-memory for reuse
- Fail-open: if upload or generation fails, logs and returns gracefully
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from .db import SessionLocal
from .models import Proposal

logger = logging.getLogger(__name__)

STORACHA_AUTO = os.getenv("STORACHA_MANIFEST_AUTO", "true").lower() == "true"
STORACHA_ASYNC = os.getenv("STORACHA_MANIFEST_ASYNC", "true").lower() == "true"
STORACHA_CLI = os.getenv("STORACHA_CLI", "storacha")
STORACHA_NO_WRAP = os.getenv("STORACHA_NO_WRAP", "true").lower() == "true"
INITIAL_MANIFEST_CID = os.getenv("STORACHA_MANIFEST_CID")

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="manifest-refresh")
_latest_manifest_cid: Optional[str] = INITIAL_MANIFEST_CID


def _generate_manifest_file() -> Optional[Path]:
    """Create a temporary manifest.json from the current proposals."""
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
                "no_votes": proposal.no_votes,
            }
            manifest.append(manifest_entry)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(tmp.name, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info("Generated manifest with %s proposals", len(manifest))
        return Path(tmp.name)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to generate manifest: %s", exc)
        return None
    finally:
        db.close()


def _upload_manifest(manifest_path: Path) -> Optional[str]:
    """Upload manifest file to Storacha and return CID."""
    if not STORACHA_CLI:
        logger.warning("STORACHA_CLI not configured; skipping manifest upload")
        return None

    if not shutil.which(STORACHA_CLI):
        logger.warning("Storacha CLI not found (%s); skipping upload", STORACHA_CLI)
        return None

    cmd = [STORACHA_CLI, "up", str(manifest_path)]
    if STORACHA_NO_WRAP:
        cmd.append("--no-wrap")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            logger.warning("Storacha upload failed (rc=%s): %s", result.returncode, output[:400])
            return None

        import re

        cid_match = re.search(r"storacha\.link/ipfs/([a-zA-Z0-9]+)", output)
        if not cid_match:
            cid_match = re.search(r"(bafy[a-zA-Z0-9]+)", output)
        if cid_match:
            cid = cid_match.group(1)
            logger.info("Uploaded manifest to Storacha: cid=%s", cid)
            return cid
        logger.warning("Could not parse CID from Storacha output")
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Manifest upload failed: %s", exc)
        return None


def refresh_manifest(source: str = "unknown") -> Optional[str]:
    """
    Generate and upload manifest. Returns CID (or existing) on success, None on failure.
    """
    global _latest_manifest_cid

    if not STORACHA_AUTO:
        return _latest_manifest_cid

    manifest_path = _generate_manifest_file()
    if not manifest_path:
        return _latest_manifest_cid

    cid = _upload_manifest(manifest_path)

    try:
        manifest_path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception:
        pass

    if cid:
        _latest_manifest_cid = cid
        logger.info(
            "Manifest refreshed",
            extra={"source": source, "cid": cid},
        )
    return _latest_manifest_cid


def schedule_manifest_refresh(source: str = "unknown") -> None:
    """Optionally refresh manifest asynchronously to avoid request latency."""
    if not STORACHA_AUTO:
        return

    if STORACHA_ASYNC:
        try:
            _executor.submit(refresh_manifest, source)
        except Exception as exc:  # pragma: no cover
            logger.debug("Manifest refresh scheduling failed: %s", exc)
    else:
        refresh_manifest(source)


def get_manifest_cid() -> Optional[str]:
    """Return the most recently known manifest CID (env-provided or refreshed)."""
    return _latest_manifest_cid

