"""
Execution Analysis Tools for Enhanced Logging Data

This module provides utilities for analyzing enhanced logging data from tau2-bench simulations.
"""

from typing import List, Dict, Any
from collections import defaultdict, Counter
import statistics

from tau2.data_model.simulation import Results, SimulationRun
from tau2.data_model.logging import ToolExecutionLog, EnvironmentStateSnapshot, ExecutionMetrics, ContextUsageSnapshot


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
        "simulations_with_changes": 0,
        "db_changes_summary": {},
        "most_common_db_changes": []
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

            # Track what triggered state changes and analyze db diffs
            for snapshot in sim.state_snapshots:
                if snapshot.state_changed:
                    analysis["change_triggers"][snapshot.triggered_by] += 1

                    # Analyze database diffs if available
                    if hasattr(snapshot, 'db_diff') and snapshot.db_diff:
                        db_diff = snapshot.db_diff
                        for change_type in ['added', 'modified', 'removed']:
                            if db_diff.get(change_type):
                                for key in db_diff[change_type].keys():
                                    change_key = f"{change_type}:{key}"
                                    if change_key not in analysis["db_changes_summary"]:
                                        analysis["db_changes_summary"][change_key] = 0
                                    analysis["db_changes_summary"][change_key] += 1

    # Calculate statistics
    if analysis["changes_per_simulation"]:
        analysis["avg_changes_per_sim"] = statistics.mean(analysis["changes_per_simulation"])
        analysis["max_changes_per_sim"] = max(analysis["changes_per_simulation"])
    else:
        analysis["avg_changes_per_sim"] = 0
        analysis["max_changes_per_sim"] = 0

    analysis["change_triggers"] = dict(analysis["change_triggers"])

    # Find most common database changes
    if analysis["db_changes_summary"]:
        analysis["most_common_db_changes"] = sorted(
            analysis["db_changes_summary"].items(),
            key=lambda x: x[1], reverse=True
        )[:5]  # Top 5 most common changes

    return analysis


def analyze_context_usage(results: Results) -> Dict[str, Any]:
    """Analyze context/token usage patterns across simulations."""
    analysis = {
        "total_snapshots": 0,
        "token_usage_stats": {},
        "context_window_usage": {},
        "high_usage_warnings": 0,
        "models_analyzed": set(),
        "usage_by_trigger": {}
    }

    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
    if not enhanced_sims:
        return analysis

    all_snapshots = []
    for sim in enhanced_sims:
        if sim.context_usage_snapshots:
            all_snapshots.extend(sim.context_usage_snapshots)

    analysis["total_snapshots"] = len(all_snapshots)

    if not all_snapshots:
        return analysis

    # Collect token usage stats
    prompt_tokens = [s.prompt_tokens for s in all_snapshots]
    completion_tokens = [s.completion_tokens for s in all_snapshots]
    total_tokens = [s.total_tokens for s in all_snapshots]

    if prompt_tokens:
        analysis["token_usage_stats"] = {
            "prompt_tokens": {
                "total": sum(prompt_tokens),
                "mean": statistics.mean(prompt_tokens),
                "max": max(prompt_tokens),
                "min": min(prompt_tokens)
            },
            "completion_tokens": {
                "total": sum(completion_tokens),
                "mean": statistics.mean(completion_tokens),
                "max": max(completion_tokens),
                "min": min(completion_tokens)
            },
            "total_tokens": {
                "total": sum(total_tokens),
                "mean": statistics.mean(total_tokens),
                "max": max(total_tokens),
                "min": min(total_tokens)
            }
        }

    # Analyze context window usage
    context_usages = [s.context_window_used for s in all_snapshots if s.context_window_used is not None]
    if context_usages:
        analysis["context_window_usage"] = {
            "mean_usage": statistics.mean(context_usages),
            "max_usage": max(context_usages),
            "min_usage": min(context_usages),
            "high_usage_count": sum(1 for usage in context_usages if usage > 80.0)
        }
        analysis["high_usage_warnings"] = analysis["context_window_usage"]["high_usage_count"]

    # Track models analyzed
    models = set()
    for s in all_snapshots:
        if hasattr(s, 'model_context_limit') and s.model_context_limit:
            # Try to extract model name from limit mapping
            model_limits = {
                8192: "gpt-4",
                128000: "gpt-4o/gpt-4o-mini",
                200000: "claude-3",
                16385: "gpt-3.5-turbo"
            }
            if s.model_context_limit in model_limits:
                models.add(model_limits[s.model_context_limit])
    analysis["models_analyzed"] = list(models)

    # Analyze usage by trigger
    trigger_stats = defaultdict(lambda: {"count": 0, "total_tokens": 0, "avg_tokens": 0})
    for s in all_snapshots:
        trigger_stats[s.triggered_by]["count"] += 1
        trigger_stats[s.triggered_by]["total_tokens"] += s.total_tokens

    for trigger, stats in trigger_stats.items():
        stats["avg_tokens"] = stats["total_tokens"] / stats["count"] if stats["count"] > 0 else 0

    analysis["usage_by_trigger"] = dict(trigger_stats)

    return analysis


