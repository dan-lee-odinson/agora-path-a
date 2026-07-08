"""Deterministic randomness with named substreams.

Determinism is a hard requirement (Sim Plan §2): identical config + seed must reproduce
a run byte-for-byte. Every subsystem draws from its own named stream so that adding a
draw in one subsystem cannot shift the sequence seen by another — the classic
reproducibility failure of a single shared RNG.

Stream seeds are derived by SHA-256 of (master_seed, stream_name), which is stable
across platforms and Python versions, unlike hash().
"""

import hashlib
import random


class RngHub:
    """Factory for named, independently-seeded random.Random streams."""

    def __init__(self, master_seed: int):
        self.master_seed = int(master_seed)
        self._streams: dict[str, random.Random] = {}

    def stream(self, name: str) -> random.Random:
        """Return the (cached) stream for `name`, e.g. 'demand' or 'delivery.epoch7'."""
        if name not in self._streams:
            digest = hashlib.sha256(f"{self.master_seed}:{name}".encode("utf-8")).digest()
            self._streams[name] = random.Random(int.from_bytes(digest[:8], "big"))
        return self._streams[name]
