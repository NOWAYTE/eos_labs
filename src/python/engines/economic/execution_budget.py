from .config import EconomicConfig


def calculate_execution_budget_bps(
    expected_edge_bps: float,
    edge_uncertainty_bps: float,
    config: EconomicConfig,
) -> float:
    return expected_edge_bps - config.gamma_edge_uncertainty * edge_uncertainty_bps
