from langchain_chroma import Chroma

import configs.config as config
from langchain_openai import OpenAIEmbeddings

def get_chroma_connection():
    embedding_model = OpenAIEmbeddings(
            model="embedding-model",  # 可以是任意名称
            openai_api_base="http://localhost:8001/v1",
            openai_api_key="token-embed123",  # vLLM 不需要密钥，但需要传一个值
        )
    chroma = Chroma(
        collection_name=config.collection_name,  # 数据库的表名
        embedding_function=embedding_model,
        # embedding_function=OpenAIEmbeddings(
        #     model="embedding-model",  # 可以是任意名称
        #     openai_api_base="http://localhost:8001/v1",
        #     openai_api_key="token-embed123",  # vLLM 不需要密钥，但需要传一个值
        # ),
        # embedding_function=HuggingFaceEmbeddings(
        #     model_name=config.embedding_model_path,
        #     model_kwargs={'device': 'cpu'},
        #     encode_kwargs={'normalize_embeddings': True}
        # ),
        persist_directory=config.persist_directory,  # 数据库本地存储文件夹
    )

    return chroma

