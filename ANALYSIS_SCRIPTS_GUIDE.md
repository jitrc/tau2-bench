# Analysis Scripts Usage Guide

This guide shows you how to use the execution analysis scripts to gain insights from your tau2-bench simulations with enhanced logging.

## Quick Start

### 1. Run Simulation with Enhanced Logging
```bash
tau2 run --domain airline --enhanced-logging --num-trials 3 --num-tasks 5
```

### 2. Choose Your Analysis
```bash
# Quick overview (recommended first step)
python scripts/basic_analysis.py data/simulations/your_results.json

# Or use the convenient script runner
./scripts/run_analysis.sh basic data/simulations/your_results.json
```

## Available Analysis Scripts

| Script | Purpose | Use When | Output |
|--------|---------|----------|--------|
| `basic_analysis.py` | Comprehensive overview | First analysis of results | Text report with key insights |
| `failure_analysis.py` | Tool failure deep dive | High failure rates detected | Detailed failure breakdown |
| `performance_analysis.py` | Performance bottlenecks | Slow execution times | Performance metrics & recommendations |
| `state_analysis.py` | Environment state tracking | Unexpected behavior | State change patterns |
| `custom_analysis.py` | Advanced patterns | Specific investigation needs | Custom insights |
| `complete_analysis.py` | All analyses + executive summary | Final evaluation | Comprehensive report + action items |

## Script Usage Patterns

### 🚀 Quick Assessment Workflow
```bash
# 1. Get overview
python scripts/basic_analysis.py data/simulations/results.json

# 2. If issues found, drill down
python scripts/failure_analysis.py data/simulations/results.json
python scripts/performance_analysis.py data/simulations/results.json
```

### 🔍 Deep Investigation Workflow
```bash
# Run comprehensive analysis
python scripts/complete_analysis.py data/simulations/results.json

# Then focus on specific areas of concern
```

### ⚡ Convenient Shell Runner
```bash
# All-in-one runner script
./scripts/run_analysis.sh complete data/simulations/results.json
./scripts/run_analysis.sh failures data/simulations/results.json
./scripts/run_analysis.sh performance data/simulations/results.json
```

## Understanding Output

### Console Output
All scripts provide:
- **Real-time progress** - See analysis steps
- **Key findings** - Critical issues highlighted
- **Recommendations** - Actionable next steps
- **Summary metrics** - Quick performance overview

### Generated Files
Scripts create analysis files in your results directory:
- `*_analysis_report.txt` - Human-readable findings
- `*_analysis_data.json` - Structured data for further processing
- `*_comprehensive_analysis.txt` - Complete detailed breakdown

### Color Coding
- 🔴 **RED** - Critical issues requiring immediate attention
- 🟠 **ORANGE** - Performance optimization opportunities
- 🟡 **YELLOW** - Areas for investigation
- ✅ **GREEN** - Systems performing well

## Common Analysis Scenarios

### Scenario 1: Agent Failing Frequently
```bash
# 1. Check overall failure rate
python scripts/basic_analysis.py data/simulations/results.json

# 2. Deep dive into failures
python scripts/failure_analysis.py data/simulations/results.json
```

**Look for:**
- Tools with >20% failure rates
- Common error patterns
- Specific tool/argument combinations causing issues

### Scenario 2: Agent Running Slowly
```bash
# 1. Identify performance bottlenecks
python scripts/performance_analysis.py data/simulations/results.json

# 2. Check for state management issues
python scripts/state_analysis.py data/simulations/results.json
```

**Look for:**
- Tools taking >2 seconds on average
- High performance variability
- Excessive environment state changes

### Scenario 3: Inconsistent Results
```bash
# 1. Compare simulation performance
python scripts/custom_analysis.py data/simulations/results.json

# 2. Check state consistency
python scripts/state_analysis.py data/simulations/results.json
```

**Look for:**
- Different final states across trials
- Tool usage pattern variations
- Success factor correlations

### Scenario 4: New Domain Evaluation
```bash
# Run complete analysis for comprehensive baseline
python scripts/complete_analysis.py data/simulations/results.json
```

