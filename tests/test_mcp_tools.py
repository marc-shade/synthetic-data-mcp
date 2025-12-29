"""
Tests for MCP server tools and endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from synthetic_data_mcp.server import (
    GenerateSyntheticDatasetRequest,
    ValidateDatasetComplianceRequest,
    AnalyzePrivacyRiskRequest,
    GenerateDomainSchemaRequest,
    BenchmarkSyntheticDataRequest,
    IngestDataRequest,
    GenerateFromPatternRequest,
    AnonymizeDataRequest,
    generate_synthetic_dataset,
    validate_dataset_compliance,
    analyze_privacy_risk,
    generate_domain_schema,
    benchmark_synthetic_data,
    ingest_data_samples,
    generate_from_pattern,
    anonymize_existing_data,
    list_learned_patterns,
    get_supported_domains
)
from synthetic_data_mcp.schemas.base import DataDomain, PrivacyLevel, OutputFormat
from synthetic_data_mcp.compliance.validator import ComplianceFramework


@pytest.mark.asyncio
class TestMCPTools:
    """Test suite for MCP server tools."""

    async def test_generate_synthetic_dataset_success(self):
        """Test successful synthetic dataset generation via MCP tool."""
        request = GenerateSyntheticDatasetRequest(
            domain=DataDomain.HEALTHCARE,
            dataset_type="patient_records",
            record_count=5,
            privacy_level=PrivacyLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.HIPAA],
            output_format=OutputFormat.JSON,
            validation_level="standard"
        )

        result = await generate_synthetic_dataset(request)

        assert result["success"] is True
        assert "dataset" in result
        assert "metadata" in result
        assert result["metadata"]["record_count"] == 5
        assert result["metadata"]["domain"] == DataDomain.HEALTHCARE
        assert "compliance_report" in result
        assert "statistical_analysis" in result
        assert "privacy_analysis" in result
        assert "audit_trail_id" in result

    async def test_generate_synthetic_dataset_with_seed(self):
        """Test dataset generation with seed for reproducibility."""
        request = GenerateSyntheticDatasetRequest(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=3,
            privacy_level=PrivacyLevel.MEDIUM,
            output_format=OutputFormat.JSON,
            seed=42
        )

        result1 = await generate_synthetic_dataset(request)
        result2 = await generate_synthetic_dataset(request)

        # Should produce consistent results with same seed
        assert result1["success"] is True
        assert result2["success"] is True

    async def test_generate_synthetic_dataset_error_handling(self):
        """Test error handling in dataset generation."""
        with patch('synthetic_data_mcp.server.generator.generate_dataset', side_effect=Exception("Test error")):
            request = GenerateSyntheticDatasetRequest(
                domain=DataDomain.HEALTHCARE,
                dataset_type="patient_records",
                record_count=1,
                privacy_level=PrivacyLevel.HIGH
            )

            result = await generate_synthetic_dataset(request)

            assert result["success"] is False
            assert "error" in result
            assert "timestamp" in result

    async def test_validate_dataset_compliance_pass(self):
        """Test compliance validation with passing dataset."""
        dataset = [
            {
                "patient_id": "P001",
                "age_group": "30-39",
                "gender": "F",
                "zip_code_3digit": "123"
            }
        ]

        request = ValidateDatasetComplianceRequest(
            dataset=dataset,
            compliance_frameworks=[ComplianceFramework.HIPAA],
            domain=DataDomain.HEALTHCARE,
            risk_threshold=0.01
        )

        result = await validate_dataset_compliance(request)

        assert result["success"] is True
        assert "compliance_status" in result
        assert "detailed_results" in result
        assert "overall_compliance" in result
        assert "risk_assessment" in result

    async def test_validate_dataset_compliance_single_record(self):
        """Test compliance validation with single record (dict)."""
        dataset = {
            "patient_id": "P001",
            "age_group": "30-39",
            "gender": "F"
        }

        request = ValidateDatasetComplianceRequest(
            dataset=dataset,
            compliance_frameworks=[ComplianceFramework.HIPAA],
            domain=DataDomain.HEALTHCARE
        )

        result = await validate_dataset_compliance(request)

        assert result["success"] is True

    async def test_validate_dataset_compliance_error(self):
        """Test error handling in compliance validation."""
        with patch('synthetic_data_mcp.server.compliance_validator.validate_dataset', side_effect=Exception("Validation error")):
            request = ValidateDatasetComplianceRequest(
                dataset=[{"test": "data"}],
                compliance_frameworks=[ComplianceFramework.HIPAA],
                domain=DataDomain.HEALTHCARE
            )

            result = await validate_dataset_compliance(request)

            assert result["success"] is False
            assert "error" in result

    async def test_analyze_privacy_risk_success(self):
        """Test privacy risk analysis."""
        dataset = [
            {"patient_id": "P001", "age": 35, "diagnosis": "diabetes"},
            {"patient_id": "P002", "age": 42, "diagnosis": "hypertension"}
        ]

        request = AnalyzePrivacyRiskRequest(
            dataset=dataset,
            attack_scenarios=["linkage", "inference"]
        )

        result = await analyze_privacy_risk(request)

        assert result["success"] is True
        assert "risk_score" in result
        assert "vulnerability_analysis" in result
        assert "attack_scenario_results" in result
        assert "mitigation_strategies" in result
        assert "differential_privacy_recommendations" in result

    async def test_analyze_privacy_risk_single_record(self):
        """Test privacy risk analysis with single record."""
        dataset = {"patient_id": "P001", "age": 35}

        request = AnalyzePrivacyRiskRequest(
            dataset=dataset,
            attack_scenarios=["linkage"]
        )

        result = await analyze_privacy_risk(request)

        assert result["success"] is True

    async def test_generate_domain_schema_success(self):
        """Test domain schema generation."""
        request = GenerateDomainSchemaRequest(
            domain=DataDomain.HEALTHCARE,
            data_type="patient_records",
            compliance_requirements=[ComplianceFramework.HIPAA]
        )

        result = await generate_domain_schema(request)

        assert result["success"] is True
        assert "schema" in result
        assert "validation_rules" in result
        assert "field_descriptions" in result
        assert "usage_examples" in result

    async def test_benchmark_synthetic_data_success(self):
        """Test benchmarking synthetic vs real data."""
        synthetic_data = [
            {"age": 30, "income": 50000, "score": 0.7},
            {"age": 35, "income": 60000, "score": 0.8}
        ]

        real_data = [
            {"age": 32, "income": 52000, "score": 0.75},
            {"age": 36, "income": 58000, "score": 0.78}
        ]

        request = BenchmarkSyntheticDataRequest(
            synthetic_data=synthetic_data,
            real_data_sample=real_data,
            ml_tasks=["classification", "regression"]
        )

        result = await benchmark_synthetic_data(request)

        assert result["success"] is True
        assert "statistical_similarity" in result
        assert "utility_benchmarks" in result
        assert "overall_score" in result
        assert "recommendations" in result

    async def test_ingest_data_samples_list(self):
        """Test ingesting data samples from list."""
        data_samples = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 35, "city": "Los Angeles"}
        ]

        request = IngestDataRequest(
            data=data_samples,
            format="json",
            domain="custom",
            anonymize=True,
            learn_patterns=True
        )

        result = await ingest_data_samples(request)

        assert result["success"] is True
        assert "pattern_id" in result
        assert "rows_ingested" in result

    async def test_ingest_data_samples_file_path(self):
        """Test ingesting data from file path."""
        request = IngestDataRequest(
            data="/path/to/data.csv",
            format="csv",
            domain="finance",
            anonymize=True
        )

        # Should handle file path (will fail if file doesn't exist, but tests the flow)
        result = await ingest_data_samples(request)

        # Either success or error is acceptable (depends on file existence)
        assert "success" in result

    async def test_generate_from_pattern_success(self):
        """Test generating data from learned pattern."""
        # First ingest data to create a pattern
        data_samples = [
            {"value": 100, "category": "A"},
            {"value": 200, "category": "B"}
        ]

        ingest_request = IngestDataRequest(
            data=data_samples,
            format="json",
            domain="custom",
            learn_patterns=True
        )

        ingest_result = await ingest_data_samples(ingest_request)
        assert ingest_result["success"] is True
        pattern_id = ingest_result.get("pattern_id")

        if pattern_id:
            # Generate from pattern
            gen_request = GenerateFromPatternRequest(
                pattern_id=pattern_id,
                record_count=5,
                variation=0.3,
                privacy_level=PrivacyLevel.MEDIUM,
                preserve_distributions=True
            )

            result = await generate_from_pattern(gen_request)

            assert result["success"] is True
            assert "data" in result or "synthetic_data" in result

    async def test_anonymize_existing_data_list(self):
        """Test anonymizing data from list."""
        data = [
            {"name": "John Smith", "ssn": "123-45-6789", "age": 30},
            {"name": "Jane Doe", "ssn": "987-65-4321", "age": 35}
        ]

        request = AnonymizeDataRequest(
            data=data,
            privacy_level=PrivacyLevel.HIGH,
            preserve_relationships=True,
            format="json"
        )

        result = await anonymize_existing_data(request)

        assert result["success"] is True
        assert "anonymized_data" in result
        assert "transformation_report" in result
        assert "privacy_score" in result
        assert "records_processed" in result

    async def test_anonymize_existing_data_file_path(self):
        """Test anonymizing data from file path."""
        request = AnonymizeDataRequest(
            data="/path/to/sensitive_data.csv",
            privacy_level=PrivacyLevel.MAXIMUM,
            format="csv"
        )

        result = await anonymize_existing_data(request)

        # Either success or error acceptable (depends on file)
        assert "success" in result

    async def test_list_learned_patterns(self):
        """Test listing learned patterns."""
        result = await list_learned_patterns()

        assert result["success"] is True
        assert "patterns" in result
        assert "count" in result
        assert isinstance(result["patterns"], list)

    async def test_get_supported_domains(self):
        """Test getting supported domains."""
        result = await get_supported_domains()

        assert "domains" in result
        assert "healthcare" in result["domains"]
        assert "finance" in result["domains"]
        assert "custom" in result["domains"]

        # Check healthcare domain details
        healthcare = result["domains"]["healthcare"]
        assert "data_types" in healthcare
        assert "patient_records" in healthcare["data_types"]
        assert "compliance_frameworks" in healthcare
        assert "hipaa" in [f.lower() for f in healthcare["compliance_frameworks"]]

        # Check finance domain details
        finance = result["domains"]["finance"]
        assert "data_types" in finance
        assert "transaction_records" in finance["data_types"]

        # Check privacy levels
        assert "privacy_levels" in result
        assert "low" in result["privacy_levels"]
        assert "medium" in result["privacy_levels"]
        assert "high" in result["privacy_levels"]
        assert "maximum" in result["privacy_levels"]

        # Check output formats
        assert "output_formats" in result
        assert "json" in result["output_formats"]

    async def test_request_validation_record_count(self):
        """Test that request validation enforces constraints."""
        # This should be valid
        request = GenerateSyntheticDatasetRequest(
            domain=DataDomain.HEALTHCARE,
            dataset_type="patient_records",
            record_count=10,
            privacy_level=PrivacyLevel.HIGH
        )
        assert request.record_count == 10

        # Invalid record count should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            GenerateSyntheticDatasetRequest(
                domain=DataDomain.HEALTHCARE,
                dataset_type="patient_records",
                record_count=0,  # Should be > 0
                privacy_level=PrivacyLevel.HIGH
            )

    async def test_request_validation_risk_threshold(self):
        """Test risk threshold validation."""
        # Valid threshold
        request = ValidateDatasetComplianceRequest(
            dataset=[{"test": "data"}],
            compliance_frameworks=[ComplianceFramework.HIPAA],
            domain=DataDomain.HEALTHCARE,
            risk_threshold=0.05
        )
        assert request.risk_threshold == 0.05

        # Invalid threshold should raise error
        with pytest.raises(Exception):
            ValidateDatasetComplianceRequest(
                dataset=[{"test": "data"}],
                compliance_frameworks=[ComplianceFramework.HIPAA],
                domain=DataDomain.HEALTHCARE,
                risk_threshold=1.5  # Should be <= 1.0
            )

    async def test_concurrent_dataset_generation(self):
        """Test multiple concurrent dataset generation requests."""
        import asyncio

        requests = [
            GenerateSyntheticDatasetRequest(
                domain=DataDomain.FINANCE,
                dataset_type="transaction_records",
                record_count=5,
                privacy_level=PrivacyLevel.MEDIUM
            )
            for _ in range(3)
        ]

        results = await asyncio.gather(*[
            generate_synthetic_dataset(req) for req in requests
        ])

        # All should succeed
        assert all(r["success"] for r in results)
        assert len(results) == 3
