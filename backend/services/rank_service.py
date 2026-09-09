"""LexoRank fractional indexing for dynamic Kanban card ordering."""
from typing import Optional


class LexoRank:
    """
    Generates string ranks that preserve natural sort order between cards
    without requiring O(N) database re-indexing on card drag-and-drop.
    """
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
    BASE = len(ALPHABET)
    MID_CHAR = "h"

    @classmethod
    def get_initial_rank(cls) -> str:
        return "0|hzzzzz:"

    @classmethod
    def between(cls, prev_rank: Optional[str], next_rank: Optional[str]) -> str:
        """Calculates a lexicographical midpoint between prev_rank and next_rank."""
        if not prev_rank and not next_rank:
            return cls.get_initial_rank()

        # Insert at the very beginning
        if not prev_rank and next_rank:
            clean_next = next_rank.split("|")[-1].replace(":", "")
            prefix = clean_next[:2] if len(clean_next) >= 2 else clean_next
            return f"0|0{prefix}:"

        # Insert at the very end
        if prev_rank and not next_rank:
            clean_prev = prev_rank.split("|")[-1].replace(":", "")
            return f"0|{clean_prev}z:"

        # Between two cards
        p = prev_rank.split("|")[-1].replace(":", "")
        n = next_rank.split("|")[-1].replace(":", "")

        common = []
        min_len = min(len(p), len(n))
        idx = 0
        while idx < min_len and p[idx] == n[idx]:
            common.append(p[idx])
            idx += 1

        prefix = "".join(common)
        p_val = cls.ALPHABET.index(p[idx]) if idx < len(p) else 0
        n_val = cls.ALPHABET.index(n[idx]) if idx < len(n) else cls.BASE - 1

        if n_val - p_val > 1:
            mid = cls.ALPHABET[(p_val + n_val) // 2]
            return f"0|{prefix}{mid}:"
        else:
            return f"0|{prefix}{cls.ALPHABET[p_val]}{cls.MID_CHAR}:"
