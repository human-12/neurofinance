"""
NeuroFinance - Real-time Financial Sentiment Analysis Platform
FastAPI Backend with WebSocket Support
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
from typing import List, Dict
import json
import logging

from services.sentiment_analyzer import SentimentAnalyzer
from services.data_aggregator import DataAggregator
from services.volatility_predictor import VolatilityPredictor
from models.schemas import (
    SentimentAnalysis,
    MarketSignal,
    VolatilityPrediction,
    NewsItem
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


# Initialize services
sentiment_analyzer = SentimentAnalyzer()
data_aggregator = DataAggregator()
volatility_predictor = VolatilityPredictor()
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Initializing NeuroFinance Platform...")
    await sentiment_analyzer.initialize()
    
    # Start background tasks
    asyncio.create_task(stream_sentiment_updates())
    
    logger.info("NeuroFinance Platform Ready ✓")
    yield
    
    # Shutdown
    logger.info("Shutting down NeuroFinance Platform...")


app = FastAPI(
    title="NeuroFinance API",
    description="Real-time Financial Sentiment Analysis Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_sentiment_updates():
    """Background task to continuously analyze and broadcast sentiment data"""
    while True:
        try:
            # Aggregate latest news and social data
            articles = await data_aggregator.fetch_latest_articles()
            
            # Process in batches for efficiency
            batch_size = 100
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                
                # Analyze sentiment
                results = await sentiment_analyzer.analyze_batch(batch)
                
                # Calculate market signals
                signals = await volatility_predictor.generate_signals(results)
                
                # Broadcast to all connected clients
                await manager.broadcast({
                    "type": "sentiment_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "results": [r.dict() for r in results],
                    "signals": [s.dict() for s in signals]
                })
            
            # Throttle to prevent overwhelming clients
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in sentiment stream: {e}")
            await asyncio.sleep(5)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "NeuroFinance",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/sentiment/analyze", response_model=List[SentimentAnalysis])
async def analyze_sentiment(text: str, source: str = "manual"):
    """
    Analyze sentiment of provided text
    
    - **text**: Text to analyze
    - **source**: Source identifier (e.g., 'twitter', 'news', 'manual')
    """
    try:
        result = await sentiment_analyzer.analyze_text(text, source)
        return [result]
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/latest", response_model=List[NewsItem])
async def get_latest_news(symbol: str = None, limit: int = 50):
    """
    Retrieve latest financial news articles
    
    - **symbol**: Filter by stock symbol (optional)
    - **limit**: Maximum number of articles to return
    """
    try:
        articles = await data_aggregator.fetch_latest_articles(
            symbol=symbol,
            limit=limit
        )
        return articles
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/current", response_model=List[MarketSignal])
async def get_current_signals(symbol: str = None):
    """
    Get current market signals based on sentiment analysis
    
    - **symbol**: Filter by stock symbol (optional)
    """
    try:
        signals = await volatility_predictor.get_current_signals(symbol=symbol)
        return signals
    except Exception as e:
        logger.error(f"Signal generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/volatility/predict", response_model=VolatilityPrediction)
async def predict_volatility(symbol: str):
    """
    Predict market volatility for a specific symbol
    
    - **symbol**: Stock symbol (e.g., 'AAPL', 'TSLA')
    """
    try:
        prediction = await volatility_predictor.predict(symbol)
        return prediction
    except Exception as e:
        logger.error(f"Volatility prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_platform_stats():
    """Get platform statistics"""
    return {
        "articles_processed_today": await data_aggregator.get_daily_count(),
        "active_connections": len(manager.active_connections),
        "average_latency_ms": sentiment_analyzer.get_avg_latency(),
        "models_loaded": sentiment_analyzer.is_ready(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.websocket("/ws/sentiment")
async def websocket_sentiment(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sentiment updates
    
    Clients receive continuous stream of:
    - Sentiment analysis results
    - Market signals
    - Volatility predictions
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to NeuroFinance real-time feed"
        })
        
        # Keep connection alive
        while True:
            # Wait for client messages (heartbeat, subscriptions, etc.)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client commands
            if message.get("type") == "subscribe":
                symbols = message.get("symbols", [])
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "symbols": symbols,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
