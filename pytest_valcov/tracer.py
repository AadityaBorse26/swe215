import os
import sys

class ValueTracer:
    def __init__(self, source_dir):
        self.source_dir = os.path.abspath(source_dir)
        # self.coverage_data[filepath][lineno] = [
        #     {"outcome": outcome, "vars": {varname: val}, "is_param": {varname: bool}}
        # ]
        self.coverage_data = {}
        self.active = False
        self.current_outcome = "passed"
        self._cache = {}  # Cache for filename filtering results

    def start(self):
        self.active = True
        sys.settrace(self._trace)

    def stop(self):
        self.active = False
        sys.settrace(None)

    def set_current_outcome(self, outcome):
        self.current_outcome = outcome

    def _trace(self, frame, event, arg):
        if not self.active:
            return None

        filename = frame.f_code.co_filename
        
        # Fast path lookup using cache to reduce trace overhead
        traced_path = self._cache.get(filename)
        if traced_path is False:
            return self._trace

        if traced_path is None:
            if not filename.endswith('.py'):
                self._cache[filename] = False
                return self._trace
            
            abs_filename = os.path.abspath(filename)
            # Only trace code that is located within the target source directory
            if not abs_filename.startswith(self.source_dir):
                self._cache[filename] = False
                return self._trace
            
            self._cache[filename] = abs_filename
            traced_path = abs_filename

        if event == 'call':
            return self._trace

        if event == 'line':
            lineno = frame.f_lineno
            locals_dict = frame.f_locals
            
            # Identify input parameters vs local variables
            arg_count = frame.f_code.co_argcount
            # Use tuple slicing to get the arg names
            arg_names = set(frame.f_code.co_varnames[:arg_count])
            
            vars_snapshot = {}
            is_param_map = {}
            
            for k, v in locals_dict.items():
                # Filter out underscore-prefixed and dunder variables
                if k.startswith('_'):
                    continue
                
                # Filter to primitive types only to avoid bloat and side effects
                if type(v) in (int, float, str, bool, type(None)):
                    vars_snapshot[k] = v
                    is_param_map[k] = (k in arg_names)
            
            file_data = self.coverage_data.setdefault(traced_path, {})
            line_snapshots = file_data.setdefault(lineno, [])
            
            # Cap captured snapshots at 1000 per line to prevent infinite loop memory bloat
            if len(line_snapshots) < 1000:
                line_snapshots.append({
                    "outcome": self.current_outcome,
                    "vars": vars_snapshot,
                    "is_param": is_param_map
                })

        return self._trace