**Look for:**
- Overall system health indicators
- Tool performance characteristics
- Optimization opportunities

## Script Output Examples

### Basic Analysis Output
```
🔍 Enhanced Logging Analysis Report
==================================================

📊 Overview:
   • Total simulations: 15
   • Enhanced logging enabled: 15

❌ Tool Failure Analysis:
   • Most failing tools:
     - validate_booking: 23.1% failure rate
     - check_availability: 12.5% failure rate

🐌 Performance Bottlenecks:
   • Slowest tools:
     - search_flights: 2,150.3ms
     - get_flight_details: 856.7ms
```

### Failure Analysis Output
```
❌ Most Problematic Tools:
   1. validate_booking: 23.1% failure rate
   2. check_availability: 12.5% failure rate

🔍 Common Error Patterns:
   1. ValidationError: 8 occurrences
   2. TimeoutError: 3 occurrences

💡 Recommendations:
🔴 HIGH PRIORITY - Fix high-failure tools:
   • validate_booking: 23.1% failure rate (3/13 calls)
```

### Performance Analysis Output
```
🐌 Performance Analysis Summary:
Slowest Tools (Average Execution Time):
   1. search_flights:     2150.3ms
   2. get_flight_details:  856.7ms

💡 Performance Optimization Recommendations:
🔴 HIGH PRIORITY - Optimize slow tools:
   • search_flights: 2150.3ms average (consider caching)
```

## Advanced Usage

### Filtering Results
Modify scripts to focus on specific data:
```python
# In any script, add filtering logic:
target_tasks = ['task_1', 'task_2', 'task_3']
filtered_sims = [sim for sim in results.simulations
                if sim.task_id in target_tasks]
```

### Custom Metrics
Add your own analysis to `custom_analysis.py`:
```python
def analyze_my_pattern(results):
    """Add your custom analysis logic here."""
    insights = []
    for sim in results.simulations:
        if sim.enhanced_logging_enabled:
            # Your analysis code
            pass
    return insights
```

### Automation Integration
Scripts return appropriate exit codes for CI/CD:
```bash
# Use in automated pipelines
if python scripts/basic_analysis.py results.json; then
    echo "Analysis passed"
else
    echo "Analysis found issues"
    exit 1
fi
```

## Troubleshooting

### Common Issues

**"No enhanced logging data found"**
```bash
# Solution: Run simulations with enhanced logging
tau2 run --domain airline --enhanced-logging --num-trials 3
```

**"Results file not found"**
```bash
# Check file path
ls data/simulations/
# Use absolute path if needed
python scripts/basic_analysis.py /full/path/to/results.json
```

**Script execution errors**
```bash
# Run from tau2-bench root directory
cd /path/to/tau2-bench
python scripts/basic_analysis.py data/simulations/results.json
```

### Performance Tips
- Start with `basic_analysis.py` for quick overview
- Use specific scripts based on findings from basic analysis
- Run `complete_analysis.py` for final comprehensive reports
- Large result files may take 1-2 minutes to process

## Integration with tau2-bench Workflow

```bash
# 1. Run simulation with enhanced logging
tau2 run --domain airline --enhanced-logging --num-trials 5

# 2. Quick assessment
python scripts/basic_analysis.py data/simulations/2024_*_airline_*.json

# 3. Address any issues found
# (fix tools, optimize performance, etc.)

# 4. Re-run and validate improvements
tau2 run --domain airline --enhanced-logging --num-trials 5
python scripts/basic_analysis.py data/simulations/2024_*_airline_*.json

# 5. Generate final report
python scripts/complete_analysis.py data/simulations/2024_*_airline_*.json
```

## Next Steps

1. **Start with basic analysis** to understand your results
2. **Use targeted scripts** based on specific issues found
3. **Implement improvements** to address identified problems
4. **Re-analyze** to validate improvements
5. **Use complete analysis** for stakeholder reporting

These analysis scripts transform enhanced logging data into actionable insights, helping you optimize agent performance and understand system behavior patterns.