# Research Pipeline Integration

## Integration points
- Central wrapper: `backend/app/research_pipeline_adapter.run_research_pipeline` (fail-open, timeout guarded).
- Call sites:
  - `backend/app/main.py::submit_memo` (HTTP proposal submissions).
  - `backend/app/main.py::submit_proposal_direct` (internal/direct submissions incl. startup discovery/debug).
  - `backend/app/storacha_sync.py::_create_proposal_in_db` (Storacha/IPFS sync paths).

## Pipeline hook
- Wrapper calls `research_pipeline.process_proposal` in a thread with a configurable timeout.
- Results are stored under reserved metadata key `_research` with tag `research_pipeline_v1`.
- Idempotent: if `_research.tag` already matches, the payload is returned untouched.
- Fail-open: import errors, exceptions, or timeouts return the original proposal; errors are logged.

## Failure behavior
- Timeout default: 2s (`RESEARCH_PIPELINE_TIMEOUT`).
- Fail-open on exceptions/timeouts; structured warnings logged.
- Optional async fire-and-forget (`RESEARCH_PIPELINE_ASYNC=true`) keeps request flow non-blocking.

## Configuration
- `RESEARCH_PIPELINE_ENABLED` (default `true`).
- `RESEARCH_PIPELINE_TIMEOUT` seconds (default `2.0`).
- `RESEARCH_PIPELINE_ASYNC` (default `false`).
- `RESEARCH_PIPELINE_TEST_MODE` (default `true`, uses mock research agent to avoid external effects).

## Tests
- `backend/tests/test_api.py::test_submit_memo_runs_research_pipeline`
- `backend/tests/test_api.py::test_submit_memo_carries_research_metadata`
- `backend/tests/test_api.py::test_run_research_pipeline_fail_open`

## Notes
- No user-visible behavior or schema changes; annotations live only in `metadata._research`.
- Metrics currently emit structured logs; ready for wiring to a real sink when available.

