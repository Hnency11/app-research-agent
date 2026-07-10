"""
Data models for the SaaS App Research Pipeline.

Contains Pydantic models for structured data representation, serialization,
validation, and CSV/JSON exporting capabilities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer


class SelfServeStatus(str, Enum):
    """Enumeration of SaaS self-serve accessibility status."""
    SELF_SERVE = "self-serve"
    GATED = "gated"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class BuildabilityVerdict(str, Enum):
    """Verdict on the ease/feasibility of building integrations/MCP servers for the app."""
    BUILDABLE = "buildable"
    UNBUILDABLE = "unbuildable"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    """Status of information verification."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class Evidence(BaseModel):
    """Official source evidence supporting the research findings."""
    model_config = ConfigDict()

    url: HttpUrl = Field(..., description="Official URL of the source evidence")
    title: str = Field(..., description="Title of the webpage/document")
    snippet: str = Field(..., description="Key textual excerpt showing proof of verification")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of retrieval")


class VerificationResult(BaseModel):
    """Detailed verification report output from the verification agent."""
    is_verified: bool = Field(..., description="Overall verification flag")
    verified_fields: List[str] = Field(default_factory=list, description="Fields validated successfully")
    mismatches: Dict[str, Any] = Field(default_factory=dict, description="Identified discrepancies by field name")
    notes: Optional[str] = Field(None, description="Detailed verification notes and observations")
    verified_at: datetime = Field(default_factory=datetime.utcnow, description="Verification execution timestamp")


class AppResearch(BaseModel):
    """SaaS Application Research Result containing all evaluated attributes."""
    app_name: str = Field(..., description="Common commercial name of the SaaS application")
    category: str = Field(..., description="SaaS industry classification (e.g. CRM, Analytics)")
    description: str = Field(..., description="One-line summary description of the application")
    auth_methods: List[str] = Field(..., description="Authentication mechanisms supported (e.g., OAuth2, API Keys)")
    self_serve_status: SelfServeStatus = Field(default=SelfServeStatus.UNKNOWN, description="Sign-up model status")
    api_surface: str = Field(..., description="Description of developer API surface scope")
    api_types: List[str] = Field(..., description="Supported protocols (e.g., REST, GraphQL, Webhooks, gRPC)")
    sdk_available: bool = Field(default=False, description="Presence of official SDKs")
    webhook_support: bool = Field(default=False, description="Supports webhooks for outbound events")
    mcp_support: bool = Field(default=False, description="Has existing Model Context Protocol support")
    buildability_verdict: BuildabilityVerdict = Field(default=BuildabilityVerdict.UNKNOWN, description="Verdict on developer buildability")
    main_blocker: Optional[str] = Field(None, description="Primary blocker to development if verdict is unbuildable/partial")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence references supporting these facts")
    confidence_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Pipeline confidence percentage from 0 to 100")
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED, description="Status of verifier validation")
    verification_notes: Optional[str] = Field(None, description="Detailed notes on the verification outcome")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    @field_serializer('evidence')
    def serialize_evidence(self, evidence: List[Evidence]) -> List[Dict[str, Any]]:
        """Custom serializer to export Evidence models to primitive dictionaries."""
        return [ev.model_dump() for ev in evidence]

    def to_csv_dict(self) -> Dict[str, Any]:
        """Flatten nested fields for tabular CSV storage compatibility.
        
        Converts lists and nested dicts/models into string representations.
        """
        data = self.model_dump()
        
        # Flatten simple list fields to string arrays/comma separated lists
        data["auth_methods"] = ", ".join(self.auth_methods)
        data["api_types"] = ", ".join(self.api_types)
        
        # Convert evidence URLs to a simple comma-separated list
        data["evidence"] = ", ".join(str(ev.url) for ev in self.evidence)
        
        # Format date as ISO string
        data["last_updated"] = self.last_updated.isoformat()
        
        return data


class ResearchStatistics(BaseModel):
    """Aggregate statistics compiled across all analyzed applications."""
    total_apps: int = Field(..., description="Total SaaS apps target list size")
    completed_apps: int = Field(0, description="Total apps successfully completed")
    failed_apps: int = Field(0, description="Total apps that failed during pipeline processing")
    average_confidence: float = Field(0.0, description="Average confidence score across SaaS reports")
    buildable_count: int = Field(0, description="Number of apps verified as buildable")
    mcp_supported_count: int = Field(0, description="Number of apps with existing MCP support")
    category_distribution: Dict[str, int] = Field(default_factory=dict, description="Count of apps by category")
    execution_time_seconds: float = Field(0.0, description="Total time taken to process the batch")
