import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agui_backend_demo.agent.campaign.graph import build_campaign_graph
from agui_backend_demo.agent.campaign.routes import router as campaign_router
from agui_backend_demo.agent.chat.graph import build_chat_agent
from agui_backend_demo.agent.chat.routes import router as chat_router
from agui_backend_demo.agent.custom_property.graph import build_custom_property_graph
from agui_backend_demo.agent.custom_property.routes import (
    router as custom_property_router,
)
from agui_backend_demo.agent.segment.graph import build_segment_graph
from agui_backend_demo.agent.segment.routes import router as segment_router
from agui_backend_demo.agent.template.graph import build_template_graph
from agui_backend_demo.agent.template.routes import router as template_router
from agui_backend_demo.api.capabilities import router as capabilities_router
from agui_backend_demo.api.threads import router as threads_router

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
    app.state.template_graph = build_template_graph()
    app.state.campaign_graph = build_campaign_graph()
    app.state.custom_property_graph = build_custom_property_graph()
    logger.info("Agents ready")
    yield


app = FastAPI(
    title="AG-UI Core Concepts Demo",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register agent routers
app.include_router(segment_router)
app.include_router(chat_router)
app.include_router(template_router)
app.include_router(campaign_router)
app.include_router(custom_property_router)

# Register API routers
app.include_router(threads_router)
app.include_router(capabilities_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("agui_backend_demo.main:app", host="0.0.0.0", port=8000, reload=True)
