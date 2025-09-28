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

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results


def find_timeout_patterns(results):
    """Find timeout-related issues and patterns."""

    print("⏰ Timeout Pattern Analysis:")
    print("-" * 30)

    timeouts = []

    for sim in results.simulations:
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
        print("✅ No timeout issues found")
        return []

    print(f"Found {len(timeouts)} timeout-related issues:")

    # Analyze by tool
    timeout_by_tool = Counter(issue['tool_name'] for issue in timeouts)
    print(f"\nTimeouts by tool:")
    for tool, count in timeout_by_tool.most_common():
        print(f"   {tool}: {count} timeouts")

    # Analyze by arguments (common patterns)
    print(f"\nTimeout examples:")
    for i, issue in enumerate(timeouts[:5], 1):
        args_preview = str(issue['arguments'])[:100]
        print(f"   {i}. Task {issue['task_id']}: {issue['tool_name']} - {issue['error']}")
        print(f"      Args: {args_preview}")

    return timeouts


def analyze_tool_usage_patterns(results):
    """Analyze which tools are used together frequently."""

    print("\n🔗 Tool Usage Pattern Analysis:")
    print("-" * 35)

    tool_sequences = []
    tool_pairs = []

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            # Get sequence of successful tool calls
            successful_tools = [log.tool_name for log in sim.execution_logs if log.success]

            if len(successful_tools) > 1:
                tool_sequences.append({
                    'task_id': sim.task_id,
                    'sequence': successful_tools
                })

                # Extract tool pairs (bigrams)
                for i in range(len(successful_tools) - 1):
                    pair = (successful_tools[i], successful_tools[i + 1])
                    tool_pairs.append(pair)

    if not tool_pairs:
        print("No tool usage patterns found")
        return

    # Most common tool pairs
    common_pairs = Counter(tool_pairs).most_common(10)

    print("Most Common Tool Sequences (Tool A → Tool B):")
    for (tool_a, tool_b), count in common_pairs:
        print(f"   {tool_a} → {tool_b}: {count} times")

    # Analyze sequence lengths
    if tool_sequences:
        sequence_lengths = [len(seq['sequence']) for seq in tool_sequences]
        avg_length = statistics.mean(sequence_lengths)
        print(f"\nSequence Statistics:")
        print(f"   Average tools per simulation: {avg_length:.1f}")
        print(f"   Longest sequence: {max(sequence_lengths)} tools")
        print(f"   Shortest sequence: {min(sequence_lengths)} tools")

    return common_pairs


def compare_simulation_performance(results):
    """Compare performance metrics across different simulations."""

    print("\n🏁 Simulation Performance Comparison:")
    print("-" * 40)

    simulation_metrics = []

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.execution_metrics:
            metrics = {
                'task_id': sim.task_id,
                'trial': sim.trial or 0,
                'total_calls': sim.execution_metrics.total_tool_calls,
                'failed_calls': sim.execution_metrics.failed_tool_calls,
                'failure_rate': sim.execution_metrics.failed_tool_calls / sim.execution_metrics.total_tool_calls if sim.execution_metrics.total_tool_calls > 0 else 0,
                'total_time': sim.execution_metrics.total_execution_time_ms,
                'avg_time': sim.execution_metrics.average_execution_time_ms,
                'state_changes': sim.execution_metrics.state_changes,
                'reward': sim.reward_info.reward if sim.reward_info else 0,
                'termination_reason': sim.termination_reason
            }
            simulation_metrics.append(metrics)

    if not simulation_metrics:
        print("No simulation metrics available")
        return []

    # Sort by composite performance score (lower failure rate + faster time + higher reward)
    def performance_score(m):
        # Lower is better: normalize and combine metrics
        failure_penalty = m['failure_rate'] * 100  # 0-100
        time_penalty = min(m['avg_time'] / 1000, 10)  # 0-10 (cap at 10 seconds)
        reward_bonus = m['reward'] * 10  # Boost for higher rewards
        return failure_penalty + time_penalty - reward_bonus

    simulation_metrics.sort(key=performance_score)

    print("Top Performing Simulations:")
    print(f"{'Rank':<5} {'Task ID':<12} {'Trial':<6} {'Calls':<6} {'Failures':<9} {'Avg Time':<10} {'Reward':<8} {'Reason'}")
    print("-" * 80)

    for i, metrics in enumerate(simulation_metrics[:10], 1):  # Top 10
        print(f"{i:<5} "
              f"{metrics['task_id']:<12} "
              f"{metrics['trial']:<6} "
              f"{metrics['total_calls']:<6} "
              f"{metrics['failure_rate']:<9.1%} "
              f"{metrics['avg_time']:<10.1f} "
              f"{metrics['reward']:<8.3f} "
              f"{metrics['termination_reason']}")

    # Performance statistics
    if len(simulation_metrics) > 1:
        failure_rates = [m['failure_rate'] for m in simulation_metrics]
        avg_times = [m['avg_time'] for m in simulation_metrics]
        rewards = [m['reward'] for m in simulation_metrics]

        print(f"\nPerformance Statistics:")
        print(f"   Failure rate: {statistics.mean(failure_rates):.1%} ± {statistics.stdev(failure_rates) if len(failure_rates) > 1 else 0:.1%}")
        print(f"   Execution time: {statistics.mean(avg_times):.1f}ms ± {statistics.stdev(avg_times) if len(avg_times) > 1 else 0:.1f}ms")
        print(f"   Reward: {statistics.mean(rewards):.3f} ± {statistics.stdev(rewards) if len(rewards) > 1 else 0:.3f}")

    return simulation_metrics


