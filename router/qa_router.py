from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from schemas.dependencies import get_qa_controller
from controller.qa_controller import QAChatController
from schemas.dto import SessionRequest, QAStreamRequest

router = APIRouter(prefix="/api/qa", tags=["QA"])

# --- 相当于 @GetMapping("/sessions") ---
@router.get("/sessions")
async def get_sessions(ctrl: QAChatController = Depends(get_qa_controller)):
    return ctrl.get_sidebar_sessions()


@router.get("/session_history")
async def get_session_history(req: SessionRequest, ctrl: QAChatController = Depends(get_qa_controller)):
    return ctrl.get_session_history(req.session_id)


@router.get("/delete_session")
async def delete_session(req: SessionRequest, ctrl: QAChatController = Depends(get_qa_controller)):
    return ctrl.delete_session(req.session_id)


@router.post("/stream")
async def stream_qa(req: QAStreamRequest, ctrl: QAChatController = Depends(get_qa_controller)):
    # 调用 Controller 层方法
    generator = ctrl.generate_response_stream(req.prompt, req.session_id, req.selected_model)

    def event_generator():
        for chunk in generator:
            content = chunk if isinstance(chunk, str) else chunk.content
            yield f"data: {content}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/regenerate")
async def regenerate(req: SessionRequest, ctrl: QAChatController = Depends(get_qa_controller)):
    user_prompt = ctrl.regenerate_last_response(req.session_id)
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Cannot regenerate.")
    return {"prompt": user_prompt}