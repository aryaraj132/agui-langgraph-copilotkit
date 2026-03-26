import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agui_backend_demo.agent.chat_agent import build_chat_agent
from agui_backend_demo.agent.graph import build_segment_graph
from agui_backend_demo.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Building agents...")
    app.state.segment_graph = build_segment_graph()
    app.state.chat_agent = build_chat_agent()
    logger.info("Agents ready")
    yield


app = FastAPI(
    title="Segment Generation Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "agui_backend_demo.main:app", host="0.0.0.0", port=8000, reload=True
    )
