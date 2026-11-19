from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str = Field(min_length=1)
    quantity: int = Field(ge=1, le=100)
