#!/usr/bin/env python3
"""
Performance Analysis Script

This script analyzes tool execution performance, identifies bottlenecks,
and provides optimization recommendations for tau2-bench simulations.

Usage:
    python scripts/performance_analysis.py <results_file.json>
"""

import sys
from pathlib import Path
import statistics
import json

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results
from tau2.metrics.execution_analysis import analyze_performance_bottlenecks


def print_performance_summary(perf_analysis):
    """Print a summary of performance analysis."""

    print("🐌 Performance Analysis Summary:")
    print("-" * 40)

    if perf_analysis['slowest_tools']:
        print("Slowest Tools (Average Execution Time):")
        for i, (tool_name, avg_time) in enumerate(perf_analysis['slowest_tools'], 1):
            print(f"   {i:2d}. {tool_name}: {avg_time:8.1f}ms")
    else:
        print("No performance data available")

    print()


def print_detailed_performance_stats(perf_analysis):
    """Print detailed performance statistics for each tool."""

    if not perf_analysis['execution_time_stats']:
        print("No detailed performance statistics available")
        return

    print("🔧 Detailed Performance Statistics:")
    print("-" * 80)
    print(f"{'Tool Name':<25} {'Count':<8} {'Mean':<10} {'Median':<10} {'Min':<10} {'Max':<10} {'Std Dev':<10}")
    print("-" * 80)

    # Sort by mean execution time (slowest first)
    sorted_tools = sorted(
        perf_analysis['execution_time_stats'].items(),
        key=lambda x: x[1]['mean'],
        reverse=True
    )

    for tool_name, stats in sorted_tools:
        print(f"{tool_name:<25} "
              f"{stats['count']:<8} "
              f"{stats['mean']:<10.1f} "
              f"{stats['median']:<10.1f} "
              f"{stats['min']:<10.1f} "
              f"{stats['max']:<10.1f} "
              f"{stats['std_dev']:<10.1f}")


def analyze_performance_patterns(results):
    """Analyze performance patterns across simulations."""

    print("\n📊 Performance Pattern Analysis:")
    print("-" * 40)

    # Collect all execution times by tool
    tool_times = {}
    simulation_metrics = []

    for sim in results.simulations:
        if sim.enhanced_logging_enabled:
            sim_total_time = 0
            sim_tool_count = 0

            if sim.execution_logs:
                for log in sim.execution_logs:
                    if log.success and log.execution_time_ms is not None:
                        # Track by tool
                        if log.tool_name not in tool_times:
                            tool_times[log.tool_name] = []
                        tool_times[log.tool_name].append(log.execution_time_ms)

                        # Track for simulation totals
                        sim_total_time += log.execution_time_ms
                        sim_tool_count += 1

            if sim_tool_count > 0:
                simulation_metrics.append({
                    'task_id': sim.task_id,
                    'trial': sim.trial,
                    'total_time': sim_total_time,
                    'tool_count': sim_tool_count,
                    'avg_time_per_tool': sim_total_time / sim_tool_count,
                    'reward': sim.reward_info.reward if sim.reward_info else 0
                })

    # Performance by simulation
    if simulation_metrics:
        print("Performance by Simulation:")
        simulation_metrics.sort(key=lambda x: x['total_time'], reverse=True)

        print(f"{'Task ID':<12} {'Trial':<6} {'Total Time':<12} {'Tool Count':<11} {'Avg/Tool':<10} {'Reward':<8}")
        print("-" * 70)

        for i, metrics in enumerate(simulation_metrics[:10], 1):  # Top 10 slowest
            print(f"{metrics['task_id']:<12} "
                  f"{metrics['trial'] or 'N/A':<6} "
                  f"{metrics['total_time']:<12.1f} "
                  f"{metrics['tool_count']:<11} "
                  f"{metrics['avg_time_per_tool']:<10.1f} "
                  f"{metrics['reward']:<8.3f}")

    # Tool variability analysis
    print(f"\nTool Performance Variability:")
    high_variance_tools = []

    for tool_name, times in tool_times.items():
        if len(times) > 1:  # Need at least 2 data points for std dev
            mean_time = statistics.mean(times)
            std_dev = statistics.stdev(times)
            coefficient_of_variation = std_dev / mean_time if mean_time > 0 else 0

            if coefficient_of_variation > 0.5:  # High variability (CV > 0.5)
                high_variance_tools.append((tool_name, coefficient_of_variation, mean_time, std_dev, len(times)))

    if high_variance_tools:
        high_variance_tools.sort(key=lambda x: x[1], reverse=True)  # Sort by CV
        print("Tools with High Performance Variability:")
        for tool, cv, mean_time, std_dev, count in high_variance_tools[:5]:
            print(f"   {tool}: CV={cv:.2f}, Mean={mean_time:.1f}ms ± {std_dev:.1f}ms (n={count})")
    else:
        print("All tools show consistent performance")


