#!/usr/bin/env python3
"""
Environment State Analysis Script

This script analyzes environment state changes during tau2-bench simulations,
helping understand system behavior and identify unexpected state modifications.

Usage:
    python scripts/state_analysis.py <results_file.json>
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results
from tau2.metrics.execution_analysis import analyze_state_changes


def print_state_summary(state_analysis):
    """Print a summary of state change analysis."""

    print("🔄 Environment State Analysis Summary:")
    print("-" * 40)

    print(f"Total state changes: {state_analysis['total_state_changes']}")
    print(f"Simulations affected: {state_analysis['simulations_with_changes']}")
    print(f"Average changes per simulation: {state_analysis['avg_changes_per_sim']:.1f}")
    print(f"Maximum changes in single simulation: {state_analysis['max_changes_per_sim']}")

    if state_analysis['changes_per_simulation']:
        changes_dist = Counter(state_analysis['changes_per_simulation'])
        print(f"\nDistribution of changes per simulation:")
        for changes, count in sorted(changes_dist.items()):
            print(f"   {changes} changes: {count} simulations")

    print()


def print_trigger_analysis(state_analysis):
    """Print analysis of what triggers state changes."""

    if not state_analysis['change_triggers']:
        print("No state change triggers found")
        return

    print("🎯 State Change Triggers:")
    print("-" * 30)

    total_triggers = sum(state_analysis['change_triggers'].values())

    print(f"{'Trigger':<25} {'Count':<8} {'Percentage'}")
    print("-" * 45)

    for trigger, count in sorted(state_analysis['change_triggers'].items(),
                                key=lambda x: x[1], reverse=True):
        percentage = count / total_triggers * 100 if total_triggers > 0 else 0
        print(f"{trigger:<25} {count:<8} {percentage:6.1f}%")

    print()


def analyze_state_change_patterns(results):
    """Analyze detailed state change patterns."""

    print("🔍 Detailed State Change Patterns:")
    print("-" * 40)

    # Collect all state snapshots
    all_snapshots = []
    simulation_changes = defaultdict(list)

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.state_snapshots:
            for snapshot in sim.state_snapshots:
                all_snapshots.append({
                    'task_id': sim.task_id,
                    'trial': sim.trial,
                    'step_idx': snapshot.step_idx,
                    'triggered_by': snapshot.triggered_by,
                    'state_changed': snapshot.state_changed,
                    'db_hash': snapshot.db_hash,
                    'timestamp': snapshot.timestamp
                })

                if snapshot.state_changed:
                    simulation_changes[sim.task_id].append(snapshot)

    if not all_snapshots:
        print("No state snapshots found")
        return

    print(f"Total state snapshots: {len(all_snapshots)}")
    state_changes = [s for s in all_snapshots if s['state_changed']]
    print(f"State changes: {len(state_changes)}")

    # Analyze change timing
    if state_changes:
        step_changes = [s['step_idx'] for s in state_changes]
        avg_change_step = sum(step_changes) / len(step_changes)
        print(f"Average step when changes occur: {avg_change_step:.1f}")

        # Changes by step distribution
        step_distribution = Counter(step_changes)
        print(f"\nState changes by step:")
        for step in sorted(step_distribution.keys())[:10]:  # First 10 steps
            count = step_distribution[step]
            print(f"   Step {step}: {count} changes")

    # Analyze change sequences for individual simulations
    print(f"\nSimulations with most state changes:")
    sorted_sims = sorted(simulation_changes.items(),
                        key=lambda x: len(x[1]), reverse=True)

    for i, (task_id, changes) in enumerate(sorted_sims[:5], 1):
        print(f"\n{i}. Task {task_id}: {len(changes)} changes")
        for j, change in enumerate(changes[:3], 1):  # First 3 changes
            print(f"   {j}. Step {change.step_idx}: {change.triggered_by}")


def analyze_state_consistency(results):
    """Analyze state consistency across simulations."""

    print(f"\n🔒 State Consistency Analysis:")
    print("-" * 35)

    # Group simulations by task
    task_simulations = defaultdict(list)
    for sim in results.simulations:
        if sim.enhanced_logging_enabled:
            task_simulations[sim.task_id].append(sim)

    consistency_issues = []

    for task_id, sims in task_simulations.items():
        if len(sims) < 2:  # Need at least 2 simulations to compare
            continue

        # Compare final state hashes across trials of the same task
        final_hashes = []
        for sim in sims:
            if sim.state_snapshots:
                # Get last snapshot with a hash
                for snapshot in reversed(sim.state_snapshots):
                    if snapshot.db_hash:
                        final_hashes.append((sim.trial, snapshot.db_hash))
                        break

        if len(final_hashes) > 1:
            # Check if all final states are the same
            unique_hashes = set(hash_val for _, hash_val in final_hashes)
            if len(unique_hashes) > 1:
                consistency_issues.append({
                    'task_id': task_id,
                    'trials': len(final_hashes),
                    'unique_final_states': len(unique_hashes),
                    'hashes': final_hashes
                })

    if consistency_issues:
        print("⚠️  Consistency Issues Found:")
        for issue in consistency_issues:
            print(f"   Task {issue['task_id']}: {issue['trials']} trials, "
                  f"{issue['unique_final_states']} different final states")
    else:
        print("✅ All task trials end in consistent states")


def analyze_state_hash_patterns(results):
    """Analyze state hash patterns to understand state evolution."""

    print(f"\n📊 State Hash Evolution Analysis:")
    print("-" * 40)

    # Collect state hash sequences
    hash_sequences = []
    unique_states_per_sim = []

    for sim in results.simulations:
        if sim.enhanced_logging_enabled and sim.state_snapshots:
            sequence = []
            unique_hashes = set()

            for snapshot in sim.state_snapshots:
                if snapshot.db_hash:
                    sequence.append(snapshot.db_hash)
                    unique_hashes.add(snapshot.db_hash)

            if sequence:
                hash_sequences.append({
                    'task_id': sim.task_id,
                    'trial': sim.trial,
                    'sequence': sequence,
                    'unique_states': len(unique_hashes),
                    'total_snapshots': len(sequence)
                })
                unique_states_per_sim.append(len(unique_hashes))

    if not hash_sequences:
        print("No state hash data available")
        return

    # Statistics
    avg_unique_states = sum(unique_states_per_sim) / len(unique_states_per_sim)
    print(f"Average unique states per simulation: {avg_unique_states:.1f}")

    # Find simulations with unusual state evolution
    high_change_sims = [seq for seq in hash_sequences if seq['unique_states'] > avg_unique_states * 1.5]
    low_change_sims = [seq for seq in hash_sequences if seq['unique_states'] < 2]

    if high_change_sims:
        print(f"\nSimulations with high state variability ({len(high_change_sims)} found):")
        for seq in sorted(high_change_sims, key=lambda x: x['unique_states'], reverse=True)[:3]:
            print(f"   Task {seq['task_id']} (trial {seq['trial']}): "
                  f"{seq['unique_states']} unique states in {seq['total_snapshots']} snapshots")

    if low_change_sims:
        print(f"\nSimulations with minimal state changes ({len(low_change_sims)} found):")
        for seq in low_change_sims[:3]:
            print(f"   Task {seq['task_id']} (trial {seq['trial']}): "
                  f"{seq['unique_states']} unique states")


def generate_state_recommendations(results, state_analysis):
    """Generate recommendations based on state analysis."""

    print("\n💡 State Management Recommendations:")
    print("-" * 40)

    recommendations = []

    # Check for excessive state changes
    if state_analysis['avg_changes_per_sim'] > 10:
        recommendations.append("🔴 HIGH - Excessive state changes detected:")
        recommendations.append(f"   • Average {state_analysis['avg_changes_per_sim']:.1f} changes per simulation")
        recommendations.append("   • Review tool implementations for unnecessary state modifications")

    # Check for inconsistent state changes
    if state_analysis['max_changes_per_sim'] > state_analysis['avg_changes_per_sim'] * 3:
        recommendations.append("🟡 MEDIUM - High variability in state changes:")
        recommendations.append(f"   • Some simulations have {state_analysis['max_changes_per_sim']} changes while average is {state_analysis['avg_changes_per_sim']:.1f}")
        recommendations.append("   • Investigate task-specific or input-dependent behavior")

    # Check trigger patterns
    if state_analysis['change_triggers']:
        dominant_trigger = max(state_analysis['change_triggers'], key=state_analysis['change_triggers'].get)
        trigger_count = state_analysis['change_triggers'][dominant_trigger]
        total_triggers = sum(state_analysis['change_triggers'].values())

        if trigger_count / total_triggers > 0.6:  # One trigger causes >60% of changes
            recommendations.append("🔍 INVESTIGATE - Dominant state change trigger:")
            recommendations.append(f"   • '{dominant_trigger}' causes {trigger_count/total_triggers:.1%} of all state changes")
            recommendations.append("   • Verify this tool's state modifications are necessary")

    # General recommendations
    if not recommendations:
        recommendations.append("✅ State management looks healthy!")

    recommendations.extend([
        "\n📋 General State Management Tips:",
        "   • Monitor tools that frequently modify environment state",
        "   • Ensure state changes are intentional and documented",
        "   • Consider state change impact on simulation reproducibility",
        "   • Use state snapshots to debug unexpected behavior"
    ])

    for rec in recommendations:
        print(rec)


def main():
    """Run detailed state analysis on simulation results."""

    if len(sys.argv) != 2:
        print("Usage: python scripts/state_analysis.py <results_file.json>")
        print("\nExample:")
        print("  python scripts/state_analysis.py data/simulations/my_results.json")
        sys.exit(1)

    results_file = Path(sys.argv[1])

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        # Load simulation results
        print(f"🔄 Analyzing environment state changes in: {results_file}")
        results = Results.load(str(results_file))

        # Check if enhanced logging data is available
        enhanced_sims = [sim for sim in results.simulations if sim.enhanced_logging_enabled]
        if not enhanced_sims:
            print("❌ No enhanced logging data found in results!")
            print("Run simulations with --enhanced-logging flag to enable state analysis")
            return

        state_snapshots_available = any(
            sim.state_snapshots for sim in enhanced_sims
        )

        if not state_snapshots_available:
            print("❌ No state snapshots found in enhanced logging data!")
            return

        print("=" * 80)

        # Run state analysis
        state_analysis = analyze_state_changes(results)

        # Print analysis results
        print_state_summary(state_analysis)
        print_trigger_analysis(state_analysis)
        analyze_state_change_patterns(results)
        analyze_state_consistency(results)
        analyze_state_hash_patterns(results)
        generate_state_recommendations(results, state_analysis)

        # Save detailed results to file
        output_file = results_file.parent / f"{results_file.stem}_state_analysis.txt"
        with open(output_file, 'w') as f:
            f.write("ENVIRONMENT STATE ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Results file: {results_file}\n")
            f.write(f"Total simulations: {len(results.simulations)}\n")
            f.write(f"Enhanced logging simulations: {len(enhanced_sims)}\n\n")

            f.write(f"STATE CHANGE SUMMARY:\n")
            f.write(f"Total state changes: {state_analysis['total_state_changes']}\n")
            f.write(f"Affected simulations: {state_analysis['simulations_with_changes']}\n")
            f.write(f"Average changes per simulation: {state_analysis['avg_changes_per_sim']:.1f}\n\n")

            f.write("CHANGE TRIGGERS:\n")
            for trigger, count in state_analysis['change_triggers'].items():
                f.write(f"{trigger}: {count} times\n")

        print(f"\n💾 Detailed state analysis saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error analyzing state changes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()