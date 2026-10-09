"""Passport data schemas."""


from pydantic import BaseModel


class PassportDataResponse(BaseModel):
    """Passport data response."""

    document_type: str
    issuing_state: str
    document_number: str
    birth_date: str
    expiry_date: str
    sex: str
    surname: str = ""
    given_names: str = ""
    nationality: str = ""
    personal_number: str = ""
    mrz_type: str = "unknown"
