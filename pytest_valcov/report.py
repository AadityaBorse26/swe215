import os
import json
import html

class HTMLReportGenerator:
    def __init__(self, source_dir, report_path):
        self.source_dir = os.path.abspath(source_dir)
        self.report_path = os.path.abspath(report_path)

    def generate(self, scores):
        # Prepare self-contained data including source code lines
        prepared_data = {}
        for filepath, file_scores in scores.items():
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code_lines = f.readlines()
            except Exception:
                code_lines = []
                
            rel_path = os.path.relpath(filepath, self.source_dir).replace('\\', '/')
            # Convert keys of file_scores to integers to ensure stable indexing in JS
            formatted_lines = {int(k): v for k, v in file_scores.items()}
            
            prepared_data[rel_path] = {
                "lines": formatted_lines,
                "code": [line.rstrip('\r\n') for line in code_lines]
            }

        # Calculate overall metrics
        total_cov_lines = 0
        total_well_tested_lines = 0
        all_scores = []
        
        for file_info in prepared_data.values():
            total_cov_lines += len(file_info["lines"])
            total_well_tested_lines += sum(1 for s in file_info["lines"].values() if s["global_score"] >= 0.7)
            all_scores.extend(s["global_score"] for s in file_info["lines"].values())
            
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        overall_well_tested_pct = (total_well_tested_lines / total_cov_lines * 100.0) if total_cov_lines else 0.0

        # Ensure parent directories exist
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)

        # Build self-contained HTML
        html_content = self.HTML_TEMPLATE.format(
            json_data=json.dumps(prepared_data),
            overall_avg=f"{overall_avg:.2f}",
            well_tested_pct=f"{overall_well_tested_pct:.1f}%",
            covered_lines=total_cov_lines,
            well_tested_lines=total_well_tested_lines
        )

        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Value Coverage Analyzer - Interactive Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #0f172a;
            --bg-sidebar: #1e293b;
            --bg-card: #1e293b9f;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --text-muted: #64748b;
            
            --color-uncovered: #475569;
            --color-low: #ef4444;
            --bg-low: rgba(239, 68, 68, 0.12);
            --color-med: #f59e0b;
            --bg-med: rgba(245, 158, 11, 0.12);
            --color-high: #10b981;
            --bg-high: rgba(16, 185, 129, 0.12);
            --color-accent: #0d9488;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        /* Header Style */
        header {{
            background-color: var(--bg-sidebar);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 70px;
        }}

        .logo-section h1 {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .logo-section h1 span {{
            background: linear-gradient(135deg, #2dd4bf, #0d9488);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stats-summary {{
            display: flex;
            gap: 1.5rem;
        }}

        .stat-badge {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            min-width: 120px;
        }}

        .stat-badge .label {{
            font-size: 0.7rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .stat-badge .value {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 0.1rem;
        }}

        .stat-badge.high .value {{ color: var(--color-high); }}
        .stat-badge.accent .value {{ color: #2dd4bf; }}

        /* Main Layout */
        .workspace {{
            display: flex;
            flex: 1;
            height: calc(100vh - 70px);
            overflow: hidden;
        }}

        /* Sidebar - File Explorer */
        .sidebar {{
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .sidebar-header {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .file-list {{
            flex: 1;
            overflow-y: auto;
            padding: 0.5rem;
        }}

        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 0.25rem;
            border: 1px solid transparent;
        }}

        .file-item:hover {{
            background-color: rgba(255, 255, 255, 0.03);
            border-color: rgba(255, 255, 255, 0.05);
        }}

        .file-item.active {{
            background-color: rgba(13, 148, 136, 0.15);
            border-color: var(--color-accent);
        }}

        .file-name {{
            font-size: 0.85rem;
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 180px;
        }}

        .file-meta {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .score-pill {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            min-width: 38px;
            text-align: center;
        }}

        .score-pill.low {{ background-color: var(--bg-low); color: var(--color-low); }}
        .score-pill.med {{ background-color: var(--bg-med); color: var(--color-med); }}
        .score-pill.high {{ background-color: var(--bg-high); color: var(--color-high); }}

        /* Code Viewer */
        .code-viewer {{
            flex: 1;
            overflow-y: auto;
            background-color: var(--bg-main);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
        }}

        .code-container {{
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            background-color: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem 0;
            overflow-x: auto;
        }}

        .code-line {{
            display: flex;
            cursor: pointer;
            transition: background-color 0.15s ease;
            position: relative;
        }}

        .code-line:hover {{
            background-color: rgba(255, 255, 255, 0.04);
        }}

        .code-line.active-line {{
            background-color: rgba(13, 148, 136, 0.12);
        }}

        .line-number {{
            width: 50px;
            text-align: right;
            padding-right: 1.5rem;
            color: var(--text-muted);
            user-select: none;
            border-right: 1px solid var(--border-color);
        }}

        .line-hits {{
            width: 40px;
            text-align: right;
            padding-right: 1rem;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-dim);
            user-select: none;
        }}

        .line-code {{
            padding-left: 1rem;
            white-space: pre;
            flex: 1;
        }}

        /* Color overlays for line coverage & diversity status */
        .code-line.cov-uncovered .line-number {{ border-right: 3px solid var(--color-uncovered); }}
        
        .code-line.cov-low {{ background-color: var(--bg-low); }}
        .code-line.cov-low .line-number {{ border-right: 3px solid var(--color-low); color: var(--color-low); }}
        
        .code-line.cov-med {{ background-color: var(--bg-med); }}
        .code-line.cov-med .line-number {{ border-right: 3px solid var(--color-med); color: var(--color-med); }}
        
        .code-line.cov-high {{ background-color: var(--bg-high); }}
        .code-line.cov-high .line-number {{ border-right: 3px solid var(--color-high); color: var(--color-high); }}

        /* Details Pane */
        .details-pane {{
            width: 380px;
            background-color: var(--bg-sidebar);
            border-left: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .details-header {{
            padding: 1.25rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .details-header h2 {{
            font-size: 1rem;
            font-weight: 700;
        }}

        .details-header .subtitle {{
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: 0.25rem;
        }}

        .details-body {{
            flex: 1;
            overflow-y: auto;
            padding: 1.25rem;
        }}

        .placeholder-text {{
            color: var(--text-muted);
            text-align: center;
            margin-top: 4rem;
            font-size: 0.85rem;
            line-height: 1.5;
        }}

        .metric-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 1rem;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.75rem;
            border-radius: 6px;
        }}

        .metric-card {{
            display: flex;
            flex-direction: column;
        }}

        .metric-card .m-label {{
            font-size: 0.65rem;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.05em;
        }}

        .metric-card .m-val {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 0.15rem;
        }}

        /* Variable detail styles */
        .variables-list {{
            margin-top: 1.5rem;
        }}

        .variables-list h3 {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-dim);
            margin-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.25rem;
        }}

        .variable-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.85rem;
            margin-bottom: 0.75rem;
        }}

        .var-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .var-name {{
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            font-weight: 600;
            color: #2dd4bf;
        }}

        .var-type-badge {{
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            padding: 0.1rem 0.35rem;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-dim);
        }}

        .var-type-badge.param {{
            background: rgba(13, 148, 136, 0.15);
            color: #2dd4bf;
            border: 1px solid rgba(13, 148, 136, 0.3);
        }}

        .var-scores {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.4rem;
            margin-top: 0.5rem;
            font-size: 0.7rem;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.4rem;
            border-radius: 4px;
        }}

        .var-score-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .var-score-item span.lbl {{
            color: var(--text-muted);
            font-size: 0.6rem;
            text-transform: uppercase;
        }}

        .var-score-item span.val {{
            font-weight: 700;
            margin-top: 0.1rem;
        }}

        .unique-vals-box {{
            margin-top: 0.6rem;
        }}

        .unique-vals-box span.lbl {{
            font-size: 0.7rem;
            color: var(--text-dim);
            display: block;
            margin-bottom: 0.25rem;
        }}

        .pills-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            max-height: 80px;
            overflow-y: auto;
        }}

        .val-pill {{
            font-family: 'Fira Code', monospace;
            font-size: 0.7rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.1rem 0.35rem;
            border-radius: 4px;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        /* Scrollbar styles */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}

        ::-webkit-scrollbar-track {{
            background: transparent;
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <h1>Value Coverage <span>Analyzer</span></h1>
        </div>
        <div class="stats-summary">
            <div class="stat-badge accent">
                <span class="label">Avg Diversity</span>
                <span class="value">{overall_avg}</span>
            </div>
            <div class="stat-badge high">
                <span class="label">Well-Tested Rate</span>
                <span class="value">{well_tested_pct}</span>
            </div>
            <div class="stat-badge">
                <span class="label">Covered Lines</span>
                <span class="value">{covered_lines}</span>
            </div>
            <div class="stat-badge">
                <span class="label">Well-Tested Lines</span>
                <span class="value">{well_tested_lines}</span>
            </div>
        </div>
    </header>

    <div class="workspace">
        <!-- File list sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">Source Files</div>
            <div class="file-list" id="file-list"></div>
        </div>

        <!-- Code viewer center panel -->
        <div class="code-viewer">
            <div class="code-container" id="code-container">
                <div class="placeholder-text" style="margin-top: 10rem;">
                    <h3>Select a file from the sidebar to view source code and value coverage details.</h3>
                </div>
            </div>
        </div>

        <!-- Details pane right panel -->
        <div class="details-pane">
            <div class="details-header">
                <h2>Line Details</h2>
                <div class="subtitle" id="details-subtitle">No line selected</div>
            </div>
            <div class="details-body" id="details-body">
                <div class="placeholder-text">
                    Click on a highlighted line of code to inspect value snapshots and Shannon entropy scoring.
                </div>
            </div>
        </div>
    </div>

    <script>
        const data = {json_data};
        let selectedFile = null;
        let selectedLine = null;

        // Render file list
        const fileList = document.getElementById('file-list');
        Object.keys(data).forEach(filename => {{
            const fileInfo = data[filename];
            const coveredCount = Object.keys(fileInfo.lines).length;
            
            let fileAvg = 0.0;
            if (coveredCount > 0) {{
                const sum = Object.values(fileInfo.lines).reduce((acc, curr) => acc + curr.global_score, 0);
                fileAvg = sum / coveredCount;
            }}

            let statusClass = 'low';
            if (fileAvg >= 0.7) statusClass = 'high';
            else if (fileAvg >= 0.35) statusClass = 'med';

            const item = document.createElement('div');
            item.className = 'file-item';
            item.onclick = () => selectFile(filename, item);
            item.innerHTML = `
                <span class="file-name" title="${{filename}}">${{filename}}</span>
                <div class="file-meta">
                    <span class="score-pill ${{statusClass}}" title="Average diversity score">${{fileAvg.toFixed(2)}}</span>
                </div>
            `;
            fileList.appendChild(item);
        }});

        function selectFile(filename, element) {{
            // Deactivate previous active file
            document.querySelectorAll('.file-item').forEach(el => el.classList.remove('active'));
            element.classList.add('active');
            
            selectedFile = filename;
            selectedLine = null;
            
            // Clear details pane
            document.getElementById('details-subtitle').innerText = "No line selected";
            document.getElementById('details-body').innerHTML = `
                <div class="placeholder-text">
                    Click on a highlighted line of code to inspect value snapshots and Shannon entropy scoring.
                </div>
            `;

            renderCode(filename);
        }}

        function renderCode(filename) {{
            const fileInfo = data[filename];
            const codeContainer = document.getElementById('code-container');
            codeContainer.innerHTML = '';

            fileInfo.code.forEach((lineText, index) => {{
                const lineno = index + 1;
                const lineInfo = fileInfo.lines[lineno];

                const lineDiv = document.createElement('div');
                lineDiv.className = 'code-line';
                
                if (lineInfo) {{
                    const score = lineInfo.global_score;
                    if (score >= 0.7) lineDiv.classList.add('cov-high');
                    else if (score >= 0.35) lineDiv.classList.add('cov-med');
                    else lineDiv.classList.add('cov-low');
                    
                    lineDiv.onclick = () => selectLine(lineno, lineDiv);
                }} else {{
                    lineDiv.classList.add('cov-uncovered');
                }}

                const hitsText = lineInfo ? lineInfo.hits : '';

                lineDiv.innerHTML = `
                    <span class="line-number">${{lineno}}</span>
                    <span class="line-hits">${{hitsText}}</span>
                    <span class="line-code">${{escapeHtml(lineText)}}</span>
                `;
                codeContainer.appendChild(lineDiv);
            }});
        }}

        function selectLine(lineno, element) {{
            document.querySelectorAll('.code-line').forEach(el => el.classList.remove('active-line'));
            element.classList.add('active-line');
            selectedLine = lineno;

            const lineInfo = data[selectedFile].lines[lineno];
            document.getElementById('details-subtitle').innerText = `${{selectedFile}} : Line ${{lineno}}`;
            
            const detailsBody = document.getElementById('details-body');
            
            let varsHtml = '';
            const varKeys = Object.keys(lineInfo.variables);
            
            if (varKeys.length === 0) {{
                varsHtml = `
                    <div class="placeholder-text" style="margin-top: 2rem;">
                        This line contains no primitive local variables or input parameters.
                    </div>
                `;
            }} else {{
                varKeys.forEach(varname => {{
                    const v = lineInfo.variables[varname];
                    const typeClass = v.is_param ? 'param' : 'local';
                    const typeLabel = v.is_param ? 'Parameter' : 'Local';
                    
                    let pills = '';
                    v.sample_values.forEach(val => {{
                        let displayVal = val === null ? 'None' : val;
                        if (typeof val === 'string') displayVal = `"${{val}}"`;
                        pills += `<span class="val-pill" title="${{escapeHtml(String(val))}}">${{escapeHtml(String(displayVal))}}</span>`;
                    }});

                    varsHtml += `
                        <div class="variable-card">
                            <div class="var-header">
                                <span class="var-name">${{varname}}</span>
                                <span class="var-type-badge ${{typeClass}}">${{typeLabel}}</span>
                            </div>
                            <div class="var-scores">
                                <div class="var-score-item">
                                    <span class="lbl">Global</span>
                                    <span class="val" style="color: ${{getScoreColor(v.global_score)}}">${{v.global_score.toFixed(2)}}</span>
                                </div>
                                <div class="var-score-item">
                                    <span class="lbl">Passed</span>
                                    <span class="val" style="color: ${{getScoreColor(v.passed_score)}}">${{v.passed_score.toFixed(2)}}</span>
                                </div>
                                <div class="var-score-item">
                                    <span class="lbl">Failed</span>
                                    <span class="val" style="color: ${{getScoreColor(v.failed_score)}}">${{v.failed_score.toFixed(2)}}</span>
                                </div>
                            </div>
                            <div class="unique-vals-box">
                                <span class="lbl">Unique values seen (${{v.unique_count}}):</span>
                                <div class="pills-container">
                                    ${{pills}}
                                </div>
                            </div>
                        </div>
                    `;
                }});
            }}

            detailsBody.innerHTML = `
                <div class="metric-row">
                    <div class="metric-card">
                        <span class="m-label">Execution Hits</span>
                        <span class="m-val">${{lineInfo.hits}}</span>
                    </div>
                    <div class="metric-card">
                        <span class="m-label">Diversity Score</span>
                        <span class="m-val" style="color: ${{getScoreColor(lineInfo.global_score)}}">${{lineInfo.global_score.toFixed(2)}}</span>
                    </div>
                </div>
                
                <div class="metric-row">
                    <div class="metric-card">
                        <span class="m-label">Passed Diversity</span>
                        <span class="m-val" style="color: ${{getScoreColor(lineInfo.passed_score)}}">${{lineInfo.passed_score.toFixed(2)}}</span>
                    </div>
                    <div class="metric-card">
                        <span class="m-label">Failed Diversity</span>
                        <span class="m-val" style="color: ${{getScoreColor(lineInfo.failed_score)}}">${{lineInfo.failed_score.toFixed(2)}}</span>
                    </div>
                </div>

                <div class="variables-list">
                    <h3>Tracked Variables</h3>
                    ${{varsHtml}}
                </div>
            `;
        }}

        function getScoreColor(score) {{
            if (score >= 0.7) return 'var(--color-high)';
            if (score >= 0.35) return 'var(--color-med)';
            return 'var(--color-low)';
        }}

        function escapeHtml(text) {{
            const map = {{
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            }};
            return String(text).replace(/[&<>"']/g, function(m) {{ return map[m]; }});
        }}
    </script>
</body>
</html>
"""
