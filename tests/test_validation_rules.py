"""Tests for critical validation rules."""

import pytest

from app.validation.consistency_rules import ConsistencyRules
from app.validation.date_rules import DateRules
from app.validation.image_rules import ImageRules
from app.validation.mrz_rules import MRZRules
from app.validation.schema_rules import SchemaRules


class TestSchemaRules:
    """Test schema validation rules."""

    def test_validate_document_number_valid(self):
        """Test valid document number."""
        result = SchemaRules.validate_document_number("A12345678")
        assert result.passed is True

    def test_validate_document_number_invalid(self):
        """Test invalid document number."""
        result = SchemaRules.validate_document_number("INVALID")
        assert result.passed is False

    def test_validate_country_code_valid(self):
        """Test valid country code."""
        result = SchemaRules.validate_country_code("USA")
        assert result.passed is True

    def test_validate_country_code_invalid(self):
        """Test invalid country code."""
        result = SchemaRules.validate_country_code("US")
        assert result.passed is False

    def test_validate_sex_valid(self):
        """Test valid sex field."""
        result = SchemaRules.validate_sex("M")
        assert result.passed is True

    def test_validate_sex_invalid(self):
        """Test invalid sex field."""
        result = SchemaRules.validate_sex("INVALID")
        assert result.passed is False


class TestDateRules:
    """Test date validation rules."""

    def test_validate_not_expired_valid(self):
        """Test valid (not expired) passport."""
        from datetime import datetime, timedelta

        future_date = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%d")
        result = DateRules.validate_not_expired(future_date)
        assert result.passed is True

    def test_validate_not_expired_invalid(self):
        """Test expired passport."""
        from datetime import datetime, timedelta

        past_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
        result = DateRules.validate_not_expired(past_date)
        assert result.passed is False

    def test_validate_reasonable_birth_date_valid(self):
        """Test reasonable birth date."""
        result = DateRules.validate_reasonable_birth_date("1990-01-01")
        assert result.passed is True

    def test_validate_reasonable_birth_date_invalid(self):
        """Test unreasonable birth date (future)."""
        from datetime import datetime, timedelta

        future_date = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%d")
        result = DateRules.validate_reasonable_birth_date(future_date)
        assert result.passed is False


class TestImageRules:
    """Test image quality validation rules."""

    def test_validate_dimensions_valid(self):
        """Test valid image dimensions."""
        result = ImageRules.validate_dimensions(1920, 1080)
        assert result.passed is True

    def test_validate_dimensions_invalid(self):
        """Test invalid image dimensions."""
        result = ImageRules.validate_dimensions(100, 100)
        assert result.passed is False

    def test_validate_blur_score_valid(self):
        """Test acceptable blur score."""
        result = ImageRules.validate_blur_score(50.0)
        assert result.passed is True

    def test_validate_blur_score_invalid(self):
        """Test excessive blur score."""
        result = ImageRules.validate_blur_score(150.0)
        assert result.passed is False

    def test_validate_mrz_detected_true(self):
        """Test MRZ detected."""
        result = ImageRules.validate_mrz_detected(True)
        assert result.passed is True

    def test_validate_mrz_detected_false(self):
        """Test MRZ not detected."""
        result = ImageRules.validate_mrz_detected(False)
        assert result.passed is False


class TestMRZRules:
    """Test MRZ validation rules."""

    def test_validate_mrz_present_valid(self):
        """Test MRZ data present."""
        mrz_data = {
            "document_number": "A12345678",
            "issuing_state": "USA",
            "birth_date": "800101",
            "expiry_date": "300101",
        }
        result = MRZRules.validate_mrz_present(mrz_data)
        assert result.passed is True

    def test_validate_mrz_present_invalid(self):
        """Test MRZ data missing."""
        result = MRZRules.validate_mrz_present(None)
        assert result.passed is False

    def test_validate_mrz_present_missing_fields(self):
        """Test MRZ data missing required fields."""
        mrz_data = {"document_number": "A12345678"}
        result = MRZRules.validate_mrz_present(mrz_data)
        assert result.passed is False


class TestConsistencyRules:
    """Test cross-field consistency rules."""

    def test_nationality_issuing_state_match(self):
        """Test matching nationality and issuing state."""
        result = ConsistencyRules.validate_nationality_issuing_state_match("USA", "USA")
        assert result.passed is True

    def test_nationality_issuing_state_mismatch(self):
        """Test mismatched nationality and issuing state."""
        result = ConsistencyRules.validate_nationality_issuing_state_match("USA", "GBR")
        assert result.passed is False

    def test_viz_mrz_document_number_match(self):
        """Test matching VIZ and MRZ document numbers."""
        result = ConsistencyRules.validate_viz_mrz_consistency("A12345678", "A12345678")
        assert result.passed is True

    def test_viz_mrz_document_number_mismatch(self):
        """Test mismatched VIZ and MRZ document numbers."""
        result = ConsistencyRules.validate_viz_mrz_consistency("A12345678", "B87654321")
        assert result.passed is False

    def test_birth_date_before_expiry_valid(self):
        """Test birth date before expiry date."""
        result = ConsistencyRules.validate_birth_date_before_expiry("1990-01-01", "2030-01-01")
        assert result.passed is True

    def test_birth_date_before_expiry_invalid(self):
        """Test birth date after expiry date."""
        result = ConsistencyRules.validate_birth_date_before_expiry("2030-01-01", "1990-01-01")
        assert result.passed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
