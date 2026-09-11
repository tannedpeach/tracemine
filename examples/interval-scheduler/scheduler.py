"""Reference scheduler for small batches; exhaustive search does not scale."""
from itertools import combinations


def select_jobs(jobs: list[tuple[int, int, int]]) -> list[int]:
    """Maximize weight of non-overlapping half-open intervals.

    Each job is (start, end, weight), with start < end and weight >= 0.
    Return original input indices in ascending order. Equal-weight schedules
    are resolved by the lexicographically smallest index list (Python ordering).
    """
    best_weight, best = 0, []
    for size in range(len(jobs) + 1):
        for selected in combinations(range(len(jobs)), size):
            if any(not (jobs[a][1] <= jobs[b][0] or jobs[b][1] <= jobs[a][0])
                   for a, b in combinations(selected, 2)):
                continue
            weight = sum(jobs[index][2] for index in selected)
            candidate = list(selected)
            if weight > best_weight or (weight == best_weight and candidate < best):
                best_weight, best = weight, candidate
    return best
