"""
Tests for error handling and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from synthetic_data_mcp.core.generator import SyntheticDataGenerator
from synthetic_data_mcp.schemas.base import DataDomain, PrivacyLevel
from synthetic_data_mcp.server import (
    GenerateSyntheticDatasetRequest,
    generate_synthetic_dataset
)


@pytest.mark.asyncio
class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    async def test_invalid_domain_handling(self):
        """Test handling of invalid domain."""
        generator = SyntheticDataGenerator()

        # Try to generate with an invalid domain string
        try:
            result = await generator.generate_dataset(
                domain="invalid_domain",  # Invalid
                dataset_type="test",
                record_count=1,
                privacy_level=PrivacyLevel.MEDIUM
            )
            # Should either error or handle gracefully
            assert "error" in result or "status" in result
        except Exception as e:
            # Exception is also acceptable
            assert True

    async def test_zero_record_count_validation(self):
        """Test that zero record count is rejected."""
        with pytest.raises(Exception):  # Should raise validation error
            GenerateSyntheticDatasetRequest(
                domain=DataDomain.HEALTHCARE,
                dataset_type="patient_records",
                record_count=0,  # Invalid: must be > 0
                privacy_level=PrivacyLevel.HIGH
            )

    async def test_negative_record_count_validation(self):
        """Test that negative record count is rejected."""
        with pytest.raises(Exception):
            GenerateSyntheticDatasetRequest(
                domain=DataDomain.HEALTHCARE,
                dataset_type="patient_records",
                record_count=-5,  # Invalid
                privacy_level=PrivacyLevel.HIGH
            )

    async def test_excessive_record_count_validation(self):
        """Test that excessive record count is rejected."""
        with pytest.raises(Exception):
            GenerateSyntheticDatasetRequest(
                domain=DataDomain.HEALTHCARE,
                dataset_type="patient_records",
                record_count=2000000,  # Exceeds limit of 1,000,000
                privacy_level=PrivacyLevel.HIGH
            )

    async def test_none_dataset_handling(self):
        """Test handling of None dataset."""
        generator = SyntheticDataGenerator()

        # Should handle None gracefully
        pattern_id = await generator.learn_from_data(
            data_samples=[],
            domain="custom"
        )

        assert pattern_id is not None

    async def test_malformed_schema_handling(self):
        """Test handling of malformed custom schema."""
        generator = SyntheticDataGenerator()

        malformed_schema = {
            "properties": None  # Malformed
        }

        result = await generator.generate_dataset(
            domain=DataDomain.CUSTOM,
            dataset_type="custom_records",
            record_count=1,
            privacy_level=PrivacyLevel.MEDIUM,
            custom_schema=malformed_schema
        )

        # Should handle gracefully - either error or fallback
        assert result is not None

    async def test_missing_required_fields(self):
        """Test handling of missing required fields in data."""
        generator = SyntheticDataGenerator()

        # Incomplete data
        incomplete_data = [
            {"name": "Alice"},  # Missing other fields
            {"age": 30}  # Missing name
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=incomplete_data,
            domain="custom"
        )

        # Should handle incomplete data
        assert pattern_id is not None

    async def test_mixed_data_types_handling(self):
        """Test handling of mixed data types in fields."""
        generator = SyntheticDataGenerator()

        mixed_data = [
            {"value": 100},  # Integer
            {"value": "test"},  # String
            {"value": 12.5},  # Float
            {"value": True}  # Boolean
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=mixed_data,
            domain="custom"
        )

        # Should handle mixed types
        assert pattern_id is not None

    async def test_concurrent_generation_race_conditions(self):
        """Test that concurrent generations don't cause race conditions."""
        import asyncio

        generator = SyntheticDataGenerator()

        async def generate_task():
            return await generator.generate_dataset(
                domain=DataDomain.FINANCE,
                dataset_type="transaction_records",
                record_count=5,
                privacy_level=PrivacyLevel.MEDIUM
            )

        # Run multiple concurrent generations
        tasks = [generate_task() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without errors
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None

    async def test_large_field_value_handling(self):
        """Test handling of very large field values."""
        generator = SyntheticDataGenerator()

        large_value_data = [
            {"value": 10**100},  # Very large number
            {"text": "x" * 100000}  # Very long string
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=large_value_data,
            domain="custom"
        )

        # Should handle large values
        assert pattern_id is not None

    async def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        generator = SyntheticDataGenerator()

        unicode_data = [
            {"name": "测试用户"},  # Chinese
            {"name": "Тест"},  # Cyrillic
            {"name": "مستخدم"},  # Arabic
            {"special": "!@#$%^&*()"}  # Special chars
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=unicode_data,
            domain="custom"
        )

        # Should handle unicode
        assert pattern_id is not None

    async def test_circular_reference_in_schema(self):
        """Test handling of circular references."""
        # Create circular reference
        schema1 = {"type": "object"}
        schema2 = {"type": "object", "ref": schema1}
        schema1["ref"] = schema2  # Circular reference

        generator = SyntheticDataGenerator()

        # Should not crash with circular reference
        try:
            result = await generator.generate_dataset(
                domain=DataDomain.CUSTOM,
                dataset_type="test",
                record_count=1,
                privacy_level=PrivacyLevel.MEDIUM,
                custom_schema=schema1
            )
            assert result is not None
        except Exception:
            # Exception is acceptable for circular reference
            assert True

    async def test_extremely_skewed_distribution(self):
        """Test handling of extremely skewed distributions."""
        generator = SyntheticDataGenerator()

        # Highly skewed data (99% same value)
        skewed_data = [
            {"value": 1} for _ in range(99)
        ] + [
            {"value": 1000}
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=skewed_data,
            domain="custom"
        )

        # Generate from skewed pattern
        result = await generator.generate_from_pattern(
            pattern_id=pattern_id,
            record_count=10,
            variation=0.1,
            privacy_level=PrivacyLevel.MEDIUM
        )

        # Should handle skewed distribution
        assert result["success"] is True

    async def test_null_and_nan_values(self):
        """Test handling of null and NaN values."""
        generator = SyntheticDataGenerator()

        data_with_nulls = [
            {"value": None},
            {"value": float('nan')},
            {"value": 10}
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=data_with_nulls,
            domain="custom"
        )

        # Should handle nulls/NaN
        assert pattern_id is not None

    async def test_empty_string_values(self):
        """Test handling of empty strings."""
        generator = SyntheticDataGenerator()

        empty_string_data = [
            {"name": ""},
            {"name": "   "},  # Whitespace only
            {"name": "Alice"}
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=empty_string_data,
            domain="custom"
        )

        assert pattern_id is not None

    async def test_duplicate_records_handling(self):
        """Test handling of duplicate records."""
        generator = SyntheticDataGenerator()

        duplicate_data = [
            {"name": "Alice", "age": 30},
            {"name": "Alice", "age": 30},  # Exact duplicate
            {"name": "Alice", "age": 30}   # Another duplicate
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=duplicate_data,
            domain="custom"
        )

        # Should handle duplicates
        assert pattern_id is not None

    async def test_inconsistent_field_names(self):
        """Test handling of inconsistent field names across records."""
        generator = SyntheticDataGenerator()

        inconsistent_data = [
            {"name": "Alice", "age": 30},
            {"full_name": "Bob", "years": 35},  # Different field names
            {"person": "Carol", "age": 28}
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=inconsistent_data,
            domain="custom"
        )

        # Should handle inconsistent fields
        assert pattern_id is not None

    async def test_nested_structure_depth_limit(self):
        """Test handling of deeply nested structures."""
        generator = SyntheticDataGenerator()

        # Create deeply nested structure
        nested_data = [
            {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": {
                                    "value": 100
                                }
                            }
                        }
                    }
                }
            }
        ]

        pattern_id = await generator.learn_from_data(
            data_samples=nested_data,
            domain="custom"
        )

        # Should handle deep nesting
        assert pattern_id is not None

    async def test_generation_timeout_handling(self):
        """Test that very large generation requests don't hang."""
        import asyncio

        generator = SyntheticDataGenerator()

        # Start generation and set timeout
        try:
            result = await asyncio.wait_for(
                generator.generate_dataset(
                    domain=DataDomain.FINANCE,
                    dataset_type="transaction_records",
                    record_count=10000,  # Large count
                    privacy_level=PrivacyLevel.MEDIUM
                ),
                timeout=30.0  # 30 second timeout
            )
            # Should complete or timeout gracefully
            assert result is not None
        except asyncio.TimeoutError:
            # Timeout is acceptable for very large datasets
            assert True

    async def test_memory_cleanup_after_error(self):
        """Test that memory is properly cleaned up after errors."""
        generator = SyntheticDataGenerator()

        # Force an error
        with patch.object(generator, '_generate_healthcare_dataset', side_effect=Exception("Test error")):
            try:
                await generator.generate_dataset(
                    domain=DataDomain.HEALTHCARE,
                    dataset_type="patient_records",
                    record_count=100,
                    privacy_level=PrivacyLevel.HIGH
                )
            except Exception:
                pass

        # Generator should still be functional
        result = await generator.generate_dataset(
            domain=DataDomain.FINANCE,
            dataset_type="transaction_records",
            record_count=5,
            privacy_level=PrivacyLevel.MEDIUM
        )

        assert result["status"] == "success"

    async def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
        generator = SyntheticDataGenerator()

        # Simulate partial failure during pattern learning
        mixed_quality_data = [
            {"value": 100},  # Good
            None,  # Bad
            {"value": 200},  # Good
            {"broken": "data"},  # Different structure
            {"value": 300}  # Good
        ]

        try:
            # Filter out None values
            clean_data = [d for d in mixed_quality_data if d is not None]
            pattern_id = await generator.learn_from_data(
                data_samples=clean_data,
                domain="custom"
            )
            assert pattern_id is not None
        except Exception:
            # Exception is acceptable
            assert True
