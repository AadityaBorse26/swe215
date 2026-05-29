import pytest
from pytest_valcov.scorer import ValueScorer

def test_compute_variable_diversity():
    # Only 1 unique value: score must be exactly 0.0
    assert ValueScorer.compute_variable_diversity([1, 1, 1, 1]) == 0.0
    
    # Empty or single item: score must be exactly 0.0
    assert ValueScorer.compute_variable_diversity([1]) == 0.0
    assert ValueScorer.compute_variable_diversity([]) == 0.0
    
    # Completely diverse uniform values (U=2, N=2) -> H=1, H_max=1, penalty = 0.5 -> score = 0.5
    assert ValueScorer.compute_variable_diversity([1, 2]) == 0.5
    
    # Skewed vs uniform values comparison
    uniform_score = ValueScorer.compute_variable_diversity([1, 2, 3, 4])
    skewed_score = ValueScorer.compute_variable_diversity([1, 1, 1, 2])
    assert uniform_score > skewed_score

def test_compute_scores_empty():
    scores = ValueScorer.compute_scores({})
    assert scores == {}

def test_compute_scores_integration():
    coverage_data = {
        "file1.py": {
            10: [
                {"outcome": "passed", "vars": {"x": 1, "y": "a"}, "is_param": {"x": True, "y": False}},
                {"outcome": "passed", "vars": {"x": 2, "y": "a"}, "is_param": {"x": True, "y": False}},
                {"outcome": "failed", "vars": {"x": 1, "y": "b"}, "is_param": {"x": True, "y": False}}
            ]
        }
    }
    
    scores = ValueScorer.compute_scores(coverage_data)
    assert "file1.py" in scores
    assert 10 in scores["file1.py"]
    
    line_info = scores["file1.py"][10]
    assert line_info["hits"] == 3
    assert line_info["global_score"] > 0
    assert "x" in line_info["variables"]
    assert "y" in line_info["variables"]
    
    assert line_info["variables"]["x"]["is_param"] is True
    assert line_info["variables"]["y"]["is_param"] is False
