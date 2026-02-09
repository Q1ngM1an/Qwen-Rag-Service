import os
import re

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from core.chat_history_service import get_qa_chat_history
from core.vector_store_service import get_vector_store


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)

    return prompt


class RagService(object):
    def __init__(self):

        # 1. 准备基础组件 (只做一次)
        self.vector_store = get_vector_store()
        self.retriever = self.vector_store.get_retriever()

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """你是一个专业的智能助手，你的任务是尽量根据提供的参考资料回答用户的问题。

                ### 核心原则
                1. **真实性**：回答之前要仔细检查【参考资料】中的内容，同时严禁编造事实。
                2. **诚实性**：只有在【参考资料】中不包含回答问题所需的信息的情况下，才使用你的训练数据回答用户问题，最后注明该回答并非基于参考资料得出。
                3. **专业性**：回答应逻辑清晰、语言流畅、结构严谨。
                4. **引用**：在回答中涉及具体数据或观点时，尽量自然地体现出是基于资料的。
        
                ### 参考资料
                {context}
                """),
                # 显式分割历史记录区域
                ("system", "### 对话历史\n以下是用户之前的对话记录（仅供上下文理解，不要与参考资料混淆）："),
                MessagesPlaceholder("history"),

                ("user", "### 用户当前问题\n{input}")
            ]
        )

        # 启动命令
        # vllm serve ./EmbeddingModel --served-model-name embedding-model --port 8001 --api-key token-embed123 --gpu-memory-utilization 0.2 --max-model-len 32000
        # vllm serve ./ChatModel/qwen06b --port 8002 --max-model-len 40960 --served-model-name qwen06b --api-key token-qwen06b123 --gpu-memory-utilization 0.2
        # vllm serve ./ChatModel/deepseek --port 8003 --max-model-len 40960 --served-model-name deepseek --api-key token-deepseek123 --gpu-memory-utilization 0.2
        # vllm serve ./ChatModel/qwen32b --port 8004 --served-model-name qwen32b --api-key token-qwen32b123 --gpu-memory-utilization 0.2 --hf_overrides '{"rope_parameters": {"rope_theta": 1000000, "rope_type": "yarn", "factor": 4.0, "original_max_position_embeddings": 40960}, "max_model_len":  81920}' 

        # 使用 OpenAI 兼容接口
        self.qwen_model_600m = ChatOpenAI(
            model="qwen06b",  # 可以是任意名称
            openai_api_base="http://localhost:8002/v1",
            openai_api_key="token-qwen06b123",  # vLLM 不需要密钥，但需要传一个值
            temperature=0.8,
            max_tokens=4096,
        )

        # self.deepseek_r1 = ChatOpenAI(
        #     model="deepseek",  # 可以是任意名称
        #     openai_api_base="http://localhost:8003/v1",
        #     openai_api_key="token-deepseek123",  # vLLM 不需要密钥，但需要传一个值
        #     temperature=0.8,
        #     max_tokens=4096,
        # )

        self.qwen_model_32b = ChatOpenAI(
            model="qwen06b",  # 可以是任意名称
            openai_api_base="http://localhost:8002/v1",
            openai_api_key="token-qwen06b123",  # vLLM 不需要密钥，但需要传一个值
            temperature=0.8,
            max_tokens=4096,
        )



    # --- 核心重构：私有方法，用于组装链 ---
    def _build_chain(self, model_name, temperature=None):
        """
        工厂方法：根据温度组装一条全新的 Chain
        """

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"

            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"

            return formatted_str

        def format_for_retriever(value: dict) -> str:
            return value["input"]

        def format_for_prompt_template(value):
            # {input, context, history}
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]
            return new_value

        def clean_thinking_from_history(value):
            think_pattern = r'<think>.*?</think>'

            # 移除所有思考标签，保留剩余内容
            raw_history = value["history"]
            history = re.sub(think_pattern, "", raw_history, flags=re.DOTALL)
            history = history.strip()

            # 更新value，添加思考内容列表
            value["history"] = history

            return value

        if model_name == "qwen_0.6b":
            chat_model = self.qwen_model_600m
        # elif model_name == "deepseek_r1":
        #     chat_model = self.deepseek_r1
        else:
            chat_model = self.qwen_model_32b

        # 1. 确定模型：如果有指定温度，就用 bind 生成一个副本；否则用默认的
        if temperature is not None:
            llm_to_use = chat_model.bind(temperature=temperature)
        else:
            llm_to_use = chat_model

        # 2. 组装 RAG 逻辑
        chain = (
                {
                    "input": RunnablePassthrough(),
                    "context": RunnableLambda(format_for_retriever) | self.retriever | format_document
                }
                | RunnableLambda(format_for_prompt_template)
                | clean_thinking_from_history
                | self.prompt_template
                | print_prompt
                | llm_to_use  # <--- 使用刚才绑定了温度的模型
                | StrOutputParser()
        )
        return chain

    # --- 场景 A: 给 QA 页面用 (自动挡) ---
    def stream_qa_response(self, prompt, session_id, model_name):
        """
        QA 模式：使用默认温度，LangChain 自动管理历史
        """
        # 1. 获取基础链 (默认温度)
        chain = self._build_chain(model_name, temperature=None)

        # 2. 包装自动历史管理
        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_qa_chat_history,  # SQLite 工厂函数
            input_messages_key="input",
            history_messages_key="history",
        )

        # 3. 执行
        return chain_with_history.stream(
            {"input": prompt},
            config={"configurable": {"session_id": session_id}}
        )

    # --- 场景 B: 给 RLHF 页面用 (手动挡) ---
    def stream_rlhf_response(self, prompt, history_list, temperature, model_name):
        """
        RLHF 模式：指定温度，手动传入历史列表 (不自动查库，不自动存库)
        """
        # 1. 获取基础链 (绑定了特定温度!)
        chain = self._build_chain(model_name, temperature=temperature)

        # 2. 直接执行 (不包 RunnableWithMessageHistory)
        # 我们手动把 history_list 传给 chain，它会填入 prompt 的 history 占位符
        return chain.stream({
            "input": prompt,
            "history": history_list  # <--- 手动喂入 List[BaseMessage]
        })

    def get_retrieved_context(self, query: str) -> str:
        """
        检索并返回格式化后的文本内容 (用于存库)
        """
        # 1. 执行检索
        docs = self.retriever.invoke(query)

        # 2. 拼接文本
        # 格式示例：
        # [Document 1]: ...内容...
        # [Document 2]: ...内容...
        context_parts = []
        for i, doc in enumerate(docs):
            source = os.path.basename(doc.metadata.get("source", "unknown"))
            content = doc.page_content.replace("\n", " ")  # 简单的去换行清洗
            context_parts.append(f"【参考片段 {i + 1} (来源: {source})】:\n{content}")

        return "\n\n".join(context_parts)