def analyze_error_patterns(results):
    """Deep dive into error patterns and correlations."""

    print("\n🐛 Error Pattern Deep Dive:")
    print("-" * 30)

    error_analysis = {
        'by_tool': defaultdict(list),
        'by_requestor': defaultdict(list),
        'by_task': defaultdict(list),
        'by_arguments': defaultdict(list)
    }

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.execution_logs:
            for log in sim.execution_logs:
                if not log.success and log.error_details:
                    error_info = {
                        'task_id': sim.task_id,
                        'tool_name': log.tool_name,
                        'requestor': log.requestor,
                        'error_details': log.error_details,
                        'arguments': log.arguments,
                        'execution_time': log.execution_time_ms
                    }

                    error_analysis['by_tool'][log.tool_name].append(error_info)
                    error_analysis['by_requestor'][log.requestor].append(error_info)
                    error_analysis['by_task'][sim.task_id].append(error_info)

                    # Group similar argument patterns
                    arg_keys = tuple(sorted(log.arguments.keys())) if log.arguments else ()
                    error_analysis['by_arguments'][arg_keys].append(error_info)

    # Analysis results
    total_errors = sum(len(errors) for errors in error_analysis['by_tool'].values())
    if total_errors == 0:
        print("✅ No errors found")
        return

    print(f"Total errors analyzed: {total_errors}")

    # Error frequency by tool
    print(f"\nError frequency by tool:")
    tool_errors = [(tool, len(errors)) for tool, errors in error_analysis['by_tool'].items()]
    for tool, count in sorted(tool_errors, key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {tool}: {count} errors")

    # Common error messages
    all_errors = []
    for errors in error_analysis['by_tool'].values():
        all_errors.extend([e['error_details'] for e in errors])

    # Group similar error messages
    error_types = defaultdict(int)
    for error in all_errors:
        # Extract error type (first 50 characters or up to first colon)
        error_key = error.split(':')[0][:50] if ':' in error else error[:50]
        error_types[error_key] += 1

    print(f"\nMost common error types:")
    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = count / total_errors * 100
        print(f"   {error_type}: {count} ({percentage:.1f}%)")

    # Task-specific error patterns
    task_with_most_errors = max(error_analysis['by_task'].items(), key=lambda x: len(x[1]))
    print(f"\nTask with most errors: {task_with_most_errors[0]} ({len(task_with_most_errors[1])} errors)")

    return error_analysis


def analyze_success_factors(results):
    """Identify factors that correlate with successful simulations."""

    print("\n🎯 Success Factor Analysis:")
    print("-" * 30)

    successful_sims = []
    failed_sims = []

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.reward_info:
            sim_data = {
                'task_id': sim.task_id,
                'reward': sim.reward_info.reward,
                'total_calls': sim.execution_metrics.total_tool_calls if sim.execution_metrics else 0,
                'failed_calls': sim.execution_metrics.failed_tool_calls if sim.execution_metrics else 0,
                'avg_time': sim.execution_metrics.average_execution_time_ms if sim.execution_metrics else 0,
                'state_changes': sim.execution_metrics.state_changes if sim.execution_metrics else 0,
                'termination_reason': sim.termination_reason,
                'tools_used': sim.execution_metrics.unique_tools_used if sim.execution_metrics else []
            }

            # Define success threshold (adjust as needed)
            if sim.reward_info.reward > 0.8:  # >80% reward
                successful_sims.append(sim_data)
            else:
                failed_sims.append(sim_data)

    if not successful_sims and not failed_sims:
        print("Insufficient data for success factor analysis")
        return

    print(f"Successful simulations: {len(successful_sims)}")
    print(f"Failed simulations: {len(failed_sims)}")

    if successful_sims and failed_sims:
        # Compare characteristics
        def avg_metric(sims, metric):
            values = [s[metric] for s in sims if isinstance(s[metric], (int, float))]
            return statistics.mean(values) if values else 0

        print(f"\nCharacteristic Comparison:")
        print(f"{'Metric':<20} {'Successful':<12} {'Failed':<12} {'Difference'}")
        print("-" * 55)

        metrics = ['total_calls', 'failed_calls', 'avg_time', 'state_changes']
        for metric in metrics:
            success_avg = avg_metric(successful_sims, metric)
            failed_avg = avg_metric(failed_sims, metric)
            diff = success_avg - failed_avg

            print(f"{metric:<20} {success_avg:<12.1f} {failed_avg:<12.1f} {diff:+12.1f}")

    # Common tools in successful simulations
    if successful_sims:
        successful_tools = []
        for sim in successful_sims:
            successful_tools.extend(sim['tools_used'])

        if successful_tools:
            tool_freq = Counter(successful_tools)
            print(f"\nMost common tools in successful simulations:")
            for tool, count in tool_freq.most_common(5):
                percentage = count / len(successful_sims) * 100
                print(f"   {tool}: {count}/{len(successful_sims)} ({percentage:.1f}%)")

    return successful_sims, failed_sims


def generate_custom_report(results, analysis_results):
    """Generate a comprehensive custom analysis report."""

    print("\n📋 Custom Analysis Summary:")
    print("=" * 40)

    timeouts, patterns, performance, errors, success_data = analysis_results

    # Key insights
    insights = []

    if timeouts:
        insights.append(f"🔴 Found {len(timeouts)} timeout issues across {len(set(t['tool_name'] for t in timeouts))} different tools")

    if patterns:
        most_common_pattern = patterns[0]
        insights.append(f"🔗 Most common tool sequence: {most_common_pattern[0][0]} → {most_common_pattern[0][1]} ({most_common_pattern[1]} times)")

    if performance:
        best_sim = performance[0]
        insights.append(f"🏆 Best performing simulation: Task {best_sim['task_id']} with {best_sim['failure_rate']:.1%} failure rate")

    if success_data:
        successful_sims, failed_sims = success_data
        success_rate = len(successful_sims) / (len(successful_sims) + len(failed_sims)) * 100
        insights.append(f"📊 Overall success rate: {success_rate:.1f}% ({len(successful_sims)} successful)")

    print("Key Insights:")
    for insight in insights:
        print(f"   {insight}")

    if not insights:
        print("   ✅ No significant issues or patterns identified")

    return insights


def main():
    """Run comprehensive custom analysis on simulation results."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/custom_analysis.py <results_file.json>")
        print("\nExample:")
        print("  python scripts/custom_analysis.py data/simulations/my_results.json")
        sys.exit(1)

    results_file = Path(sys.argv[1])

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        # Load simulation results
        print(f"🔍 Running custom analysis on: {results_file}")
        results = Results.load(str(results_file))

        # Check if enhanced logging data is available
        enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
        if not enhanced_sims:
            print("❌ No enhanced logging data found in results!")
            print("Run simulations with --enhanced-logging flag to enable custom analysis")
            return

        print("=" * 80)

        # Run all custom analyses
        timeouts = find_timeout_patterns(results)
        patterns = analyze_tool_usage_patterns(results)
        performance = compare_simulation_performance(results)
        errors = analyze_error_patterns(results)
        success_data = analyze_success_factors(results)

        # Generate summary report
        analysis_results = (timeouts, patterns, performance, errors, success_data)
        insights = generate_custom_report(results, analysis_results)

        # Save comprehensive analysis to JSON
        output_data = {
            'file_analyzed': str(results_file),
            'total_simulations': len(results.simulations),
            'enhanced_simulations': len(enhanced_sims),
            'insights': insights,
            'timeout_issues': len(timeouts) if timeouts else 0,
            'tool_patterns': len(patterns) if patterns else 0,
            'performance_rankings': len(performance) if performance else 0,
            'error_categories': len(set(e['tool_name'] for errors_list in errors.values() for e in errors_list)) if errors else 0
        }

        output_file = results_file.parent / f"{results_file.stem}_custom_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)

        print(f"\n💾 Custom analysis results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error running custom analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()