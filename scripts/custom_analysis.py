#!/usr/bin/env python3
"""
Custom Analysis Script - Advanced Examples

This script demonstrates custom analysis patterns using the enhanced logging data
from tau2-bench simulations. Use this as a template for your own analysis needs.

Usage:
    python scripts/custom_analysis.py <results_file.json>
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict
import statistics
import json
from typing import List

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results, SimulationRun


import io

def find_timeout_patterns(simulations: List[SimulationRun], file=None):
    """Find timeout-related issues and patterns."""

    print("⏰ Timeout Pattern Analysis:", file=file)
    print("-" * 30, file=file)

    timeouts = []

    for sim in simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            for log in sim.execution_logs:
                if log.error_details and 'timeout' in log.error_details.lower():
                    timeouts.append({
                        'task_id': sim.task_id,
                        'trial': sim.trial,
                        'tool_name': log.tool_name,
                        'requestor': log.requestor,
                        'execution_time': log.execution_time_ms,
                        'arguments': log.arguments,
                        'error': log.error_details
                    })

    if not timeouts:
        print("✅ No timeout issues found", file=file)
        return []

    print(f"Found {len(timeouts)} timeout-related issues:", file=file)

    # Analyze by tool
    timeout_by_tool = Counter(issue['tool_name'] for issue in timeouts)
    print(f"\nTimeouts by tool:", file=file)
    for tool, count in timeout_by_tool.most_common():
        print(f"   {tool}: {count} timeouts", file=file)

    return timeouts


def analyze_tool_usage_patterns(simulations: List[SimulationRun], file=None):
    """Analyze which tools are used together frequently."""

    print("\n🔗 Tool Usage Pattern Analysis:", file=file)
    print("-" * 35, file=file)

    tool_pairs = []

    for sim in simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            successful_tools = [log.tool_name for log in sim.execution_logs if log.success]
            if len(successful_tools) > 1:
                for i in range(len(successful_tools) - 1):
                    tool_pairs.append((successful_tools[i], successful_tools[i + 1]))

    if not tool_pairs:
        print("No tool usage patterns found", file=file)
        return []

    common_pairs = Counter(tool_pairs).most_common(10)
    print("Most Common Tool Sequences (Tool A → Tool B):", file=file)
    for (tool_a, tool_b), count in common_pairs:
        print(f"   {tool_a} → {tool_b}: {count} times", file=file)

    return common_pairs


def compare_simulation_performance(simulations: List[SimulationRun], file=None):
    """Compare performance metrics across different simulations."""

    print("\n🏁 Simulation Performance Comparison:", file=file)
    print("-" * 40, file=file)

    simulation_metrics = []
    for sim in simulations:
        if sim.enhanced_logging_enabled and sim.execution_metrics:
            metrics = {
                'task_id': sim.task_id,
                'trial': sim.trial or 0,
                'failure_rate': sim.execution_metrics.failed_tool_calls / sim.execution_metrics.total_tool_calls if sim.execution_metrics.total_tool_calls > 0 else 0,
                'avg_time': sim.execution_metrics.average_execution_time_ms,
                'reward': sim.reward_info.reward if sim.reward_info else 0,
            }
            simulation_metrics.append(metrics)

    if not simulation_metrics:
        print("No simulation metrics available", file=file)
        return []

    # Sort by performance
    simulation_metrics.sort(key=lambda m: (m['failure_rate'], m['avg_time'], -m['reward']))

    print("Top Performing Simulations:", file=file)
    for metrics in simulation_metrics[:10]:
        print(f"  Task {metrics['task_id']} (Trial {metrics['trial']}): Fail rate {metrics['failure_rate']:.1%}, Avg time {metrics['avg_time']:.1f}ms, Reward {metrics['reward']:.2f}", file=file)

    return simulation_metrics


def main():
    """Run comprehensive custom analysis on simulation results."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/custom_analysis.py <results_file.json>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        print(f"🔍 Running custom analysis on: {results_file}")
        simulations = list(Results.stream_simulations(results_file))

        if not any(sim.enhanced_logging_enabled for sim in simulations):
            print("❌ No enhanced logging data found in results!")
            return

        print("=" * 80)
        report_buffer = io.StringIO()

        # Run all custom analyses
        find_timeout_patterns(simulations, file=report_buffer)
        analyze_tool_usage_patterns(simulations, file=report_buffer)
        compare_simulation_performance(simulations, file=report_buffer)

        report_content = report_buffer.getvalue()
        print(report_content)

        output_txt_file = results_file.parent / f"{results_file.stem}_custom_analysis.txt"
        output_txt_file.write_text(report_content)
        print(f"\n💾 Custom analysis report saved to: {output_txt_file}")

    except Exception as e:
        print(f"❌ Error running custom analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
