import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Game, Puzzle, Lesson, ChatMessage

app = FastAPI(title="Chess Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class IDModel(BaseModel):
    id: str


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
def read_root():
    return {"message": "Chess Platform Backend Ready"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# Auth-lite: create user
@app.post("/users", response_model=IDModel)
def create_user(user: User):
    user_id = create_document("user", user)
    return {"id": user_id}


@app.get("/users")
def list_users(limit: int = 20):
    docs = get_documents("user", {}, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Games
class CreateGameRequest(BaseModel):
    white_id: str
    black_id: str
    time_control: str = "blitz"
    increment: int = 0


@app.post("/games", response_model=IDModel)
def create_game(payload: CreateGameRequest):
    game = Game(
        white_id=payload.white_id,
        black_id=payload.black_id,
        time_control=payload.time_control,  # bullet/blitz/rapid/classical
        increment=payload.increment,
    )
    gid = create_document("game", game)
    return {"id": gid}


@app.get("/games")
def list_games(limit: int = 20):
    docs = get_documents("game", {}, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Learning content
@app.post("/puzzles", response_model=IDModel)
def create_puzzle(puzzle: Puzzle):
    pid = create_document("puzzle", puzzle)
    return {"id": pid}


@app.get("/puzzles")
def list_puzzles(limit: int = 20):
    docs = get_documents("puzzle", {}, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.post("/lessons", response_model=IDModel)
def create_lesson(lesson: Lesson):
    lid = create_document("lesson", lesson)
    return {"id": lid}


@app.get("/lessons")
def list_lessons(limit: int = 20):
    docs = get_documents("lesson", {}, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Simple matchmaking prototype: find the closest-rated opponent
class MatchRequest(BaseModel):
    user_id: str


@app.post("/matchmake")
def matchmake(req: MatchRequest):
    # fetch all users, find someone else with minimal rating diff
    users = get_documents("user")
    # locate requesting user
    me = None
    for u in users:
        if str(u.get("_id")) == req.user_id:
            me = u
            break
    if not me:
        raise HTTPException(status_code=404, detail="User not found")

    best = None
    best_diff = 10**9
    for u in users:
        if str(u.get("_id")) == req.user_id:
            continue
        diff = abs(int(u.get("rating", 1200)) - int(me.get("rating", 1200)))
        if diff < best_diff:
            best_diff = diff
            best = u

    if not best:
        return {"found": False}

    return {
        "found": True,
        "opponent": {
            "id": str(best.get("_id")),
            "username": best.get("username"),
            "rating": best.get("rating", 1200)
        }
    }


# Chat messages (store)
@app.post("/chat", response_model=IDModel)
def post_chat(msg: ChatMessage):
    cid = create_document("chatmessage", msg)
    return {"id": cid}


@app.get("/chat")
def list_chat(game_id: Optional[str] = None, limit: int = 50):
    filt = {"game_id": game_id} if game_id else {}
    docs = get_documents("chatmessage", filt, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
