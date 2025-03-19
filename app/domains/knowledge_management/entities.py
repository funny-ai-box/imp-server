"""知识管理领域实体"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid

class DocumentStatus(Enum):
    """文档状态枚举"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    PROCESSED = "processed"  # 已处理
    FAILED = "failed"  # 处理失败
    DELETED = "deleted"  # 已删除

class DocumentType(Enum):
    """文档类型枚举"""
    TEXT = "text"  # 纯文本
    PDF = "pdf"  # PDF文件
    DOCX = "docx"  # Word文档
    CSV = "csv"  # CSV表格
    EXCEL = "excel"  # Excel表格
    HTML = "html"  # HTML页面
    MARKDOWN = "markdown"  # Markdown文档
    JSON = "json"  # JSON文件
    XML = "xml"  # XML文件
    URL = "url"  # 网页URL

class ChunkingStrategy(Enum):
    """文本分块策略枚举"""
    FIXED_SIZE = "fixed_size"  # 固定大小分块
    SEMANTIC = "semantic"  # 语义分块
    PARAGRAPH = "paragraph"  # 段落分块
    SENTENCE = "sentence"  # 句子分块
    CUSTOM = "custom"  # 自定义分块

class IndexStatus(Enum):
    """索引状态枚举"""
    CREATING = "creating"  # 创建中
    READY = "ready"  # 就绪
    UPDATING = "updating"  # 更新中
    ERROR = "error"  # 错误状态
    DELETED = "deleted"  # 已删除

@dataclass
class TextChunk:
    """文本块"""
    id: str  # 块ID
    text: str  # 块内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    document_id: Optional[str] = None  # 所属文档ID
    page_number: Optional[int] = None  # 页码（如适用）
    position: Optional[int] = None  # 块在文档中的位置
    tokens: Optional[int] = None  # Token数量
    embedding_id: Optional[str] = None  # 向量存储中的嵌入ID
    
    @classmethod
    def create(cls, text: str, document_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'TextChunk':
        """创建文本块
        
        Args:
            text: 文本内容
            document_id: 所属文档ID
            metadata: 元数据
            
        Returns:
            创建的文本块
        """
        return cls(
            id=str(uuid.uuid4()),
            text=text,
            document_id=document_id,
            metadata=metadata or {}
        )

@dataclass
class Document:
    """文档实体"""
    id: str  # 文档ID
    title: str  # 文档标题
    type: DocumentType  # 文档类型
    status: DocumentStatus  # 处理状态
    content: Optional[str] = None  # 原始内容（可选，对于大文档可能不存储）
    content_length: int = 0  # 内容长度（字符数）
    chunks: List[TextChunk] = field(default_factory=list)  # 分块后的文本
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    source_url: Optional[str] = None  # 源URL（如适用）
    file_path: Optional[str] = None  # 文件路径（如适用）
    file_size: Optional[int] = None  # 文件大小（字节）
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    knowledge_base_id: Optional[str] = None  # 所属知识库ID
    embedding_model: Optional[str] = None  # 使用的嵌入模型
    error_message: Optional[str] = None  # 错误信息（如适用）
    
    @classmethod
    def create(cls, title: str, doc_type: DocumentType, kb_id: Optional[str] = None) -> 'Document':
        """创建文档实体
        
        Args:
            title: 文档标题
            doc_type: 文档类型
            kb_id: 知识库ID
            
        Returns:
            创建的文档实体
        """
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            type=doc_type,
            status=DocumentStatus.PENDING,
            knowledge_base_id=kb_id
        )
    
    def add_chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> TextChunk:
        """添加文本块
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            创建的文本块
        """
        # 设置块位置为当前块数
        position = len(self.chunks)
        
        # 创建新块
        chunk = TextChunk(
            id=str(uuid.uuid4()),
            text=text,
            document_id=self.id,
            position=position,
            metadata=metadata or {}
        )
        
        # 添加到块列表
        self.chunks.append(chunk)
        self.updated_at = datetime.now()
        
        return chunk
    
    def update_status(self, status: DocumentStatus, error_message: Optional[str] = None) -> None:
        """更新文档处理状态
        
        Args:
            status: 新状态
            error_message: 错误信息（如适用）
        """
        self.status = status
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.now()
    
    def get_chunk_count(self) -> int:
        """获取块数量
        
        Returns:
            块数量
        """
        return len(self.chunks)
    
    def to_dict(self) -> Dict[str, Any]:
        """将文档转换为字典
        
        Returns:
            字典表示
        """
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "status": self.status.value,
            "content_length": self.content_length,
            "chunks_count": len(self.chunks),
            "metadata": self.metadata,
            "source_url": self.source_url,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "knowledge_base_id": self.knowledge_base_id,
            "embedding_model": self.embedding_model,
            "error_message": self.error_message
        }

