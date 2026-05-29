import math

class ValueScorer:
    @staticmethod
    def compute_variable_diversity(values):
        """
        Computes the diversity score of a list of primitive values.
        Score is in [0, 1].
        """
        N = len(values)
        if N <= 1:
            return 0.0
            
        # Count value frequencies
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
            
        U = len(counts)
        if U <= 1:
            return 0.0
            
        # Shannon Entropy calculation
        entropy = 0.0
        for count in counts.values():
            p = count / N
            entropy -= p * math.log2(p)
            
        # Normalize entropy by theoretical maximum log2(N)
        h_max = math.log2(N)
        h_norm = entropy / h_max
        
        # Penalize small unique counts (e.g. U=2 has max factor of 0.5)
        var_score = h_norm * (1.0 - 1.0 / U)
        return round(var_score, 4)

    @classmethod
    def compute_scores(cls, coverage_data):
        """
        Processes tracer data and computes nested dictionary of metrics:
        {
            filepath: {
                lineno: {
                    "hits": int,
                    "global_score": float,
                    "passed_score": float,
                    "failed_score": float,
                    "variables": {
                        varname: {
                            "is_param": bool,
                            "unique_count": int,
                            "sample_values": list,
                            "global_score": float,
                            "passed_score": float,
                            "failed_score": float
                        }
                    }
                }
            }
        }
        """
        scores = {}
        
        for filepath, lines in coverage_data.items():
            file_scores = {}
            for lineno, snapshots in lines.items():
                hits = len(snapshots)
                
                # Separate snapshots by outcome
                passed_snaps = [s for s in snapshots if s["outcome"] == "passed"]
                failed_snaps = [s for s in snapshots if s["outcome"] == "failed"]
                
                # Identify all unique variable names seen at this line
                all_vars = set()
                var_is_param = {}
                for s in snapshots:
                    for varname in s["vars"]:
                        all_vars.add(varname)
                        var_is_param[varname] = s["is_param"][varname]
                
                if not all_vars:
                    # Covered but no variables: score based purely on execution hits
                    global_score = min(hits, 5) / 5.0
                    passed_score = min(len(passed_snaps), 5) / 5.0 if passed_snaps else 0.0
                    failed_score = min(len(failed_snaps), 5) / 5.0 if failed_snaps else 0.0
                    
                    file_scores[lineno] = {
                        "hits": hits,
                        "global_score": round(global_score, 4),
                        "passed_score": round(passed_score, 4),
                        "failed_score": round(failed_score, 4),
                        "variables": {}
                    }
                    continue
                
                # Compute per-variable scores
                vars_summary = {}
                global_var_scores = []
                passed_var_scores = []
                failed_var_scores = []
                
                for varname in all_vars:
                    # Extract list of primitive values
                    global_vals = [s["vars"][varname] for s in snapshots if varname in s["vars"]]
                    passed_vals = [s["vars"][varname] for s in passed_snaps if varname in s["vars"]]
                    failed_vals = [s["vars"][varname] for s in failed_snaps if varname in s["vars"]]
                    
                    g_score = cls.compute_variable_diversity(global_vals)
                    p_score = cls.compute_variable_diversity(passed_vals)
                    f_score = cls.compute_variable_diversity(failed_vals)
                    
                    global_var_scores.append(g_score)
                    if passed_vals:
                        passed_var_scores.append(p_score)
                    if failed_vals:
                        failed_var_scores.append(f_score)
                        
                    # Extract unique values for sample display
                    unique_vals = sorted(list(set(global_vals)), key=lambda x: str(x))
                    
                    vars_summary[varname] = {
                        "is_param": var_is_param[varname],
                        "unique_count": len(unique_vals),
                        "sample_values": unique_vals[:10],  # Show up to 10 sample values
                        "global_score": g_score,
                        "passed_score": p_score,
                        "failed_score": f_score
                    }
                
                # Line-level score is the average of variable-level scores
                global_score = sum(global_var_scores) / len(global_var_scores)
                passed_score = sum(passed_var_scores) / len(passed_var_scores) if passed_var_scores else 0.0
                failed_score = sum(failed_var_scores) / len(failed_var_scores) if failed_var_scores else 0.0
                
                file_scores[lineno] = {
                    "hits": hits,
                    "global_score": round(global_score, 4),
                    "passed_score": round(passed_score, 4),
                    "failed_score": round(failed_score, 4),
                    "variables": vars_summary
                }
                
            scores[filepath] = file_scores
            
        return scores