def analyze_correlation_with_success(results):
    """Analyze correlation between execution time and success rates."""

    print(f"\n🎯 Performance vs Success Correlation:")
    print("-" * 40)

    tool_performance = {}

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            for log in sim.execution_logs:
                if log.tool_name not in tool_performance:
                    tool_performance[log.tool_name] = {
                        'successful_times': [],
                        'failed_times': [],
                        'total_calls': 0,
                        'successful_calls': 0
                    }

                tool_performance[log.tool_name]['total_calls'] += 1

                if log.success:
                    tool_performance[log.tool_name]['successful_calls'] += 1
                    if log.execution_time_ms is not None:
                        tool_performance[log.tool_name]['successful_times'].append(log.execution_time_ms)
                else:
                    if log.execution_time_ms is not None:
                        tool_performance[log.tool_name]['failed_times'].append(log.execution_time_ms)

    # Analyze tools where we have both successful and failed timing data
    correlation_insights = []

    for tool_name, data in tool_performance.items():
        if (len(data['successful_times']) > 0 and len(data['failed_times']) > 0 and
            data['total_calls'] > 5):  # At least 5 calls for meaningful analysis

            success_avg = statistics.mean(data['successful_times'])
            failed_avg = statistics.mean(data['failed_times'])
            success_rate = data['successful_calls'] / data['total_calls']

            correlation_insights.append({
                'tool': tool_name,
                'success_avg_time': success_avg,
                'failed_avg_time': failed_avg,
                'success_rate': success_rate,
                'total_calls': data['total_calls'],
                'time_difference': failed_avg - success_avg
            })

    if correlation_insights:
        print("Performance Difference: Successful vs Failed Calls")
        print(f"{'Tool':<20} {'Success Rate':<12} {'Success Avg':<12} {'Failed Avg':<12} {'Difference':<12}")
        print("-" * 70)

        for insight in sorted(correlation_insights, key=lambda x: abs(x['time_difference']), reverse=True):
            diff_str = f"{insight['time_difference']:+.1f}ms"
            print(f"{insight['tool']:<20} "
                  f"{insight['success_rate']:<12.1%} "
                  f"{insight['success_avg_time']:<12.1f} "
                  f"{insight['failed_avg_time']:<12.1f} "
                  f"{diff_str:<12}")
    else:
        print("Insufficient data for correlation analysis")


