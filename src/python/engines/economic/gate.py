from .config import EconomicConfig


def approve(nev_bps: float, ppe: float, config: EconomicConfig) -> bool:
    return nev_bps > config.minimum_nev_bps and ppe >= config.ppe_threshold
