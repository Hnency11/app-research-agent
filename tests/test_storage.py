"""
Tests for SaaS Research Pipeline Storage.

Validates that JSONStorage and CSVStorage correctly serialize, consolidate,
and persist data structures under isolated test directories.
"""

import json
from pathlib import Path
import pytest
from core.models import AppResearch
from storage.json_storage import JSONStorage
from storage.csv_storage import CSVStorage


@pytest.mark.asyncio
async def test_json_storage_operations(tmp_path, mock_app_research):
    """Verifies JSONStorage saves individual app files and consolidates bulk listings."""
    # Override settings BASE_DIR inside storage using temp path
    storage = JSONStorage(base_dir=tmp_path)
    
    # Save individual staged app research
    await storage.save_app_research(mock_app_research, stage="raw")
    
    # Verify file is created in target structure
    expected_file = tmp_path / "data" / "raw" / "stripe.json"
    assert expected_file.exists()
    
    # Load individual staged app research
    loaded_app = await storage.load_app_research("Stripe", stage="raw")
    assert loaded_app is not None
    assert loaded_app.app_name == "Stripe"
    assert loaded_app.category == "Payment Gateway"

    # Save consolidated bulk outputs
    await storage.save_bulk_research([mock_app_research], "research.json")
    consolidated_file = tmp_path / "output" / "research.json"
    assert consolidated_file.exists()
    
    with open(consolidated_file, "r") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["app_name"] == "Stripe"


@pytest.mark.asyncio
async def test_csv_storage_bulk_operations(tmp_path, mock_app_research):
    """Verifies CSVStorage converts structured lists to flat CSV layouts."""
    storage = CSVStorage(base_dir=tmp_path)
    
    # Save bulk CSV
    await storage.save_bulk_research([mock_app_research], "research.csv")
    csv_file = tmp_path / "output" / "research.csv"
    assert csv_file.exists()
    
    # Verify content formatting
    import pandas as pd
    df = pd.read_csv(csv_file)
    assert len(df) == 1
    assert df.iloc[0]["app_name"] == "Stripe"
    assert df.iloc[0]["auth_methods"] == "API Key, OAuth2"  # Flattened list formatting
    assert df.iloc[0]["api_types"] == "REST, Webhooks"
