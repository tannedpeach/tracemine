"""Behavior-preserving refactors must agree with the exhaustive oracle."""
from itertools import combinations
from hypothesis import given, settings, strategies as st
from scheduler import select_jobs


def oracle(jobs):
    schedules = [list(indices) for size in range(len(jobs) + 1)
                 for indices in combinations(range(len(jobs)), size)
                 if all(jobs[a][1] <= jobs[b][0] or jobs[b][1] <= jobs[a][0]
                        for a, b in combinations(indices, 2))]
    return min(schedules, key=lambda indices: (-sum(jobs[i][2] for i in indices), indices))


job = st.tuples(st.integers(0, 8), st.integers(1, 5), st.integers(0, 8)).map(
    lambda item: (item[0], item[0] + item[1], item[2]))


@given(st.lists(job, max_size=9))
@settings(print_blob=True)
def test_matches_exhaustive_contract(jobs):
    assert select_jobs(jobs) == oracle(jobs)


def test_examples():
    assert select_jobs([(0, 2, 3), (2, 4, 3), (0, 4, 5)]) == [0, 1]
    assert select_jobs([(0, 1, 0), (2, 3, 1)]) == [0, 1]
    assert select_jobs([]) == []
    assert select_jobs([(0, 1, 0)]) == []
