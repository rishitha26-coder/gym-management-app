"""Membership plan duration helpers (1–12 months)."""

from pydantic import BaseModel, Field, field_validator

MIN_PLAN_MONTHS = 1
MAX_PLAN_MONTHS = 12

LEGACY_PLAN_MAP: dict[str, int] = {
    "3 Months": 3,
    "6 Months": 6,
    "1 Year": 12,
}


class PlanMonths(BaseModel):
    """Validated membership duration in months."""

    months: int = Field(ge=MIN_PLAN_MONTHS, le=MAX_PLAN_MONTHS)

    @field_validator("months", mode="before")
    @classmethod
    def coerce_months(cls, value: object) -> int:
        return normalize_plan_months(value)

    @property
    def label(self) -> str:
        return plan_label(self.months)


def plan_label(months: int) -> str:
    """Human-readable plan label for UI and exports."""
    if months == 12:
        return "12 Months (1 Year)"
    if months == 1:
        return "1 Month"
    return f"{months} Months"


def plan_choices() -> list[tuple[int, str]]:
    """Dropdown options as (value, label) pairs."""
    return [(month, plan_label(month)) for month in range(MIN_PLAN_MONTHS, MAX_PLAN_MONTHS + 1)]


def normalize_plan_months(value: object) -> int:
    """Convert form values, legacy strings, or ints to plan months."""
    if isinstance(value, PlanMonths):
        return value.months
    if isinstance(value, int):
        months = value
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            months = int(stripped)
        elif stripped in LEGACY_PLAN_MAP:
            months = LEGACY_PLAN_MAP[stripped]
        else:
            raise ValueError(f"Invalid membership plan: {value}")
    else:
        raise ValueError(f"Invalid membership plan type: {type(value)!r}")

    if not MIN_PLAN_MONTHS <= months <= MAX_PLAN_MONTHS:
        raise ValueError(f"Plan must be between {MIN_PLAN_MONTHS} and {MAX_PLAN_MONTHS} months")
    return months
