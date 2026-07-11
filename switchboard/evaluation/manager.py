from switchboard.interfaces.evaluation import IEvaluationEngine, IEvaluator
from switchboard.interfaces.service import IService
from switchboard.interfaces.event_bus import IEventBus
from switchboard.interfaces.memory import IMemoryEngine
from switchboard.types.task import Task, TaskResult
from switchboard.types.evaluation import EvaluationReport
from switchboard.types.memory import Reflection
from switchboard.types.events import (
    EvaluationStartedEvent,
    EvaluationCompletedEvent,
    EvaluationFailedEvent,
    RecommendationGeneratedEvent,
)
from switchboard.evaluation.evaluators import ExecutionEvaluator, ResourceEvaluator, ArtifactEvaluator
from switchboard.evaluation.report import ReportBuilder
from switchboard.logging.config import get_logger

logger = get_logger("evaluation_engine")

class EvaluationEngine(IEvaluationEngine, IService):
    """
    Subsystem coordinator managing evaluation plugins, executing scoring pipelines,
    generating final reports, broadcasting events, and compiling Reflections for the Memory Engine.
    """

    def __init__(
        self,
        memory_engine: IMemoryEngine | None = None,
        event_bus: IEventBus | None = None
    ) -> None:
        self._memory_engine = memory_engine
        self._event_bus = event_bus
        self._evaluators: list[IEvaluator] = []

    @property
    def name(self) -> str:
        return "evaluation_engine"

    @property
    def dependencies(self) -> list[str]:
        return ["event_bus", "memory_engine"]

    async def initialize(self) -> None:
        logger.info("Initializing Evaluation Engine")
        # Register default rule-based evaluators
        self.register_evaluator(ExecutionEvaluator())
        self.register_evaluator(ResourceEvaluator())
        self.register_evaluator(ArtifactEvaluator())

    async def start(self) -> None:
        logger.info("Evaluation Engine started")

    async def shutdown(self) -> None:
        logger.info("Shutting down Evaluation Engine")
        self._evaluators.clear()

    # IEvaluationEngine Interface

    def register_evaluator(self, evaluator: IEvaluator) -> None:
        """Register a new evaluation plugin."""
        self._evaluators.append(evaluator)
        logger.info("Registered evaluator plugin", plugin_name=evaluator.__class__.__name__)

    async def evaluate_task(self, task: Task, result: TaskResult) -> EvaluationReport:
        """Execute evaluation pipelines, compile reports, and record reflections."""
        logger.info("Executing task evaluation pipeline", task_id=str(task.task_id))
        
        if self._event_bus:
            await self._event_bus.publish(EvaluationStartedEvent(task.task_id))
            
        metrics = []
        recommendations = []
        
        try:
            # 1. Run all registered evaluator plugins
            for evaluator in self._evaluators:
                try:
                    eval_metrics, eval_recs = evaluator.evaluate(task, result)
                    metrics.extend(eval_metrics)
                    recommendations.extend(eval_recs)
                except Exception as ex:
                    logger.error(
                        "Evaluator execution crashed", 
                        evaluator=evaluator.__class__.__name__, 
                        error=str(ex)
                    )
                    
            # 2. Publish generated recommendations on Event Bus
            if self._event_bus:
                for rec in recommendations:
                    await self._event_bus.publish(
                        RecommendationGeneratedEvent(task.task_id, rec.actionable_insight)
                    )
                    
            # 3. Aggregate metrics and compile report
            report = ReportBuilder.build_report(task, metrics, recommendations)
            
            # 4. Generate reflection and send to Memory Engine to close the loop
            if self._memory_engine:
                what_worked = ""
                what_failed = ""
                if report.passed:
                    what_worked = f"Task '{task.name}' completed with score {report.overall_score:.2f}."
                else:
                    what_failed = (
                        f"Task '{task.name}' failed evaluation checks. "
                        f"Overall score: {report.overall_score:.2f}. Result error: {result.error or 'None'}"
                    )
                    
                reflection = Reflection(
                    task_id=task.task_id,
                    what_worked=what_worked,
                    what_failed=what_failed,
                    recommendations=[r.actionable_insight for r in recommendations],
                    metrics={m.name: m.value for m in metrics}
                )
                
                await self._memory_engine.record_reflection(reflection)
                
            logger.info(
                "Task evaluation completed", 
                task_id=str(task.task_id), 
                overall_score=report.overall_score, 
                passed=report.passed
            )
            
            if self._event_bus:
                await self._event_bus.publish(
                    EvaluationCompletedEvent(task.task_id, report.overall_score, report.passed)
                )
                
            return report
            
        except Exception as ex:
            logger.error("Failed to run task evaluation loop", task_id=str(task.task_id), error=str(ex))
            if self._event_bus:
                await self._event_bus.publish(EvaluationFailedEvent(task.task_id, str(ex)))
            raise
