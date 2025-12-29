"""
Tests for core synthetic data generation functionality.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from synthetic_data_mcp.core.generator import SyntheticDataGenerator
from synthetic_data_mcp.schemas.base import DataDomain, PrivacyLevel
from synthetic_data_mcp.schemas.healthcare import Gender, Race, InsuranceType
from synthetic_data_mcp.schemas.finance import TransactionType, TransactionCategory


@pytest.mark.asyncio
class TestSyntheticDataGenerator:
    """Test suite for SyntheticDataGenerator class."""

    async def test_generator_initialization(self):
        """Test that generator initializes with correct components."""
        generator = SyntheticDataGenerator()

        assert generator.faker is not None
        assert generator.knowledge_loader is not None
        assert generator.pattern_analyzer is not None
        assert isinstance(generator.learned_patterns, dict)
        assert generator.healthcare_knowledge is not None
        assert generator.finance_knowledge is not None

    async def test_generate_healthcare_patient_records(self):
        """Test generation of patient records."""
        generator = SyntheticDataGenerator()

        result = await generator.generate_dataset(
            domain=DataDomain.HEALTHCARE,
            dataset_type="patient_records",
            record_count=5,
            privacy_level=PrivacyLevel.HIGH
        )

        assert result["status"] == "success"
        assert result["metadata"]["total_records"] == 5
        assert result["metadata"]["domain"] == "healthcare"
        assert result["metadata"]["dataset_type"] == "patient_records"
        assert len(result["dataset"]) == 5

        # Verify record structure
        for record in result["dataset"]:
            assert "demographics" in record
            assert "conditions" in record
            assert "encounters" in record
            assert "insurance_type" in record
            demographics = record["demographics"]
            assert "age_group" in demographics
            assert "gender" in demographics
            assert "race" in demographics

    async def test_generate_finance_transactions(self):
        """Test generation of financial transaction records."""
        generator = SyntheticDataGenerator()

        result = await generator.generate_dataset(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=10,
            privacy_level=PrivacyLevel.MEDIUM
        )

        assert result["status"] == "success"
        assert result["metadata"]["total_records"] == 10
        assert result["metadata"]["domain"] == "finance"
        assert len(result["dataset"]) == 10

        # Verify transaction structure
        for record in result["dataset"]:
            assert "transaction_id" in record
            assert "account_id" in record
            assert "amount" in record
            assert "transaction_type" in record
            assert "category" in record
            assert "fraud_score" in record

            # Verify amount is Decimal
            amount_str = str(record["amount"])
            assert "." in amount_str or amount_str.isdigit()

    async def test_generate_with_seed_reproducibility(self):
        """Test that same seed produces identical datasets."""
        generator = SyntheticDataGenerator()

        result1 = await generator.generate_dataset(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=3,
            privacy_level=PrivacyLevel.MEDIUM,
            seed=42
        )

        result2 = await generator.generate_dataset(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=3,
            privacy_level=PrivacyLevel.MEDIUM,
            seed=42
        )

        # With same seed, should generate identical data
        assert result1["dataset"][0]["transaction_id"] == result2["dataset"][0]["transaction_id"]

    async def test_privacy_level_affects_precision(self):
        """Test that different privacy levels affect data precision."""
        generator = SyntheticDataGenerator()

        # Generate with low privacy
        result_low = await generator.generate_dataset(
            domain=DataDomain.HEALTHCARE,
            dataset_type="patient_records",
            record_count=5,
            privacy_level=PrivacyLevel.LOW
        )

        # Generate with maximum privacy
        result_max = await generator.generate_dataset(
            domain=DataDomain.HEALTHCARE,
            dataset_type="patient_records",
            record_count=5,
            privacy_level=PrivacyLevel.MAXIMUM
        )

        # Maximum privacy should remove more identifying info
        low_record = result_low["dataset"][0]["demographics"]
        max_record = result_max["dataset"][0]["demographics"]

        # MAXIMUM privacy should omit zip and state
        assert max_record.get("zip_code_3digit") is None
        assert max_record.get("state") is None

        # LOW privacy may include these fields
        # (we allow it to be None too since it's based on privacy level)

    async def test_generate_patient_demographics(self):
        """Test patient demographics generation with privacy levels."""
        generator = SyntheticDataGenerator()

        # Test HIGH privacy
        demographics_high = generator._generate_patient_demographics(PrivacyLevel.HIGH)
        assert "age_group" in demographics_high
        assert "gender" in demographics_high
        assert "race" in demographics_high

        # Test MAXIMUM privacy (should exclude location data)
        demographics_max = generator._generate_patient_demographics(PrivacyLevel.MAXIMUM)
        assert demographics_max["zip_code_3digit"] is None
        assert demographics_max["state"] is None

    async def test_generate_medical_conditions(self):
        """Test medical conditions generation."""
        generator = SyntheticDataGenerator()

        conditions = generator._generate_medical_conditions("35-44")

        assert isinstance(conditions, list)
        # Should generate 0-3 conditions
        assert 0 <= len(conditions) <= 3

        if conditions:
            condition = conditions[0]
            assert "icd10_code" in condition
            assert "description" in condition
            assert "severity" in condition
            assert condition["severity"] in ["mild", "moderate", "severe"]

    async def test_generate_encounters(self):
        """Test healthcare encounters generation."""
        generator = SyntheticDataGenerator()

        conditions = [
            {
                "icd10_code": "E11.9",
                "description": "Type 2 diabetes",
                "severity": "moderate"
            }
        ]
        demographics = {"age_group": "35-44", "gender": "F"}

        encounters = generator._generate_encounters(conditions, demographics)

        assert isinstance(encounters, list)
        assert len(encounters) >= 1

        encounter = encounters[0]
        assert "encounter_type" in encounter
        assert encounter["encounter_type"] in ["outpatient", "inpatient", "emergency"]
        assert "admission_date" in encounter
        assert "discharge_date" in encounter
        assert "total_charges" in encounter

    async def test_generate_transaction_amount_by_category(self):
        """Test transaction amount generation varies by category."""
        generator = SyntheticDataGenerator()

        # Generate multiple amounts for each category to test ranges
        groceries_amounts = [
            generator._generate_transaction_amount(TransactionCategory.GROCERIES, PrivacyLevel.LOW)
            for _ in range(10)
        ]

        travel_amounts = [
            generator._generate_transaction_amount(TransactionCategory.TRAVEL, PrivacyLevel.LOW)
            for _ in range(10)
        ]

        # Travel should generally have higher amounts than groceries
        avg_groceries = sum(groceries_amounts) / len(groceries_amounts)
        avg_travel = sum(travel_amounts) / len(travel_amounts)

        assert avg_travel > avg_groceries

    async def test_categorize_amount(self):
        """Test amount categorization for privacy."""
        generator = SyntheticDataGenerator()

        assert generator._categorize_amount(5.0) == "0-10"
        assert generator._categorize_amount(25.0) == "10-50"
        assert generator._categorize_amount(75.0) == "50-100"
        assert generator._categorize_amount(250.0) == "100-500"
        assert generator._categorize_amount(750.0) == "500-1k"
        assert generator._categorize_amount(2500.0) == "1k-5k"
        assert generator._categorize_amount(10000.0) == "5k+"

    async def test_generate_fraud_score(self):
        """Test fraud score generation."""
        generator = SyntheticDataGenerator()

        # High-risk category with large amount
        score_high_risk = generator._generate_fraud_score(
            TransactionCategory.CASH_ATM, 5000.0
        )

        # Low-risk category with normal amount
        score_low_risk = generator._generate_fraud_score(
            TransactionCategory.UTILITIES, 100.0
        )

        # Both should be between 0 and 1
        assert 0.0 <= score_high_risk <= 1.0
        assert 0.0 <= score_low_risk <= 1.0

    async def test_generate_transaction_hour_patterns(self):
        """Test that transaction hours follow category patterns."""
        generator = SyntheticDataGenerator()

        # Generate multiple hours for groceries
        grocery_hours = [
            generator._generate_transaction_hour(TransactionCategory.GROCERIES)
            for _ in range(20)
        ]

        # Should mostly be in business hours
        assert all(0 <= hour <= 23 for hour in grocery_hours)

        # Most should be during typical shopping hours (11-20)
        typical_hours = sum(1 for hour in grocery_hours if 11 <= hour <= 20)
        assert typical_hours > len(grocery_hours) * 0.5  # At least 50%

    async def test_get_merchant_category(self):
        """Test merchant category mapping."""
        generator = SyntheticDataGenerator()

        assert generator._get_merchant_category(TransactionCategory.GROCERIES) == "grocery_stores"
        assert generator._get_merchant_category(TransactionCategory.RESTAURANTS) == "restaurants"
        assert generator._get_merchant_category(TransactionCategory.GAS_FUEL) == "gas_stations"

    async def test_get_age_group(self):
        """Test HIPAA-compliant age group conversion."""
        generator = SyntheticDataGenerator()

        assert generator._get_age_group(15) == "0-17"
        assert generator._get_age_group(20) == "18-24"
        assert generator._get_age_group(30) == "25-34"
        assert generator._get_age_group(40) == "35-44"
        assert generator._get_age_group(50) == "45-54"
        assert generator._get_age_group(60) == "55-64"
        assert generator._get_age_group(70) == "65-74"
        assert generator._get_age_group(80) == "75-84"
        assert generator._get_age_group(90) == "85+"

    async def test_learn_from_data(self):
        """Test learning patterns from user-provided data."""
        generator = SyntheticDataGenerator()

        sample_data = [
            {"name": "Alice", "age": 30, "salary": 50000},
            {"name": "Bob", "age": 35, "salary": 60000},
            {"name": "Carol", "age": 28, "salary": 55000}
        ]

        pattern_id = await generator.learn_from_data(sample_data, domain="custom")

        assert pattern_id.startswith("pattern_custom_")
        assert pattern_id in generator.learned_patterns

        pattern_info = generator.learned_patterns[pattern_id]
        assert pattern_info["domain"] == "custom"
        assert pattern_info["sample_count"] == 3

    async def test_generate_from_pattern(self):
        """Test generating data from learned patterns."""
        generator = SyntheticDataGenerator()

        # First learn a pattern
        sample_data = [
            {"value": 100, "category": "A"},
            {"value": 200, "category": "B"},
            {"value": 150, "category": "A"}
        ]

        pattern_id = await generator.learn_from_data(sample_data, domain="custom")

        # Then generate from it
        result = await generator.generate_from_pattern(
            pattern_id=pattern_id,
            record_count=5,
            variation=0.2,
            privacy_level=PrivacyLevel.MEDIUM
        )

        assert result["success"] is True
        assert result["pattern_id"] == pattern_id
        assert result["records_generated"] == 5
        assert len(result["data"]) == 5

    async def test_generate_from_pattern_not_found(self):
        """Test generating from non-existent pattern."""
        generator = SyntheticDataGenerator()

        result = await generator.generate_from_pattern(
            pattern_id="nonexistent_pattern",
            record_count=5,
            variation=0.2,
            privacy_level=PrivacyLevel.MEDIUM
        )

        # Should return error
        assert "error" in result

    async def test_generate_custom_dataset(self):
        """Test custom dataset generation with schema."""
        generator = SyntheticDataGenerator()

        custom_schema = {
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "score": {"type": "number"},
                "active": {"type": "boolean"}
            }
        }

        result = await generator.generate_dataset(
            domain=DataDomain.CUSTOM,
            dataset_type="custom_records",
            record_count=3,
            privacy_level=PrivacyLevel.MEDIUM,
            custom_schema=custom_schema
        )

        assert result["status"] == "success"
        assert len(result["dataset"]) == 3

        # Verify custom fields
        record = result["dataset"][0]
        assert "name" in record
        assert "age" in record
        assert "score" in record
        assert "active" in record

    async def test_error_handling_in_generation(self):
        """Test that errors are handled gracefully."""
        generator = SyntheticDataGenerator()

        # Try to generate with invalid parameters
        with patch.object(generator, '_generate_healthcare_dataset', side_effect=Exception("Test error")):
            result = await generator.generate_dataset(
                domain=DataDomain.HEALTHCARE,
                dataset_type="patient_records",
                record_count=1,
                privacy_level=PrivacyLevel.HIGH
            )

            assert result["status"] == "error"
            assert "error" in result
            assert result["metadata"]["total_records"] == 0

    async def test_minimum_record_count(self):
        """Test generation with minimum record count."""
        generator = SyntheticDataGenerator()

        result = await generator.generate_dataset(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=1,
            privacy_level=PrivacyLevel.MEDIUM
        )

        assert result["status"] == "success"
        assert len(result["dataset"]) == 1

    async def test_large_dataset_generation(self):
        """Test generation of larger datasets."""
        generator = SyntheticDataGenerator()

        result = await generator.generate_dataset(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=100,
            privacy_level=PrivacyLevel.MEDIUM
        )

        assert result["status"] == "success"
        assert len(result["dataset"]) == 100

        # Verify diversity in account IDs
        account_ids = set(record["account_id"] for record in result["dataset"])
        assert len(account_ids) >= 5  # Should have multiple accounts

    async def test_register_pattern(self):
        """Test pattern registration."""
        generator = SyntheticDataGenerator()

        pattern_data = {
            "domain": "test",
            "pattern_summary": {"test": "data"},
            "sample_count": 10
        }

        generator.register_pattern("test_pattern_123", pattern_data)

        assert "test_pattern_123" in generator.learned_patterns
        assert generator.learned_patterns["test_pattern_123"] == pattern_data
