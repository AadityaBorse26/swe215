import os
import pytest
from pytest_valcov.tracer import ValueTracer
from pytest_valcov.scorer import ValueScorer

def pytest_addoption(parser):
    group = parser.getgroup("value-coverage", "Value Coverage Analyzer options")
    group.addoption(
        "--valcov",
        action="store_true",
        default=False,
        help="Enable value coverage analysis."
    )
    group.addoption(
        "--valcov-source",
        action="store",
        default=".",
        help="Directory or package path to trace for value coverage (default: current directory)."
    )
    group.addoption(
        "--valcov-report",
        action="store",
        default="htmlcov_val/index.html",
        help="Path where the value coverage HTML report should be saved (default: htmlcov_val/index.html)."
    )

def pytest_configure(config):
    if config.getoption("--valcov"):
        source_dir = os.path.abspath(config.getoption("--valcov-source"))
        tracer = ValueTracer(source_dir)
        config._valcov_tracer = tracer
        
        # Override tracer's _trace to append to temporary list per test execution
        # to enable retroactive outcome mapping in logreport
        tracer.current_snapshots = []
        
        def custom_trace(frame, event, arg):
            if not tracer.active:
                return None

            filename = frame.f_code.co_filename
            traced_path = tracer._cache.get(filename)
            if traced_path is False:
                return tracer._trace

            if traced_path is None:
                if not filename.endswith('.py'):
                    tracer._cache[filename] = False
                    return tracer._trace
                abs_filename = os.path.abspath(filename)
                if not abs_filename.startswith(tracer.source_dir):
                    tracer._cache[filename] = False
                    return tracer._trace
                tracer._cache[filename] = abs_filename
                traced_path = abs_filename

            if event == 'call':
                return tracer._trace

            if event == 'line':
                lineno = frame.f_lineno
                locals_dict = frame.f_locals
                
                arg_count = frame.f_code.co_argcount
                arg_names = set(frame.f_code.co_varnames[:arg_count])
                
                vars_snapshot = {}
                is_param_map = {}
                
                for k, v in locals_dict.items():
                    if k.startswith('_'):
                        continue
                    if type(v) in (int, float, str, bool, type(None)):
                        vars_snapshot[k] = v
                        is_param_map[k] = (k in arg_names)
                
                # Store temporarily in current test's list
                if len(tracer.current_snapshots) < 10000:  # Safety cap per test case
                    tracer.current_snapshots.append({
                        "filename": traced_path,
                        "lineno": lineno,
                        "vars": vars_snapshot,
                        "is_param": is_param_map
                    })

            return tracer._trace
            
        tracer._trace = custom_trace

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    tracer = getattr(item.config, "_valcov_tracer", None)
    if tracer:
        tracer.current_snapshots = []
        tracer.start()
    try:
        yield
    finally:
        if tracer:
            tracer.stop()
            # Attach captured snapshots to test item for retroactive outcome mapping
            item._valcov_snapshots = tracer.current_snapshots

def pytest_runtest_logreport(report):
    if report.when == 'call':
        # Retrieve test item from active pytest node or similar
        # Since report has test id, we can associate.
        # However, pytest allows accessing item from report.nodeid if needed.
        pass

# We hook into pytest_runtest_makereport to get access to both the item and its outcome
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    if report.when == 'call':
        tracer = getattr(item.config, "_valcov_tracer", None)
        snapshots = getattr(item, "_valcov_snapshots", None)
        
        if tracer and snapshots:
            test_outcome = report.outcome  # 'passed', 'failed', or 'skipped'
            # Retroactively map outcome and merge into main coverage database
            for snap in snapshots:
                filename = snap["filename"]
                lineno = snap["lineno"]
                
                file_data = tracer.coverage_data.setdefault(filename, {})
                line_snapshots = file_data.setdefault(lineno, [])
                
                if len(line_snapshots) < 1000:
                    line_snapshots.append({
                        "outcome": test_outcome,
                        "vars": snap["vars"],
                        "is_param": snap["is_param"]
                    })

def pytest_sessionfinish(session, exitstatus):
    tracer = getattr(session.config, "_valcov_tracer", None)
    if not tracer:
        return

    # Calculate scores
    scores = ValueScorer.compute_scores(tracer.coverage_data)
    
    # Print terminal report
    print("\n" + "=" * 60)
    print(" VALUE COVERAGE ANALYSIS SUMMARY ".center(60, "="))
    print("=" * 60)
    print(f"{'File':<35} {'Covered':<8} {'Avg Div':<8} {'Well-Tested %':<12}")
    print("-" * 60)

    total_cov_lines = 0
    total_well_tested_lines = 0
    total_scores = []

    for filepath, file_scores in scores.items():
        rel_path = os.path.relpath(filepath, tracer.source_dir)
        covered_count = len(file_scores)
        if covered_count == 0:
            print(f"{rel_path:<35} {0:<8} {0.0:<8} {'0.0%':<12}")
            continue

        file_avg_score = sum(s["global_score"] for s in file_scores.values()) / covered_count
        well_tested_count = sum(1 for s in file_scores.values() if s["global_score"] >= 0.7)
        well_tested_pct = (well_tested_count / covered_count) * 100.0

        total_cov_lines += covered_count
        total_well_tested_lines += well_tested_count
        total_scores.extend(s["global_score"] for s in file_scores.values())

        print(f"{rel_path:<35} {covered_count:<8} {file_avg_score:<8.2f} {well_tested_pct:<11.1f}%")

    print("-" * 60)
    overall_avg = sum(total_scores) / len(total_scores) if total_scores else 0.0
    overall_well_tested_pct = (total_well_tested_lines / total_cov_lines * 100.0) if total_cov_lines else 0.0
    print(f"{'OVERALL':<35} {total_cov_lines:<8} {overall_avg:<8.2f} {overall_well_tested_pct:<11.1f}%")
    print("=" * 60)

    # Generate HTML Report & JSON raw scores
    from pytest_valcov.report import HTMLReportGenerator
    report_path = session.config.getoption("--valcov-report")
    generator = HTMLReportGenerator(tracer.source_dir, report_path)
    generator.generate(scores)
    
    # Save scores to JSON file for correlation script consumption
    json_path = os.path.splitext(report_path)[0] + ".json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2)
        
    print(f"Interactive Value Coverage HTML report generated at:\n  {os.path.abspath(report_path)}")
    print(f"Raw Value Coverage JSON scores saved at:\n  {os.path.abspath(json_path)}")
    print("=" * 60 + "\n")
