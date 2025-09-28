#!/usr/bin/env python3
"""
Tool Failure Analysis Script

This script provides detailed analysis of tool failures in tau2-bench simulations,
helping identify problematic tools and common error patterns.

Usage:
    python scripts/failure_analysis.py <results_file.json>
"""

import sys
from pathlib import Path
from collections import Counter

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results
from tau2.metrics.execution_analysis import analyze_tool_failures


def print_failure_summary(failure_analysis):
    """Print a summary of tool failure analysis."""

    print(f"📊 Failure Analysis Summary:")
    print(f"   • Total simulations: {failure_analysis['total_simulations']}")
    print(f"   • Enhanced logging available: {failure_analysis['enhanced_logging_simulations']}")
    print()

    # Show most failing tools
    if failure_analysis['most_failing_tools']:
        print("❌ Most Problematic Tools:")
        for i, (tool_name, failure_rate) in enumerate(failure_analysis['most_failing_tools'][:10], 1):
            print(f"   {i:2d}. {tool_name}: {failure_rate:.1%} failure rate")
        print()

    # Show common error patterns
    if failure_analysis['failure_patterns']:
        print("🔍 Common Error Patterns:")
        for i, (error_pattern, count) in enumerate(failure_analysis['failure_patterns'].items(), 1):
            print(f"   {i:2d}. {error_pattern}: {count} occurrences")
        print()


def print_detailed_tool_stats(failure_analysis):
    """Print detailed statistics for each tool."""

    print("🔧 Detailed Tool Statistics:")
    print("-" * 80)

    for tool_name, stats in failure_analysis['tool_failure_stats'].items():
        if stats['total'] > 0:  # Only show tools that were actually called
            success_rate = (stats['total'] - stats['failed']) / stats['total']

            print(f"\n{tool_name}:")
            print(f"   Total calls: {stats['total']:4d}")
            print(f"   Successful:  {stats['total'] - stats['failed']:4d} ({success_rate:6.1%})")
            print(f"   Failed:      {stats['failed']:4d} ({stats['failure_rate']:6.1%})")
            print(f"   Avg time:    {stats['avg_execution_time']:8.1f}ms")

            # Color-code based on performance
            if stats['failure_rate'] > 0.2:  # >20% failure rate
                status = "🔴 HIGH FAILURE RATE"
            elif stats['failure_rate'] > 0.1:  # >10% failure rate
                status = "🟡 MODERATE FAILURES"
            elif stats['avg_execution_time'] > 2000:  # >2 seconds
                status = "🟠 SLOW EXECUTION"
            else:
                status = "✅ PERFORMING WELL"

            print(f"   Status:      {status}")


def analyze_failure_patterns(results):
    """Analyze specific failure patterns and provide insights."""

    print("\n🕵️ Failure Pattern Analysis:")
    print("-" * 40)

    # Collect all failed tool calls
    failed_calls = []
    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            for log in sim.execution_logs:
                if not log.success:
                    failed_calls.append({
                        'task_id': sim.task_id,
                        'tool_name': log.tool_name,
                        'requestor': log.requestor,
                        'error_details': log.error_details,
                        'arguments': log.arguments,
                        'execution_time': log.execution_time_ms
                    })

    if not failed_calls:
        print("✅ No tool failures found!")
        return

    print(f"Total failed tool calls: {len(failed_calls)}")

    # Analyze error types
    error_types = Counter()
    for call in failed_calls:
        if call['error_details']:
            # Extract error type (first word before colon or first 20 chars)
            if ':' in call['error_details']:
                error_type = call['error_details'].split(':')[0].strip()
            else:
                error_type = call['error_details'][:20].strip()
            error_types[error_type] += 1

    print(f"\nError Type Distribution:")
    for error_type, count in error_types.most_common(10):
        percentage = count / len(failed_calls) * 100
        print(f"   {error_type}: {count} ({percentage:.1f}%)")

    # Analyze failure by requestor
    requestor_failures = Counter(call['requestor'] for call in failed_calls)
    print(f"\nFailures by Requestor:")
    for requestor, count in requestor_failures.most_common():
        percentage = count / len(failed_calls) * 100
        print(f"   {requestor}: {count} ({percentage:.1f}%)")

    # Show some example failures
    print(f"\n📋 Example Failures (first 5):")
    for i, call in enumerate(failed_calls[:5], 1):
        print(f"\n   {i}. Task {call['task_id']} - {call['tool_name']} ({call['requestor']})")
        print(f"      Error: {call['error_details']}")
        if call['arguments']:
            # Show first few arguments
            args_str = str(call['arguments'])
            if len(args_str) > 100:
                args_str = args_str[:97] + "..."
            print(f"      Args: {args_str}")


