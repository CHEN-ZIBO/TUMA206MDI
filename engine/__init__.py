"""Simulation engine package - wires M1+M2 closed loop into M3."""

from .runtime import SimulationEngine
from .remote import RemoteEngineProxy

__all__ = ["SimulationEngine", "RemoteEngineProxy"]
