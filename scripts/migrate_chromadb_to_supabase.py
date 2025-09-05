#!/usr/bin/env python3
"""
Migration script to transfer data from ChromaDB to Supabase vector store.
This script reads all documents from an existing ChromaDB collection and transfers them to Supabase.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import argparse

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.backend.vector_store.supabase_vector_store import SupabaseVectorStore
from src.backend.chain.config import (
    CHROMA_DB_PATH,
    GEMINI_EMBEDDING_MODEL
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChromaEmbeddingWrapper:
    """Wrapper to make LangChain embeddings compatible with ChromaDB"""
    
    def __init__(self, langchain_embeddings):
        self.embeddings = langchain_embeddings
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """ChromaDB expects this signature"""
        return self.embeddings.embed_documents(input)
    
    def name(self) -> str:
        """ChromaDB expects this method"""
        return "google_generative_ai_embeddings"


class ChromaToSupabaseMigrator:
    """
    Handles migration from ChromaDB to Supabase vector store.
    """
    
    def __init__(self, 
                 chroma_db_path: str = CHROMA_DB_PATH,
                 chroma_collection_name: str = "rag_chunks",
                 supabase_table_name: str = "document_embeddings",
                 embedding_dimension: int = 768):
        
        self.chroma_db_path = chroma_db_path
        self.chroma_collection_name = chroma_collection_name
        self.supabase_table_name = supabase_table_name
        self.embedding_dimension = embedding_dimension
        
        # Initialize Gemini API
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Initialize embedding model
        self.langchain_embeddings = GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBEDDING_MODEL,
            google_api_key=api_key
        )
        self.embedding_wrapper = ChromaEmbeddingWrapper(self.langchain_embeddings)
        
        # Initialize ChromaDB client
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
            self.chroma_collection = self.chroma_client.get_collection(
                name=self.chroma_collection_name,
                embedding_function=self.embedding_wrapper
            )
            logger.info(f"Connected to ChromaDB collection: {self.chroma_collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
        
        # Initialize Supabase vector store
        try:
            self.supabase_store = SupabaseVectorStore(
                table_name=self.supabase_table_name,
                embedding_dimension=self.embedding_dimension
            )
            logger.info(f"Connected to Supabase table: {self.supabase_table_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def get_chromadb_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection."""
        try:
            count = self.chroma_collection.count()
            return {
                "collection_name": self.chroma_collection_name,
                "total_documents": count,
                "path": self.chroma_db_path
            }
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {}
    
    def get_supabase_stats(self) -> Dict[str, Any]:
        """Get statistics about the Supabase collection."""
        try:
            return self.supabase_store.get_collection_info()
        except Exception as e:
            logger.error(f"Failed to get Supabase stats: {e}")
            return {}
    
    def migrate_data(self, batch_size: int = 100, clear_supabase: bool = False) -> Dict[str, Any]:
        """
        Migrate all data from ChromaDB to Supabase.
        
        Args:
            batch_size: Number of documents to process in each batch
            clear_supabase: Whether to clear existing data in Supabase first
            
        Returns:
            Migration statistics
        """
        logger.info("Starting migration from ChromaDB to Supabase...")
        
        # Get initial stats
        chroma_stats = self.get_chromadb_stats()
        logger.info(f"ChromaDB stats: {chroma_stats}")
        
        if clear_supabase:
            logger.info("Clearing existing data in Supabase...")
            self.supabase_store.clear_collection()
        
        supabase_stats_before = self.get_supabase_stats()
        logger.info(f"Supabase stats before migration: {supabase_stats_before}")
        
        # Get all data from ChromaDB
        try:
            # ChromaDB get() method retrieves all documents if no IDs specified
            chroma_results = self.chroma_collection.get(
                include=['documents', 'metadatas', 'embeddings']
            )
            
            documents = chroma_results['documents']
            metadatas = chroma_results['metadatas'] 
            embeddings = chroma_results['embeddings']
            ids = chroma_results.get('ids', [])
            
            total_docs = len(documents)
            logger.info(f"Retrieved {total_docs} documents from ChromaDB")
            
        except Exception as e:
            logger.error(f"Failed to retrieve data from ChromaDB: {e}")
            raise
        
        if total_docs == 0:
            logger.warning("No documents found in ChromaDB collection")
            return {"migrated_documents": 0, "errors": 0}
        
        # Migrate in batches
        migrated_count = 0
        error_count = 0
        
        for i in range(0, total_docs, batch_size):
            batch_end = min(i + batch_size, total_docs)
            batch_docs = documents[i:batch_end]
            batch_metas = metadatas[i:batch_end]
            batch_embeddings = embeddings[i:batch_end]
            batch_ids = ids[i:batch_end] if ids else None
            
            logger.info(f"Processing batch {i//batch_size + 1}: docs {i+1}-{batch_end}")
            
            try:
                # Convert ChromaDB metadata format to Supabase format
                converted_metadatas = []
                for meta in batch_metas:
                    converted_meta = {}
                    for key, value in meta.items():
                        # Convert all values to appropriate types for JSON storage
                        if isinstance(value, (str, int, float, bool)):
                            converted_meta[key] = value
                        else:
                            converted_meta[key] = str(value)
                    converted_metadatas.append(converted_meta)
                
                # Store batch in Supabase
                batch_result_ids = self.supabase_store.add_documents(
                    documents=batch_docs,
                    embeddings=batch_embeddings,
                    metadatas=converted_metadatas,
                    ids=batch_ids
                )
                
                migrated_count += len(batch_result_ids)
                logger.info(f"Successfully migrated batch: {len(batch_result_ids)} documents")
                
            except Exception as e:
                logger.error(f"Error migrating batch {i//batch_size + 1}: {e}")
                error_count += len(batch_docs)
                continue
        
        # Get final stats
        supabase_stats_after = self.get_supabase_stats()
        logger.info(f"Supabase stats after migration: {supabase_stats_after}")
        
        migration_stats = {
            "source_documents": total_docs,
            "migrated_documents": migrated_count,
            "error_count": error_count,
            "success_rate": f"{(migrated_count/total_docs)*100:.1f}%" if total_docs > 0 else "0%",
            "supabase_total_after": supabase_stats_after.get("total_documents", 0)
        }
        
        logger.info("Migration completed!")
        logger.info(f"Migration stats: {migration_stats}")
        
        return migration_stats
    
    def verify_migration(self, sample_size: int = 10) -> Dict[str, Any]:
        """
        Verify the migration by comparing a sample of documents.
        
        Args:
            sample_size: Number of documents to sample for verification
            
        Returns:
            Verification results
        """
        logger.info(f"Verifying migration with sample size: {sample_size}")
        
        try:
            # Get a sample from ChromaDB
            chroma_sample = self.chroma_collection.get(
                limit=sample_size,
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not chroma_sample['documents']:
                logger.warning("No documents found in ChromaDB for verification")
                return {"verification": "failed", "reason": "No ChromaDB documents"}
            
            # Check if these documents exist in Supabase
            verified_count = 0
            missing_count = 0
            
            for i, doc_content in enumerate(chroma_sample['documents']):
                # Try to find similar document in Supabase using similarity search
                # Generate embedding for the document
                doc_embedding = self.langchain_embeddings.embed_query(doc_content)
                
                # Search for similar documents
                similar_docs = self.supabase_store.similarity_search(
                    query_embedding=doc_embedding,
                    k=1
                )
                
                if similar_docs and similar_docs[0].distance < 0.01:  # Very close match
                    verified_count += 1
                else:
                    missing_count += 1
                    logger.warning(f"Document {i+1} not found or not similar in Supabase")
            
            verification_stats = {
                "sample_size": len(chroma_sample['documents']),
                "verified_documents": verified_count,
                "missing_documents": missing_count,
                "verification_rate": f"{(verified_count/len(chroma_sample['documents']))*100:.1f}%"
            }
            
            logger.info(f"Verification results: {verification_stats}")
            return verification_stats
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"verification": "failed", "error": str(e)}


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description="Migrate ChromaDB data to Supabase vector store")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration")
    parser.add_argument("--clear-supabase", action="store_true", help="Clear existing Supabase data first")
    parser.add_argument("--verify", action="store_true", help="Run verification after migration")
    parser.add_argument("--sample-size", type=int, default=10, help="Sample size for verification")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without migrating")
    
    args = parser.parse_args()
    
    try:
        # Initialize migrator
        migrator = ChromaToSupabaseMigrator()
        
        if args.dry_run:
            logger.info("DRY RUN: Showing statistics without migration")
            chroma_stats = migrator.get_chromadb_stats()
            supabase_stats = migrator.get_supabase_stats()
            
            print("\n" + "="*60)
            print("CURRENT STATE")
            print("="*60)
            print(f"ChromaDB: {chroma_stats}")
            print(f"Supabase: {supabase_stats}")
            print("="*60)
            
            return
        
        # Run migration
        migration_stats = migrator.migrate_data(
            batch_size=args.batch_size,
            clear_supabase=args.clear_supabase
        )
        
        print("\n" + "="*60)
        print("MIGRATION RESULTS")
        print("="*60)
        for key, value in migration_stats.items():
            print(f"{key}: {value}")
        
        # Run verification if requested
        if args.verify:
            print("\n" + "="*60)
            print("VERIFICATION RESULTS")
            print("="*60)
            
            verification_stats = migrator.verify_migration(sample_size=args.sample_size)
            for key, value in verification_stats.items():
                print(f"{key}: {value}")
        
        print("="*60)
        
        if migration_stats.get("error_count", 0) == 0:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.warning("⚠️  Migration completed with some errors. Check logs above.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
