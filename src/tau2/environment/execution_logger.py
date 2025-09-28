import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from tau2.data_model.logging import (
    ToolExecutionLog,
    EnvironmentStateSnapshot,
    ExecutionMetrics,
    ContextUsageSnapshot
)
from tau2.utils.utils import get_now
from tau2.utils.llm_utils import get_token_usage

if TYPE_CHECKING:
    from tau2.environment.environment import Environment


class ExecutionLogger:
    """Handles detailed logging of tool executions and environment state"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.execution_logs: List[ToolExecutionLog] = []
        self.state_snapshots: List[EnvironmentStateSnapshot] = []
        self.context_snapshots: List[ContextUsageSnapshot] = []
        self.current_step_idx = 0
        self.current_messages: List = []  # Track current conversation messages
        self.previous_db_state: Optional[Dict[str, Any]] = None  # Track previous db state for diff
        self.previous_user_db_state: Optional[Dict[str, Any]] = None  # Track previous user db state for diff

    def _calculate_db_diff(self, current_state: Optional[Dict[str, Any]],
                          previous_state: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate the diff between current and previous database states"""
        if current_state is None or previous_state is None:
            return None

        if current_state == previous_state:
            return None  # No changes

        diff = {
            "added": {},
            "modified": {},
            "removed": {}
        }

        # Find added and modified items
        for key, current_value in current_state.items():
            if key not in previous_state:
                diff["added"][key] = current_value
            elif previous_state[key] != current_value:
                diff["modified"][key] = {
                    "from": previous_state[key],
                    "to": current_value
                }

        # Find removed items
        for key in previous_state:
            if key not in current_state:
                diff["removed"][key] = previous_state[key]

        # Return None if no actual changes
        if not any([diff["added"], diff["modified"], diff["removed"]]):
            return None

        return diff

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
        """Log environment state snapshot with database diff calculation"""
        if not self.enabled:
            return

        # Get current database states
        current_db_state = env.get_db_state()
        current_user_db_state = env.get_user_db_state()

        # Calculate diffs
        db_diff = self._calculate_db_diff(current_db_state, self.previous_db_state)
        user_db_diff = self._calculate_db_diff(current_user_db_state, self.previous_user_db_state)

        # Determine if state actually changed based on diff calculation
        actual_state_changed = db_diff is not None or user_db_diff is not None

        snapshot = EnvironmentStateSnapshot(
            step_idx=self.current_step_idx,
            db_hash=env.get_db_hash(),
            user_db_hash=env.get_user_db_hash(),
            db_diff=db_diff,
            user_db_diff=user_db_diff,
            state_changed=actual_state_changed or state_changed,  # Use calculated change or passed parameter
            triggered_by=triggered_by
        )
        self.state_snapshots.append(snapshot)

        # Update previous states for next comparison
        self.previous_db_state = current_db_state
        self.previous_user_db_state = current_user_db_state

    def increment_step(self):
        """Increment the current step index"""
        self.current_step_idx += 1

    def log_context_usage(self, messages: List, triggered_by: str, model_name: Optional[str] = None):
        """Log context/token usage snapshot"""
        if not self.enabled:
            return

        # Get token usage from current messages
        usage = get_token_usage(messages)

        total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        # Estimate context window usage if we know the model
        context_window_used = None
        model_context_limit = None

        if model_name:
            # Common model context limits (could be expanded)
            model_limits = {
                "gpt-4": 8192,
                "gpt-4o": 128000,
                "gpt-4o-mini": 128000,
                "gpt-3.5-turbo": 16385,
                "claude-3-sonnet": 200000,
                "claude-3-haiku": 200000,
                "claude-3-opus": 200000,
                "claude-3.5-sonnet": 200000,
            }

            # Match partial model names
            for model_key, limit in model_limits.items():
                if model_key in model_name.lower():
                    model_context_limit = limit
                    context_window_used = (total_tokens / limit) * 100 if limit > 0 else None
                    break

        snapshot = ContextUsageSnapshot(
            step_idx=self.current_step_idx,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=total_tokens,
            context_window_used=context_window_used,
            model_context_limit=model_context_limit,
            triggered_by=triggered_by
        )

        self.context_snapshots.append(snapshot)

    def update_messages(self, messages: List):
        """Update the current message list for context tracking"""
        if self.enabled:
            self.current_messages = messages

    def get_execution_metrics(self) -> ExecutionMetrics:
        """Compute execution metrics from logs"""
        if not self.execution_logs and not self.context_snapshots:
            return ExecutionMetrics(
                total_tool_calls=0,
                failed_tool_calls=0,
                total_execution_time_ms=0.0,
                average_execution_time_ms=0.0,
                unique_tools_used=[],
                state_changes=0,
                total_prompt_tokens=0,
                total_completion_tokens=0,
                total_tokens=0,
                max_context_used=None,
                context_window_warnings=0
            )

        # Tool execution metrics
        total_calls = len(self.execution_logs)
        failed_calls = sum(1 for log in self.execution_logs if not log.success)
        execution_times = [log.execution_time_ms for log in self.execution_logs
                          if log.execution_time_ms is not None]
        total_time = sum(execution_times)
        avg_time = total_time / len(execution_times) if execution_times else 0.0
        unique_tools = list(set(log.tool_name for log in self.execution_logs))
        state_changes = len([s for s in self.state_snapshots if s.state_changed])

        # Context usage metrics
        total_prompt_tokens = 0
        total_completion_tokens = 0
        max_context_used = None
        context_warnings = 0

        if self.context_snapshots:
            # Sum all tokens from snapshots
            for snapshot in self.context_snapshots:
                total_prompt_tokens += snapshot.prompt_tokens
                total_completion_tokens += snapshot.completion_tokens

            # Find maximum context usage
            context_usages = [s.context_window_used for s in self.context_snapshots
                            if s.context_window_used is not None]
            if context_usages:
                max_context_used = max(context_usages)
                context_warnings = sum(1 for usage in context_usages if usage > 80.0)

        total_tokens = total_prompt_tokens + total_completion_tokens

        return ExecutionMetrics(
            total_tool_calls=total_calls,
            failed_tool_calls=failed_calls,
            total_execution_time_ms=total_time,
            average_execution_time_ms=avg_time,
            unique_tools_used=unique_tools,
            state_changes=state_changes,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            max_context_used=max_context_used,
            context_window_warnings=context_warnings
        )