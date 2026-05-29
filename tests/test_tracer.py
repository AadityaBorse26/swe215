import os
import pytest
from pytest_valcov.tracer import ValueTracer

def dummy_function(a, b):
    x = a + b
    y = "hello"
    z = [1, 2] # Non-primitive, should be ignored
    _ignored = 42 # Underscore prefixed, should be ignored
    return x

def test_tracer_capture():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tracer = ValueTracer(current_dir)
    
    # Run tracing on dummy function execution
    tracer.start()
    try:
        dummy_function(5, 10)
    finally:
        tracer.stop()
        
    # Find dummy_function filepath key in coverage data
    this_file = os.path.abspath(__file__)
    assert this_file in tracer.coverage_data
    
    line_data = tracer.coverage_data[this_file]
    assert len(line_data) > 0
    
    # Find line with x and y in snapshots
    found_line_with_vars = False
    for lineno, snapshots in line_data.items():
        for snap in snapshots:
            if "x" in snap["vars"]:
                found_line_with_vars = True
                assert snap["vars"]["a"] == 5
                assert snap["vars"]["b"] == 10
                assert snap["vars"]["x"] == 15
                assert snap["vars"]["y"] == "hello"
                assert "z" not in snap["vars"] # ignored
                assert "_ignored" not in snap["vars"] # ignored
                
                # Check parameter markers
                assert snap["is_param"]["a"] is True
                assert snap["is_param"]["b"] is True
                assert snap["is_param"]["x"] is False
                assert snap["is_param"]["y"] is False
                
    assert found_line_with_vars is True
