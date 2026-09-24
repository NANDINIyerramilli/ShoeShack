import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_agent.graph import graph

app = FastAPI(title="ShoeShack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    user_id: str = "user_1"


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    try:
        result = graph.invoke({"query": req.query, "user_id": req.user_id})
        return {
            "response": result.get("response", ""),
            "messages": [
                {
                    "role": getattr(m, "type", "assistant"),
                    "content": getattr(m, "content", str(m)),
                }
                for m in result.get("messages", [])
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "ShoeShack"}


# Mount static directory for images
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# If frontend/dist exists, mount it
dist_dir = PROJECT_ROOT / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
