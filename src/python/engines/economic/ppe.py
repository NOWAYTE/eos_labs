import math


def calculate_ppe(
    expected_edge_bps: float,
    expected_cost_bps: float,
    edge_uncertainty_bps: float,
    cost_uncertainty_bps: float,
    correlation: float,
) -> float | None:
    """Return P(E - C > 0) under the documented normality assumption."""
    variance = (
        edge_uncertainty_bps ** 2
        + cost_uncertainty_bps ** 2
        - 2 * correlation * edge_uncertainty_bps * cost_uncertainty_bps
    )
    if variance < 0:
        return None
    if variance == 0:
        return 1.0 if expected_edge_bps > expected_cost_bps else 0.0
    z_score = (expected_edge_bps - expected_cost_bps) / math.sqrt(variance)
    return 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
