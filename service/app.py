"""The routing service: one endpoint and one screen.

Start:  uvicorn service.app:app --port 8000      then open http://localhost:8000
Needs no API key and no internet. If the model file is missing it still starts and says what to do.
"""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from src.explain import MODEL_PATH, explain

app = FastAPI(title="Kestrel routing")
STATIC = os.path.join(os.path.dirname(__file__), "static")


class Request(BaseModel):
    request_text: str = Field(..., description="The customer's opening message or IVR transcript")
    # channel, product_family and warranty_status may be sent but are not used: they added nothing in testing
    channel: str = Field("", description="not used by the model")
    product_family: str = Field("", description="not used by the model")
    warranty_status: str = Field("", description="not used by the model")


@app.get("/health")
def health():
    ready = os.path.exists(MODEL_PATH)
    return {"status": "ok" if ready else "model_missing", "model_file": MODEL_PATH, "model_ready": ready,
            "paid_api_needed": False}


@app.post("/route")
def route(req: Request):
    """Takes one request as JSON. Returns the team, how sure the model is, whether to route automatically
    or send to a person, and reasons written for a Kestrel employee."""
    if not req.request_text.strip():
        return JSONResponse(status_code=422, content={"error": "request_text is empty. Paste the customer's message."})
    if not os.path.exists(MODEL_PATH):
        return JSONResponse(status_code=503, content={
            "error": "The routing model has not been trained on this machine yet.",
            "fix": "Put the Kestrel CSVs in data/raw/ and run: python -m src.clean && python -m src.train"})
    return explain(req.model_dump())


@app.get("/")
def screen():
    return FileResponse(os.path.join(STATIC, "index.html"))
