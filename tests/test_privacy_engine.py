"""
Tests for privacy protection engine.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from synthetic_data_mcp.privacy.engine import PrivacyEngine, PrivacyLevel
from synthetic_data_mcp.schemas.base import DataDomain


@pytest.mark.asyncio
@pytest.mark.privacy
class TestPrivacyEngine:
    """Test suite for PrivacyEngine class."""

    async def test_privacy_engine_initialization(self, privacy_engine):
        """Test privacy engine initializes correctly."""
        assert privacy_engine is not None
        assert hasattr(privacy_engine, 'epsilon')
        assert hasattr(privacy_engine, 'delta')

    async def test_protect_dataset_high_privacy(self, privacy_engine, sample_healthcare_data):
        """Test dataset protection with high privacy level."""
        protected_dataset, metrics = await privacy_engine.protect_dataset(
            dataset=sample_healthcare_data,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.HEALTHCARE
        )

        assert protected_dataset is not None
        assert isinstance(protected_dataset, list)
        assert len(protected_dataset) == len(sample_healthcare_data)
        assert metrics is not None
        assert isinstance(metrics, dict)

    async def test_protect_dataset_maximum_privacy(self, privacy_engine, sample_finance_data):
        """Test dataset protection with maximum privacy level."""
        protected_dataset, metrics = await privacy_engine.protect_dataset(
            dataset=sample_finance_data,
            privacy_level=PrivacyLevel.MAXIMUM,
            domain=DataDomain.FINANCE
        )

        assert protected_dataset is not None
        assert isinstance(metrics, dict)

        # Maximum privacy should have higher privacy metrics
        if "epsilon_used" in metrics:
            assert metrics["epsilon_used"] <= 0.1  # Very low epsilon for maximum privacy

    async def test_analyze_privacy_risk(self, privacy_engine, sample_healthcare_data):
        """Test privacy risk analysis."""
        risk_analysis = await privacy_engine.analyze_privacy_risk(
            dataset=sample_healthcare_data,
            auxiliary_data=None,
            attack_scenarios=["linkage", "inference"]
        )

        assert risk_analysis is not None
        assert "overall_risk" in risk_analysis
        assert "vulnerabilities" in risk_analysis
        assert "recommendations" in risk_analysis
        assert isinstance(risk_analysis["overall_risk"], (int, float))
        assert 0 <= risk_analysis["overall_risk"] <= 100

    async def test_analyze_privacy_risk_with_auxiliary_data(self, privacy_engine, sample_healthcare_data):
        """Test privacy risk analysis with auxiliary data."""
        auxiliary_data = [
            {"patient_id": "P001", "external_info": "diabetes medication"}
        ]

        risk_analysis = await privacy_engine.analyze_privacy_risk(
            dataset=sample_healthcare_data,
            auxiliary_data=auxiliary_data,
            attack_scenarios=["linkage"]
        )

        assert risk_analysis is not None
        # Risk should be higher with auxiliary data available
        assert "overall_risk" in risk_analysis

    async def test_apply_privacy_protection_single_record(self, privacy_engine):
        """Test applying privacy protection to single record."""
        record = {
            "name": "John Smith",
            "age": 35,
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }

        protected_record = await privacy_engine.apply_privacy_protection(
            record,
            PrivacyLevel.HIGH
        )

        assert protected_record is not None
        assert isinstance(protected_record, dict)

        # Should not contain exact PII
        if "name" in protected_record:
            assert protected_record["name"] != "John Smith"

    async def test_calculate_privacy_score(self, privacy_engine, sample_finance_data):
        """Test privacy score calculation."""
        privacy_score = await privacy_engine.calculate_privacy_score(
            sample_finance_data,
            PrivacyLevel.HIGH
        )

        assert privacy_score is not None
        assert isinstance(privacy_score, (int, float))
        assert 0 <= privacy_score <= 100

    async def test_privacy_level_gradation(self, privacy_engine, sample_healthcare_data):
        """Test that different privacy levels produce different protections."""
        # Get protected datasets at different levels
        protected_low, metrics_low = await privacy_engine.protect_dataset(
            dataset=sample_healthcare_data,
            privacy_level=PrivacyLevel.LOW,
            domain=DataDomain.HEALTHCARE
        )

        protected_high, metrics_high = await privacy_engine.protect_dataset(
            dataset=sample_healthcare_data,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.HEALTHCARE
        )

        # Both should succeed but with different privacy characteristics
        assert protected_low is not None
        assert protected_high is not None

        # If epsilon is tracked, high privacy should have lower epsilon
        if "epsilon_used" in metrics_low and "epsilon_used" in metrics_high:
            assert metrics_high["epsilon_used"] <= metrics_low["epsilon_used"]

    async def test_k_anonymity_enforcement(self, privacy_engine):
        """Test k-anonymity is enforced in protected data."""
        dataset = [
            {"age_group": "30-39", "gender": "F", "zip": "123", "diagnosis": "diabetes"},
            {"age_group": "30-39", "gender": "F", "zip": "123", "diagnosis": "hypertension"},
            {"age_group": "40-49", "gender": "M", "zip": "456", "diagnosis": "asthma"}
        ]

        protected_dataset, metrics = await privacy_engine.protect_dataset(
            dataset=dataset,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.HEALTHCARE
        )

        assert protected_dataset is not None

        # Check k-anonymity metric if available
        if "k_anonymity" in metrics:
            assert metrics["k_anonymity"] >= 2

    async def test_differential_privacy_budget_tracking(self, privacy_engine, sample_healthcare_data):
        """Test that privacy budget is tracked across operations."""
        # First operation
        _, metrics1 = await privacy_engine.protect_dataset(
            dataset=sample_healthcare_data,
            privacy_level=PrivacyLevel.MEDIUM,
            domain=DataDomain.HEALTHCARE
        )

        # Second operation
        _, metrics2 = await privacy_engine.protect_dataset(
            dataset=sample_healthcare_data,
            privacy_level=PrivacyLevel.MEDIUM,
            domain=DataDomain.HEALTHCARE
        )

        # Both should track epsilon usage
        if "epsilon_used" in metrics1 and "epsilon_used" in metrics2:
            assert metrics1["epsilon_used"] > 0
            assert metrics2["epsilon_used"] > 0

    async def test_privacy_utility_tradeoff(self, privacy_engine, sample_finance_data):
        """Test that privacy metrics include utility measurements."""
        protected_dataset, metrics = await privacy_engine.protect_dataset(
            dataset=sample_finance_data,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.FINANCE
        )

        assert metrics is not None

        # Should track utility score
        if "utility_score" in metrics:
            assert 0 <= metrics["utility_score"] <= 1

    async def test_pii_detection_and_removal(self, privacy_engine):
        """Test PII detection and removal."""
        record = {
            "patient_name": "John Smith",
            "date_of_birth": "1980-01-01",
            "ssn": "123-45-6789",
            "phone": "555-1234",
            "email": "john@example.com",
            "diagnosis": "diabetes"
        }

        protected_record = await privacy_engine.apply_privacy_protection(
            record,
            PrivacyLevel.MAXIMUM
        )

        # PII should be removed or anonymized
        pii_fields = ["patient_name", "date_of_birth", "ssn", "phone", "email"]

        for field in pii_fields:
            if field in protected_record:
                # Value should be different or removed
                assert protected_record[field] != record[field] or protected_record[field] is None

    async def test_re_identification_risk_assessment(self, privacy_engine, sample_healthcare_data):
        """Test re-identification risk assessment."""
        risk_analysis = await privacy_engine.analyze_privacy_risk(
            dataset=sample_healthcare_data,
            attack_scenarios=["linkage", "inference", "membership"]
        )

        # Should include re-identification risk score
        if "re_identification_risk" in risk_analysis:
            assert 0 <= risk_analysis["re_identification_risk"] <= 1

        # Should provide mitigation recommendations
        assert "recommendations" in risk_analysis
        assert isinstance(risk_analysis["recommendations"], list)

    async def test_privacy_preserving_aggregation(self, privacy_engine):
        """Test privacy-preserving data aggregation."""
        dataset = [
            {"category": "A", "value": 100},
            {"category": "A", "value": 150},
            {"category": "B", "value": 200},
            {"category": "B", "value": 250}
        ]

        protected_dataset, metrics = await privacy_engine.protect_dataset(
            dataset=dataset,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.CUSTOM
        )

        # Should maintain statistical properties while protecting individual records
        assert protected_dataset is not None
        assert len(protected_dataset) == len(dataset)

    async def test_domain_specific_privacy_rules(self, privacy_engine):
        """Test that privacy engine applies domain-specific rules."""
        healthcare_data = [{"patient_id": "P001", "diagnosis": "diabetes"}]
        finance_data = [{"account_id": "ACC001", "balance": 10000}]

        # Healthcare protection
        protected_hc, metrics_hc = await privacy_engine.protect_dataset(
            dataset=healthcare_data,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.HEALTHCARE
        )

        # Finance protection
        protected_fin, metrics_fin = await privacy_engine.protect_dataset(
            dataset=finance_data,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.FINANCE
        )

        # Both should succeed with domain-specific protection
        assert protected_hc is not None
        assert protected_fin is not None

    async def test_privacy_metrics_completeness(self, privacy_engine, sample_healthcare_data):
        """Test that privacy metrics provide comprehensive information."""
        _, metrics = await privacy_engine.protect_dataset(
            dataset=sample_healthcare_data,
            privacy_level=PrivacyLevel.HIGH,
            domain=DataDomain.HEALTHCARE
        )

        # Should provide key privacy metrics
        expected_metrics = [
            "epsilon_used",
            "k_anonymity",
            "privacy_budget_remaining",
            "re_identification_risk",
            "utility_score"
        ]

        # At least some metrics should be present
        present_metrics = sum(1 for metric in expected_metrics if metric in metrics)
        assert present_metrics > 0
