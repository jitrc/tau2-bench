#!/usr/bin/env python3
"""
Basic Analysis Script - Generate comprehensive execution report

This script demonstrates the simplest way to analyze enhanced logging data
from tau2-bench simulations using the built-in analysis tools.

This version is optimized to handle large results files by streaming simulations
instead of loading them all into memory at once.

Usage:
    python scripts/basic_analysis.py <results_file.json>
"""

import sys
from pathlib import Path

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results
from tau2.metrics.execution_analysis import generate_execution_report


def main():
    """Generate a basic analysis report from simulation results."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/basic_analysis.py <results_file.json>")
        print("\nExample:")
        print("  python scripts/basic_analysis.py data/simulations/my_results.json")
        sys.exit(1)

    results_file = Path(sys.argv[1])

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        print("\nMake sure to run simulations with --enhanced-logging first:")
        print("  tau2 run --domain airline --enhanced-logging --num-trials 3")
        sys.exit(1)

    try:
        # Stream simulation results to avoid high memory usage
        print(f"📊 Streaming results from: {results_file}")
        simulations_stream = Results.stream_simulations(results_file)

        # Generate comprehensive analysis report from the stream
        report = generate_execution_report(simulations_stream)
        
        if "No enhanced logging data found" in report:
            print(f"⚠️ {report}")
            return

        print("=" * 60)
        print(report)

        # Save report to file
        report_file = results_file.parent / f"{results_file.stem}_analysis_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\n💾 Analysis report saved to: {report_file}")

    except Exception as e:
        print(f"❌ Error analyzing results: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