@dataclass
class KnowledgeBase:
    """知识库实体"""
    id: str  # 知识库ID
    name: str  # 知识库名称
    description: str  # 知识库描述
    documents: List[Document] = field(default_factory=list)  # 文档列表
    index_status: IndexStatus = IndexStatus.CREATING  # 索引状态
    embedding_model: str = "text-embedding-ada-002"  # 嵌入模型
    embedding_dimension: int = 1536  # 嵌入维度
    vector_store: str = "pinecone"  # 向量存储服务
    index_name: Optional[str] = None  # 向量索引名称
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.PARAGRAPH  # 分块策略
    chunk_size: int = 1000  # 块大小（字符数）
    chunk_overlap: int = 200  # 块重叠（字符数）
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    tags: List[str] = field(default_factory=list)  # 标签列表
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    @classmethod
    def create(cls, name: str, description: str, embedding_model: str = "text-embedding-ada-002") -> 'KnowledgeBase':
        """创建知识库
        
        Args:
            name: 知识库名称
            description: 知识库描述
            embedding_model: 嵌入模型名称
            
        Returns:
            创建的知识库
        """
        kb_id = str(uuid.uuid4())
        return cls(
            id=kb_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            index_name=f"kb-{kb_id}"
        )
    
    def add_document(self, document: Document) -> None:
        """添加文档
        
        Args:
            document: 要添加的文档
        """
        document.knowledge_base_id = self.id
        self.documents.append(document)
        self.updated_at = datetime.now()
    
    def remove_document(self, document_id: str) -> bool:
        """移除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否成功移除
        """
        for i, doc in enumerate(self.documents):
            if doc.id == document_id:
                self.documents.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def update_status(self, status: IndexStatus) -> None:
        """更新索引状态
        
        Args:
            status: 新状态
        """
        self.index_status = status
        self.updated_at = datetime.now()
    
    def get_document_count(self) -> int:
        """获取文档数量
        
        Returns:
            文档数量
        """
        return len(self.documents)
    
    def get_processed_document_count(self) -> int:
        """获取已处理文档数量
        
        Returns:
            已处理文档数量
        """
        return sum(1 for doc in self.documents if doc.status == DocumentStatus.PROCESSED)
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档实体或None
        """
        for doc in self.documents:
            if doc.id == document_id:
                return doc
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """将知识库转换为字典
        
        Returns:
            字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "document_count": len(self.documents),
            "processed_document_count": self.get_processed_document_count(),
            "index_status": self.index_status.value,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "vector_store": self.vector_store,
            "index_name": self.index_name,
            "chunking_strategy": self.chunking_strategy.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata
        }

@dataclass
class SearchResult:
    """搜索结果"""
    chunk: TextChunk  # 匹配的文本块
    score: float  # 相似度分数
    document_title: Optional[str] = None  # 文档标题
    document_type: Optional[str] = None  # 文档类型
    
    def to_dict(self) -> Dict[str, Any]:
        """将搜索结果转换为字典
        
        Returns:
            字典表示
        """
        return {
            "text": self.chunk.text,
            "score": self.score,
            "document_id": self.chunk.document_id,
            "document_title": self.document_title,
            "document_type": self.document_type,
            "metadata": self.chunk.metadata,
            "page_number": self.chunk.page_number,
            "position": self.chunk.position
        }

@dataclass
class SearchQuery:
    """搜索查询"""
    query: str  # 查询文本
    knowledge_base_id: str  # 知识库ID
    top_k: int = 5  # 返回结果数量
    filters: Dict[str, Any] = field(default_factory=dict)  # 过滤条件
    min_score: Optional[float] = None  # 最小分数阈值