def analyze_database_diffs(results: Results) -> Dict[str, Any]:
    """Analyze detailed database diff patterns across simulations."""
    analysis = {
        "snapshots_with_diffs": 0,
        "total_db_changes": 0,
        "detailed_changes": [],
        "change_patterns": {},
        "fields_changed_most": Counter(),
        "change_types_distribution": Counter()
    }

    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
    if not enhanced_sims:
        return analysis

    for sim in enhanced_sims:
        if sim.state_snapshots:
            for snapshot in sim.state_snapshots:
                if hasattr(snapshot, 'db_diff') and snapshot.db_diff:
                    analysis["snapshots_with_diffs"] += 1
                    db_diff = snapshot.db_diff

                    change_summary = {
                        "simulation_id": sim.id,
                        "step_idx": snapshot.step_idx,
                        "triggered_by": snapshot.triggered_by,
                        "timestamp": snapshot.timestamp,
                        "changes": db_diff
                    }
                    analysis["detailed_changes"].append(change_summary)

                    # Analyze change patterns
                    for change_type in ['added', 'modified', 'removed']:
                        if db_diff.get(change_type):
                            analysis["change_types_distribution"][change_type] += len(db_diff[change_type])
                            analysis["total_db_changes"] += len(db_diff[change_type])

                            for field_name in db_diff[change_type].keys():
                                analysis["fields_changed_most"][field_name] += 1

    return analysis


def generate_execution_report(results: Results) -> str:
    """Generate a comprehensive execution analysis report."""
    if not any(sim.enhanced_logging_enabled for sim in results.simulations):
        return "❌ No enhanced logging data found in results. Run simulations with --enhanced-logging flag."

    failure_analysis = analyze_tool_failures(results)
    performance_analysis = analyze_performance_bottlenecks(results)
    state_analysis = analyze_state_changes(results)
    context_analysis = analyze_context_usage(results)

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

    # Database changes analysis
    if state_analysis["most_common_db_changes"]:
        report_lines.extend([
            f"   • Most common database changes:"
        ])
        for change_desc, count in state_analysis["most_common_db_changes"][:3]:
            change_type, field = change_desc.split(':', 1)
            report_lines.append(f"     - {field} ({change_type}): {count} times")

    report_lines.append("")

    # Context usage analysis
    if context_analysis["total_snapshots"] > 0:
        report_lines.extend([
            "📊 Context/Token Usage Analysis:",
            f"   • Total context snapshots: {context_analysis['total_snapshots']}"
        ])

        if context_analysis["token_usage_stats"]:
            token_stats = context_analysis["token_usage_stats"]
            report_lines.extend([
                f"   • Token usage:",
                f"     - Total tokens used: {token_stats['total_tokens']['total']:,}",
                f"     - Average tokens per call: {token_stats['total_tokens']['mean']:.1f}",
                f"     - Max tokens in single call: {token_stats['total_tokens']['max']:,}"
            ])

        if context_analysis["context_window_usage"]:
            ctx_stats = context_analysis["context_window_usage"]
            report_lines.extend([
                f"   • Context window utilization:",
                f"     - Average usage: {ctx_stats['mean_usage']:.1f}%",
                f"     - Peak usage: {ctx_stats['max_usage']:.1f}%"
            ])

            if context_analysis["high_usage_warnings"] > 0:
                report_lines.append(f"     - ⚠️  High usage warnings (>80%): {context_analysis['high_usage_warnings']}")

        if context_analysis["models_analyzed"]:
            models_str = ", ".join(context_analysis["models_analyzed"])
            report_lines.append(f"   • Models analyzed: {models_str}")

        if context_analysis["usage_by_trigger"]:
            report_lines.append(f"   • Usage by trigger:")
            sorted_triggers = sorted(context_analysis["usage_by_trigger"].items(),
                                   key=lambda x: x[1]["avg_tokens"], reverse=True)[:3]
            for trigger, stats in sorted_triggers:
                report_lines.append(f"     - {trigger}: {stats['avg_tokens']:.0f} avg tokens ({stats['count']} calls)")
    else:
        report_lines.append("📊 No context usage data available")

    report_lines.extend([
        "",
        "💡 Tips:",
        "   • Use this data to identify which tools need optimization",
        "   • High failure rates may indicate validation issues",
        "   • Slow tools could benefit from performance improvements",
        "   • Monitor state changes to understand system behavior",
        "   • Watch context usage to avoid hitting model limits",
        "   • High token usage may indicate inefficient prompts"
    ])

    return "\n".join(report_lines)