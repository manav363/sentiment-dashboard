from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    label: str
    score: float


class SentimentResult(BaseModel):
    label: str
    score: float
    breakdown: list[ScoreBreakdown]
    text_preview: str


class URLAnalysisResult(BaseModel):
    url: str
    title: str
    result: SentimentResult
    chunk_count: int
