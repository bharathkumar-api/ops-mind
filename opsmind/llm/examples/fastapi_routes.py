from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..config import LLMSettings, get_settings
from ..errors import OpsMindLLMError
from ..router import LLMRouter
from ..types import LLMRequest

router = APIRouter(prefix="/api/llm", tags=["llm"])


def get_llm_router(settings: LLMSettings = Depends(get_settings)) -> LLMRouter:
    return LLMRouter(settings=settings)


@router.post("/generate")
async def generate(request: LLMRequest, llm_router: LLMRouter = Depends(get_llm_router)) -> dict:
    try:
        response = await llm_router.generate(request)
        return response.model_dump()
    except OpsMindLLMError as exc:
        raise HTTPException(status_code=exc.http_status, detail={"code": exc.code, "message": exc.message}) from exc


@router.post("/stream")
async def stream(request: LLMRequest, llm_router: LLMRouter = Depends(get_llm_router)) -> StreamingResponse:
    async def event_stream():
        try:
            async for chunk in llm_router.stream(request):
                yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        except OpsMindLLMError as exc:
            payload = {"code": exc.code, "message": exc.message}
            yield f"event: error\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
