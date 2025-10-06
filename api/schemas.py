from pydantic import BaseModel, Field
from typing import List

class UserRating(BaseModel):
    userId: int = Field(..., ge=1)
    movieId: int = Field(..., ge=1)
    rating: float = Field(..., ge=0, le=5)

class SyncProfileRequest(BaseModel):
    ratings: List[UserRating]

class RecommendRequest(BaseModel):
    userId: int
    topN: int = 10
