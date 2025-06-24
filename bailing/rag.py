import logging
import hashlib
from typing import List, Dict, Any
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
import markdown
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RAG:
    """RAG (Retrieval-Augmented Generation) 类，用于文档检索和查询"""

    def __init__(
        self,
        documents_dir: str = "documents",
        db_path: str = "data/chroma_db",
        collection_name: str = "documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        初始化RAG系统

        Args:
            documents_dir: 文档目录路径
            db_path: Chroma数据库存储路径
            collection_name: 集合名称
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠长度
        """
        self.documents_dir = Path(documents_dir)
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 确保目录存在
        self.db_path.mkdir(parents=True, exist_ok=True)

        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(path=str(self.db_path))

        # 使用默认的embedding函数
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name, embedding_function=self.embedding_function
            )
            logger.info(f"已加载现有集合: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name, embedding_function=self.embedding_function
            )
            logger.info(f"已创建新集合: {self.collection_name}")

    def _load_markdown_file(self, file_path: Path) -> str:
        """
        加载并解析markdown文件

        Args:
            file_path: markdown文件路径

        Returns:
            解析后的纯文本内容
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 将markdown转换为HTML，然后提取纯文本
            html: str = markdown.markdown(content)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()

            return text.strip()
        except Exception as e:
            logger.error(f"加载文件 {file_path} 失败: {e}")
            return ""

    def _chunk_text(self, text: str) -> List[str]:
        """
        将文本分割成块

        Args:
            text: 待分割的文本

        Returns:
            文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # 计算当前块的结束位置
            end = start + self.chunk_size

            if end >= len(text):
                # 最后一块
                chunks.append(text[start:])
                break

            # 尝试在句号、换行符或空格处分割
            chunk_end = end
            for delimiter in ["\n\n", "\n", ". ", " "]:
                pos = text.rfind(delimiter, start, end)
                if pos > start:
                    chunk_end = pos + len(delimiter)
                    break

            chunks.append(text[start:chunk_end])

            # 下一块的开始位置（考虑重叠）
            start = max(start + 1, chunk_end - self.chunk_overlap)

        return chunks

    def _generate_id(self, file_path: str, chunk_index: int) -> str:
        """
        生成文档块的唯一ID

        Args:
            file_path: 文件路径
            chunk_index: 块索引

        Returns:
            唯一ID
        """
        content = f"{file_path}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()

    def load_documents(self) -> None:
        """加载documents目录下的所有markdown文档到向量数据库"""
        if not self.documents_dir.exists():
            logger.warning(f"文档目录不存在: {self.documents_dir}")
            return

        markdown_files = list(self.documents_dir.glob("**/*.md"))
        logger.info(f"找到 {len(markdown_files)} 个markdown文件")

        # 获取已存在的文档ID
        existing_ids = set()
        try:
            result = self.collection.get()
            existing_ids = set(result["ids"])
        except Exception:
            pass

        documents = []
        metadatas = []
        ids = []

        for file_path in markdown_files:
            logger.info(f"处理文件: {file_path}")

            # 加载文档内容
            content = self._load_markdown_file(file_path)
            if not content:
                continue

            # 分割文档
            chunks = self._chunk_text(content)

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                doc_id = self._generate_id(str(file_path), i)

                # 跳过已存在的文档
                if doc_id in existing_ids:
                    continue

                documents.append(chunk)
                metadatas.append(
                    {
                        "file_path": str(file_path),
                        "chunk_index": i,
                        "file_name": file_path.name,
                    }
                )
                ids.append(doc_id)

        # 批量添加到数据库
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"已添加 {len(documents)} 个文档块到数据库")
        else:
            logger.info("没有新文档需要添加")

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关文档

        Args:
            query: 查询文本
            n_results: 返回结果数量

        Returns:
            搜索结果列表
        """
        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)

            # 格式化结果
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append(
                        {
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i]
                            if results["distances"]
                            else None,
                        }
                    )

            return formatted_results
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def get_relevant_context(self, query: str, max_context_length: int = 2000) -> str:
        """
        获取与查询相关的上下文

        Args:
            query: 查询文本
            max_context_length: 最大上下文长度

        Returns:
            相关上下文文本
        """
        results = self.search(query, n_results=5)

        context_parts = []
        current_length = 0

        for result in results:
            content = result["content"]
            file_name = result["metadata"].get("file_name", "unknown")

            # 添加文件来源信息
            part = f"[来源: {file_name}]\n{content}\n"

            if current_length + len(part) <= max_context_length:
                context_parts.append(part)
                current_length += len(part)
            else:
                # 如果添加当前部分会超出长度限制，尝试添加部分内容
                remaining_length = (
                    max_context_length
                    - current_length
                    - len(f"[来源: {file_name}]\n\n")
                )
                if remaining_length > 100:  # 只有在剩余长度足够时才添加
                    truncated_content = content[:remaining_length] + "..."
                    context_parts.append(f"[来源: {file_name}]\n{truncated_content}\n")
                break

        return "\n".join(context_parts)

    def rebuild_index(self) -> None:
        """重建索引，删除现有数据并重新加载"""
        try:
            # 删除现有集合
            self.client.delete_collection(self.collection_name)
            logger.info(f"已删除现有集合: {self.collection_name}")
        except Exception:
            pass

        # 重新创建集合
        self.collection = self.client.create_collection(
            name=self.collection_name, embedding_function=self.embedding_function
        )
        logger.info(f"已重新创建集合: {self.collection_name}")

        # 重新加载文档
        self.load_documents()

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "db_path": str(self.db_path),
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}


# 创建全局RAG实例
def create_rag_instance(documents_dir: str = "documents") -> RAG:
    """创建RAG实例"""
    rag = RAG(documents_dir=documents_dir)
    # 自动加载文档
    rag.load_documents()
    return rag
