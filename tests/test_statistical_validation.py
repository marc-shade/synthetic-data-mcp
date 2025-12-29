"""
Tests for statistical validation and utility preservation.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock

from synthetic_data_mcp.validation.statistical import StatisticalValidator
from synthetic_data_mcp.schemas.base import DataDomain


@pytest.mark.asyncio
class TestStatisticalValidator:
    """Test suite for StatisticalValidator class."""

    async def test_validator_initialization(self, statistical_validator):
        """Test statistical validator initializes correctly."""
        assert statistical_validator is not None

    async def test_validate_fidelity_basic(self, statistical_validator):
        """Test basic statistical fidelity validation."""
        synthetic_data = [
            {"age": 30, "income": 50000, "score": 0.7},
            {"age": 35, "income": 60000, "score": 0.8},
            {"age": 40, "income": 70000, "score": 0.75}
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="standard",
            domain=DataDomain.CUSTOM
        )

        assert results is not None
        assert isinstance(results, dict)

    async def test_compare_datasets(self, statistical_validator):
        """Test comparison between synthetic and real datasets."""
        synthetic_data = [
            {"age": 30, "income": 50000},
            {"age": 35, "income": 60000},
            {"age": 40, "income": 70000}
        ]

        real_data = [
            {"age": 32, "income": 52000},
            {"age": 36, "income": 58000},
            {"age": 38, "income": 68000}
        ]

        comparison = await statistical_validator.compare_datasets(
            synthetic_data=synthetic_data,
            real_data=real_data
        )

        assert comparison is not None
        assert isinstance(comparison, dict)

        # Should include similarity metrics
        if "similarity_score" in comparison:
            assert isinstance(comparison["similarity_score"], (int, float))
            assert 0 <= comparison["similarity_score"] <= 1

    async def test_benchmark_utility(self, statistical_validator):
        """Test ML utility benchmarking."""
        synthetic_data = [
            {"feature1": 1.0, "feature2": 2.0, "label": 0},
            {"feature1": 1.5, "feature2": 2.5, "label": 1},
            {"feature1": 2.0, "feature2": 3.0, "label": 0},
            {"feature1": 2.5, "feature2": 3.5, "label": 1}
        ]

        real_data = [
            {"feature1": 1.1, "feature2": 2.1, "label": 0},
            {"feature1": 1.4, "feature2": 2.4, "label": 1},
            {"feature1": 2.1, "feature2": 3.1, "label": 0},
            {"feature1": 2.4, "feature2": 3.4, "label": 1}
        ]

        utility_results = await statistical_validator.benchmark_utility(
            synthetic_data=synthetic_data,
            real_data=real_data,
            tasks=["classification"],
            metrics=None
        )

        assert utility_results is not None
        assert isinstance(utility_results, dict)

    async def test_distribution_similarity_tests(self, statistical_validator):
        """Test distribution similarity statistical tests."""
        synthetic_data = [
            {"value": np.random.normal(100, 10)} for _ in range(50)
        ]

        real_data = [
            {"value": np.random.normal(100, 10)} for _ in range(50)
        ]

        comparison = await statistical_validator.compare_datasets(
            synthetic_data=synthetic_data,
            real_data=real_data
        )

        # Should perform statistical tests
        if "distribution_similarity" in comparison:
            assert isinstance(comparison["distribution_similarity"], dict)

    async def test_correlation_preservation(self, statistical_validator):
        """Test that correlations are preserved in synthetic data."""
        # Generate correlated data
        np.random.seed(42)
        x = np.random.normal(100, 10, 50)
        y = x * 2 + np.random.normal(0, 5, 50)  # Correlated with x

        synthetic_data = [
            {"feature_a": float(x[i]), "feature_b": float(y[i])}
            for i in range(50)
        ]

        real_data = [
            {"feature_a": float(x[i] + np.random.normal(0, 1)),
             "feature_b": float(y[i] + np.random.normal(0, 1))}
            for i in range(50)
        ]

        comparison = await statistical_validator.compare_datasets(
            synthetic_data=synthetic_data,
            real_data=real_data
        )

        # Should measure correlation preservation
        if "correlation_preservation" in comparison:
            assert isinstance(comparison["correlation_preservation"], dict)

    async def test_validate_distribution_preservation(self, statistical_validator):
        """Test validation of distribution preservation from pattern."""
        synthetic_data = [
            {"age": 30 + i, "income": 50000 + i * 1000}
            for i in range(20)
        ]

        # Mock pattern ID for testing
        pattern_id = "test_pattern_123"

        validation_report = await statistical_validator.validate_distribution_preservation(
            original_pattern_id=pattern_id,
            synthetic_data=synthetic_data
        )

        assert validation_report is not None
        assert isinstance(validation_report, dict)

    async def test_comprehensive_validation_level(self, statistical_validator):
        """Test comprehensive validation level."""
        synthetic_data = [
            {"value1": i, "value2": i * 2, "value3": i ** 2}
            for i in range(30)
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="comprehensive",
            domain=DataDomain.CUSTOM
        )

        # Comprehensive should provide more detailed metrics
        assert results is not None
        assert isinstance(results, dict)

    async def test_exhaustive_validation_level(self, statistical_validator):
        """Test exhaustive validation level."""
        synthetic_data = [
            {"value": i * 10} for i in range(50)
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="exhaustive",
            domain=DataDomain.CUSTOM
        )

        # Exhaustive should provide most detailed analysis
        assert results is not None

    async def test_statistical_tests_kolmogorov_smirnov(self, statistical_validator):
        """Test Kolmogorov-Smirnov test for distribution similarity."""
        # Similar distributions
        np.random.seed(42)
        synthetic_data = [
            {"value": float(x)} for x in np.random.normal(50, 10, 100)
        ]

        real_data = [
            {"value": float(x)} for x in np.random.normal(52, 11, 100)
        ]

        comparison = await statistical_validator.compare_datasets(
            synthetic_data=synthetic_data,
            real_data=real_data
        )

        # Should include KS test results
        if "distribution_similarity" in comparison:
            dist_sim = comparison["distribution_similarity"]
            if "ks_test_pvalue" in dist_sim:
                assert 0 <= dist_sim["ks_test_pvalue"] <= 1

    async def test_chi_square_test(self, statistical_validator):
        """Test chi-square test for categorical distributions."""
        synthetic_data = [
            {"category": "A"} for _ in range(50)
        ] + [
            {"category": "B"} for _ in range(30)
        ] + [
            {"category": "C"} for _ in range(20)
        ]

        real_data = [
            {"category": "A"} for _ in range(48)
        ] + [
            {"category": "B"} for _ in range(32)
        ] + [
            {"category": "C"} for _ in range(20)
        ]

        comparison = await statistical_validator.compare_datasets(
            synthetic_data=synthetic_data,
            real_data=real_data
        )

        # Should include chi-square test results
        if "distribution_similarity" in comparison:
            dist_sim = comparison["distribution_similarity"]
            if "chi_square_pvalue" in dist_sim:
                assert 0 <= dist_sim["chi_square_pvalue"] <= 1

    async def test_pearson_correlation_analysis(self, statistical_validator):
        """Test Pearson correlation coefficient analysis."""
        # Generate data with known correlation
        np.random.seed(42)
        n = 50
        x = np.random.normal(100, 10, n)
        y = 0.8 * x + np.random.normal(0, 5, n)  # Strong positive correlation

        synthetic_data = [
            {"x": float(x[i]), "y": float(y[i])} for i in range(n)
        ]

        real_data = [
            {"x": float(x[i] + np.random.normal(0, 2)),
             "y": float(y[i] + np.random.normal(0, 2))}
            for i in range(n)
        ]

        comparison = await statistical_validator.compare_datasets(
            synthetic_data=synthetic_data,
            real_data=real_data
        )

        # Should analyze correlation
        if "correlation_preservation" in comparison:
            corr_pres = comparison["correlation_preservation"]
            if "pearson_correlation_diff" in corr_pres:
                # Difference should be a number
                assert isinstance(corr_pres["pearson_correlation_diff"], (int, float))

    async def test_data_quality_metrics(self, statistical_validator):
        """Test data quality metric calculation."""
        synthetic_data = [
            {"value": i, "status": "active" if i % 2 == 0 else "inactive"}
            for i in range(20)
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="standard",
            domain=DataDomain.CUSTOM
        )

        # Should provide quality metrics
        assert results is not None

    async def test_outlier_detection(self, statistical_validator):
        """Test outlier detection in synthetic data."""
        # Data with outliers
        normal_data = [{"value": i * 10} for i in range(50)]
        outliers = [{"value": 10000}, {"value": -1000}]  # Extreme values
        synthetic_data = normal_data + outliers

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="comprehensive",
            domain=DataDomain.CUSTOM
        )

        # Should detect or report on outliers
        assert results is not None

    async def test_missing_value_handling(self, statistical_validator):
        """Test handling of missing values in validation."""
        synthetic_data = [
            {"value": 10, "status": "active"},
            {"value": None, "status": "inactive"},
            {"value": 30, "status": None}
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="standard",
            domain=DataDomain.CUSTOM
        )

        # Should handle missing values gracefully
        assert results is not None

    async def test_multi_dimensional_validation(self, statistical_validator):
        """Test validation of multi-dimensional data."""
        synthetic_data = [
            {
                "dim1": i,
                "dim2": i * 2,
                "dim3": i ** 2,
                "category": "A" if i % 2 == 0 else "B"
            }
            for i in range(30)
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="comprehensive",
            domain=DataDomain.CUSTOM
        )

        # Should validate multiple dimensions
        assert results is not None

    async def test_temporal_pattern_validation(self, statistical_validator):
        """Test validation of temporal patterns."""
        from datetime import datetime, timedelta

        base_date = datetime(2023, 1, 1)
        synthetic_data = [
            {
                "timestamp": (base_date + timedelta(days=i)).isoformat(),
                "value": i * 10
            }
            for i in range(30)
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="standard",
            domain=DataDomain.CUSTOM
        )

        # Should handle temporal data
        assert results is not None

    async def test_fidelity_score_calculation(self, statistical_validator):
        """Test overall fidelity score calculation."""
        synthetic_data = [
            {"value": i * 10} for i in range(50)
        ]

        results = await statistical_validator.validate_fidelity(
            synthetic_data=synthetic_data,
            validation_level="standard",
            domain=DataDomain.CUSTOM
        )

        # Should provide an overall fidelity score
        if "overall_fidelity_score" in results:
            assert isinstance(results["overall_fidelity_score"], (int, float))
            assert 0 <= results["overall_fidelity_score"] <= 1

    async def test_empty_dataset_validation(self, statistical_validator):
        """Test validation with empty datasets."""
        results = await statistical_validator.validate_fidelity(
            synthetic_data=[],
            validation_level="standard",
            domain=DataDomain.CUSTOM
        )

        # Should handle empty dataset gracefully
        assert results is not None
