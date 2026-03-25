from functools import lru_cache

import configs.config as config


@lru_cache(maxsize=1)
def get_chroma_connection():
    config.ensure_runtime_directories()

    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    embedding_model = OpenAIEmbeddings(
        model=config.embedding_model_name,
        openai_api_base=config.embedding_api_base,
        openai_api_key=config.embedding_api_key,
    )

    return Chroma(
        collection_name=config.collection_name,
        embedding_function=embedding_model,
        persist_directory=config.persist_directory,
    )
