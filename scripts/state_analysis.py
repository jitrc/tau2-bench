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
from typing import Iterable

# Add src to path so we can import tau2 modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tau2.data_model.simulation import Results, SimulationRun
from tau2.metrics.execution_analysis import analyze_state_changes


import io

def print_state_summary(state_analysis, file=None):
    """Print a summary of state change analysis."""

    print("🔄 Environment State Analysis Summary:", file=file)
    print("-" * 40, file=file)

    print(f"Total state changes: {state_analysis['total_state_changes']}", file=file)
    print(f"Simulations affected: {state_analysis['simulations_with_changes']}", file=file)
    print(f"Average changes per simulation: {state_analysis['avg_changes_per_sim']:.1f}", file=file)
    print(f"Maximum changes in single simulation: {state_analysis['max_changes_per_sim']}", file=file)

    if state_analysis['changes_per_simulation']:
        changes_dist = Counter(state_analysis['changes_per_simulation'])
        print(f"\nDistribution of changes per simulation:", file=file)
        for changes, count in sorted(changes_dist.items()):
            print(f"   {changes} changes: {count} simulations", file=file)

    print(file=file)


def print_trigger_analysis(state_analysis, file=None):
    """Print analysis of what triggers state changes."""

    if not state_analysis['change_triggers']:
        print("No state change triggers found", file=file)
        return

    print("🎯 State Change Triggers:", file=file)
    print("-" * 30, file=file)

    total_triggers = sum(state_analysis['change_triggers'].values())

    print(f"{'Trigger':<25} {'Count':<8} {'Percentage'}", file=file)
    print("-" * 45, file=file)

    for trigger, count in sorted(state_analysis['change_triggers'].items(),
                                key=lambda x: x[1], reverse=True):
        percentage = count / total_triggers * 100 if total_triggers > 0 else 0
        print(f"{trigger:<25} {count:<8} {percentage:6.1f}%", file=file)

    print(file=file)


def analyze_state_change_patterns(simulations: Iterable[SimulationRun], file=None):
    """Analyze detailed state change patterns."""

    print("🔍 Detailed State Change Patterns:", file=file)
    print("-" * 40, file=file)

    all_snapshots = []
    simulation_changes = defaultdict(list)

    for sim in simulations:
        if sim.enhanced_logging_enabled and sim.state_snapshots:
            for snapshot in sim.state_snapshots:
                all_snapshots.append({'task_id': sim.task_id, 'step_idx': snapshot.step_idx, 'state_changed': snapshot.state_changed})
                if snapshot.state_changed:
                    simulation_changes[sim.task_id].append(snapshot)

    if not all_snapshots:
        print("No state snapshots found", file=file)
        return

    state_changes = [s for s in all_snapshots if s['state_changed']]
    print(f"Total state snapshots: {len(all_snapshots)}", file=file)
    print(f"State changes: {len(state_changes)}", file=file)

    if state_changes:
        step_changes = [s['step_idx'] for s in state_changes]
        avg_change_step = sum(step_changes) / len(step_changes)
        print(f"Average step when changes occur: {avg_change_step:.1f}", file=file)


def analyze_state_consistency(simulations: Iterable[SimulationRun], file=None):
    """Analyze state consistency across simulations."""

    print(f"\n🔒 State Consistency Analysis:", file=file)
    print("-" * 35, file=file)

    task_simulations = defaultdict(list)
    for sim in simulations:
        if sim.enhanced_logging_enabled:
            task_simulations[sim.task_id].append(sim)

    consistency_issues = []
    for task_id, sims in task_simulations.items():
        if len(sims) < 2: continue
        final_hashes = []
        for sim in sims:
            if sim.state_snapshots:
                for snapshot in reversed(sim.state_snapshots):
                    if snapshot.db_hash:
                        final_hashes.append((sim.trial, snapshot.db_hash))
                        break
        if len(final_hashes) > 1 and len(set(h for _, h in final_hashes)) > 1:
            consistency_issues.append({'task_id': task_id, 'trials': len(final_hashes), 'unique_final_states': len(set(h for _, h in final_hashes))})

    if consistency_issues:
        print("⚠️  Consistency Issues Found:", file=file)
        for issue in consistency_issues:
            print(f"   Task {issue['task_id']}: {issue['trials']} trials, {issue['unique_final_states']} different final states", file=file)
    else:
        print("✅ All task trials end in consistent states", file=file)


def main():
    """Run detailed state analysis on simulation results."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/state_analysis.py <results_file.json>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    try:
        print(f"🔄 Analyzing environment state changes in: {results_file}")
        
        simulations_list = list(Results.stream_simulations(results_file))
        
        if not any(s.enhanced_logging_enabled and s.state_snapshots for s in simulations_list):
            print("❌ No enhanced logging data with state snapshots found!")
            return

        print("=" * 80)
        state_analysis = analyze_state_changes(simulations_list)
        
        report_buffer = io.StringIO()
        print_state_summary(state_analysis, file=report_buffer)
        print_trigger_analysis(state_analysis, file=report_buffer)
        analyze_state_change_patterns(simulations_list, file=report_buffer)
        analyze_state_consistency(simulations_list, file=report_buffer)
        
        report_content = report_buffer.getvalue()
        print(report_content)

        output_file = results_file.parent / f"{results_file.stem}_state_analysis.txt"
        output_file.write_text(f"ENVIRONMENT STATE ANALYSIS REPORT\n{'='*50}\n\nResults file: {results_file}\n\n{report_content}")
        print(f"\n💾 Detailed state analysis saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error analyzing state changes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
