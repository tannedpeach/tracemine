"""Persisted API contracts. Outcomes describe commands, never semantic correctness."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    repo: str = Field(min_length=1, max_length=4096)
    task: str = Field(min_length=1, max_length=20000)
    test_command: str = Field(min_length=1, max_length=4000)
    evaluator_path: str | None = Field(default=None, max_length=4096)


class ProcessResult(BaseModel):
    exit_code: int
    duration_ms: int
    timed_out: bool = False


class Event(BaseModel):
    id: str
    sequence: int
    timestamp: str
    event_type: str
    title: str
    summary: str = ""
    raw_event: dict[str, Any]
    action_id: str | None = None


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["diagnosed", "insufficient_evidence"]
    first_consequential_event_id: str | None
    failure_mode: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=6000)
    evidence: list[str] = Field(max_length=12)
    suggested_intervention: str = Field(max_length=1500)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def coherent(self) -> "Diagnosis":
        if self.status == "diagnosed":
            if not self.first_consequential_event_id or not self.evidence:
                raise ValueError("A diagnosis requires a referenced event and evidence")
            if not self.suggested_intervention.strip():
                raise ValueError("A diagnosis requires an actionable intervention")
        elif self.first_consequential_event_id is not None:
            raise ValueError("Insufficient evidence must not select a causal event")
        return self


Status = Literal[
    "created",
    "preparing",
    "baseline_testing",
    "running_agent",
    "testing",
    "diagnosing",
    "baseline_failed",
    "failed",
    "succeeded",
    "error",
    "cancelled",
]
TERMINAL = {"baseline_failed", "failed", "succeeded", "error", "cancelled"}


class Run(BaseModel):
    id: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_repo: str
    task: str
    test_command: str
    evaluator_path: str | None = None
    status: Status = "created"
    working_repo: str = ""
    snapshot_id: str = ""
    source_commit: str | None = None
    snapshot_digest: str | None = None
    original_commit: str | None = None
    baseline: ProcessResult | None = None
    agent: ProcessResult | None = None
    final_test: ProcessResult | None = None
    duration_ms: int | None = None
    action_count: int = 0
    files_changed: list[str] = Field(default_factory=list)
    final_diff: str = ""
    diagnosis: Diagnosis | None = None
    diagnosis_error: str | None = None
    error: str | None = None
    parent_run_id: str | None = None
    intervention: str | None = None
    codex_version: str | None = None
    recorded: bool = False
    agent_backend: Literal["codex", "test-double"] = "codex"
