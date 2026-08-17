"""
CampusOS Milestone 6 Bounded Trust Score Engine.
TrustService is an alias for TrustScoreService in trust_score_service.py.
"""

from app.services.trust_score_service import TrustScoreService

# Backwards compatibility alias for existing callers
TrustService = TrustScoreService

__all__ = ["TrustScoreService", "TrustService"]
