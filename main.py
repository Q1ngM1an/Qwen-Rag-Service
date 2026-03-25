from pathlib import Path

import configs.config as config
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from core.domain_exceptions import DomainError
from router.dashboard_router import router as dashboard_router
from router.file_router import router as file_router
from router.knowledge_base_group_router import router as knowledge_base_group_router
from router.knowledge_base_router import router as knowledge_base_router
from router.qa_router import router as qa_router
from router.rlhf_api_router import router as rlhf_router
from router.session_scope_router import router as session_scope_router
from schemas.response import R

app = FastAPI(title="RAG-Service API")

# 配置 CORS 跨域，允许 Vue 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境建议指定具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(qa_router)
app.include_router(rlhf_router)
app.include_router(file_router)
app.include_router(knowledge_base_router)
app.include_router(knowledge_base_group_router)
app.include_router(session_scope_router)
app.include_router(dashboard_router)


def _frontend_unavailable_response():
    payload = R.fail(code=503, message="Frontend dist not found.")
    return JSONResponse(status_code=503, content=payload.model_dump())


def _serve_frontend_entry():
    frontend_dist = config.get_frontend_dist_dir()
    if not frontend_dist:
        return _frontend_unavailable_response()

    index_file = frontend_dist / "index.html"
    if not index_file.is_file():
        return _frontend_unavailable_response()

    return FileResponse(index_file)


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, exc: DomainError):
    payload = R.fail(code=exc.status_code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(HTTPException)
async def handle_http_error(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        payload = detail
        status_code = int(detail.get("code") or exc.status_code)
    else:
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("detail") or "error"
            data = detail.get("data")
        else:
            message = str(detail or "error")
            data = None
        payload = R.fail(code=exc.status_code, message=message, data=data).model_dump()
        status_code = exc.status_code
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else {}
    message = first_error.get("msg") or "Request validation failed."
    payload = R.fail(code=422, message=message, data=exc.errors())
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.get("/", include_in_schema=False)
async def serve_frontend_root():
    return _serve_frontend_entry()


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_path(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        payload = R.fail(code=404, message="API route not found.")
        return JSONResponse(status_code=404, content=payload.model_dump())

    frontend_dist = config.get_frontend_dist_dir()
    if not frontend_dist:
        return _frontend_unavailable_response()

    candidate = (frontend_dist / full_path).resolve()
    frontend_root = frontend_dist.resolve()

    try:
        candidate.relative_to(frontend_root)
    except ValueError:
        payload = R.fail(code=404, message="File not found.")
        return JSONResponse(status_code=404, content=payload.model_dump())

    if candidate.is_file():
        return FileResponse(candidate)

    return _serve_frontend_entry()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
