#!/usr/bin/env python3
"""
Complete Analysis Workflow Script

This script runs all available analyses on tau2-bench simulation results
with enhanced logging data. Use this for comprehensive evaluation of your results.

This version is optimized to handle large results files by streaming simulations.

Usage:
    python scripts/complete_analysis.py <results_file.json>
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import io
import statistics

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results
from tau2.metrics.execution_analysis import run_streaming_analysis


def print_comprehensive_results(analyses, file=None):
    """Print comprehensive analysis results from a pre-computed analysis dictionary."""
    
    overview = analyses['overview']
    failure_analysis = analyses['failure_analysis']
    performance_analysis = analyses['performance_analysis']
    state_analysis = analyses['state_analysis']

    print("\n" + "="*80, file=file)
    print("🔍 COMPREHENSIVE ANALYSIS RESULTS", file=file)
    print("="*80, file=file)

    print(f"\n📊 ANALYSIS OVERVIEW:", file=file)
    print(f"   • Total simulations: {overview['total_simulations']}", file=file)
    print(f"   • Enhanced logging enabled: {overview['enhanced_logging_simulations']}", file=file)
    print(f"   • Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=file)

    # Detailed Failure Analysis
    if failure_analysis['tool_failure_stats']:
        print(f"\n❌ DETAILED FAILURE BREAKDOWN:", file=file)
        problematic_tools = [(tool, stats) for tool, stats in failure_analysis['tool_failure_stats'].items() if stats['failure_rate'] > 0.1]
        if problematic_tools:
            for tool, stats in problematic_tools:
                print(f"   🔴 {tool}: {stats['failure_rate']:.1%} failure rate", file=file)
        else:
            print("   ✅ No high-failure tools identified.", file=file)

    # Performance Insights
    if performance_analysis['slowest_tools']:
        print(f"\n⚡ PERFORMANCE INSIGHTS:", file=file)
        for tool, avg_time in performance_analysis['slowest_tools']:
            if avg_time > 1000:
                print(f"   🐌 {tool}: {avg_time:.1f}ms (optimization target)", file=file)

    # Action Items
    print(f"\n🎯 RECOMMENDED ACTION ITEMS:", file=file)
    action_items = []
    high_failure_tools = [tool for tool, stats in failure_analysis.get('tool_failure_stats', {}).items() if stats['failure_rate'] > 0.2]
    if high_failure_tools:
        action_items.append(f"🔴 Fix high-failure tools: {', '.join(high_failure_tools)}")
    if state_analysis['avg_changes_per_sim'] > 10:
        action_items.append(f"🔄 Review excessive state changes ({state_analysis['avg_changes_per_sim']:.1f} per sim)")
    if action_items:
        for item in action_items:
            print(f"   • {item}", file=file)
    else:
        print("   ✅ No critical issues identified - system performing well!", file=file)


def main():
    """Run comprehensive analysis workflow."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/complete_analysis.py <results_file.json>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        print(f"🚀 Starting comprehensive analysis of: {results_file.name}")
        simulations_stream = Results.stream_simulations(results_file)
        
        # Run the single-pass streaming analysis
        analyses = run_streaming_analysis(simulations_stream)

        if analyses['overview']['enhanced_logging_simulations'] == 0:
            print("❌ No enhanced logging data found in results!")
            return

        print(f"✅ Found enhanced logging data in {analyses['overview']['enhanced_logging_simulations']}/{analyses['overview']['total_simulations']} simulations")

        report_buffer = io.StringIO()
        print_comprehensive_results(analyses, file=report_buffer)
        report_content = report_buffer.getvalue()
        print(report_content)

        print(f"\n💾 Saving analysis results...")
        report_file = results_file.parent / f"{results_file.stem}_comprehensive_analysis.txt"
        report_file.write_text(report_content)

        json_file = results_file.parent / f"{results_file.stem}_analysis_data.json"
        with open(json_file, 'w') as f:
            json.dump(analyses, f, indent=2, default=str)

        print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print(f"   📄 Text report: {report_file}")
        print(f"   📊 JSON data: {json_file}")

    except Exception as e:
        print(f"\n❌ An error occurred during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
