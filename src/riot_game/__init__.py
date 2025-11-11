"""Riot: Civil Unrest — Kosovo–Serbia simulation package.

This package provides an ethically-aware educational prototype that models
crowd sentiment, faction morale, and humanitarian logistics in a
fictionalized civic unrest scenario. All systems emphasize de-escalation
and civilian protection.
"""

from .game import Simulation
from .gui import SimulationGUI

__all__ = ["Simulation", "SimulationGUI"]