def generate_recommendations(failure_analysis):
    """Generate actionable recommendations based on failure analysis."""

    print("\n💡 Recommendations:")
    print("-" * 20)

    recommendations = []

    # Check for high-failure tools
    high_failure_tools = [
        (tool, stats) for tool, stats in failure_analysis['tool_failure_stats'].items()
        if stats['failure_rate'] > 0.15 and stats['total'] > 3  # >15% failure rate, at least 3 calls
    ]

    if high_failure_tools:
        recommendations.append("🔴 HIGH PRIORITY - Fix high-failure tools:")
        for tool, stats in sorted(high_failure_tools, key=lambda x: x[1]['failure_rate'], reverse=True):
            recommendations.append(f"   • {tool}: {stats['failure_rate']:.1%} failure rate ({stats['failed']}/{stats['total']} calls)")

    # Check for slow tools
    slow_tools = [
        (tool, stats) for tool, stats in failure_analysis['tool_failure_stats'].items()
        if stats['avg_execution_time'] > 2000 and stats['total'] > 1  # >2 seconds
    ]

    if slow_tools:
        recommendations.append("\n🟠 MEDIUM PRIORITY - Optimize slow tools:")
        for tool, stats in sorted(slow_tools, key=lambda x: x[1]['avg_execution_time'], reverse=True):
            recommendations.append(f"   • {tool}: {stats['avg_execution_time']:.1f}ms average execution time")

    # Check error patterns
    common_errors = [
        error for error, count in failure_analysis['failure_patterns'].items()
        if count > 2
    ]

    if common_errors:
        recommendations.append("\n🔍 INVESTIGATE - Common error patterns:")
        for error in common_errors[:3]:  # Top 3
            recommendations.append(f"   • {error}: {failure_analysis['failure_patterns'][error]} occurrences")

    if not recommendations:
        recommendations.append("✅ No critical issues found! Tools are performing well.")

    for rec in recommendations:
        print(rec)


def main():
    """Run detailed failure analysis on simulation results."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/failure_analysis.py <results_file.json>")
        print("\nExample:")
        print("  python scripts/failure_analysis.py data/simulations/my_results.json")
        sys.exit(1)

    results_file = Path(sys.argv[1])

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        # Load simulation results
        print(f"🔍 Analyzing tool failures in: {results_file}")
        results = Results.load(str(results_file))

        # Check if enhanced logging data is available
        enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
        if not enhanced_sims:
            print("❌ No enhanced logging data found in results!")
            print("Run simulations with --enhanced-logging flag to enable failure analysis")
            return

        print("=" * 80)

        # Run failure analysis
        failure_analysis = analyze_tool_failures(results)

        # Print analysis results
        print_failure_summary(failure_analysis)
        print_detailed_tool_stats(failure_analysis)
        analyze_failure_patterns(results)
        generate_recommendations(failure_analysis)

        # Save detailed results to file
        output_file = results_file.parent / f"{results_file.stem}_failure_analysis.txt"
        with open(output_file, 'w') as f:
            f.write("TOOL FAILURE ANALYSIS REPORT\n")
            f.write("=" * 40 + "\n\n")

            f.write(f"Results file: {results_file}\n")
            f.write(f"Total simulations: {failure_analysis['total_simulations']}\n")
            f.write(f"Enhanced logging simulations: {failure_analysis['enhanced_logging_simulations']}\n\n")

            f.write("TOOL STATISTICS:\n")
            for tool_name, stats in failure_analysis['tool_failure_stats'].items():
                if stats['total'] > 0:
                    f.write(f"{tool_name}: {stats['total']} calls, {stats['failed']} failures "
                           f"({stats['failure_rate']:.1%}), {stats['avg_execution_time']:.1f}ms avg\n")

            f.write("\nERROR PATTERNS:\n")
            for error, count in failure_analysis['failure_patterns'].items():
                f.write(f"{error}: {count} occurrences\n")

        print(f"\n💾 Detailed failure analysis saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error analyzing failures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()