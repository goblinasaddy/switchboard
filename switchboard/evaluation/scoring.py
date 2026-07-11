from switchboard.types.evaluation import MetricScore

class ScoringAggregator:
    """
    Computes overall aggregated weighted scores and pass/fail thresholds for evaluation metrics.
    """

    @staticmethod
    def calculate_overall(metrics: list[MetricScore]) -> tuple[float, bool]:
        """
        Aggregate metric scores.
        
        Args:
            metrics: List of individual MetricScore logs.
            
        Returns:
            Tuple of (overall_score, passed).
        """
        if not metrics:
            return 1.0, True
            
        total_weight = sum(m.weight for m in metrics)
        if total_weight == 0.0:
            return 1.0, True
            
        weighted_sum = sum(m.value * m.weight for m in metrics)
        overall_score = weighted_sum / total_weight
        
        # Determine overall pass status
        # If overall score is below 0.5, or if any highly-weighted metric (weight >= 2.0) failed, mark overall fail.
        passed = overall_score >= 0.5
        for metric in metrics:
            if metric.weight >= 2.0 and not metric.passed:
                passed = False
                break
                
        return round(overall_score, 4), passed
