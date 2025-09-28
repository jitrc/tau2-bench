# Analysis Scripts for Enhanced Logging Data

This directory contains practical scripts for analyzing tau2-bench simulation results with enhanced logging data. Each script provides different insights into your agent performance and system behavior.

## Available Scripts

### 1. Basic Analysis (`basic_analysis.py`)
**Quick comprehensive overview**
```bash
python scripts/basic_analysis.py data/simulations/your_results.json
```
- Generates overall performance report
- Shows failure rates, performance issues, and state changes
- Perfect for initial assessment
- Saves report to text file

### 2. Failure Analysis (`failure_analysis.py`)
**Deep dive into tool failures**
```bash
python scripts/failure_analysis.py data/simulations/your_results.json
```
- Identifies problematic tools and error patterns
- Shows failure frequency by tool and error type
- Provides specific examples and recommendations
- Essential for debugging tool implementations

### 3. Performance Analysis (`performance_analysis.py`)
**Performance bottleneck identification**
```bash
python scripts/performance_analysis.py data/simulations/your_results.json
```
- Finds slow tools and execution patterns
- Analyzes performance variability and consistency
- Correlates performance with success rates
- Saves detailed performance data to JSON

### 4. State Analysis (`state_analysis.py`)
**Environment state change tracking**
```bash
python scripts/state_analysis.py data/simulations/your_results.json
```
- Tracks environment state modifications
- Identifies unexpected state changes
- Analyzes state consistency across trials
- Useful for understanding system side effects

### 5. Custom Analysis (`custom_analysis.py`)
**Advanced analysis patterns**
```bash
python scripts/custom_analysis.py data/simulations/your_results.json
```
- Timeout pattern detection
- Tool usage sequence analysis
- Success factor identification
- Template for custom analysis needs

### 6. Complete Analysis (`complete_analysis.py`)
**Comprehensive analysis workflow**
```bash
python scripts/complete_analysis.py data/simulations/your_results.json
```
- Runs ALL available analyses
- Generates comprehensive reports
- Provides executive summary and action items
- Best for thorough evaluation

## Prerequisites

1. **Enhanced Logging Data**: All scripts require simulation results with enhanced logging:
   ```bash
   tau2 run --domain airline --enhanced-logging --num-trials 3 --num-tasks 5
   ```

2. **Dependencies**: Scripts use standard tau2-bench dependencies (already installed)

## Quick Start Workflow

### Step 1: Run Simulation with Enhanced Logging
```bash
# Example: airline domain with enhanced logging
tau2 run --domain airline --enhanced-logging --num-trials 3 --num-tasks 5
```

### Step 2: Choose Analysis Script Based on Need

**For quick overview:**
```bash
python scripts/basic_analysis.py data/simulations/your_results.json
```

**For debugging tool failures:**
```bash
python scripts/failure_analysis.py data/simulations/your_results.json
```

**For performance optimization:**
```bash
python scripts/performance_analysis.py data/simulations/your_results.json
```

**For comprehensive evaluation:**
```bash
python scripts/complete_analysis.py data/simulations/your_results.json
```

## Script Outputs

### Generated Files
Each script creates analysis output files in the same directory as your results:

- **Text Reports**: `*_analysis_report.txt` - Human-readable analysis
- **JSON Data**: `*_analysis_data.json` - Structured data for further processing
- **Detailed Logs**: `*_detailed_analysis.txt` - Complete analysis breakdown

### Console Output
Scripts provide:
- Real-time analysis progress
- Key findings and insights
- Actionable recommendations
- Summary statistics

## Example Usage Session

```bash
# 1. Run simulation with enhanced logging
tau2 run --domain airline --enhanced-logging --num-trials 2 --num-tasks 3

# 2. Check basic performance overview
python scripts/basic_analysis.py data/simulations/2024_*_airline_*.json

# 3. If failures detected, analyze in detail
python scripts/failure_analysis.py data/simulations/2024_*_airline_*.json

# 4. Identify performance bottlenecks
python scripts/performance_analysis.py data/simulations/2024_*_airline_*.json

# 5. Generate comprehensive report for stakeholders
python scripts/complete_analysis.py data/simulations/2024_*_airline_*.json
```

## Understanding Script Output

### Success Indicators ✅
- Low failure rates (<10%)
- Consistent execution times
- Minimal state changes
- High reward scores

### Warning Signs ⚠️
- High failure rates (>15%)
- Inconsistent performance (high variance)
- Excessive state changes
- Common error patterns

### Critical Issues 🔴
- Tools failing >25% of calls
- Execution times >5 seconds
- Frequent timeout errors
- System instability

## Customization

### Adding Custom Analysis
Use `custom_analysis.py` as a template:

```python
def my_custom_analysis(results):
    """Add your custom analysis logic here."""
    for sim in results.simulations:
        if sim.enhanced_logging_enabled:
            # Your analysis code
            pass

# Add to main() function
custom_results = my_custom_analysis(results)
```

### Filtering Results
Most scripts support filtering by modifying the data loading:

```python
# Filter by task ID
target_tasks = ['task_1', 'task_2']
filtered_sims = [sim for sim in results.simulations
                if sim.task_id in target_tasks]

# Filter by performance
successful_sims = [sim for sim in results.simulations
                  if sim.reward_info and sim.reward_info.reward > 0.8]
```

## Troubleshooting

### Common Issues

**"No enhanced logging data found"**
- Run simulations with `--enhanced-logging` flag
- Check that results file contains enhanced logging data

**"File not found"**
- Verify results file path is correct
- Use absolute path if needed: `/full/path/to/results.json`

**Import errors**
- Run scripts from tau2-bench root directory
- Ensure tau2-bench is properly installed

**Empty analysis results**
- Check that simulation actually ran (non-empty results file)
- Verify enhanced logging was enabled during simulation
- Ensure tools were actually called during simulation

### Performance Tips

- Use `basic_analysis.py` first for quick overview
- Run specific analysis scripts based on findings
- Use `complete_analysis.py` for final comprehensive reports
- Large result files may take longer to process

## Integration with Existing Workflow

These scripts integrate seamlessly with:
- **tau2 view**: Dashboard can show enhanced metrics
- **Results.to_df()**: DataFrame includes logging columns
- **Existing analysis**: Scripts extend rather than replace current tools
- **CI/CD**: Scripts return exit codes for automated pipelines

## Next Steps

1. **Start with basic analysis** to understand your results
2. **Identify specific issues** using targeted scripts
3. **Optimize based on findings** (fix failing tools, improve performance)
4. **Re-run analysis** to validate improvements
5. **Use complete analysis** for final evaluation and reporting

These scripts transform the enhanced logging data into actionable insights, helping you understand and optimize your tau2-bench agent performance.