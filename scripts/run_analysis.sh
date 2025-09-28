#!/bin/bash
# Analysis Script Runner for tau2-bench Enhanced Logging Data
#
# This script provides a convenient way to run different analysis scripts
# on your tau2-bench simulation results.
#
# Usage:
#   ./scripts/run_analysis.sh <analysis_type> <results_file>
#
# Analysis types:
#   basic      - Quick comprehensive overview
#   failures   - Deep dive into tool failures
#   performance - Performance bottleneck analysis
#   state      - Environment state change analysis
#   custom     - Advanced custom analysis patterns
#   complete   - Run all analyses (comprehensive)
#
# Examples:
#   ./scripts/run_analysis.sh basic data/simulations/my_results.json
#   ./scripts/run_analysis.sh complete data/simulations/my_results.json

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Check arguments
if [ $# -ne 2 ]; then
    print_color $RED "❌ Error: Incorrect number of arguments"
    echo
    echo "Usage: $0 <analysis_type> <results_file>"
    echo
    echo "Analysis types:"
    echo "  basic       - Quick comprehensive overview"
    echo "  failures    - Deep dive into tool failures"
    echo "  performance - Performance bottleneck analysis"
    echo "  state       - Environment state change analysis"
    echo "  custom      - Advanced custom analysis patterns"
    echo "  complete    - Run all analyses (comprehensive)"
    echo
    echo "Example:"
    echo "  $0 basic data/simulations/my_results.json"
    exit 1
fi

ANALYSIS_TYPE=$1
RESULTS_FILE=$2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validate results file exists
if [ ! -f "$RESULTS_FILE" ]; then
    print_color $RED "❌ Error: Results file not found: $RESULTS_FILE"
    echo
    echo "💡 Make sure to run simulations with enhanced logging first:"
    echo "   tau2 run --domain airline --enhanced-logging --num-trials 3"
    exit 1
fi

# Function to run analysis script
run_script() {
    local script_name=$1
    local description=$2

    print_color $BLUE "🚀 Running $description..."
    print_color $YELLOW "   Script: $script_name"
    print_color $YELLOW "   Results: $RESULTS_FILE"
    echo

    if python "$SCRIPT_DIR/$script_name" "$RESULTS_FILE"; then
        print_color $GREEN "✅ $description completed successfully"
    else
        print_color $RED "❌ $description failed"
        return 1
    fi
    echo
}

# Main execution
print_color $GREEN "🔍 TAU2-BENCH ENHANCED LOGGING ANALYSIS"
print_color $GREEN "======================================"
echo

case $ANALYSIS_TYPE in
    basic)
        run_script "basic_analysis.py" "Basic Analysis"
        ;;
    failures)
        run_script "failure_analysis.py" "Failure Analysis"
        ;;
    performance)
        run_script "performance_analysis.py" "Performance Analysis"
        ;;
    state)
        run_script "state_analysis.py" "State Analysis"
        ;;
    custom)
        run_script "custom_analysis.py" "Custom Analysis"
        ;;
    complete)
        print_color $BLUE "🎯 Running Complete Analysis Workflow"
        echo "This will run all available analyses..."
        echo
        run_script "complete_analysis.py" "Complete Analysis"
        ;;
    *)
        print_color $RED "❌ Error: Unknown analysis type: $ANALYSIS_TYPE"
        echo
        echo "Valid analysis types:"
        echo "  basic, failures, performance, state, custom, complete"
        exit 1
        ;;
esac

# Final summary
print_color $GREEN "🎉 Analysis workflow completed!"
print_color $BLUE "📁 Check the same directory as your results file for generated reports."
echo

# Show generated files
RESULTS_DIR="$(dirname "$RESULTS_FILE")"
RESULTS_BASE="$(basename "$RESULTS_FILE" .json)"

print_color $YELLOW "Generated files:"
for file in "$RESULTS_DIR"/${RESULTS_BASE}_*analysis*.{txt,json}; do
    if [ -f "$file" ]; then
        echo "   📄 $(basename "$file")"
    fi
done 2>/dev/null || true

echo
print_color $BLUE "💡 Tip: Use 'complete' analysis type for comprehensive evaluation"
print_color $BLUE "💡 Tip: Check scripts/README.md for detailed usage instructions"