from typing import Protocol
from switchboard.interfaces.service import IService
from switchboard.types.task import Task, TaskResult
from switchboard.types.evaluation import MetricScore, Recommendation, EvaluationReport

class IEvaluator(Protocol):
    """Plugin contract representing a single dimension of task evaluations."""

    def evaluate(self, task: Task, result: TaskResult) -> tuple[list[MetricScore], list[Recommendation]]:
        """
        Analyze task output and resource logs to produce metrics and insights.
        
        Args:
            task: Task description.
            result: Completed TaskResult payload.
            
        Returns:
            Tuple of (list of MetricScore, list of Recommendation).
        """
        ...


class IEvaluationEngine(IService, Protocol):
    """Platform coordinator coordinating metrics collection and reflection generation."""

    async def evaluate_task(self, task: Task, result: TaskResult) -> EvaluationReport:
        """
        Run all registered evaluators, compile the report, and update Memory.
        
        Args:
            task: Completed Task context.
            result: Completed TaskResult metrics.
            
        Returns:
            Aggregated EvaluationReport snapshot.
        """
        ...

    def register_evaluator(self, evaluator: IEvaluator) -> None:
        """
        Register a new evaluator plugin.
        
        Args:
            evaluator: Custom evaluator implementing IEvaluator.
        """
        ...
