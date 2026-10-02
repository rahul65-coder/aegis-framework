"""Specific Agent Roles."""
from .base import BaseAgent

class Architect(BaseAgent): pass
class Implementer(BaseAgent): pass
class Verifier(BaseAgent): pass
class DriftGuard(BaseAgent): pass
class Integrator(BaseAgent): pass
