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
from collections import defaultdict
from typing import Iterable

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results, SimulationRun
from tau2.metrics.execution_analysis import analyze_performance_bottlenecks


import io

def print_performance_summary(perf_analysis, file=None):
    """Print a summary of performance analysis."""

    print("🐌 Performance Analysis Summary:", file=file)
    print("-" * 40, file=file)

    if perf_analysis['slowest_tools']:
        print("Slowest Tools (Average Execution Time):", file=file)
        for i, (tool_name, avg_time) in enumerate(perf_analysis['slowest_tools'], 1):
            print(f"   {i:2d}. {tool_name}: {avg_time:8.1f}ms", file=file)
    else:
        print("No performance data available", file=file)

    print(file=file)


def print_detailed_performance_stats(perf_analysis, file=None):
    """Print detailed performance statistics for each tool."""

    if not perf_analysis['execution_time_stats']:
        print("No detailed performance statistics available", file=file)
        return

    print("🔧 Detailed Performance Statistics:", file=file)
    print("-" * 80, file=file)
    print(f"{ 'Tool Name':<25} {'Count':<8} {'Mean':<10} {'Median':<10} {'Min':<10} {'Max':<10} {'Std Dev':<10}", file=file)
    print("-" * 80, file=file)

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
              f"{stats['std_dev']:<10.1f}", file=file)


def analyze_performance_patterns(simulations: Iterable[SimulationRun], file=None):
    """Analyze performance patterns across simulations."""

    print("\n📊 Performance Pattern Analysis:", file=file)
    print("-" * 40, file=file)

    # Collect all execution times by tool
    tool_times = defaultdict(list)
    simulation_metrics = []

    for sim in simulations:
        if sim.enhanced_logging_enabled:
            sim_total_time = 0
            sim_tool_count = 0

            if sim.execution_logs:
                for log in sim.execution_logs:
                    if log.success and log.execution_time_ms is not None:
                        tool_times[log.tool_name].append(log.execution_time_ms)
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
        print("Performance by Simulation:", file=file)
        simulation_metrics.sort(key=lambda x: x['total_time'], reverse=True)

        print(f"{ 'Task ID':<12} {'Trial':<6} {'Total Time':<12} {'Tool Count':<11} {'Avg/Tool':<10} {'Reward':<8}", file=file)
        print("-" * 70, file=file)

        for metrics in simulation_metrics[:10]:  # Top 10 slowest
            print(f"{metrics['task_id']:<12} "
                  f"{metrics['trial'] or 'N/A':<6} "
                  f"{metrics['total_time']:<12.1f} "
                  f"{metrics['tool_count']:<11} "
                  f"{metrics['avg_time_per_tool']:<10.1f} "
                  f"{metrics['reward']:<8.3f}", file=file)

    # Tool variability analysis
    print(f"\nTool Performance Variability:", file=file)
    high_variance_tools = []

    for tool_name, times in tool_times.items():
        if len(times) > 1:
            mean_time = statistics.mean(times)
            std_dev = statistics.stdev(times)
            coefficient_of_variation = std_dev / mean_time if mean_time > 0 else 0
            if coefficient_of_variation > 0.5:
                high_variance_tools.append((tool_name, coefficient_of_variation, mean_time, std_dev, len(times)))

    if high_variance_tools:
        high_variance_tools.sort(key=lambda x: x[1], reverse=True)
        print("Tools with High Performance Variability:", file=file)
        for tool, cv, mean_time, std_dev, count in high_variance_tools[:5]:
            print(f"   {tool}: CV={cv:.2f}, Mean={mean_time:.1f}ms ± {std_dev:.1f}ms (n={count})", file=file)
    else:
        print("All tools show consistent performance", file=file)


def analyze_correlation_with_success(simulations: Iterable[SimulationRun], file=None):
    """Analyze correlation between execution time and success rates."""

    print(f"\n🎯 Performance vs Success Correlation:", file=file)
    print("-" * 40, file=file)

    tool_performance = defaultdict(lambda: {'successful_times': [], 'failed_times': [], 'total_calls': 0, 'successful_calls': 0})

    for sim in simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            for log in sim.execution_logs:
                tool_performance[log.tool_name]['total_calls'] += 1
                if log.success:
                    tool_performance[log.tool_name]['successful_calls'] += 1
                    if log.execution_time_ms is not None:
                        tool_performance[log.tool_name]['successful_times'].append(log.execution_time_ms)
                elif log.execution_time_ms is not None:
                    tool_performance[log.tool_name]['failed_times'].append(log.execution_time_ms)

    correlation_insights = []
    for tool_name, data in tool_performance.items():
        if len(data['successful_times']) > 0 and len(data['failed_times']) > 0 and data['total_calls'] > 5:
            success_avg = statistics.mean(data['successful_times'])
            failed_avg = statistics.mean(data['failed_times'])
            success_rate = data['successful_calls'] / data['total_calls']
            correlation_insights.append({
                'tool': tool_name, 'success_avg_time': success_avg, 'failed_avg_time': failed_avg,
                'success_rate': success_rate, 'total_calls': data['total_calls'],
                'time_difference': failed_avg - success_avg
            })

    if correlation_insights:
        print("Performance Difference: Successful vs Failed Calls", file=file)
        print(f"{ 'Tool':<20} {'Success Rate':<12} {'Success Avg':<12} {'Failed Avg':<12} {'Difference':<12}", file=file)
        print("-" * 70, file=file)
        for insight in sorted(correlation_insights, key=lambda x: abs(x['time_difference']), reverse=True):
            diff_str = f"{insight['time_difference']:+.1f}ms"
            print(f"{insight['tool']:<20} {insight['success_rate']:<12.1%} {insight['success_avg_time']:<12.1f} {insight['failed_avg_time']:<12.1f} {diff_str:<12}", file=file)
    else:
        print("Insufficient data for correlation analysis", file=file)


