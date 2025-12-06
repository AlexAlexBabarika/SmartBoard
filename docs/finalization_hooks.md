## Finalization hooks

The contract now exposes two public hook functions you can customize to run logic when a proposal is finalized:

- `on_proposal_approved(proposal_id, title, ipfs_hash, yes_votes, no_votes)`
- `on_proposal_rejected(proposal_id, title, ipfs_hash, yes_votes, no_votes)`

### How it works

During `finalize_proposal`, the contract:
1. Checks the deadline and marks the proposal as finalized.
2. Compares `yes_votes` vs `no_votes` stored on-chain.
3. Calls the appropriate hook:
   - Approved if `yes_votes > no_votes`
   - Rejected (or tie) otherwise

### Customizing the hook logic

Edit the hook functions in `contracts/proposal_contract.py`. By default they are no-ops that return `True`.

Example: emit a notification on approval and revert on rejection:

```python
from boa3.builtin.interop.runtime import notify

@public
def on_proposal_approved(proposal_id: int, title: str, ipfs_hash: str, yes_votes: int, no_votes: int) -> bool:
    notify(["approved", proposal_id, yes_votes, no_votes])
    return True

@public
def on_proposal_rejected(proposal_id: int, title: str, ipfs_hash: str, yes_votes: int, no_votes: int) -> bool:
    # Abort on rejection to signal failure upstream
    abort()
    return False
```

> Note: If your custom logic returns `False` or aborts, it will fail the transaction that called `finalize_proposal`, so ensure callers can handle that behavior.

