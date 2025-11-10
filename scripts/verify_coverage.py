"""
Performs post-test coverage verification against defined thresholds.

Conforms to Software Assurance standards by implementing explicit,
auditable, and layer-granular coverage validation.
"""

import json
import sys

from pathlib import Path
from typing import Any

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Configuration paths                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
ROOT_DIR = Path(__file__).resolve().parents[1]
COVERAGE_JSON = ROOT_DIR / "build" / "coverage" / "coverage.json"
THRESHOLDS_FILE = ROOT_DIR / "assurance" / "quality" / "coverage_thresholds.json"
REPORT_DIR = ROOT_DIR / "build" / "reports" / "coverage"
REPORT_JSON = REPORT_DIR / "coverage_verification_report.json"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Utility functions                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file safely, fail-fast on syntax errors."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict[str, Any], path: Path) -> None:
    """Write JSON with UTF-8 encoding, formatted and deterministic."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def compute_coverage_by_layer(
    coverage_data: dict[str, Any], thresholds: dict[str, Any]
) -> dict[str, dict[str, float]]:
    """
    Aggregate coverage statistics per architectural layer.
    Returns a dict: { layer_name: { "covered": X, "total": Y, "percent": Z } }
    """
    layer_stats: dict[str, dict[str, float]] = {}

    files = coverage_data.get("files", {})
    if not files:
        raise RuntimeError("Coverage JSON has no 'files' section.")

    for layer_name, cfg in thresholds.get("layers", {}).items():
        layer_paths = cfg.get("paths", [])
        total, covered = 0, 0

        for path, data in files.items():
            if any(p in path.replace("\\", "/") for p in layer_paths):
                summary = data.get("summary", {})
                total += summary.get("num_statements", 0)
                covered += summary.get("covered_lines", 0)

        percent = (covered / total * 100.0) if total > 0 else 0.0
        layer_stats[layer_name] = {
            "covered": covered,
            "total": total,
            "percent": round(percent, 2),
        }

    return layer_stats


def evaluate_thresholds(
    layer_results: dict[str, dict[str, float]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate each layer's coverage against defined thresholds.
    Returns a detailed dict with pass/fail per layer and overall verdict.
    """
    verdict = {"layers": {}, "overall": "PASS"}

    for layer_name, result in layer_results.items():
        cfg = thresholds.get("layers", {}).get(layer_name, {})
        statement_min = cfg.get("statement_min", 0.0)
        # TODO: branch_min reserved for future branch coverage enforcement (pytest-cov --cov-branch)
        # branch_min = cfg.get("branch_min", None)

        percent = result.get("percent", 0.0)
        layer_pass = percent >= statement_min

        verdict["layers"][layer_name] = {
            "actual": percent,
            "required_statement_min": statement_min,
            "passed": layer_pass,
        }

        if not layer_pass:
            verdict["overall"] = "FAIL"

    return verdict


def main() -> int:
    """Main verification process: load coverage data and thresholds."""
    print("Verifying coverage thresholds...\n")

    # Validate source files
    if not COVERAGE_JSON.exists():
        print(f"[ERROR] Coverage report not found at: {COVERAGE_JSON}")
        print("   Please run `make test` before executing this verification.")
        return 1

    if not THRESHOLDS_FILE.exists():
        print(f"[ERROR] Threshold definition not found at: {THRESHOLDS_FILE}")
        return 1

    # Load and validate JSONs
    try:
        coverage_data = load_json(COVERAGE_JSON)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON format in coverage file: {COVERAGE_JSON}\n{e}")
        return 1

    try:
        thresholds = load_json(THRESHOLDS_FILE)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON format in thresholds file: {THRESHOLDS_FILE}\n{e}")
        return 1

    print("[OK] Loaded coverage report and thresholds successfully.")
    print(f"   • Coverage data keys: {', '.join(coverage_data.keys())[:120]}...")
    print(
        f"   • Thresholds version: {thresholds.get('metadata', {}).get('version', 'N/A')}\n"
    )
    print("Ready for layer-by-layer coverage evaluation.\n")

    try:
        layer_results = compute_coverage_by_layer(coverage_data, thresholds)
    except Exception as e:
        print(f"[ERROR] Error computing layer coverage: {e}")
        return 1

    print("Layer coverage summary:")
    for name, res in layer_results.items():
        print(
            f"   • {name:<15} {res['percent']:>6.2f}% ({res['covered']}/{res['total']} lines)"
        )

    save_json({"status": "aggregated", "layers": layer_results}, REPORT_JSON)
    # print(f"\nUpdated report with layer coverage summary: {REPORT_JSON}")
    # return 0
    try:
        evaluation = evaluate_thresholds(layer_results, thresholds)
    except Exception as e:
        print(f"[ERROR] Error evaluating thresholds: {e}")
        return 1

    print("\nThreshold evaluation summary:")
    for layer, res in evaluation["layers"].items():
        status = "✅ PASS" if res["passed"] else "❌ FAIL"
        print(
            f"   • {layer:<15} {res['actual']:>6.2f}% (min {res['required_statement_min']:>5.2f}%)  →  {status}"
        )

    print(f"\nOverall coverage verdict: {evaluation['overall']}")
    save_json(evaluation, REPORT_JSON)
    print(f"Final verification report written to: {REPORT_JSON}")

    # Exit code drives CI result
    return 0 if evaluation["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
