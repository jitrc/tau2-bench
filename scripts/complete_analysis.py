#!/usr/bin/env python3
"""
Complete Analysis Workflow Script

This script runs all available analyses on tau2-bench simulation results
with enhanced logging data. Use this for comprehensive evaluation of your results.

Usage:
    python scripts/complete_analysis.py <results_file.json>
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results
from tau2.metrics.execution_analysis import (
    generate_execution_report,
    analyze_tool_failures,
    analyze_performance_bottlenecks,
    analyze_state_changes
)


def run_comprehensive_analysis(results):
    """Run all available analyses and return results."""

    analyses = {}

    print("Running comprehensive analysis...")
    print("=" * 50)

    # 1. Generate overall report
    print("\n1️⃣ Generating execution report...")
    analyses['execution_report'] = generate_execution_report(results)

    # 2. Tool failure analysis
    print("2️⃣ Analyzing tool failures...")
    analyses['failure_analysis'] = analyze_tool_failures(results)

    # 3. Performance analysis
    print("3️⃣ Analyzing performance bottlenecks...")
    analyses['performance_analysis'] = analyze_performance_bottlenecks(results)

    # 4. State change analysis
    print("4️⃣ Analyzing environment state changes...")
    analyses['state_analysis'] = analyze_state_changes(results)

    return analyses


def print_comprehensive_results(analyses, results):
    """Print comprehensive analysis results."""

    print("\n" + "="*80)
    print("🔍 COMPREHENSIVE ANALYSIS RESULTS")
    print("="*80)

    # Overview
    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
    print(f"\n📊 ANALYSIS OVERVIEW:")
    print(f"   • Total simulations: {len(results.simulations)}")
    print(f"   • Enhanced logging enabled: {len(enhanced_sims)}")
    print(f"   • Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Executive Summary from main report
    print(f"\n📋 EXECUTIVE SUMMARY:")
    print("-" * 30)
    print(analyses['execution_report'])

    # 2. Detailed Failure Analysis
    failure_analysis = analyses['failure_analysis']
    if failure_analysis['tool_failure_stats']:
        print(f"\n❌ DETAILED FAILURE BREAKDOWN:")
        print("-" * 40)
        print(f"Tools analyzed: {len(failure_analysis['tool_failure_stats'])}")

        # Show problematic tools
        problematic_tools = [
            (tool, stats) for tool, stats in failure_analysis['tool_failure_stats'].items()
            if stats['failure_rate'] > 0.1 and stats['total'] > 2  # >10% failure rate, >2 calls
        ]

        if problematic_tools:
            problematic_tools.sort(key=lambda x: x[1]['failure_rate'], reverse=True)
            print(f"High-failure tools ({len(problematic_tools)} found):")
            for tool, stats in problematic_tools:
                print(f"   🔴 {tool}: {stats['failure_rate']:.1%} failure rate "
                      f"({stats['failed']}/{stats['total']} calls, {stats['avg_execution_time']:.1f}ms avg)")
        else:
            print("✅ No high-failure tools identified")

    # 3. Performance Insights
    perf_analysis = analyses['performance_analysis']
    if perf_analysis['slowest_tools']:
        print(f"\n⚡ PERFORMANCE INSIGHTS:")
        print("-" * 35)
        print("Slowest tools requiring optimization:")
        for tool, avg_time in perf_analysis['slowest_tools'][:5]:
            if avg_time > 1000:  # >1 second
                print(f"   🐌 {tool}: {avg_time:.1f}ms (optimization target)")

        # Show statistics summary
        if perf_analysis['execution_time_stats']:
            all_means = [stats['mean'] for stats in perf_analysis['execution_time_stats'].values()]
            import statistics
            overall_avg = statistics.mean(all_means) if all_means else 0
            print(f"Overall average tool execution time: {overall_avg:.1f}ms")

    # 4. State Management Summary
    state_analysis = analyses['state_analysis']
    print(f"\n🔄 STATE MANAGEMENT SUMMARY:")
    print("-" * 35)
    print(f"Total state changes: {state_analysis['total_state_changes']}")
    print(f"Simulations affected: {state_analysis['simulations_with_changes']}")
    print(f"Average changes per simulation: {state_analysis['avg_changes_per_sim']:.1f}")

    if state_analysis['change_triggers']:
        dominant_trigger = max(state_analysis['change_triggers'], key=state_analysis['change_triggers'].get)
        print(f"Most frequent trigger: {dominant_trigger} ({state_analysis['change_triggers'][dominant_trigger]} times)")

    # 5. Action Items
    print(f"\n🎯 RECOMMENDED ACTION ITEMS:")
    print("-" * 35)

    action_items = []

    # High-priority items from failure analysis
    high_failure_tools = [
        tool for tool, stats in failure_analysis.get('tool_failure_stats', {}).items()
        if stats['failure_rate'] > 0.2 and stats['total'] > 3
    ]
    if high_failure_tools:
        action_items.append(f"🔴 HIGH PRIORITY: Fix high-failure tools: {', '.join(high_failure_tools[:3])}")

    # Performance optimization targets
    slow_tools = [tool for tool, time in perf_analysis.get('slowest_tools', [])[:3] if time > 2000]
    if slow_tools:
        action_items.append(f"🟠 OPTIMIZE: Performance bottlenecks in: {', '.join(slow_tools)}")

    # State management issues
    if state_analysis['avg_changes_per_sim'] > 10:
        action_items.append(f"🔄 REVIEW: Excessive state changes ({state_analysis['avg_changes_per_sim']:.1f} per sim)")

    # Error pattern investigation
    if failure_analysis.get('failure_patterns'):
        common_errors = [error for error, count in failure_analysis['failure_patterns'].items() if count > 3][:2]
        if common_errors:
            action_items.append(f"🔍 INVESTIGATE: Common errors: {', '.join(common_errors)}")

    if action_items:
        for i, item in enumerate(action_items, 1):
            print(f"   {i}. {item}")
    else:
        print("   ✅ No critical issues identified - system performing well!")


def generate_summary_metrics(analyses, results):
    """Generate summary metrics for dashboard/monitoring."""

    enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]

    # Calculate overall metrics
    total_tool_calls = 0
    total_failed_calls = 0
    total_execution_time = 0
    simulation_rewards = []

    for sim in enhanced_sims:
        if sim.execution_metrics:
            total_tool_calls += sim.execution_metrics.total_tool_calls
            total_failed_calls += sim.execution_metrics.failed_tool_calls
            total_execution_time += sim.execution_metrics.total_execution_time_ms

        if sim.reward_info:
            simulation_rewards.append(sim.reward_info.reward)

    # Summary metrics
    metrics = {
        'total_simulations': len(results.simulations),
        'enhanced_simulations': len(enhanced_sims),
        'overall_success_rate': (total_tool_calls - total_failed_calls) / total_tool_calls if total_tool_calls > 0 else 0,
        'average_reward': sum(simulation_rewards) / len(simulation_rewards) if simulation_rewards else 0,
        'total_tool_calls': total_tool_calls,
        'total_execution_time_ms': total_execution_time,
        'average_execution_time_ms': total_execution_time / total_tool_calls if total_tool_calls > 0 else 0,
        'unique_tools_analyzed': len(analyses['performance_analysis'].get('execution_time_stats', {})),
        'state_changes_per_sim': analyses['state_analysis']['avg_changes_per_sim'],
        'analysis_timestamp': datetime.now().isoformat()
    }

    return metrics


def save_comprehensive_results(analyses, results, results_file):
    """Save all analysis results to files."""

    base_path = results_file.parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Save comprehensive text report
    report_file = base_path / f"{results_file.stem}_comprehensive_analysis_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write("COMPREHENSIVE ANALYSIS REPORT\n")
        f.write("="*50 + "\n\n")

        f.write(f"Results file: {results_file}\n")
        f.write(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Executive summary
        f.write("EXECUTIVE SUMMARY:\n")
        f.write("-" * 20 + "\n")
        f.write(analyses['execution_report'])
        f.write("\n\n")

        # Detailed sections
        f.write("TOOL FAILURE DETAILS:\n")
        f.write("-" * 25 + "\n")
        for tool, stats in analyses['failure_analysis'].get('tool_failure_stats', {}).items():
            if stats['total'] > 0:
                f.write(f"{tool}: {stats['total']} calls, {stats['failed']} failures "
                       f"({stats['failure_rate']:.1%}), {stats['avg_execution_time']:.1f}ms\n")

        f.write("\nPERFORMANCE STATISTICS:\n")
        f.write("-" * 25 + "\n")
        for tool, stats in analyses['performance_analysis'].get('execution_time_stats', {}).items():
            f.write(f"{tool}: {stats['mean']:.1f}ms ± {stats['std_dev']:.1f}ms "
                   f"(range: {stats['min']:.1f}-{stats['max']:.1f}ms, n={stats['count']})\n")

    # 2. Save structured JSON data
    json_file = base_path / f"{results_file.stem}_analysis_data_{timestamp}.json"
    analysis_data = {
        'metadata': {
            'source_file': str(results_file),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_simulations': len(results.simulations),
            'enhanced_simulations': len([s for s in results.simulations if s.enhanced_logging_enabled])
        },
        'summary_metrics': generate_summary_metrics(analyses, results),
        'detailed_analyses': {
            'failure_analysis': analyses['failure_analysis'],
            'performance_analysis': analyses['performance_analysis'],
            'state_analysis': analyses['state_analysis']
        }
    }

    with open(json_file, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)

    return report_file, json_file


def main():
    """Run comprehensive analysis workflow."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/complete_analysis.py <results_file.json>")
        print("\nExample:")
        print("  python scripts/complete_analysis.py data/simulations/my_results.json")
        print("\nThis will run ALL available analyses and generate comprehensive reports.")
        sys.exit(1)

    results_file = Path(sys.argv[1])

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        print("\nMake sure to run simulations with --enhanced-logging first:")
        print("  tau2 run --domain airline --enhanced-logging --num-trials 3")
        sys.exit(1)

    try:
        # Load simulation results
        print(f"🚀 Starting comprehensive analysis of: {results_file.name}")
        results = Results.load(str(results_file))

        # Validate enhanced logging availability
        enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
        if not enhanced_sims:
            print("❌ No enhanced logging data found in results!")
            print("\n💡 To enable enhanced logging for future runs:")
            print("   tau2 run --enhanced-logging [other options...]")
            return

        print(f"✅ Found enhanced logging data in {len(enhanced_sims)}/{len(results.simulations)} simulations")

        # Run comprehensive analysis
        analyses = run_comprehensive_analysis(results)

        # Display results
        print_comprehensive_results(analyses, results)

        # Save results
        print(f"\n💾 Saving analysis results...")
        report_file, json_file = save_comprehensive_results(analyses, results, results_file)

        print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print(f"   📄 Text report: {report_file}")
        print(f"   📊 JSON data: {json_file}")

        # Summary metrics for quick reference
        metrics = generate_summary_metrics(analyses, results)
        print(f"\n📈 QUICK METRICS:")
        print(f"   • Success rate: {metrics['overall_success_rate']:.1%}")
        print(f"   • Average reward: {metrics['average_reward']:.3f}")
        print(f"   • Avg execution time: {metrics['average_execution_time_ms']:.1f}ms")
        print(f"   • Tools analyzed: {metrics['unique_tools_analyzed']}")

    except Exception as e:
        print(f"❌ Error running comprehensive analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()