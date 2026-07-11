import time
from switchboard.types.evaluation import EvaluationReport, MetricScore, Recommendation
from switchboard.evaluation.scoring import ScoringAggregator
from switchboard.types.task import Task

class ReportBuilder:
    """
    Utility builder for constructing formatted EvaluationReports from metrics and recommendations.
    """

    @staticmethod
    def build_report(
        task: Task,
        metrics: list[MetricScore],
        recommendations: list[Recommendation]
    ) -> EvaluationReport:
        """Compiles and scores an EvaluationReport."""
        overall_score, passed = ScoringAggregator.calculate_overall(metrics)
        
        return EvaluationReport(
            task_id=task.task_id,
            metrics=metrics,
            overall_score=overall_score,
            passed=passed,
            recommendations=recommendations,
            created_at=time.time()
        )
