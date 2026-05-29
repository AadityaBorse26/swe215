import pytest
import random
from evaluation.codebases.proj2.auction import (
    dist,
    path_cost,
    hill_climbing,
    greedy_hill_climbing,
    parallel_auction,
    sequential_auction
)

def test_dist():
    assert dist((0, 0), (3, 4)) == 7
    assert dist((1, 1), (1, 1)) == 0
    assert dist((-1, -2), (2, 2)) == 7

def test_path_cost():
    assert path_cost((0, 0), []) == 0
    assert path_cost((0, 0), [(1, 1)]) == 2
    assert path_cost((0, 0), [(1, 1), (2, 2)]) == 4

def test_hill_climbing_algorithms():
    random.seed(42)
    start = (0, 0)
    goals = [(2, 3), (1, 1), (5, 5), (0, 4)]
    
    cost1, seq1 = hill_climbing(start, goals)
    cost2, seq2 = greedy_hill_climbing(start, goals)
    
    assert cost1 > 0
    assert len(seq1) == len(goals)
    assert cost2 > 0
    assert len(seq2) == len(goals)

def test_auctions():
    random.seed(42)
    starts = [(0, 0), (10, 10)]
    goals = [(2, 2), (8, 8), (1, 9), (9, 1)]
    
    p_cost, p_assign = parallel_auction(starts, goals)
    s_cost, s_assign = sequential_auction(starts, goals)
    
    assert p_cost > 0
    assert len(p_assign) == len(starts)
    assert s_cost > 0
    assert len(s_assign) == len(starts)
    
    # Ensure all goals are assigned
    p_assigned_goals = sum(len(v) for v in p_assign.values())
    s_assigned_goals = sum(len(v) for v in s_assign.values())
    assert p_assigned_goals == len(goals)
    assert s_assigned_goals == len(goals)
