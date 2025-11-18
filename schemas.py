"""
Database Schemas for the Chess Platform

Each Pydantic model maps to a MongoDB collection with the lowercase class name.
- User -> "user"
- Game -> "game"
- Puzzle -> "puzzle"
- Lesson -> "lesson"
- ChatMessage -> "chatmessage"
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class User(BaseModel):
    """
    Users of the platform
    """
    username: str = Field(..., min_length=3, max_length=32, description="Unique handle")
    display_name: Optional[str] = Field(None, max_length=64)
    email: Optional[str] = Field(None, description="Email for account recovery/notifications")
    rating: int = Field(1200, ge=100, le=4000, description="Elo-like rating")
    country: Optional[str] = Field(None, description="ISO country code")


class Game(BaseModel):
    """
    Real-time or correspondence chess game
    """
    white_id: str = Field(..., description="User ID for White")
    black_id: str = Field(..., description="User ID for Black")
    status: Literal["ongoing", "white_won", "black_won", "draw"] = "ongoing"
    time_control: Literal["bullet", "blitz", "rapid", "classical"] = "blitz"
    increment: int = Field(0, ge=0, le=60, description="Increment per move (seconds)")
    fen: str = Field(
        "rn1qkbnr/pp3ppp/2p1p3/3p4/3P4/2N1PN2/PPP2PPP/R1BQKB1R w KQkq - 0 1",
        description="Current FEN position"
    )
    moves: List[str] = Field(default_factory=list, description="SAN or UCI moves history")
    turn: Literal["w", "b"] = "w"
    white_time_ms: int = Field(300000, ge=0)
    black_time_ms: int = Field(300000, ge=0)


class Puzzle(BaseModel):
    """
    Tactics puzzles with a target best move sequence starting from a FEN
    """
    fen: str
    moves: List[str] = Field(..., description="Best line in UCI, e.g., ['e2e4','e7e5']")
    themes: List[str] = Field(default_factory=list)
    rating: int = 1000


class Lesson(BaseModel):
    """
    Short learning items
    """
    title: str
    content: str
    topic: Literal["openings", "strategy", "tactics", "endgames", "basics"] = "basics"
    difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner"


class ChatMessage(BaseModel):
    """
    In-game chat
    """
    game_id: str
    user_id: str
    text: str
