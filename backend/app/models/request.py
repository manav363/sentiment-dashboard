from pydantic import BaseModel, Field, HttpUrl


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000)


class AnalyzeURLRequest(BaseModel):
    url: HttpUrl
