"""
Embedding Table Router

Handles routing embedding operations to the correct dimension-specific table.
Supports multiple embedding models with different dimensions.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class EmbeddingTableRouter:
    """Routes embedding operations to dimension-specific tables."""
    
    # Supported dimensions and their corresponding table names (provider-agnostic)
    DIMENSION_TABLES = {
        384: "archon_crawled_pages_384",   # Cohere light, Ollama all-minilm
        768: "archon_crawled_pages_768",   # Google, Ollama nomic-embed
        1024: "archon_crawled_pages_1024", # Cohere standard, Mistral, Ollama mxbai
        1536: "archon_crawled_pages_1536", # OpenAI small/ada-002
        3072: "archon_crawled_pages_3072"  # OpenAI large
    }
    
    @classmethod
    def get_table_name(cls, dimensions: int) -> str:
        """Get the table name for given embedding dimensions."""
        if dimensions not in cls.DIMENSION_TABLES:
            supported = list(cls.DIMENSION_TABLES.keys())
            raise ValueError(f"Unsupported embedding dimension: {dimensions}. Supported: {supported}")
        
        return cls.DIMENSION_TABLES[dimensions]
    
    @classmethod
    def get_supported_dimensions(cls) -> List[int]:
        """Get list of supported embedding dimensions."""
        return list(cls.DIMENSION_TABLES.keys())
    
    @classmethod
    async def insert_embeddings(cls, client, embeddings_data: List[Dict[str, Any]], dimensions: int):
        """Insert embeddings into the correct dimension-specific table."""
        table_name = cls.get_table_name(dimensions)
        
        logger.info(f"Inserting {len(embeddings_data)} embeddings into {table_name} (dimensions: {dimensions})")
        
        try:
            # Insert into dimension-specific table
            result = client.table(table_name).insert(embeddings_data).execute()
            logger.info(f"Successfully inserted {len(embeddings_data)} embeddings into {table_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to insert embeddings into {table_name}: {e}")
            raise
    
    @classmethod
    async def delete_by_url(cls, client, urls: List[str], dimensions: int):
        """Delete embeddings by URL from the correct dimension-specific table."""
        table_name = cls.get_table_name(dimensions)
        
        logger.info(f"Deleting embeddings for {len(urls)} URLs from {table_name}")
        
        try:
            for url in urls:
                client.table(table_name).delete().eq("url", url).execute()
            logger.info(f"Successfully deleted embeddings from {table_name}")
        except Exception as e:
            logger.error(f"Failed to delete embeddings from {table_name}: {e}")
            raise
    
    @classmethod
    async def search_embeddings(cls, client, query_embedding: List[float], dimensions: int, 
                               match_count: int = 5, filter_metadata: Dict = None) -> List[Dict[str, Any]]:
        """Search embeddings in the correct dimension-specific table."""
        table_name = cls.get_table_name(dimensions)
        
        if len(query_embedding) != dimensions:
            raise ValueError(f"Query embedding dimension {len(query_embedding)} doesn't match table dimension {dimensions}")
        
        logger.info(f"Searching {table_name} for {match_count} matches")
        
        try:
            # Build the query
            query = client.table(table_name).select("*")
            
            # Add metadata filter if provided
            if filter_metadata:
                for key, value in filter_metadata.items():
                    query = query.eq(f"metadata->{key}", value)
            
            # Add similarity search
            query = query.order("embedding.cosine_distance", {
                "column": "embedding", 
                "value": query_embedding
            }).limit(match_count)
            
            result = query.execute()
            
            logger.info(f"Found {len(result.data)} matches in {table_name}")
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to search embeddings in {table_name}: {e}")
            raise