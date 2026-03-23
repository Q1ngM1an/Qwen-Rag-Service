from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from controller.rlhf_controller import RLHFCollectController
from schemas.dependencies import get_rlhf_controller
from schemas.dto import RLHFSavePreferenceRequest, RLHFStreamRequest
from schemas.response import R


router = APIRouter(prefix="/api/rlhf", tags=["RLHF"])


@router.get("/sessions")
async def get_sessions(ctrl: RLHFCollectController = Depends(get_rlhf_controller)):
    return R.success(data=ctrl.get_sidebar_sessions())


@router.get("/session_history/{session_id}")
async def get_session_history(session_id: str, ctrl: RLHFCollectController = Depends(get_rlhf_controller)):
    return R.success(data=ctrl.get_session_history(session_id))


@router.get("/delete_session/{session_id}")
async def delete_session(session_id: str, ctrl: RLHFCollectController = Depends(get_rlhf_controller)):
    ctrl.delete_session(session_id)
    return R.success(message="Session deleted successfully.")


@router.post("/stream_candidate")
async def stream_candidate(
    req: RLHFStreamRequest,
    ctrl: RLHFCollectController = Depends(get_rlhf_controller),
):
    generator = ctrl.generate_candidate_stream(
        prompt=req.prompt,
        session_id=req.session_id,
        temperature=req.temperature,
        selected_model=req.selected_model,
    )

    def event_generator():
        for chunk in generator:
            content = chunk if isinstance(chunk, str) else chunk.content
            yield f"data: {content}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/commit_preference")
async def commit_preference(
    req: RLHFSavePreferenceRequest,
    ctrl: RLHFCollectController = Depends(get_rlhf_controller),
):
    try:
        ctrl.save_preference(
            session_id=req.session_id,
            prompt=req.prompt,
            answers=req.answers,
            temperatures=req.temperatures,
            choice_idx=req.choice_idx,
            context_text=req.context_text,
        )
        ctrl.commit_interaction(
            session_id=req.session_id,
            prompt=req.prompt,
            answers=req.answers,
            choice_idx=req.choice_idx,
        )
        return R.success(message="Preference saved successfully.")
    except Exception as exc:
        return R.fail(message="Failed to save preference.", data=str(exc))
