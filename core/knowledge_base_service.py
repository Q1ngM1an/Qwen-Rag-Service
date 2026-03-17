import os
from typing import List, Dict, Any

import configs.config as config
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

from core.vector_store_service import get_vector_store


def check_md5(md5_str: str, filename: str = None):
    """检查传入的md5字符串是否已经被处理过了
        return False(md5未处理过)  True(已经处理过，已有记录）
    """
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()
            if line:
                # 新格式: 文件名:md5
                stored_filename, stored_md5 = line.split(':', 1)
                if stored_md5 == md5_str:
                    return True
        return False


def save_md5(md5_str: str, filename: str):
    """将传入的md5字符串和文件名关联保存"""
    with open(config.md5_path, 'a', encoding="utf-8") as f:
        f.write(f"{filename}:{md5_str}\n")


def delete_md5_by_filename(filename: str):
    """根据文件名删除对应的md5记录"""
    if not os.path.exists(config.md5_path):
        return

    # 读取所有行，过滤掉包含该文件名的行
    with open(config.md5_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        line = line.strip()
        if line:
            stored_filename, _ = line.split(':', 1)
            if stored_filename != filename:
                new_lines.append(line + '\n')
    # 写回文件
    with open(config.md5_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def get_string_md5(input_str: str, encoding='utf-8'):
    """将传入的字符串转换为md5字符串"""

    # 将字符串转换为bytes字节数组
    str_bytes = input_str.encode(encoding=encoding)

    # 创建md5对象
    md5_obj = hashlib.md5()     # 得到md5对象
    md5_obj.update(str_bytes)   # 更新内容（传入即将要转换的字节数组）
    md5_hex = md5_obj.hexdigest()       # 得到md5的十六进制字符串

    return md5_hex


class KnowledgeBaseService(object):
    def __init__(self):
        # 如果文件夹不存在则创建，如果存在则跳过
        os.makedirs(config.persist_directory, exist_ok=True)

        self.vector_store = get_vector_store()

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,       # 分割后的文本段最大长度
            chunk_overlap=config.chunk_overlap,     # 连续文本段之间的字符重叠数量
            separators=config.separators,       # 自然段落划分的符号
            length_function=len,                # 使用Python自带的len函数做长度统计的依据
        )     # 文本分割器的对象

    def upload_by_str(self, data: str, filename):
        """将传入的字符串，进行向量化，存入向量数据库中"""
        # 先得到传入字符串的md5值
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex, filename):
            return "[跳过]内容已经存在知识库中"

        if len(data) > config.max_split_char_number:
            knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "source": filename,
            # 2025-01-01 10:00:00
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "admain",
        }

        self.vector_store.add_texts(      # 内容就加载到向量库中了
            # iterable -> list \ tuple
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks],
        )

        #
        save_md5(md5_hex, filename)

        return "[成功]内容已经成功载入向量库"


    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        获取向量库中所有文档的唯一列表
        返回格式：[{'source': '文件名', 'create_time': '创建时间'}, ...]
        """
        try:
            # 获取所有文档数据
            collection_data = self.vector_store.get(
                include=["metadatas"]
            )

            # 提取唯一的文档信息（基于source字段）
            documents_map = {}
            for metadata in collection_data.get("metadatas", []):
                source = metadata.get("source")
                create_time = metadata.get("create_time")

                if source and source not in documents_map:
                    documents_map[source] = {
                        "source": source,
                        "create_time": create_time
                    }

            # 转换为列表并按创建时间倒序排序
            documents_list = list(documents_map.values())
            documents_list.sort(
                key=lambda x: x.get("create_time", ""),
                reverse=True
            )

            return documents_list

        except Exception as e:
            print(f"获取文档列表失败: {str(e)}")
            return []

    def delete_document(self, filename: str) -> bool:
        """
        删除指定文件名的所有文档块
        """
        try:
            # 首先检查文档是否存在
            all_docs = self.get_all_documents()
            file_exists = any(doc["source"] == filename for doc in all_docs)

            if not file_exists:
                print(f"文件不存在: {filename}")
                return False

            # 删除指定source的所有文档
            # 注意：Chroma的delete方法可能因版本不同而有所差异
            # 这里假设Chroma支持通过metadata过滤删除
            self.vector_store.delete(
                where={"source": filename}
            )
            # 删除对应的md5记录
            delete_md5_by_filename(filename)
            print(f"已删除文件: {filename}")
            return True

        except Exception as e:
            print(f"删除文件失败 {filename}: {str(e)}")
            return False

    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        根据文件名搜索文档
        """
        all_docs = self.get_all_documents()

        if not query:
            return all_docs

        # 简单的文件名模糊搜索
        search_results = []
        query_lower = query.lower()

        for doc in all_docs:
            source = doc.get("source", "").lower()
            if query_lower in source:
                search_results.append(doc)

        return search_results


