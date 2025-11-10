"""
Generate Assurance Report (HTML)
────────────────────────────────
Combines pytest results, coverage metrics, and verification verdict into a single HTML summary.
"""

import json

from datetime import UTC, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BUILD_DIR = BASE_DIR / "build"
REPORTS_DIR = BUILD_DIR / "reports" / "assurance"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Input sources
JUNIT_XML = BUILD_DIR / "test-results" / "results.xml"
COVERAGE_JSON = BUILD_DIR / "coverage" / "coverage.json"
VERIFICATION_JSON = (
    BUILD_DIR / "reports" / "coverage" / "coverage_verification_report.json"
)

# Output file
REPORT_HTML = REPORTS_DIR / "report.html"


def load_json_safe(path: Path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        return {"error": f"Failed to parse {path.name}: {e}"}


def generate_html(coverage_data, verification_data):
    date = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    overall = verification_data.get("overall", "UNKNOWN")
    layers = verification_data.get("layers", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Quantum Software Assurance Report</title>
<style>
body {{ font-family: "Segoe UI", sans-serif; margin: 40px; background: #f9fafb; color: #111; }}
h1 {{ color: #1f2937; }}
h2 {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
th, td {{ border: 1px solid #e5e7eb; padding: 8px; text-align: left; }}
th {{ background-color: #f3f4f6; }}
.pass {{ color: #16a34a; font-weight: bold; }}
.fail {{ color: #dc2626; font-weight: bold; }}
.meta {{ font-size: 0.9em; color: #6b7280; margin-bottom: 20px; }}
</style>
</head>
<body>
<h1>Quantum Software Assurance Report</h1>
<div class="meta">Generated at {date}</div>

<h2>Overall Coverage Verdict</h2>
<p><strong>Status:</strong> <span class="{ 'pass' if overall == 'PASS' else 'fail' }">{overall}</span></p>

<h2>Layer Coverage Summary</h2>
<table>
<tr><th>Layer</th><th>Actual %</th><th>Required %</th><th>Status</th></tr>
"""
    for name, res in layers.items():
        status = "PASS" if res.get("passed") else "FAIL"
        css = "pass" if res.get("passed") else "fail"
        html += f"<tr><td>{name}</td><td>{res.get('actual', 0):.2f}</td><td>{res.get('required_statement_min', 0):.2f}</td><td class='{css}'>{status}</td></tr>"

    html += """
</table>

<h2>Coverage Details</h2>
<p>Raw JSON report: <code>build/coverage/coverage.json</code></p>

<h2>Next Steps</h2>
<ul>
  <li>Ensure any failing layers meet their required coverage thresholds.</li>
  <li>Attach this HTML to audit documentation (QA-Assurance chain).</li>
  <li>Include <code>coverage_verification_report.json</code> in CI artifacts.</li>
</ul>

</body>
</html>
"""
    return html


def main():
    coverage_data = load_json_safe(COVERAGE_JSON)
    verification_data = load_json_safe(VERIFICATION_JSON)

    html = generate_html(coverage_data, verification_data)
    REPORT_HTML.write_text(html, encoding="utf-8")

    print(f"✅ Assurance report generated: {REPORT_HTML}\n")


if __name__ == "__main__":
    main()