def generate_performance_recommendations(perf_analysis, results):
    """Generate actionable performance optimization recommendations."""

    print("\n💡 Performance Optimization Recommendations:")
    print("-" * 50)

    recommendations = []

    # Identify slow tools
    if perf_analysis['slowest_tools']:
        slow_threshold = 1000  # 1 second
        slow_tools = [(tool, time) for tool, time in perf_analysis['slowest_tools'] if time > slow_threshold]

        if slow_tools:
            recommendations.append("🔴 HIGH PRIORITY - Optimize slow tools:")
            for tool, avg_time in slow_tools[:3]:  # Top 3 slowest
                recommendations.append(f"   • {tool}: {avg_time:.1f}ms average (consider caching, async operations, or algorithm optimization)")

    # Identify high-variance tools
    high_variance_threshold = 0.7  # Coefficient of variation > 0.7
    high_variance_tools = []

    for tool_name, stats in perf_analysis['execution_time_stats'].items():
        if stats['count'] > 1:
            cv = stats['std_dev'] / stats['mean'] if stats['mean'] > 0 else 0
            if cv > high_variance_threshold:
                high_variance_tools.append((tool_name, cv, stats['mean']))

    if high_variance_tools:
        recommendations.append("\n🟡 MEDIUM PRIORITY - Investigate inconsistent performance:")
        high_variance_tools.sort(key=lambda x: x[1], reverse=True)
        for tool, cv, mean_time in high_variance_tools[:3]:
            recommendations.append(f"   • {tool}: High variability (CV={cv:.2f}) - check for input-dependent performance")

    # Check for tools with many calls (potential optimization targets)
    high_usage_tools = [
        (tool, stats['count'], stats['mean'])
        for tool, stats in perf_analysis['execution_time_stats'].items()
        if stats['count'] > 20 and stats['mean'] > 200  # >20 calls and >200ms
    ]

    if high_usage_tools:
        recommendations.append("\n🟠 OPTIMIZATION OPPORTUNITY - High-usage tools:")
        high_usage_tools.sort(key=lambda x: x[1] * x[2], reverse=True)  # Sort by total time spent
        for tool, count, avg_time in high_usage_tools[:3]:
            total_time = count * avg_time
            recommendations.append(f"   • {tool}: {count} calls × {avg_time:.1f}ms = {total_time:.0f}ms total (high impact optimization target)")

    if not recommendations:
        recommendations.append("✅ Performance looks good! No major optimization opportunities identified.")

    # Additional general recommendations
    recommendations.extend([
        "\n📋 General Performance Tips:",
        "   • Monitor tools with >1000ms average execution time",
        "   • Consider caching for frequently called tools with stable inputs",
        "   • Use async/parallel execution for independent tool calls",
        "   • Profile individual tool implementations for bottlenecks"
    ])

    for rec in recommendations:
        print(rec)


def main():
    """Run detailed performance analysis on simulation results."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/performance_analysis.py <results_file.json>")
        print("\nExample:")
        print("  python scripts/performance_analysis.py data/simulations/my_results.json")
        sys.exit(1)

    results_file = Path(sys.argv[1])

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        # Load simulation results
        print(f"⚡ Analyzing performance in: {results_file}")
        results = Results.load(str(results_file))

        # Check if enhanced logging data is available
        enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
        if not enhanced_sims:
            print("❌ No enhanced logging data found in results!")
            print("Run simulations with --enhanced-logging flag to enable performance analysis")
            return

        print("=" * 80)

        # Run performance analysis
        perf_analysis = analyze_performance_bottlenecks(results)

        # Print analysis results
        print_performance_summary(perf_analysis)
        print_detailed_performance_stats(perf_analysis)
        analyze_performance_patterns(results)
        analyze_correlation_with_success(results)
        generate_performance_recommendations(perf_analysis, results)

        # Save detailed results to JSON file
        output_file = results_file.parent / f"{results_file.stem}_performance_analysis.json"
        analysis_data = {
            'file_analyzed': str(results_file),
            'analysis_timestamp': str(Path(__file__).stat().st_mtime),
            'performance_analysis': perf_analysis,
            'summary': {
                'total_simulations': len(results.simulations),
                'enhanced_simulations': len(enhanced_sims),
                'tools_analyzed': len(perf_analysis.get('execution_time_stats', {}))
            }
        }

        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)

        print(f"\n💾 Detailed performance data saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error analyzing performance: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()