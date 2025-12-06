import re


def clean_cid(cid: str) -> str:
    """Normalize CID to a bare hash for duplicate checks."""
    if not cid:
        return cid
    clean = cid.replace("https://", "").replace("http://", "")
    clean = re.sub(r"^[^/]+/ipfs/", "", clean)
    clean = clean.replace("ipfs://", "")
    return clean

