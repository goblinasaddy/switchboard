from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Any

class EvaluationMetricType(str, Enum):
    EXECUTION = "execution"
    RESOURCE = "resource"
    OUTPUT = "output"
    WORKFLOW = "workflow"
    MEMORY = "memory"

class MetricScore(BaseModel):
    name: str
    type: EvaluationMetricType
    value: float = 0.0  # Normalized score (0.0 to 1.0)
    passed: bool = True
    weight: float = 1.0
    confidence: float = 1.0
    details: dict[str, Any] = Field(default_factory=dict)

class Recommendation(BaseModel):
    recommendation_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    actionable_insight: str
    category: str = "compute"  # compute, context, retry, memory
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvaluationReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    metrics: list[MetricScore] = Field(default_factory=list)
    overall_score: float = 0.0  # Weighted average of all metric scores
    passed: bool = True
    recommendations: list[Recommendation] = Field(default_factory=list)
    created_at: float = 0.0
