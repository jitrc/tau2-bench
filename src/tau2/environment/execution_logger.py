import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from tau2.data_model.logging import (
    ToolExecutionLog,
    EnvironmentStateSnapshot,
    ExecutionMetrics
)
from tau2.utils.utils import get_now

if TYPE_CHECKING:
    from tau2.environment.environment import Environment


class ExecutionLogger:
    """Handles detailed logging of tool executions and environment state"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.execution_logs: List[ToolExecutionLog] = []
        self.state_snapshots: List[EnvironmentStateSnapshot] = []
        self.current_step_idx = 0

    def log_tool_call_start(self, tool_name: str, requestor: str, arguments: Dict[str, Any], call_id: str):
        """Log the start of a tool call"""
        if not self.enabled:
            return

        log_entry = ToolExecutionLog(
            tool_call_id=call_id,
            tool_name=tool_name,
            requestor=requestor,
            arguments=arguments,
            pre_call_timestamp=get_now(),
            success=False  # Will be updated on completion
        )
        self.execution_logs.append(log_entry)

    def log_tool_call_end(self, call_id: str, success: bool, result: Any = None,
                         error: Exception = None, execution_time_ms: float = None):
        """Log the completion of a tool call"""
        if not self.enabled:
            return

        # Find the matching log entry
        log_entry = next((log for log in self.execution_logs if log.tool_call_id == call_id), None)
        if log_entry:
            log_entry.post_call_timestamp = get_now()
            log_entry.success = success
            log_entry.execution_time_ms = execution_time_ms
            if result is not None:
                log_entry.result_preview = str(result)[:200]
            if error is not None:
                log_entry.error_details = str(error)

    def log_state_snapshot(self, env: 'Environment', triggered_by: str, state_changed: bool = False):
        """Log environment state snapshot"""
        if not self.enabled:
            return

        snapshot = EnvironmentStateSnapshot(
            step_idx=self.current_step_idx,
            db_hash=env.get_db_hash(),
            user_db_hash=env.get_user_db_hash(),
            state_changed=state_changed,
            triggered_by=triggered_by
        )
        self.state_snapshots.append(snapshot)

    def increment_step(self):
        """Increment the current step index"""
        self.current_step_idx += 1

    def get_execution_metrics(self) -> ExecutionMetrics:
        """Compute execution metrics from logs"""
        if not self.execution_logs:
            return ExecutionMetrics(
                total_tool_calls=0,
                failed_tool_calls=0,
                total_execution_time_ms=0.0,
                average_execution_time_ms=0.0,
                unique_tools_used=[],
                state_changes=0
            )

        total_calls = len(self.execution_logs)
        failed_calls = sum(1 for log in self.execution_logs if not log.success)
        execution_times = [log.execution_time_ms for log in self.execution_logs
                          if log.execution_time_ms is not None]
        total_time = sum(execution_times)
        avg_time = total_time / len(execution_times) if execution_times else 0.0
        unique_tools = list(set(log.tool_name for log in self.execution_logs))
        state_changes = len([s for s in self.state_snapshots if s.state_changed])

        return ExecutionMetrics(
            total_tool_calls=total_calls,
            failed_tool_calls=failed_calls,
            total_execution_time_ms=total_time,
            average_execution_time_ms=avg_time,
            unique_tools_used=unique_tools,
            state_changes=state_changes
        )