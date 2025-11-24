"""Small diff util to compute simple text diffs for snapshots."""
import difflib
from typing import List


def compute_diff(a: str, b: str) -> List[str]:
    """Return a unified diff (as list of lines) between a and b."""
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)
    diff = list(difflib.unified_diff(a_lines, b_lines, fromfile='old', tofile='new'))
    return diff
