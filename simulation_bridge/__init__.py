"""Convenience utilities for the Simulation Bridge package."""
from .src.utils.config_loader import set_inmemory_mode

set_inmemory_mode(True)

from .src.protocol_adapters.inmemory.inmemory_adapter import SimulationBridge

__all__ = ["SimulationBridge"]
