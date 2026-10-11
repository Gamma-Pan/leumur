from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Query(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    mode: Literal['live', 'demo'] = 'live'

class ChartPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dataset: Literal['nama_10_gdp', 'demo_gind', 'une_rt_a']
    geo: Literal['EL', 'DE', 'FR', 'IT', 'ES', 'PT', 'NL', 'BE', 'AT', 'IE', 'PL', 'SE', 'FI', 'DK', 'CY']
    years: int = Field(ge=1, le=30)
    chart_type: Literal['line', 'bar']
    time_basis: Literal['latest_available', 'calendar_years']

class Clarification(Exception):
    pass
