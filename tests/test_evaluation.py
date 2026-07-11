import pytest
import time
from uuid import uuid4
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.types.task import Task, TaskResult, TaskStatus, Artifact, ArtifactType
from switchboard.types.evaluation import MetricScore, Recommendation, EvaluationMetricType
from switchboard.evaluation.evaluators import ExecutionEvaluator, ResourceEvaluator, ArtifactEvaluator
from switchboard.evaluation.scoring import ScoringAggregator
from switchboard.types.events import (
    EvaluationStartedEvent,
    RecommendationGeneratedEvent,
    EvaluationCompletedEvent,
)

def test_evaluators_rules() -> None:
    # 1. Prepare success task
    task = Task(name="Success Task", objective="write code", context_id=uuid4())
    task.max_retries = 3
    task.retry_count = 0
    task.started_at = 100.0
    task.finished_at = 102.0  # 2 seconds duration
    
    result = TaskResult(status=TaskStatus.COMPLETED, artifacts=[Artifact(name="code.py", type=ArtifactType.CODE)])
    
    exec_eval = ExecutionEvaluator()
    res_eval = ResourceEvaluator()
    art_eval = ArtifactEvaluator()
    
    # Evaluate
    m_exec, r_exec = exec_eval.evaluate(task, result)
    m_res, r_res = res_eval.evaluate(task, result)
    m_art, r_art = art_eval.evaluate(task, result)
    
    # Success task should have high scores
    assert any(m.name == "task_success" and m.value == 1.0 for m in m_exec)
    assert any(m.name == "retry_overhead" and m.value == 1.0 for m in m_exec)
    assert any(m.name == "execution_latency" and m.value == 1.0 for m in m_exec)
    assert len(r_exec) == 0
    
    assert any(m.name == "vram_efficiency" and m.value == 1.0 for m in m_res)
    assert any(m.name == "artifact_validity" and m.value == 1.0 for m in m_art)
    
    # 2. Prepare failed task with retries and no artifacts
    task_fail = Task(name="Generate code", objective="write code", context_id=uuid4())
    task_fail.max_retries = 3
    task_fail.retry_count = 2
    task_fail.started_at = 100.0
    task_fail.finished_at = 135.0  # 35 seconds (slow!)
    
    result_fail = TaskResult(status=TaskStatus.FAILED, artifacts=[], error="SyntaxError")
    
    m_fail_exec, r_fail_exec = exec_eval.evaluate(task_fail, result_fail)
    m_fail_art, r_fail_art = art_eval.evaluate(task_fail, result_fail)
    
    # Scores should decay/be zero
    assert any(m.name == "task_success" and m.value == 0.0 for m in m_fail_exec)
    assert any(m.name == "retry_overhead" and m.value == 1.0 - (2.0/3.0) for m in m_fail_exec)
    assert any(m.name == "execution_latency" and m.value == 0.0 for m in m_fail_exec)
    assert len(r_fail_exec) == 1
    assert "lowering LLM temperature" in r_fail_exec[0].actionable_insight
    
    assert any(m.name == "artifact_validity" and m.value == 0.0 for m in m_fail_art)
    assert len(r_fail_art) == 1
    assert "expected code or report output" in r_fail_art[0].actionable_insight


def test_scoring_aggregator() -> None:
    # Weighted average calculation
    metrics = [
        MetricScore(name="m1", type=EvaluationMetricType.EXECUTION, value=1.0, weight=2.0),
        MetricScore(name="m2", type=EvaluationMetricType.RESOURCE, value=0.4, weight=1.0)
    ]
    score, passed = ScoringAggregator.calculate_overall(metrics)
    # (1.0*2.0 + 0.4*1.0) / 3.0 = 0.8
    assert score == 0.8
    assert passed is True
    
    # Highly weighted metric failed (weight >= 2.0)
    metrics_critical = [
        MetricScore(name="m1", type=EvaluationMetricType.EXECUTION, value=0.0, passed=False, weight=2.0),
        MetricScore(name="m2", type=EvaluationMetricType.RESOURCE, value=1.0, weight=1.0)
    ]
    score_crit, passed_crit = ScoringAggregator.calculate_overall(metrics_critical)
    assert score_crit == 0.3333
    assert passed_crit is False


@pytest.mark.asyncio
async def test_evaluation_engine_pipeline_and_memory_reflection_loop() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    evaluation_engine = kernel.get_service("evaluation_engine")
    memory_engine = kernel.get_service("memory_engine")
    event_bus = kernel.get_service("event_bus")
    
    # Track event bus dispatches
    dispatched_events = []
    async def log_event(event) -> None:
        dispatched_events.append(event)
        
    await event_bus.subscribe(EvaluationStartedEvent, log_event)
    await event_bus.subscribe(RecommendationGeneratedEvent, log_event)
    await event_bus.subscribe(EvaluationCompletedEvent, log_event)
    
    # Create failing task context
    task = Task(name="failing code block", objective="write code", context_id=uuid4())
    task.max_retries = 2
    task.retry_count = 1
    task.started_at = time.time() - 10.0
    task.finished_at = time.time()
    
    result = TaskResult(status=TaskStatus.FAILED, error="Timeout")
    
    # Evaluate
    report = await evaluation_engine.evaluate_task(task, result)
    
    assert report.passed is False
    assert report.overall_score < 0.5
    assert len(report.recommendations) > 0
    
    # Verify event dispatches
    event_types = [type(e) for e in dispatched_events]
    assert EvaluationStartedEvent in event_types
    assert RecommendationGeneratedEvent in event_types
    assert EvaluationCompletedEvent in event_types
    
    # Query reflection stored in Memory Engine to verify the loop is closed!
    from switchboard.types.memory import MemoryQuery
    reflections = await memory_engine.retrieve_memories(
        query=MemoryQuery(tags=[f"task_{task.task_id}"], limit=5)
    )
    assert len(reflections) == 1
    assert reflections[0].task_id == task.task_id
    assert "Timeout" in reflections[0].payload["what_failed"]
    assert any("lowering LLM temperature" in r for r in reflections[0].payload["recommendations"])
    
    await kernel.shutdown()
