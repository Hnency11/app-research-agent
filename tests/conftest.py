"""
Pytest configuration file.

Contains base shared test fixtures, path mockups, and structured app research items.
"""

from datetime import datetime
import pytest
from core.models import AppResearch, Evidence, VerificationStatus, SelfServeStatus, BuildabilityVerdict


@pytest.fixture
def mock_evidence() -> Evidence:
    """Provides a sample Evidence data model."""
    return Evidence(
        url="https://docs.stripe.com/api",
        title="Stripe API Reference",
        snippet="Stripe supports REST API keys and webhooks.",
        extracted_at=datetime.utcnow()
    )


@pytest.fixture
def mock_app_research(mock_evidence) -> AppResearch:
    """Provides a sample AppResearch data model for validation testing."""
    return AppResearch(
        app_name="Stripe",
        category="Payment Gateway",
        description="Online payment processing for internet businesses.",
        auth_methods=["API Key", "OAuth2"],
        self_serve_status=SelfServeStatus.SELF_SERVE,
        api_surface="Public REST API with official client SDKs",
        api_types=["REST", "Webhooks"],
        sdk_available=True,
        webhook_support=True,
        mcp_support=False,
        buildability_verdict=BuildabilityVerdict.BUILDABLE,
        main_blocker=None,
        evidence=[mock_evidence],
        confidence_score=95.0,
        verification_status=VerificationStatus.VERIFIED,
        verification_notes="Documentation checked directly.",
        last_updated=datetime.utcnow()
    )
