from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse

from controller.rlhf_controller import RLHFCollectController
from schemas.dependencies import get_rlhf_controller

from schemas.dto import SessionRequest, RLHFStreamRequest, RLHFSavePreferenceRequest
from schemas.response import R

router = APIRouter(prefix="/api/rlhf", tags=["RLHF"])


@router.get("/sessions")
async def get_sessions(ctrl: RLHFCollectController = Depends(get_rlhf_controller)):
    # sessions =  ctrl.get_sidebar_sessions()
    return R.success(data="hello world1223")


@router.get("/session_history/{session_id}")
async def get_session_history(req: SessionRequest, ctrl: RLHFCollectController = Depends(get_rlhf_controller)):
    session_history = ctrl.get_session_history(req.session_id)
    return R.success(data=session_history)


@router.get("/delete_session/{session_id}")
async def delete_session(req: SessionRequest, ctrl: RLHFCollectController = Depends(get_rlhf_controller)):
    ctrl.delete_session(req.session_id)
    return R.success(message="会话删除成功")


@router.post("/stream_candidate")
async def stream_candidate(
        req: RLHFStreamRequest,
        ctrl: RLHFCollectController = Depends(get_rlhf_controller)
):
    """
        接收前端参数，生成单路回答流 (Server-Sent Events)
    """
    # 1. 调用 Controller 层获取生成器 (Generator)
    generator = ctrl.generate_candidate_stream(
        prompt=req.prompt,
        session_id=req.session_id,
        temperature=req.temperature,
        selected_model=req.selected_model
    )

    # 2. 封装为 SSE 格式
    def event_generator():
        for chunk in generator:
            # 兼容普通文本和 LangChain 的 AIMessageChunk
            content = chunk if isinstance(chunk, str) else chunk.content
            # SSE 规范：以 "data: " 开头，两个换行符结尾
            yield f"data: {content}\n\n"

    # 3. 返回流式响应
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/commit_preference")
async def commit_preference(
        req: RLHFSavePreferenceRequest,
        ctrl: RLHFCollectController = Depends(get_rlhf_controller)
):
    """
    前端用户点击【✅ 接受】时调用此接口。
    """
    try:
        # 1. 保存偏好数据到 DPO 数据集 (作为未来微调的语料)
        ctrl.save_preference(
            session_id=req.session_id,
            prompt=req.prompt,
            answers=req.answers,
            temperatures=req.temperatures,
            choice_idx=req.choice_idx,
            context_text=req.context_text
        )

        # 2. 提交交互记录到历史会话 (为了接下来的多轮对话有上下文)
        ctrl.commit_interaction(
            session_id=req.session_id,
            prompt=req.prompt,
            answers=req.answers,
            choice_idx=req.choice_idx
        )

        return R.success(message="偏好已记录，对话已保存")

    except Exception as e:
        return R.failure(message="偏好保存失败", data=str(e))
