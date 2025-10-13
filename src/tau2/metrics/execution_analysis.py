"""
Execution Analysis Tools for Enhanced Logging Data

This module provides utilities for analyzing enhanced logging data from tau2-bench simulations.
All analysis functions are designed to work with streams of simulations to keep memory usage low.
"""

from typing import Dict, Any, Iterable
from collections import defaultdict, Counter
import statistics

from tau2.data_model.simulation import SimulationRun


def run_streaming_analysis(simulations: Iterable[SimulationRun]) -> Dict[str, Any]:
    """
    Run a comprehensive analysis by streaming simulations. This is the core
    function that processes simulations in a single pass to generate all metrics.
    """
    # Initialize accumulators
    total_simulations = 0
    enhanced_logging_simulations = 0
    
    # Tool failure stats
    tool_stats = defaultdict(lambda: {"total": 0, "failed": 0, "avg_time": []})
    error_patterns = Counter()

    # Performance stats
    tool_times = defaultdict(list)

    # State change stats
    total_state_changes = 0
    changes_per_simulation = []
    change_triggers = Counter()
    simulations_with_changes = 0
    db_changes_summary = Counter()

    # Context usage stats
    total_snapshots = 0
    prompt_tokens, completion_tokens, total_tokens = [], [], []
    context_usages = []
    models_analyzed = set()
    usage_by_trigger = defaultdict(lambda: {"count": 0, "total_tokens": 0})

    # Single pass over the simulation stream
    for sim in simulations:
        total_simulations += 1
        if not sim.enhanced_logging_enabled:
            continue
        enhanced_logging_simulations += 1

        # Tool failures and performance
        if sim.execution_logs:
            for log in sim.execution_logs:
                tool_stats[log.tool_name]["total"] += 1
                if log.execution_time_ms is not None:
                    tool_stats[log.tool_name]["avg_time"].append(log.execution_time_ms)
                    if log.success:
                        tool_times[log.tool_name].append(log.execution_time_ms)
                if not log.success:
                    tool_stats[log.tool_name]["failed"] += 1
                    if log.error_details:
                        error_type = log.error_details.split(':')[0] if ':' in log.error_details else log.error_details[:50]
                        error_patterns[error_type] += 1
        
        # State changes
        changes_in_sim = 0
        if sim.state_snapshots:
            changes_in_sim = sum(1 for s in sim.state_snapshots if s.state_changed)
            if changes_in_sim > 0:
                simulations_with_changes += 1
                total_state_changes += changes_in_sim
                for s in sim.state_snapshots:
                    if s.state_changed:
                        change_triggers[s.triggered_by] += 1
                        if hasattr(s, 'db_diff') and s.db_diff:
                            for change_type, changes in s.db_diff.items():
                                if changes:
                                    for key in changes.keys():
                                        db_changes_summary[f"{change_type}:{key}"] += 1
        changes_per_simulation.append(changes_in_sim)
        
        # Context usage
        if sim.context_usage_snapshots:
            total_snapshots += len(sim.context_usage_snapshots)
            for s in sim.context_usage_snapshots:
                prompt_tokens.append(s.prompt_tokens)
                completion_tokens.append(s.completion_tokens)
                total_tokens.append(s.total_tokens)
                if s.context_window_used is not None:
                    context_usages.append(s.context_window_used)
                if hasattr(s, 'model_context_limit') and s.model_context_limit:
                    model_limits = { 8192: "gpt-4", 128000: "gpt-4o/gpt-4o-mini", 200000: "claude-3", 16385: "gpt-3.5-turbo" }
                    if s.model_context_limit in model_limits:
                        models_analyzed.add(model_limits[s.model_context_limit])
                usage_by_trigger[s.triggered_by]["count"] += 1
                usage_by_trigger[s.triggered_by]["total_tokens"] += s.total_tokens

    # Finalize calculations
    for stats in tool_stats.values():
        stats["failure_rate"] = stats["failed"] / stats["total"] if stats["total"] > 0 else 0
        stats["avg_execution_time"] = statistics.mean(stats["avg_time"]) if stats["avg_time"] else 0
    
    execution_time_stats = {}
    for tool_name, times in tool_times.items():
        if times:
            execution_time_stats[tool_name] = {
                "mean": statistics.mean(times), "median": statistics.median(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "min": min(times), "max": max(times), "count": len(times)
            }

    for trigger, stats in usage_by_trigger.items():
        stats["avg_tokens"] = stats["total_tokens"] / stats["count"] if stats["count"] > 0 else 0

    # Assemble analysis dictionaries
    failure_analysis = {
        "total_simulations": total_simulations,
        "enhanced_logging_simulations": enhanced_logging_simulations,
        "tool_failure_stats": dict(tool_stats),
        "most_failing_tools": sorted([(name, stats["failure_rate"]) for name, stats in tool_stats.items() if stats["failure_rate"] > 0], key=lambda x: x[1], reverse=True)[:5],
        "failure_patterns": dict(error_patterns.most_common(10))
    }

    performance_analysis = {
        "slowest_tools": [(name, stats["mean"]) for name, stats in sorted(execution_time_stats.items(), key=lambda x: x[1]["mean"], reverse=True)[:5]],
        "execution_time_stats": execution_time_stats
    }

    state_analysis = {
        "total_state_changes": total_state_changes,
        "changes_per_simulation": changes_per_simulation,
        "change_triggers": dict(change_triggers),
        "simulations_with_changes": simulations_with_changes,
        "db_changes_summary": dict(db_changes_summary),
        "most_common_db_changes": db_changes_summary.most_common(5),
        "avg_changes_per_sim": statistics.mean(changes_per_simulation) if changes_per_simulation else 0,
        "max_changes_per_sim": max(changes_per_simulation) if changes_per_simulation else 0
    }

    context_analysis = {
        "total_snapshots": total_snapshots,
        "token_usage_stats": {
            "prompt_tokens": {"total": sum(prompt_tokens), "mean": statistics.mean(prompt_tokens), "max": max(prompt_tokens), "min": min(prompt_tokens)} if prompt_tokens else {},
            "completion_tokens": {"total": sum(completion_tokens), "mean": statistics.mean(completion_tokens), "max": max(completion_tokens), "min": min(completion_tokens)} if completion_tokens else {},
            "total_tokens": {"total": sum(total_tokens), "mean": statistics.mean(total_tokens), "max": max(total_tokens), "min": min(total_tokens)} if total_tokens else {}
        },
        "context_window_usage": {"mean_usage": statistics.mean(context_usages), "max_usage": max(context_usages), "min_usage": min(context_usages), "high_usage_count": sum(1 for u in context_usages if u > 80.0)} if context_usages else {},
        "high_usage_warnings": sum(1 for u in context_usages if u > 80.0),
        "models_analyzed": list(models_analyzed),
        "usage_by_trigger": dict(usage_by_trigger)
    }

    return {
        "overview": {"total_simulations": total_simulations, "enhanced_logging_simulations": enhanced_logging_simulations},
        "failure_analysis": failure_analysis,
        "performance_analysis": performance_analysis,
        "state_analysis": state_analysis,
        "context_analysis": context_analysis
    }


def analyze_tool_failures(simulations: Iterable[SimulationRun]) -> Dict[str, Any]:
    """Analyze tool failure patterns from a stream of simulations."""
    return run_streaming_analysis(simulations)["failure_analysis"]


def analyze_performance_bottlenecks(simulations: Iterable[SimulationRun]) -> Dict[str, Any]:
    """Identify performance bottlenecks from a stream of simulations."""
    return run_streaming_analysis(simulations)["performance_analysis"]


def analyze_state_changes(simulations: Iterable[SimulationRun]) -> Dict[str, Any]:
    """Analyze environment state change patterns from a stream of simulations."""
    return run_streaming_analysis(simulations)["state_analysis"]


def generate_execution_report(simulations: Iterable[SimulationRun]) -> str:
    """Generate a comprehensive execution analysis report from a stream of simulations."""
    
    all_analyses = run_streaming_analysis(simulations)
    overview = all_analyses["overview"]
    failure_analysis = all_analyses["failure_analysis"]
    performance_analysis = all_analyses["performance_analysis"]
    state_analysis = all_analyses["state_analysis"]
    context_analysis = all_analyses["context_analysis"]

    if overview['enhanced_logging_simulations'] == 0:
        return "❌ No enhanced logging data found in results. Run simulations with --enhanced-logging flag."

    report_lines = [
        "🔍 Enhanced Logging Analysis Report", "=" * 50, "",
        f"📊 Overview:",
        f"   • Total simulations: {overview['total_simulations']}",
        f"   • Enhanced logging enabled: {overview['enhanced_logging_simulations']}", ""
    ]

    # Tool failure analysis
    if failure_analysis["most_failing_tools"]:
        report_lines.extend(["❌ Tool Failure Analysis:", "   • Most failing tools:"])
        for tool_name, failure_rate in failure_analysis["most_failing_tools"]:
            report_lines.append(f"     - {tool_name}: {failure_rate:.1%} failure rate")
        if failure_analysis["failure_patterns"]:
            report_lines.append("   • Common error patterns:")
            for error, count in list(failure_analysis["failure_patterns"].items())[:3]:
                report_lines.append(f"     - {error}: {count} occurrences")
    else:
        report_lines.append("✅ No tool failures detected!")
    report_lines.append("")

    # Performance analysis
    if performance_analysis["slowest_tools"]:
        report_lines.extend(["🐌 Performance Bottlenecks:", "   • Slowest tools (average execution time):"])
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
        report_lines.append("   • Most common triggers:")
        for trigger, count in sorted(state_analysis["change_triggers"].items(), key=lambda x: x[1], reverse=True)[:3]:
            report_lines.append(f"     - {trigger}: {count} times")
    if state_analysis["most_common_db_changes"]:
        report_lines.append("   • Most common database changes:")
        for change_desc, count in state_analysis["most_common_db_changes"][:3]:
            change_type, field = change_desc.split(':', 1)
            report_lines.append(f"     - {field} ({change_type}): {count} times")
    report_lines.append("")

    # Context usage analysis
    if context_analysis["total_snapshots"] > 0:
        report_lines.extend(["📊 Context/Token Usage Analysis:", f"   • Total context snapshots: {context_analysis['total_snapshots']}"])
        if context_analysis["token_usage_stats"].get("total_tokens"):
            token_stats = context_analysis["token_usage_stats"]["total_tokens"]
            report_lines.extend([
                f"   • Token usage:",
                f"     - Total tokens used: {token_stats['total']:,}",
                f"     - Average tokens per call: {token_stats['mean']:.1f}",
                f"     - Max tokens in single call: {token_stats['max']:,}"
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
            report_lines.append(f"   • Models analyzed: {', '.join(context_analysis['models_analyzed'])}")
        if context_analysis["usage_by_trigger"]:
            report_lines.append(f"   • Usage by trigger:")
            sorted_triggers = sorted(context_analysis["usage_by_trigger"].items(), key=lambda x: x[1]["avg_tokens"], reverse=True)[:3]
            for trigger, stats in sorted_triggers:
                report_lines.append(f"     - {trigger}: {stats['avg_tokens']:.0f} avg tokens ({stats['count']} calls)")
    else:
        report_lines.append("📊 No context usage data available")

    report_lines.extend([
        "", "💡 Tips:",
        "   • Use this data to identify which tools need optimization",
        "   • High failure rates may indicate validation issues",
        "   • Slow tools could benefit from performance improvements",
        "   • Monitor state changes to understand system behavior",
        "   • Watch context usage to avoid hitting model limits",
        "   • High token usage may indicate inefficient prompts"
    ])

    return "\n".join(report_lines)