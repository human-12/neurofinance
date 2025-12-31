"""
BERT-based Sentiment Analysis Service
Optimized for financial text with <50ms latency
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import asyncio
from typing import List, Dict
from datetime import datetime
import time
import numpy as np
from collections import deque

from models.schemas import SentimentAnalysis


class SentimentAnalyzer:
    """
    Financial sentiment analyzer using fine-tuned BERT
    Optimized for high-throughput, low-latency inference
    """
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Performance tracking
        self.latency_history = deque(maxlen=1000)
        
        # Sentiment labels for financial domain
        self.label_map = {
            0: "negative",
            1: "neutral",
            2: "positive"
        }
    
    async def initialize(self):
        """Load model and tokenizer"""
        print(f"Loading FinBERT model on {self.device}...")
        
        # Load in separate thread to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, self._load_model
        )
        
        print("FinBERT model loaded successfully ✓")
    
    def _load_model(self):
        """Synchronous model loading"""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name
        )
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode
        
        # Optimize for inference
        if self.device.type == "cuda":
            self.model = torch.jit.script(self.model)
    
    async def analyze_text(
        self,
        text: str,
        source: str = "unknown",
        metadata: Dict = None
    ) -> SentimentAnalysis:
        """
        Analyze sentiment of a single text
        
        Args:
            text: Input text to analyze
            source: Source identifier (e.g., 'twitter', 'news')
            metadata: Additional metadata to attach
        
        Returns:
            SentimentAnalysis object with scores and labels
        """
        start_time = time.time()
        
        # Run inference in executor to avoid blocking
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._analyze_sync, text
        )
        
        latency_ms = (time.time() - start_time) * 1000
        self.latency_history.append(latency_ms)
        
        return SentimentAnalysis(
            text=text[:500],  # Truncate for storage
            source=source,
            sentiment=result["label"],
            confidence=result["confidence"],
            scores=result["scores"],
            entities=self._extract_entities(text),
            timestamp=datetime.utcnow(),
            latency_ms=latency_ms,
            metadata=metadata or {}
        )
    
    def _analyze_sync(self, text: str) -> Dict:
        """Synchronous sentiment analysis"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
        
        # Get predictions
        scores = probs.cpu().numpy()[0]
        predicted_class = torch.argmax(probs, dim=1).item()
        confidence = float(scores[predicted_class])
        
        return {
            "label": self.label_map[predicted_class],
            "confidence": confidence,
            "scores": {
                "negative": float(scores[0]),
                "neutral": float(scores[1]),
                "positive": float(scores[2])
            }
        }
    
    async def analyze_batch(
        self,
        items: List[Dict],
        batch_size: int = 32
    ) -> List[SentimentAnalysis]:
        """
        Analyze multiple texts in batches for efficiency
        
        Args:
            items: List of dicts with 'text', 'source', 'metadata'
            batch_size: Batch size for inference
        
        Returns:
            List of SentimentAnalysis results
        """
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch
            batch_results = await asyncio.get_event_loop().run_in_executor(
                None, self._analyze_batch_sync, batch
            )
            
            # Convert to SentimentAnalysis objects
            for item, result in zip(batch, batch_results):
                results.append(SentimentAnalysis(
                    text=item.get("text", "")[:500],
                    source=item.get("source", "unknown"),
                    sentiment=result["label"],
                    confidence=result["confidence"],
                    scores=result["scores"],
                    entities=self._extract_entities(item.get("text", "")),
                    timestamp=datetime.utcnow(),
                    latency_ms=result["latency_ms"],
                    metadata=item.get("metadata", {})
                ))
        
        return results
    
    def _analyze_batch_sync(self, items: List[Dict]) -> List[Dict]:
        """Synchronous batch processing"""
        texts = [item.get("text", "") for item in items]
        start_time = time.time()
        
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Batch inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
        
        # Process results
        scores = probs.cpu().numpy()
        predicted_classes = torch.argmax(probs, dim=1).cpu().numpy()
        
        latency_ms = (time.time() - start_time) * 1000 / len(items)
        
        results = []
        for i in range(len(texts)):
            results.append({
                "label": self.label_map[predicted_classes[i]],
                "confidence": float(scores[i][predicted_classes[i]]),
                "scores": {
                    "negative": float(scores[i][0]),
                    "neutral": float(scores[i][1]),
                    "positive": float(scores[i][2])
                },
                "latency_ms": latency_ms
            })
        
        return results
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract financial entities (tickers, companies) from text
        Simplified version - use spaCy or custom NER in production
        """
        import re
        
        # Extract potential stock tickers (1-5 uppercase letters)
        tickers = re.findall(r'\b[A-Z]{1,5}\b', text)
        
        # Common financial entities
        companies = [
            "Apple", "Microsoft", "Google", "Amazon", "Tesla",
            "Meta", "Netflix", "NVIDIA", "Intel", "AMD"
        ]
        
        entities = []
        for company in companies:
            if company.lower() in text.lower():
                entities.append(company)
        
        # Add unique tickers
        entities.extend([t for t in tickers if len(t) <= 5 and t not in entities])
        
        return list(set(entities))[:10]  # Limit to 10 entities
    
    def get_avg_latency(self) -> float:
        """Get average latency in milliseconds"""
        if not self.latency_history:
            return 0.0
        return float(np.mean(self.latency_history))
    
    def is_ready(self) -> bool:
        """Check if model is loaded and ready"""
        return self.model is not None and self.tokenizer is not None
