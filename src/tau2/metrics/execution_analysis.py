"""
Execution Analysis Tools for Enhanced Logging Data

This module provides utilities for analyzing enhanced logging data from tau2-bench simulations.
"""

from typing import List, Dict, Any
from collections import defaultdict, Counter
import statistics

from tau2.data_model.simulation import Results, SimulationRun
from tau2.data_model.logging import ToolExecutionLog, EnvironmentStateSnapshot, ExecutionMetrics


def analyze_tool_failures(results: Results) -> Dict[str, Any]:
    """Analyze tool failure patterns across simulations."""
    analysis = {
        "total_simulations": len(results.simulations),
        "enhanced_logging_simulations": 0,
        "tool_failure_stats": {},
        "most_failing_tools": [],
        "failure_patterns": {}
    }

    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
    analysis["enhanced_logging_simulations"] = len(enhanced_sims)

    if not enhanced_sims:
        return analysis

    # Collect all tool execution logs
    all_logs = []
    for sim in enhanced_sims:
        if sim.execution_logs:
            all_logs.extend(sim.execution_logs)

    if not all_logs:
        return analysis

    # Analyze failure patterns
    tool_stats = defaultdict(lambda: {"total": 0, "failed": 0, "avg_time": []})
    error_patterns = Counter()

    for log in all_logs:
        tool_stats[log.tool_name]["total"] += 1
        if log.execution_time_ms:
            tool_stats[log.tool_name]["avg_time"].append(log.execution_time_ms)

        if not log.success:
            tool_stats[log.tool_name]["failed"] += 1
            if log.error_details:
                # Extract error type
                error_type = log.error_details.split(':')[0] if ':' in log.error_details else log.error_details[:50]
                error_patterns[error_type] += 1

    # Calculate failure rates and average times
    for tool_name, stats in tool_stats.items():
        stats["failure_rate"] = stats["failed"] / stats["total"] if stats["total"] > 0 else 0
        stats["avg_execution_time"] = statistics.mean(stats["avg_time"]) if stats["avg_time"] else 0

    analysis["tool_failure_stats"] = dict(tool_stats)

    # Find most failing tools
    failing_tools = [(name, stats["failure_rate"]) for name, stats in tool_stats.items()
                     if stats["failure_rate"] > 0]
    analysis["most_failing_tools"] = sorted(failing_tools, key=lambda x: x[1], reverse=True)[:5]

    # Common error patterns
    analysis["failure_patterns"] = dict(error_patterns.most_common(10))

    return analysis


def analyze_performance_bottlenecks(results: Results) -> Dict[str, Any]:
    """Identify performance bottlenecks in tool execution."""
    analysis = {
        "slowest_tools": [],
        "execution_time_stats": {},
        "performance_trends": {}
    }

    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
    if not enhanced_sims:
        return analysis

    # Collect execution times by tool
    tool_times = defaultdict(list)
    for sim in enhanced_sims:
        if sim.execution_logs:
            for log in sim.execution_logs:
                if log.execution_time_ms is not None and log.success:
                    tool_times[log.tool_name].append(log.execution_time_ms)

    # Calculate statistics for each tool
    for tool_name, times in tool_times.items():
        if times:
            analysis["execution_time_stats"][tool_name] = {
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "min": min(times),
                "max": max(times),
                "count": len(times)
            }

    # Find slowest tools
    if analysis["execution_time_stats"]:
        slowest = sorted(analysis["execution_time_stats"].items(),
                        key=lambda x: x[1]["mean"], reverse=True)[:5]
        analysis["slowest_tools"] = [(name, stats["mean"]) for name, stats in slowest]

    return analysis


