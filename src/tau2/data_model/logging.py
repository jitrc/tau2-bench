from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from tau2.utils.utils import get_now


class ToolExecutionLog(BaseModel):
    """Individual tool execution log entry"""
    tool_call_id: str = Field(description="Unique identifier for this tool call")
    tool_name: str = Field(description="Name of the tool called")
    requestor: str = Field(description="Who made the call (user/assistant)")
    arguments: Dict[str, Any] = Field(description="Tool call arguments")
    pre_call_timestamp: str = Field(description="Timestamp before execution")
    post_call_timestamp: Optional[str] = Field(description="Timestamp after execution", default=None)
    execution_time_ms: Optional[float] = Field(description="Execution time in milliseconds", default=None)
    success: bool = Field(description="Whether the call succeeded")
    result_preview: Optional[str] = Field(description="First 200 chars of result", default=None)
    error_details: Optional[str] = Field(description="Error message if failed", default=None)
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class EnvironmentStateSnapshot(BaseModel):
    """Environment state at a point in time"""
    timestamp: str = Field(default_factory=get_now)
    step_idx: int = Field(description="Step number in simulation")
    db_hash: Optional[str] = Field(description="Hash of environment database", default=None)
    user_db_hash: Optional[str] = Field(description="Hash of user database", default=None)
    state_changed: bool = Field(description="Whether state changed from previous snapshot")
    triggered_by: str = Field(description="What triggered this snapshot (tool_call, step_start, etc)")


class ExecutionMetrics(BaseModel):
    """High-level execution metrics for a simulation"""
    total_tool_calls: int = Field(description="Total number of tool calls made")
    failed_tool_calls: int = Field(description="Number of failed tool calls")
    total_execution_time_ms: float = Field(description="Total time spent in tool execution")
    average_execution_time_ms: float = Field(description="Average tool execution time")
    unique_tools_used: List[str] = Field(description="List of unique tool names used")
    state_changes: int = Field(description="Number of environment state changes")