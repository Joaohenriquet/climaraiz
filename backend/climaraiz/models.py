"""Validated public requests. All dates and intervals have explicit semantics."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HistoricalPeriod(StrictModel):
    start_year: int = Field(default=2001, ge=1900, le=2100)
    end_year: int = Field(default=2025, ge=1900, le=2100)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_year < self.start_year or self.end_year - self.start_year > 99:
            raise ValueError("The period must be ordered and contain at most 100 years.")
        return self


class ScenarioPhase(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,49}$")
    name: str = Field(min_length=1, max_length=80)
    start_day: int = Field(ge=0, le=364)
    end_day: int = Field(ge=0, le=364)


class CheckWindow(ScenarioPhase):
    phase_id: Optional[str] = Field(default=None, pattern=r"^[a-z][a-z0-9_]{0,49}$",
        description="Optional ID of the submitted cycle segment receiving this check window's results. The window must be entirely inside that segment; its own ID still selects the crop rules.")


class PlantingRequest(StrictModel):
    municipality_id: int = 2504009
    crop_id: int = Field(gt=0, strict=True, description="Numeric crop ID returned by GET /api/v1/crops.")
    production_system: Literal["rainfed"] = "rainfed"
    planting_year: int = Field(ge=2000, le=2100)
    historical_period: HistoricalPeriod = Field(default_factory=HistoricalPeriod)
    cycle_days: int = Field(ge=1, le=365, description="User-selected scenario duration; not a validated crop profile.")
    phases: List[ScenarioPhase] = Field(default_factory=list, max_length=20)
    check_windows: List[CheckWindow] = Field(default_factory=list, max_length=20,
        description="Optional rule-evaluation windows; inclusive cycle-day offsets may overlap, e.g. pollination within flowering. Not validated crop phenology.")
    daily_mean_threshold_c: Optional[float] = Field(default=None, ge=-50, le=60,
        description="Optional descriptive threshold for daily mean temperature. Not a crop stress limit.")

    @model_validator(mode="after")
    def validate_phases(self):
        for window in [*self.phases, *self.check_windows]:
            if window.id == "cycle" and (window.start_day != 0 or window.end_day != self.cycle_days-1):
                raise ValueError("The reserved cycle window must cover the entire cycle.")
        window_ids = [window.id for window in self.check_windows]
        if len(set(window_ids)) != len(window_ids) or set(window_ids) & {p.id for p in self.phases}:
            raise ValueError("Evaluation window identifiers must be unique across phases and check_windows.")
        for window in self.check_windows:
            if window.start_day > window.end_day or window.end_day >= self.cycle_days:
                raise ValueError("Evaluation windows must be ordered intervals within the cycle.")
        if self.phases:
            if len({phase.id for phase in self.phases}) != len(self.phases):
                raise ValueError("Phase identifiers must be unique.")
            expected_start = 0
            for phase in self.phases:
                if phase.start_day != expected_start or phase.end_day < phase.start_day:
                    raise ValueError("Ordered phases must cover the cycle without gaps or overlaps.")
                expected_start = phase.end_day + 1
            if expected_start != self.cycle_days:
                raise ValueError("Inclusive phase endpoints must cover exactly cycle_days.")
        phases_by_id = {phase.id: phase for phase in self.phases}
        for window in self.check_windows:
            if window.phase_id is not None:
                phase = phases_by_id.get(window.phase_id)
                if phase is None:
                    raise ValueError("A check window's phase_id must reference a submitted phase.")
                if window.start_day < phase.start_day or window.end_day > phase.end_day:
                    raise ValueError("A linked check window must be entirely inside its referenced phase.")
        return self
