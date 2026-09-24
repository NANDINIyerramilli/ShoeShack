from fastapi import FastAPI
from pydantic import BaseModel

from agent import run_agent

app = FastAPI(title="SQL Agent")


class QueryRequest(BaseModel):
    query: str
    user_id: str


@app.post("/invoke")
def invoke_agent(request: QueryRequest):
    try:
        result = run_agent(request.query)
        return {"response": result}
    except ValueError as e:
        return {"response": f"Blocked: {e}"}
    except Exception as e:
        return {"response": f"Error: {e}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
