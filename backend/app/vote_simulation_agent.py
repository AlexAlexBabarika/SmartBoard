"""
Background agent that simulates real-time voting on proposals.

Designed to integrate with the existing agentic stack by reusing the shared
`process_vote` logic and database/Neo client paths. Emits one vote per
proposal every `interval_seconds`, capped per proposal to avoid unbounded
growth in demo scenarios.
"""

import logging
import random
import threading
import time
from collections import defaultdict
from typing import Callable, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Proposal as DBProposal
from .vote_service import process_vote

logger = logging.getLogger(__name__)


class SimulatedVotingAgent:
    """
    Fire-and-forget agent that casts simulated votes on active proposals.

    - Emits one vote per proposal every `interval_seconds`
    - Stops voting once `max_votes_per_proposal` is reached
    - Biases toward "yes" using a configurable probability blended with the
      proposal's confidence score for more realistic behavior
    """

    def __init__(
        self,
        *,
        interval_seconds: float = 2.0,
        max_votes_per_proposal: int = 200,
        yes_probability: float = 0.65,
        db_factory: Optional[Callable[[], Session]] = None,
    ) -> None:
        self.interval_seconds = max(interval_seconds, 0.5)
        self.max_votes_per_proposal = max(max_votes_per_proposal, 1)
        self.yes_probability = min(max(yes_probability, 0.0), 1.0)
        self.db_factory = db_factory or SessionLocal

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_vote_at: Dict[int, float] = {}
        self._vote_counters: Dict[int, int] = defaultdict(int)

    def start(self) -> None:
        """Start the background voting loop."""
        if self._thread and self._thread.is_alive():
            logger.info("SimulatedVotingAgent already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("SimulatedVotingAgent thread started")

    def stop(self) -> None:
        """Stop the background voting loop."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("SimulatedVotingAgent stopped")

    def _run_loop(self) -> None:
        """Main loop that periodically checks and casts votes."""
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(f"SimulatedVotingAgent tick failed: {exc}")
            time.sleep(0.5)

    def _tick(self) -> None:
        """Process one iteration across all active proposals."""
        db = self.db_factory()
        now = time.time()

        try:
            active = db.query(DBProposal).filter(DBProposal.status == "active").all()
            for proposal in active:
                current_votes = proposal.yes_votes + proposal.no_votes
                if current_votes >= self.max_votes_per_proposal:
                    continue

                if proposal.deadline and now > proposal.deadline:
                    continue

                last = self._last_vote_at.get(proposal.id, 0.0)
                if now - last < self.interval_seconds:
                    continue

                vote_value = self._decide_vote(proposal)
                voter_address = self._generate_voter_address(proposal.id, current_votes)

                try:
                    process_vote(
                        db=db,
                        proposal=proposal,
                        voter_address=voter_address,
                        vote_value=vote_value,
                    )
                    self._last_vote_at[proposal.id] = now
                    self._vote_counters[proposal.id] += 1
                    logger.debug(
                        "Simulated vote cast",
                        extra={
                            "proposal_id": proposal.id,
                            "voter": voter_address,
                            "vote": vote_value,
                        },
                    )
                except HTTPException as exc:
                    # Duplicate vote attempts are expected when concurrency overlaps
                    if exc.status_code != 400:
                        logger.warning(
                            "Simulated vote rejected",
                            extra={
                                "proposal_id": proposal.id,
                                "voter": voter_address,
                                "detail": exc.detail,
                            },
                        )
                except Exception as exc:
                    logger.error(
                        "Simulated vote failed",
                        extra={
                            "proposal_id": proposal.id,
                            "voter": voter_address,
                            "error": str(exc),
                        },
                    )
        finally:
            db.close()

    def _decide_vote(self, proposal: DBProposal) -> int:
        """Blend configured bias with proposal confidence for realism."""
        confidence = proposal.confidence or 50
        confidence_weight = min(max(confidence / 100, 0.0), 1.0)
        blended_yes_probability = min(
            max((self.yes_probability + confidence_weight) / 2, 0.05), 0.95
        )
        return 1 if random.random() < blended_yes_probability else 0

    def _generate_voter_address(self, proposal_id: int, current_votes: int) -> str:
        """
        Generate deterministic, unique voter addresses per proposal to avoid
        duplicate-vote conflicts while keeping them recognizable in logs.
        """
        next_index = max(self._vote_counters[proposal_id], current_votes) + 1
        return f"sim-voter-{proposal_id}-{next_index:05d}"