def generate_performance_recommendations(perf_analysis, file=None):
    """Generate actionable performance optimization recommendations."""

    print("\n💡 Performance Optimization Recommendations:", file=file)
    print("-" * 50, file=file)
    recommendations = []

    if perf_analysis['slowest_tools']:
        slow_tools = [(tool, time) for tool, time in perf_analysis['slowest_tools'] if time > 1000]
        if slow_tools:
            recommendations.append("🔴 HIGH PRIORITY - Optimize slow tools:")
            for tool, avg_time in slow_tools[:3]:
                recommendations.append(f"   • {tool}: {avg_time:.1f}ms average (consider caching, async operations, or algorithm optimization)")

    high_variance_tools = []
    for tool_name, stats in perf_analysis['execution_time_stats'].items():
        if stats['count'] > 1 and stats['mean'] > 0:
            cv = stats['std_dev'] / stats['mean']
            if cv > 0.7:
                high_variance_tools.append((tool_name, cv, stats['mean']))
    if high_variance_tools:
        recommendations.append("\n🟡 MEDIUM PRIORITY - Investigate inconsistent performance:")
        for tool, cv, mean_time in sorted(high_variance_tools, key=lambda x: x[1], reverse=True)[:3]:
            recommendations.append(f"   • {tool}: High variability (CV={cv:.2f}) - check for input-dependent performance")

    if not recommendations:
        recommendations.append("✅ Performance looks good! No major optimization opportunities identified.")
    recommendations.extend([
        "\n📋 General Performance Tips:", "   • Monitor tools with >1000ms average execution time",
        "   • Consider caching for frequently called tools with stable inputs",
        "   • Use async/parallel execution for independent tool calls",
        "   • Profile individual tool implementations for bottlenecks"
    ])
    for rec in recommendations:
        print(rec, file=file)


def main():
    """Run detailed performance analysis on simulation results."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/performance_analysis.py <results_file.json>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        print(f"⚡ Analyzing performance in: {results_file}")
        simulations_stream = Results.stream_simulations(results_file)
        
        # Since the stream is consumable only once, we must load it into memory if multiple functions need it,
        # or refactor the functions to work on the same stream pass.
        # For this script, we'll convert to a list to maintain script structure.
        # A more advanced version would integrate all analysis into a single loop.
        simulations_list = list(simulations_stream)
        
        if not any(s.enhanced_logging_enabled for s in simulations_list):
            print("❌ No enhanced logging data found in results!")
            return

        print("=" * 80)
        perf_analysis = analyze_performance_bottlenecks(simulations_list)
        
        report_buffer = io.StringIO()
        print_performance_summary(perf_analysis, file=report_buffer)
        print_detailed_performance_stats(perf_analysis, file=report_buffer)
        analyze_performance_patterns(simulations_list, file=report_buffer)
        analyze_correlation_with_success(simulations_list, file=report_buffer)
        generate_performance_recommendations(perf_analysis, file=report_buffer)
        
        report_content = report_buffer.getvalue()
        print(report_content)

        output_txt_file = results_file.parent / f"{results_file.stem}_performance_analysis.txt"
        output_txt_file.write_text(f"PERFORMANCE ANALYSIS REPORT\n{'='*40}\n\nResults file: {results_file}\n\n{report_content}")
        print(f"\n💾 Detailed performance report saved to: {output_txt_file}")

        output_json_file = results_file.parent / f"{results_file.stem}_performance_analysis.json"
        with open(output_json_file, 'w') as f:
            json.dump({
                'file_analyzed': str(results_file),
                'performance_analysis': perf_analysis,
            }, f, indent=2, default=str)
        print(f"💾 Detailed performance data saved to: {output_json_file}")

    except Exception as e:
        print(f"❌ Error analyzing performance: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
