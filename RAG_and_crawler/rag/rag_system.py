"""
RAG System - Retrieval-Augmented Generation for gut health insights
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
import asyncio
import json
from pathlib import Path
import time

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class HealthRAGSystem:
    """RAG system for gut health and nutrition knowledge"""
    
    def __init__(self, 
                 chroma_db_path: str = "./data/chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 collection_name: str = "gut_health_knowledge"):
        
        self.chroma_db_path = Path(chroma_db_path)
        self.chroma_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.collection_name = collection_name
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Gut health and nutrition knowledge base"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """
        Add documents to the vector database
        
        Args:
            documents: List of document dictionaries with content and metadata
            batch_size: Number of documents to process at once
        """
        logger.info(f"Adding {len(documents)} documents to vector database...")
        
        processed_docs = []
        
        for doc in documents:
            try:
                # Prepare document chunks
                chunks = self._chunk_document(doc)
                processed_docs.extend(chunks)
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('title', 'Unknown')}: {e}")
        
        # Process in batches
        for i in range(0, len(processed_docs), batch_size):
            batch = processed_docs[i:i + batch_size]
            self._add_batch_to_collection(batch)
            
            if i % (batch_size * 10) == 0:
                logger.info(f"Processed {i + len(batch)}/{len(processed_docs)} chunks")
        
        logger.info(f"✅ Added {len(processed_docs)} document chunks to vector database")
    
    def _chunk_document(self, document: Dict, 
                       chunk_size: int = 1000, 
                       overlap: int = 200) -> List[Dict]:
        """Split document into overlapping chunks"""
        content = document.get('content', '')
        title = document.get('title', '')
        
        if not content:
            return []
        
        # Simple text chunking
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) < 100:  # Skip very short chunks
                continue
            
            chunk = {
                'text': chunk_text,
                'metadata': {
                    'source': document.get('source', ''),
                    'title': title,
                    'url': document.get('url', ''),
                    'author': document.get('author', ''),
                    'publication_date': document.get('publication_date', ''),
                    'categories': document.get('categories', []),
                    'chunk_index': len(chunks),
                    'total_chunks': 0,  # Will be updated
                    'content_type': document.get('content_type', 'article')
                }
            }
            chunks.append(chunk)
        
        # Update total_chunks
        for chunk in chunks:
            chunk['metadata']['total_chunks'] = len(chunks)
        
        return chunks
    
    def _add_batch_to_collection(self, batch: List[Dict]):
        """Add a batch of chunks to ChromaDB"""
        try:
            texts = [chunk['text'] for chunk in batch]
            metadatas = [chunk['metadata'] for chunk in batch]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Generate IDs
            ids = [f"doc_{int(time.time())}_{i}" for i in range(len(batch))]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
        except Exception as e:
            logger.error(f"Error adding batch to collection: {e}")
    
    def search(self, 
               query: str, 
               n_results: int = 5,
               filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of relevant document chunks with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filters
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'relevance_score': 1 - results['distances'][0][i]  # Convert distance to relevance
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector database: {e}")
            return []
    
    def get_context_for_query(self, 
                            query: str,
                            max_context_length: int = 4000,
                            diversity_threshold: float = 0.7) -> str:
        """
        Get relevant context for a query, optimized for LLM input
        
        Args:
            query: User query
            max_context_length: Maximum context length in characters
            diversity_threshold: Minimum diversity score for including results
            
        Returns:
            Formatted context string
        """
        # Search for relevant documents
        results = self.search(query, n_results=10)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        # Select diverse, high-quality results
        selected_results = self._select_diverse_results(results, diversity_threshold)
        
        # Format context
        context_parts = []
        current_length = 0
        
        for result in selected_results:
            content = result['content']
            metadata = result['metadata']
            
            # Create source citation
            source_info = f"Source: {metadata.get('title', 'Unknown')} "
            if metadata.get('author'):
                source_info += f"by {metadata['author']} "
            if metadata.get('source'):
                source_info += f"({metadata['source']})"
            
            formatted_chunk = f"{source_info}\n{content}\n---\n"
            
            if current_length + len(formatted_chunk) > max_context_length:
                break
            
            context_parts.append(formatted_chunk)
            current_length += len(formatted_chunk)
        
        if not context_parts:
            return "No relevant information found in the knowledge base."
        
        context = "Relevant scientific and expert information:\n\n" + "\n".join(context_parts)
        return context
    
    def _select_diverse_results(self, 
                              results: List[Dict], 
                              diversity_threshold: float) -> List[Dict]:
        """Select diverse results to avoid redundancy"""
        if not results:
            return []
        
        selected = [results[0]]  # Always include the most relevant result
        
        for result in results[1:]:
            # Check diversity against already selected results
            is_diverse = True
            for selected_result in selected:
                # Simple diversity check based on content similarity
                content_similarity = self._calculate_text_similarity(
                    result['content'], selected_result['content']
                )
                
                if content_similarity > diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse and result['relevance_score'] > 0.5:  # Minimum relevance threshold
                selected.append(result)
            
            if len(selected) >= 5:  # Limit number of results
                break
        
        return selected
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector database"""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze sources
            sample_results = self.collection.get(limit=min(1000, count))
            
            sources = {}
            content_types = {}
            
            for metadata in sample_results['metadatas']:
                source = metadata.get('source', 'unknown')
                content_type = metadata.get('content_type', 'unknown')
                
                sources[source] = sources.get(source, 0) + 1
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            return {
                'total_chunks': count,
                'sources': sources,
                'content_types': content_types,
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)}
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Gut health and nutrition knowledge base"}
            )
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")

# Utility functions for loading crawled data
def load_crawled_documents(data_dir: str = "./data/crawled") -> List[Dict]:
    """Load all crawled documents from JSON files"""
    documents = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory {data_dir} does not exist")
        return []
    
    for json_file in data_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                documents.extend(data)
            else:
                documents.append(data)
                
            logger.info(f"Loaded {len(data)} documents from {json_file.name}")
            
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
    
    logger.info(f"Total documents loaded: {len(documents)}")
    return documents

async def build_knowledge_base(data_dir: str = "./data/crawled",
                             chroma_db_path: str = "./data/chroma_db") -> HealthRAGSystem:
    """
    Build the complete knowledge base from crawled data
    
    Args:
        data_dir: Directory containing crawled JSON files
        chroma_db_path: Path for ChromaDB storage
        
    Returns:
        Initialized RAG system
    """
    logger.info("Building gut health knowledge base...")
    
    # Initialize RAG system
    rag_system = HealthRAGSystem(chroma_db_path)
    
    # Load crawled documents
    documents = load_crawled_documents(data_dir)
    
    if documents:
        # Add documents to vector database
        rag_system.add_documents(documents)
        
        # Show statistics
        stats = rag_system.get_collection_stats()
        logger.info(f"Knowledge base built with {stats['total_chunks']} chunks")
        logger.info(f"Sources: {list(stats['sources'].keys())}")
    else:
        logger.warning("No documents found to add to knowledge base")
    
    return rag_system

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        # Build knowledge base
        rag = await build_knowledge_base()
        
        # Test search
        test_query = "What foods are good for gut microbiome health?"
        context = rag.get_context_for_query(test_query)
        
        print(f"Query: {test_query}")
        print(f"Context length: {len(context)} characters")
        print("\nRelevant context:")
        print(context[:1000] + "..." if len(context) > 1000 else context)
    
    asyncio.run(main())
