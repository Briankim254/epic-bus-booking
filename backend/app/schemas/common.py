from typing import Literal

from pydantic import BaseModel, ConfigDict

Currency = Literal["USD"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
