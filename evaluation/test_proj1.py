import pytest
from evaluation.codebases.proj1.single_agent_planner import (
    move,
    get_sum_of_cost,
    compute_heuristics,
    build_constraint_table,
    is_constrained,
    a_star
)

def test_move():
    # Test all directions
    assert move((1, 1), 0) == (1, 0) # up
    assert move((1, 1), 1) == (2, 1) # right
    assert move((1, 1), 2) == (1, 2) # down
    assert move((1, 1), 3) == (0, 1) # left
    assert move((1, 1), 4) == (1, 1) # wait

def test_get_sum_of_cost():
    paths = [
        [(0, 0), (0, 1), (0, 2)], # len=3, cost=2
        [(1, 1), (1, 1), (1, 2)]  # len=3, cost=2
    ]
    assert get_sum_of_cost(paths) == 4

def test_compute_heuristics():
    my_map = [
        [False, False, False],
        [False, True,  False],
        [False, False, False]
    ]
    # Dijkstra heuristic rooted at goal (2, 2)
    h_values = compute_heuristics(my_map, (2, 2))
    assert h_values[(2, 2)] == 0
    assert h_values[(0, 2)] == 2
    assert h_values[(2, 0)] == 2
    assert (1, 1) not in h_values # obstacle

def test_build_constraint_table():
    constraints = [
        {'agent': 0, 'loc': [(1, 1)], 'timestep': 1},
        {'agent': 0, 'loc': [(1, 2), (1, 3)], 'timestep': 2},
        {'agent': 1, 'loc': [(0, 0)], 'timestep': 1}
    ]
    table = build_constraint_table(constraints, 0)
    assert 1 in table
    assert 2 in table
    assert len(table[1]) == 1
    assert table[1][0]['loc'] == [(1, 1)]

def test_is_constrained():
    table = {
        1: [{'agent': 0, 'loc': [(1, 1)], 'timestep': 1}],
        2: [{'agent': 0, 'loc': [(1, 1), (1, 2)], 'timestep': 2}]
    }
    assert is_constrained((1, 0), (1, 1), 1, table) is True
    assert is_constrained((1, 0), (1, 2), 1, table) is False
    assert is_constrained((1, 1), (1, 2), 2, table) is True

def test_a_star_simple():
    my_map = [
        [False, False, False],
        [False, True,  False],
        [False, False, False]
    ]
    h_values = compute_heuristics(my_map, (2, 2))
    path = a_star(my_map, (0, 0), (2, 2), h_values, 0, [])
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (2, 2)

def test_a_star_with_constraints():
    my_map = [
        [False, False, False],
        [False, False, False],
        [False, False, False]
    ]
    h_values = compute_heuristics(my_map, (2, 2))
    
    # Block goal (2, 2) at time 1 and 2
    constraints = [
        {'agent': 0, 'loc': [(2, 2)], 'timestep': 1},
        {'agent': 0, 'loc': [(2, 2)], 'timestep': 2}
    ]
    path = a_star(my_map, (0, 0), (2, 2), h_values, 0, constraints)
    assert path is not None
    assert len(path) > 3  # Should delay/wait due to constraints