def analyze_state_changes(results: Results) -> Dict[str, Any]:
    """Analyze environment state change patterns."""
    analysis = {
        "total_state_changes": 0,
        "changes_per_simulation": [],
        "change_triggers": Counter(),
        "simulations_with_changes": 0
    }

    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
    if not enhanced_sims:
        return analysis

    for sim in enhanced_sims:
        if sim.state_snapshots:
            changes_in_sim = sum(1 for snapshot in sim.state_snapshots if snapshot.state_changed)
            analysis["changes_per_simulation"].append(changes_in_sim)
            analysis["total_state_changes"] += changes_in_sim

            if changes_in_sim > 0:
                analysis["simulations_with_changes"] += 1

            # Track what triggered state changes
            for snapshot in sim.state_snapshots:
                if snapshot.state_changed:
                    analysis["change_triggers"][snapshot.triggered_by] += 1

    # Calculate statistics
    if analysis["changes_per_simulation"]:
        analysis["avg_changes_per_sim"] = statistics.mean(analysis["changes_per_simulation"])
        analysis["max_changes_per_sim"] = max(analysis["changes_per_simulation"])
    else:
        analysis["avg_changes_per_sim"] = 0
        analysis["max_changes_per_sim"] = 0

    analysis["change_triggers"] = dict(analysis["change_triggers"])

    return analysis


def generate_execution_report(results: Results) -> str:
    """Generate a comprehensive execution analysis report."""
    if not any(sim.enhanced_logging_enabled for sim in results.simulations):
        return "❌ No enhanced logging data found in results. Run simulations with --enhanced-logging flag."

    failure_analysis = analyze_tool_failures(results)
    performance_analysis = analyze_performance_bottlenecks(results)
    state_analysis = analyze_state_changes(results)

    report_lines = [
        "🔍 Enhanced Logging Analysis Report",
        "=" * 50,
        "",
        f"📊 Overview:",
        f"   • Total simulations: {failure_analysis['total_simulations']}",
        f"   • Enhanced logging enabled: {failure_analysis['enhanced_logging_simulations']}",
        ""
    ]

    # Tool failure analysis
    if failure_analysis["most_failing_tools"]:
        report_lines.extend([
            "❌ Tool Failure Analysis:",
            f"   • Most failing tools:"
        ])
        for tool_name, failure_rate in failure_analysis["most_failing_tools"]:
            report_lines.append(f"     - {tool_name}: {failure_rate:.1%} failure rate")

        if failure_analysis["failure_patterns"]:
            report_lines.extend([
                f"   • Common error patterns:"
            ])
            for error, count in list(failure_analysis["failure_patterns"].items())[:3]:
                report_lines.append(f"     - {error}: {count} occurrences")
    else:
        report_lines.append("✅ No tool failures detected!")

    report_lines.append("")

    # Performance analysis
    if performance_analysis["slowest_tools"]:
        report_lines.extend([
            "🐌 Performance Bottlenecks:",
            f"   • Slowest tools (average execution time):"
        ])
        for tool_name, avg_time in performance_analysis["slowest_tools"]:
            report_lines.append(f"     - {tool_name}: {avg_time:.1f}ms")

    report_lines.append("")

    # State change analysis
    report_lines.extend([
        "🔄 Environment State Changes:",
        f"   • Total state changes: {state_analysis['total_state_changes']}",
        f"   • Simulations with changes: {state_analysis['simulations_with_changes']}",
        f"   • Average changes per simulation: {state_analysis['avg_changes_per_sim']:.1f}"
    ])

    if state_analysis["change_triggers"]:
        report_lines.extend([
            f"   • Most common triggers:"
        ])
        sorted_triggers = sorted(state_analysis["change_triggers"].items(),
                               key=lambda x: x[1], reverse=True)[:3]
        for trigger, count in sorted_triggers:
            report_lines.append(f"     - {trigger}: {count} times")

    report_lines.extend([
        "",
        "💡 Tips:",
        "   • Use this data to identify which tools need optimization",
        "   • High failure rates may indicate validation issues",
        "   • Slow tools could benefit from performance improvements",
        "   • Monitor state changes to understand system behavior"
    ])

    return "\n".join(report_lines)