#!/usr/bin/env python3
"""
Basic Analysis Script - Generate comprehensive execution report

This script demonstrates the simplest way to analyze enhanced logging data
from tau2-bench simulations using the built-in analysis tools.

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
        # Load simulation results
        print(f"📊 Loading results from: {results_file}")
        results = Results.load(str(results_file))

        # Check if enhanced logging data is available
        enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
        if not enhanced_sims:
            print("❌ No enhanced logging data found in results!")
            print("\n💡 To enable enhanced logging, run simulations with:")
            print("  tau2 run --enhanced-logging [other options...]")
            return

        print(f"✅ Found {len(enhanced_sims)} simulations with enhanced logging data")
        print("=" * 60)

        # Generate comprehensive analysis report
        report = generate_execution_report(results)
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