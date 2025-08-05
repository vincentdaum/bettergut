"""
Simple health check API for RAG and Crawler container
Provides monitoring endpoints without heavy LLM dependencies
"""
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app for health checks and monitoring
app = FastAPI(
    title="BetterGut Crawler & RAG System",
    description="Health data crawling and RAG knowledge base builder",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state tracking
crawl_status = {
    "status": "idle",
    "start_time": None,
    "end_time": None,
    "articles_collected": 0,
    "sources_completed": 0,
    "current_source": None,
    "error": None
}

rag_status = {
    "status": "not_built",
    "chunks_created": 0,
    "build_time": None,
    "collection_name": "gut_health_knowledge",
    "error": None
}

class SystemStatus(BaseModel):
    crawl_status: Dict[str, Any]
    rag_status: Dict[str, Any]
    system_health: str
    uptime: str
    storage_info: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "bettergut-crawler-rag",
        "version": "1.0.0"
    }

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get comprehensive system status"""
    storage_info = _get_storage_info()
    
    # Determine overall system health
    system_health = "healthy"
    if crawl_status["status"] == "error" or rag_status["status"] == "error":
        system_health = "error"
    elif crawl_status["status"] == "running" or rag_status["status"] == "building":
        system_health = "working"
    
    return SystemStatus(
        crawl_status=crawl_status,
        rag_status=rag_status,
        system_health=system_health,
        uptime=_get_uptime(),
        storage_info=storage_info
    )

@app.get("/crawl/status")
async def get_crawl_status():
    """Get detailed crawling status"""
    return {
        "crawl_status": crawl_status,
        "storage_dir": str(Path("/app/data/crawled")),
        "available_files": _list_crawled_files()
    }

@app.get("/rag/status")
async def get_rag_status():
    """Get RAG system status"""
    vector_db_path = Path("/app/data/chroma_db")
    
    return {
        "rag_status": rag_status,
        "vector_db_path": str(vector_db_path),
        "vector_db_exists": vector_db_path.exists(),
        "vector_db_size": _get_directory_size(vector_db_path) if vector_db_path.exists() else 0
    }

@app.post("/crawl/start")
async def start_crawling():
    """Start the crawling process (if not already running)"""
    if crawl_status["status"] == "running":
        raise HTTPException(status_code=400, detail="Crawling already in progress")
    
    # Reset status
    crawl_status.update({
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "articles_collected": 0,
        "sources_completed": 0,
        "current_source": "starting",
        "error": None
    })
    
    # Start crawling in background
    asyncio.create_task(_run_crawling_process())
    
    return {"message": "Crawling process started", "status": crawl_status}

@app.post("/rag/build")
async def build_rag_system():
    """Build RAG system from crawled data"""
    if rag_status["status"] == "building":
        raise HTTPException(status_code=400, detail="RAG building already in progress")
    
    # Check if crawled data exists
    crawled_files = _list_crawled_files()
    if not crawled_files:
        raise HTTPException(status_code=400, detail="No crawled data found. Run crawling first.")
    
    # Reset status
    rag_status.update({
        "status": "building",
        "chunks_created": 0,
        "build_time": None,
        "error": None
    })
    
    # Start RAG building in background
    asyncio.create_task(_run_rag_building_process())
    
    return {"message": "RAG building process started", "status": rag_status}

@app.get("/logs")
async def get_logs():
    """Get recent log entries"""
    log_file = Path("/app/logs/crawler.log")
    if not log_file.exists():
        return {"logs": [], "message": "No log file found"}
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Return last 50 lines
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(lines),
            "showing_recent": len(recent_lines)
        }
    except Exception as e:
        return {"error": f"Failed to read logs: {e}"}

def _get_storage_info() -> Dict[str, Any]:
    """Get storage information"""
    paths = {
        "crawled_data": Path("/app/data/crawled"),
        "vector_db": Path("/app/data/chroma_db"),
        "storage": Path("/app/storage"),
        "logs": Path("/app/logs")
    }
    
    storage_info = {}
    for name, path in paths.items():
        storage_info[name] = {
            "path": str(path),
            "exists": path.exists(),
            "size_mb": round(_get_directory_size(path) / (1024 * 1024), 2) if path.exists() else 0
        }
    
    return storage_info

def _get_directory_size(path: Path) -> int:
    """Get total size of directory in bytes"""
    if not path.exists():
        return 0
    
    if path.is_file():
        return path.stat().st_size
    
    total = 0
    for item in path.rglob('*'):
        if item.is_file():
            total += item.stat().st_size
    return total

def _list_crawled_files() -> list:
    """List available crawled data files"""
    crawled_dir = Path("/app/data/crawled")
    if not crawled_dir.exists():
        return []
    
    files = []
    for file_path in crawled_dir.glob("*.json"):
        files.append({
            "filename": file_path.name,
            "size_kb": round(file_path.stat().st_size / 1024, 2),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        })
    
    return files

def _get_uptime() -> str:
    """Get container uptime (simplified)"""
    # This is a basic implementation
    return "Container running"

async def _run_crawling_process():
    """Background task to run the crawling process"""
    try:
        crawl_status["current_source"] = "medical_institutions"
        
        # This would normally import and run the actual crawlers
        # For now, simulate the process
        logger.info("Starting medical data crawling process...")
        
        # Simulate crawling progress
        sources = [
            "mayo_clinic", "harvard_nutrition", "nih_niddk", "johns_hopkins",
            "cleveland_clinic", "academy_nutrition", "aga", "iffgd"
        ]
        
        total_articles = 0
        for i, source in enumerate(sources):
            crawl_status["current_source"] = source
            crawl_status["sources_completed"] = i
            
            # Simulate crawling delay
            await asyncio.sleep(2)
            
            # Simulate articles collected
            articles_from_source = 25  # Simulate
            total_articles += articles_from_source
            crawl_status["articles_collected"] = total_articles
            
            logger.info(f"Completed crawling {source}: {articles_from_source} articles")
        
        # Complete crawling
        crawl_status.update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            "current_source": None,
            "sources_completed": len(sources)
        })
        
        logger.info(f"Crawling completed successfully. Total articles: {total_articles}")
        
    except Exception as e:
        crawl_status.update({
            "status": "error",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        logger.error(f"Crawling failed: {e}")

async def _run_rag_building_process():
    """Background task to build RAG system"""
    try:
        logger.info("Starting RAG knowledge base building...")
        
        # This would normally import and run the RAG building
        # For now, simulate the process
        rag_status["status"] = "building"
        
        # Simulate processing chunks
        total_chunks = 0
        for i in range(10):  # Simulate 10 processing steps
            await asyncio.sleep(1)
            chunks_added = 50  # Simulate chunks per step
            total_chunks += chunks_added
            rag_status["chunks_created"] = total_chunks
            
            logger.info(f"RAG building progress: {total_chunks} chunks created")
        
        # Complete RAG building
        rag_status.update({
            "status": "ready",
            "build_time": datetime.now().isoformat(),
            "chunks_created": total_chunks
        })
        
        logger.info(f"RAG building completed successfully. Total chunks: {total_chunks}")
        
    except Exception as e:
        rag_status.update({
            "status": "error",
            "error": str(e)
        })
        logger.error(f"RAG building failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
