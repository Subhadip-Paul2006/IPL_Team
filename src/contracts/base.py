"""Base contract specification for all RR Platform entities."""

from pydantic import BaseModel, ConfigDict


class BaseContract(BaseModel):
    """Base Pydantic contract establishing schema discipline and attribute mapping."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
    )
