from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.file_router import router as file_router
from router.knowledge_base_group_router import router as knowledge_base_group_router
from router.knowledge_base_router import router as knowledge_base_router
from router.qa_router import router as qa_router
from router.rlhf_api_router import router as rlhf_router
from router.session_scope_router import router as session_scope_router

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
