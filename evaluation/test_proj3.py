import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/codebases/proj3"))

import pytest
from evaluation.codebases.proj3.planner import PIBTPlanner
from evaluation.codebases.proj3.planner.heuristics import (
    StandardTimeHeuristic,
    WaitTimeHeuristic,
    CongestionHeuristic
)

def build_simple_graph():
    # 3x3 grid graph
    graph = {}
    for r in range(3):
        for c in range(3):
            neighbors = []
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 3 and 0 <= nc < 3:
                    neighbors.append((nr, nc))
            graph[(r, c)] = neighbors
    return graph

def test_pibt_with_standard_heuristic():
    graph = build_simple_graph()
    starts = {"A1": (0, 0), "A2": (2, 2)}
    goals = {"A1": (2, 2), "A2": (0, 0)}
    
    heuristic = StandardTimeHeuristic()
    planner = PIBTPlanner(graph, starts, goals, heuristic=heuristic, max_steps=50)
    paths = planner.plan()
    
    assert paths is not None
    assert "A1" in paths
    assert "A2" in paths
    assert paths["A1"][0] == (0, 0)
    assert paths["A2"][0] == (2, 2)
    # The planner should be able to run and return paths
    assert len(paths["A1"]) > 1

def test_pibt_with_wait_time_heuristic():
    graph = build_simple_graph()
    starts = {"A1": (0, 0), "A2": (2, 2)}
    goals = {"A1": (2, 2), "A2": (0, 0)}
    
    heuristic = WaitTimeHeuristic()
    planner = PIBTPlanner(graph, starts, goals, heuristic=heuristic, max_steps=50)
    paths = planner.plan()
    
    assert paths is not None
    assert len(paths["A1"]) > 1

def test_pibt_with_congestion_heuristic():
    graph = build_simple_graph()
    starts = {"A1": (0, 0), "A2": (2, 2)}
    goals = {"A1": (2, 2), "A2": (0, 0)}
    
    heuristic = CongestionHeuristic()
    planner = PIBTPlanner(graph, starts, goals, heuristic=heuristic, max_steps=50)
    paths = planner.plan()
    
    assert paths is not None
    assert len(paths["A1"]) > 1
