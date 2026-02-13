"""Domain-specific exception hierarchy for Digital Surveyor."""


class DigitalSurveyorError(Exception):
    """Base exception for all domain errors."""


class PostcodeNotFoundError(DigitalSurveyorError):
    """Postcode could not be geocoded."""


class InvalidPostcodeError(DigitalSurveyorError):
    """Postcode failed format validation."""


class ExternalAPIError(DigitalSurveyorError):
    """An external API (OS, HERE, postcodes.io) returned an error."""


class LiDARTileNotFoundError(DigitalSurveyorError):
    """No LiDAR tile covers the requested coordinates."""


class PipelineError(DigitalSurveyorError):
    """Assessment pipeline encountered an unrecoverable error."""
