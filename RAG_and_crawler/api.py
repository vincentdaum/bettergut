"""
FastAPI service for AI pipeline - Health data crawling, RAG, and LLM services
"""
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our modules (when dependencies are installed)
try:
    from crawlers.health_crawler import HealthDataCrawler
    from rag.rag_system import HealthRAGSystem, build_knowledge_base
    from models.llama3_service import Llama3HealthAssistant
except ImportError as e:
    logging.warning(f"Could not import AI modules: {e}")
    HealthDataCrawler = None
    HealthRAGSystem = None
    Llama3HealthAssistant = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="BetterGut AI Pipeline",
    description="AI-powered gut health insights using RAG and Llama 3",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for services
rag_system: Optional[HealthRAGSystem] = None
health_assistant: Optional[Llama3HealthAssistant] = None
crawler: Optional[HealthDataCrawler] = None

# Pydantic models
class CrawlRequest(BaseModel):
    topics: List[str] = ["gut health", "microbiome", "nutrition", "digestive health"]
    max_articles_per_source: int = 50

class UserHealthData(BaseModel):
    user_id: str
    goals: List[str] = []
    dietary_restrictions: List[str] = []
    activity_level: str = "moderate"
    current_nutrition: Dict[str, float] = {}
    symptoms: List[str] = []
    nutrition_history: List[Dict] = []

class HealthQuery(BaseModel):
    user_data: UserHealthData
    question: Optional[str] = None

class MealSuggestionRequest(BaseModel):
    user_profile: Dict[str, Any]
    nutrition_goals: Dict[str, float]
    current_intake: Dict[str, float]

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize AI services on startup"""
    global rag_system, health_assistant, crawler
    
    logger.info("🚀 Starting BetterGut AI Pipeline...")
    
    try:
        # Initialize RAG system
        if HealthRAGSystem:
            logger.info("Initializing RAG system...")
            rag_system = HealthRAGSystem()
            
            # Initialize health assistant with RAG
            if Llama3HealthAssistant:
                logger.info("Initializing Llama 3 health assistant...")
                health_assistant = Llama3HealthAssistant(rag_system=rag_system)
        
        # Initialize crawler
        if HealthDataCrawler:
            logger.info("Initializing health data crawler...")
            crawler = HealthDataCrawler()
        
        logger.info("✅ AI Pipeline initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services_status = {
        "rag_system": rag_system is not None,
        "health_assistant": health_assistant is not None,
        "crawler": crawler is not None,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "status": "healthy",
        "services": services_status,
        "version": "1.0.0"
    }

# Data crawling endpoints
@app.post("/crawl/start")
async def start_crawling(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start health data crawling in the background"""
    if not crawler:
        raise HTTPException(status_code=503, detail="Crawler not available")
    
    # Start crawling in background
    background_tasks.add_task(
        run_crawling_task, 
        request.topics, 
        request.max_articles_per_source
    )
    
    return {
        "message": "Crawling started",
        "topics": request.topics,
        "max_articles_per_source": request.max_articles_per_source,
        "status": "running"
    }

async def run_crawling_task(topics: List[str], max_articles: int):
    """Background task for data crawling"""
    try:
        logger.info(f"Starting crawl for topics: {topics}")
        
        async with crawler:
            results = await crawler.crawl_all_sources(topics, max_articles)
            
        logger.info(f"Crawling completed. Results: {len(results)} sources")
        
        # Rebuild knowledge base with new data
        if rag_system:
            await rebuild_knowledge_base()
            
    except Exception as e:
        logger.error(f"Crawling task failed: {e}")

@app.get("/crawl/status")
async def get_crawl_status():
    """Get crawling statistics"""
    if not crawler:
        raise HTTPException(status_code=503, detail="Crawler not available")
    
    stats = crawler.get_crawl_statistics()
    return stats

# RAG system endpoints
@app.post("/rag/rebuild")
async def rebuild_knowledge_base():
    """Rebuild the RAG knowledge base from crawled data"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        # Load and add documents to RAG system
        from rag.rag_system import load_crawled_documents
        documents = load_crawled_documents("./data/crawled")
        
        if documents:
            # Clear existing collection and rebuild
            rag_system.clear_collection()
            rag_system.add_documents(documents)
            
            stats = rag_system.get_collection_stats()
            return {
                "message": "Knowledge base rebuilt successfully",
                "stats": stats
            }
        else:
            raise HTTPException(status_code=404, detail="No crawled documents found")
            
    except Exception as e:
        logger.error(f"Error rebuilding knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search")
async def search_knowledge_base(query: str, n_results: int = 5):
    """Search the RAG knowledge base"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        results = rag_system.search(query, n_results)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    stats = rag_system.get_collection_stats()
    return stats

# LLM health insights endpoints
@app.post("/insights/generate")
async def generate_health_insights(request: HealthQuery):
    """Generate personalized gut health insights"""
    if not health_assistant:
        raise HTTPException(status_code=503, detail="Health assistant not available")
    
    try:
        user_data = request.user_data.dict()
        insights = await health_assistant.generate_gut_health_insights(
            user_data, request.question
        )
        
        return {
            "insights": insights,
            "generated_at": datetime.now().isoformat(),
            "user_id": user_data.get("user_id")
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights/meal-suggestions")
async def generate_meal_suggestions(request: MealSuggestionRequest):
    """Generate personalized meal suggestions"""
    if not health_assistant:
        raise HTTPException(status_code=503, detail="Health assistant not available")
    
    try:
        suggestions = await health_assistant.generate_meal_suggestions(
            request.user_profile,
            request.nutrition_goals,
            request.current_intake
        )
        
        return {
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating meal suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights/food-analysis")
async def analyze_food_photo(
    food_analysis: Dict[str, Any],
    user_context: Dict[str, Any]
):
    """Analyze food photo for gut health impact"""
    if not health_assistant:
        raise HTTPException(status_code=503, detail="Health assistant not available")
    
    try:
        analysis = await health_assistant.analyze_food_photo(
            food_analysis, user_context
        )
        
        return {
            "analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing food photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.post("/admin/reset")
async def reset_system():
    """Reset the entire AI pipeline (admin only)"""
    global rag_system, health_assistant
    
    try:
        if rag_system:
            rag_system.clear_collection()
        
        return {"message": "System reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries (admin only)"""
    try:
        log_file = "./logs/ai_pipeline.log"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
                return {"logs": recent_logs, "total_lines": len(log_lines)}
        else:
            return {"logs": [], "message": "Log file not found"}
            
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility endpoints
@app.get("/info")
async def get_system_info():
    """Get system information and capabilities"""
    return {
        "name": "BetterGut AI Pipeline",
        "version": "1.0.0",
        "capabilities": [
            "Health data crawling from scientific sources",
            "RAG-based knowledge retrieval",
            "Llama 3 powered health insights",
            "Personalized nutrition recommendations",
            "Food photo analysis"
        ],
        "data_sources": [
            "PubMed Central",
            "NIH Health Information", 
            "CDC Nutrition Guidelines",
            "Harvard Nutrition Source",
            "Specialist gut health sites"
        ],
        "models": {
            "llm": "Llama 3 8B",
            "embeddings": "all-MiniLM-L6-v2",
            "vector_db": "ChromaDB"
        }
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
