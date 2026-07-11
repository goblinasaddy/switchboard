from switchboard.interfaces.evaluation import IEvaluator
from switchboard.types.task import Task, TaskResult, TaskStatus
from switchboard.types.evaluation import MetricScore, Recommendation, EvaluationMetricType

class ExecutionEvaluator(IEvaluator):
    """
    Evaluator checking task completion success, retry counts, and latency bounds.
    """

    def evaluate(self, task: Task, result: TaskResult) -> tuple[list[MetricScore], list[Recommendation]]:
        metrics: list[MetricScore] = []
        recommendations: list[Recommendation] = []
        
        # 1. Success validation
        success_val = 1.0 if result.status == TaskStatus.COMPLETED else 0.0
        metrics.append(
            MetricScore(
                name="task_success",
                type=EvaluationMetricType.EXECUTION,
                value=success_val,
                passed=(success_val == 1.0),
                weight=3.0
            )
        )
        
        # 2. Retry counts validation
        retry_val = 1.0 - min(1.0, task.retry_count / max(1, task.max_retries))
        metrics.append(
            MetricScore(
                name="retry_overhead",
                type=EvaluationMetricType.EXECUTION,
                value=retry_val,
                passed=(task.retry_count < task.max_retries),
                weight=1.0,
                details={"retry_count": task.retry_count}
            )
        )
        if task.retry_count > 0:
            recommendations.append(
                Recommendation(
                    task_id=task.task_id,
                    actionable_insight="Task required retries. Consider lowering LLM temperature or increasing resource buffers.",
                    category="retry",
                    metadata={"retries": task.retry_count}
                )
            )
            
        # 3. Latency scoring (assume under 5s is optimal 1.0, decaying to 0.0 at 30s)
        duration = 0.0
        if task.finished_at and task.started_at:
            duration = task.finished_at - task.started_at
            
        latency_val = 1.0 if duration <= 5.0 else max(0.0, 1.0 - (duration - 5.0) / 25.0)
        metrics.append(
            MetricScore(
                name="execution_latency",
                type=EvaluationMetricType.EXECUTION,
                value=latency_val,
                passed=(duration <= 15.0),
                weight=1.5,
                details={"duration_sec": duration}
            )
        )
        
        return metrics, recommendations


class ResourceEvaluator(IEvaluator):
    """
    Evaluator measuring physical resources allocation efficiency.
    """

    def evaluate(self, task: Task, result: TaskResult) -> tuple[list[MetricScore], list[Recommendation]]:
        metrics: list[MetricScore] = []
        recommendations: list[Recommendation] = []
        
        # Check VRAM limits
        vram_req = task.requirements.estimated_vram_gb if task.requirements else 0.0
        
        # High VRAM tasks score slightly lower on resource footprint efficiency
        vram_score = 1.0 if vram_req < 4.0 else 0.5
        metrics.append(
            MetricScore(
                name="vram_efficiency",
                type=EvaluationMetricType.RESOURCE,
                value=vram_score,
                passed=True,
                weight=1.0,
                details={"vram_gb": vram_req}
            )
        )
        
        if vram_req >= 8.0:
            recommendations.append(
                Recommendation(
                    task_id=task.task_id,
                    actionable_insight="Task VRAM requirements are high. Try quantizing models or using hybrid scheduling policies.",
                    category="compute",
                    metadata={"vram_gb": vram_req}
                )
            )
            
        return metrics, recommendations


class ArtifactEvaluator(IEvaluator):
    """
    Evaluator checking the existence and validity of produced output artifacts.
    """

    def evaluate(self, task: Task, result: TaskResult) -> tuple[list[MetricScore], list[Recommendation]]:
        metrics: list[MetricScore] = []
        recommendations: list[Recommendation] = []
        
        # Determine if task expected artifacts (e.g. CLI Assistant, GitHub Solver)
        has_artifacts = len(result.artifacts) > 0 if result.artifacts else False
        
        # If task description or name mentions 'code', 'file', 'report', or 'patch', it likely expects an artifact
        expects_artifacts = any(word in task.name.lower() or word in task.objective.lower() 
                                for word in ["code", "file", "report", "patch", "artifact"])
        
        artifact_score = 1.0
        passed = True
        if expects_artifacts and not has_artifacts:
            artifact_score = 0.0
            passed = False
            recommendations.append(
                Recommendation(
                    task_id=task.task_id,
                    actionable_insight="Task expected code or report output artifacts, but none were registered. Validate output paths.",
                    category="artifact",
                    metadata={"expected": True}
                )
            )
            
        metrics.append(
            MetricScore(
                name="artifact_validity",
                type=EvaluationMetricType.OUTPUT,
                value=artifact_score,
                passed=passed,
                weight=2.0,
                details={"produced_count": len(result.artifacts) if result.artifacts else 0}
            )
        )
        
        return metrics, recommendations
