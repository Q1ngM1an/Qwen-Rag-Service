from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from controller.qa_controller import QAChatController
from schemas.dependencies import get_qa_controller, get_qa_stream_controller
from schemas.dto import QAStreamRequest
from schemas.response import R

router = APIRouter(prefix="/api/qa", tags=["QA"])


@router.post("/sessions")
async def create_session(ctrl: QAChatController = Depends(get_qa_controller)):
    return R.success(data=ctrl.create_session())

# --- 相当于 @GetMapping("/sessions") ---
@router.get("/sessions")
async def get_sessions(ctrl: QAChatController = Depends(get_qa_controller)):
    return R.success(data=ctrl.get_sidebar_sessions())

@router.get("/sessions/{session_id}/messages")
async def get_session_history(session_id: str, ctrl: QAChatController = Depends(get_qa_controller)):
    return R.success(data=ctrl.get_session_history(session_id))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, ctrl: QAChatController = Depends(get_qa_controller)):
    ctrl.delete_session(session_id)
    return R.success(message="Session deleted successfully.")


@router.post("/sessions/{session_id}/messages/stream")
async def stream_qa(session_id: str, req: QAStreamRequest, ctrl: QAChatController = Depends(get_qa_stream_controller)):
    # 调用 Controller 层方法
    generator = ctrl.generate_response_stream(req.prompt, session_id, req.selected_model)

    def event_generator():
        for chunk in generator:
            content = chunk if isinstance(chunk, str) else chunk.content
            yield f"data: {content}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/messages/regenerate")
async def regenerate(session_id: str, ctrl: QAChatController = Depends(get_qa_controller)):
    user_prompt = ctrl.regenerate_last_response(session_id)
    if not user_prompt:
        return JSONResponse(status_code=400, content=R.fail(code=400, message="Cannot regenerate.").model_dump())
    return R.success(data={"prompt": user_prompt})
