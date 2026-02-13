"""Tests for domain error hierarchy."""

import pytest

from app.errors import (
    DigitalSurveyorError,
    ExternalAPIError,
    InvalidPostcodeError,
    LiDARTileNotFoundError,
    PipelineError,
    PostcodeNotFoundError,
)


class TestErrorHierarchy:
    def test_base_class(self):
        assert issubclass(PostcodeNotFoundError, DigitalSurveyorError)
        assert issubclass(InvalidPostcodeError, DigitalSurveyorError)
        assert issubclass(ExternalAPIError, DigitalSurveyorError)
        assert issubclass(LiDARTileNotFoundError, DigitalSurveyorError)
        assert issubclass(PipelineError, DigitalSurveyorError)

    def test_all_inherit_from_exception(self):
        assert issubclass(DigitalSurveyorError, Exception)

    def test_error_message(self):
        err = InvalidPostcodeError("Bad postcode: XYZ")
        assert "Bad postcode: XYZ" in str(err)

    def test_catch_by_base(self):
        with pytest.raises(DigitalSurveyorError):
            raise PostcodeNotFoundError("Not found")

    def test_catch_specific(self):
        with pytest.raises(PostcodeNotFoundError):
            raise PostcodeNotFoundError("Not found")
