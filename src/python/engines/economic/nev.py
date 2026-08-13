from .config import EconomicConfig


def calculate_nev(
    expected_edge_bps: float,
    expected_cost_bps: float,
    edge_uncertainty_bps: float,
    cost_uncertainty_bps: float,
    config: EconomicConfig,
) -> float:
    return (
        expected_edge_bps
        - expected_cost_bps
        - config.lambda_cost_uncertainty * cost_uncertainty_bps
        - config.gamma_edge_uncertainty * edge_uncertainty_bps
    )
