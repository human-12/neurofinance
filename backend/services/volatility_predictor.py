"""
Volatility Prediction Service
Generates market signals from sentiment analysis
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np

from models.schemas import (
    SentimentAnalysis,
    MarketSignal,
    VolatilityPrediction
)


class VolatilityPredictor:
    """
    Predicts market volatility based on sentiment analysis
    Generates actionable trading signals
    """
    
    def __init__(self):
        # Store recent sentiment history for each symbol
        self.sentiment_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        
        # Current signals cache
        self.current_signals: List[MarketSignal] = []
    
    async def generate_signals(
        self,
        sentiment_results: List[SentimentAnalysis]
    ) -> List[MarketSignal]:
        """
        Generate market signals from sentiment analysis results
        
        Args:
            sentiment_results: List of sentiment analysis results
        
        Returns:
            List of MarketSignal objects
        """
        signals = []
        
        # Group by symbol/entity
        symbol_sentiments = defaultdict(list)
        
        for result in sentiment_results:
            for entity in result.entities:
                symbol_sentiments[entity].append(result)
                
                # Update history
                self.sentiment_history[entity].append({
                    "sentiment": result.sentiment,
                    "confidence": result.confidence,
                    "scores": result.scores,
                    "timestamp": result.timestamp
                })
        
        # Generate signals for each symbol
        for symbol, sentiments in symbol_sentiments.items():
            signal = self._calculate_signal(symbol, sentiments)
            if signal:
                signals.append(signal)
        
        # Cache signals
        self.current_signals = signals
        
        return signals
    
    def _calculate_signal(
        self,
        symbol: str,
        recent_sentiments: List[SentimentAnalysis]
    ) -> Optional[MarketSignal]:
        """
        Calculate trading signal for a symbol
        
        Signal logic:
        - Strong positive sentiment shift → BUY
        - Strong negative sentiment shift → SELL
        - Mixed or stable sentiment → HOLD
        """
        if not recent_sentiments:
            return None
        
        # Calculate aggregate sentiment score
        positive_scores = []
        negative_scores = []
        confidences = []
        
        for sentiment in recent_sentiments:
            positive_scores.append(sentiment.scores.get("positive", 0))
            negative_scores.append(sentiment.scores.get("negative", 0))
            confidences.append(sentiment.confidence)
        
        avg_positive = np.mean(positive_scores)
        avg_negative = np.mean(negative_scores)
        avg_confidence = np.mean(confidences)
        
        # Calculate sentiment momentum (if we have history)
        momentum = self._calculate_momentum(symbol)
        
        # Generate signal
        signal_type = "HOLD"
        strength = 0.5
        
        net_sentiment = avg_positive - avg_negative
        
        if net_sentiment > 0.3 and momentum > 0:
            signal_type = "BUY"
            strength = min(0.95, avg_positive * avg_confidence)
        elif net_sentiment < -0.3 and momentum < 0:
            signal_type = "SELL"
            strength = min(0.95, avg_negative * avg_confidence)
        else:
            signal_type = "HOLD"
            strength = 0.5
        
        # Calculate predicted volatility
        volatility = self._estimate_volatility(symbol)
        
        return MarketSignal(
            symbol=symbol,
            signal=signal_type,
            strength=strength,
            sentiment_score=net_sentiment,
            volume=len(recent_sentiments),
            volatility_prediction=volatility,
            confidence=avg_confidence,
            timestamp=datetime.utcnow(),
            reasoning=self._generate_reasoning(
                signal_type, net_sentiment, momentum, volatility
            )
        )
    
    def _calculate_momentum(self, symbol: str) -> float:
        """
        Calculate sentiment momentum (trend direction)
        
        Returns:
            Positive value = bullish momentum
            Negative value = bearish momentum
        """
        history = self.sentiment_history.get(symbol, [])
        
        if len(history) < 10:
            return 0.0
        
        # Take last 20 data points
        recent = list(history)[-20:]
        
        # Calculate average sentiment over time windows
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        def avg_sentiment(items):
            scores = [
                item["scores"].get("positive", 0) - item["scores"].get("negative", 0)
                for item in items
            ]
            return np.mean(scores) if scores else 0.0
        
        momentum = avg_sentiment(second_half) - avg_sentiment(first_half)
        
        return np.clip(momentum, -1.0, 1.0)
    
    def _estimate_volatility(self, symbol: str) -> float:
        """
        Estimate predicted volatility based on sentiment variance
        
        Returns:
            Volatility score (0-1, higher = more volatile)
        """
        history = self.sentiment_history.get(symbol, [])
        
        if len(history) < 5:
            return 0.5  # Default moderate volatility
        
        # Calculate sentiment variance
        recent = list(history)[-30:]
        sentiments = [
            item["scores"].get("positive", 0) - item["scores"].get("negative", 0)
            for item in recent
        ]
        
        variance = np.var(sentiments)
        
        # Normalize to 0-1 range
        volatility = min(1.0, variance * 10)
        
        return volatility
    
    def _generate_reasoning(
        self,
        signal: str,
        sentiment: float,
        momentum: float,
        volatility: float
    ) -> str:
        """Generate human-readable reasoning for the signal"""
        
        if signal == "BUY":
            return f"Strong positive sentiment ({sentiment:.2f}) with bullish momentum ({momentum:.2f}). Predicted volatility: {volatility:.2f}"
        elif signal == "SELL":
            return f"Strong negative sentiment ({sentiment:.2f}) with bearish momentum ({momentum:.2f}). Predicted volatility: {volatility:.2f}"
        else:
            return f"Mixed sentiment ({sentiment:.2f}) with low conviction. Recommend holding position. Volatility: {volatility:.2f}"
    
    async def predict(self, symbol: str) -> VolatilityPrediction:
        """
        Predict market volatility for a specific symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            VolatilityPrediction object
        """
        history = self.sentiment_history.get(symbol, [])
        
        if len(history) < 5:
            # Insufficient data
            return VolatilityPrediction(
                symbol=symbol,
                predicted_volatility=0.5,
                confidence=0.3,
                time_horizon="1h",
                factors={
                    "sentiment_variance": 0.0,
                    "volume": 0,
                    "momentum": 0.0
                },
                timestamp=datetime.utcnow()
            )
        
        # Calculate volatility metrics
        recent = list(history)[-50:]
        
        sentiments = [
            item["scores"].get("positive", 0) - item["scores"].get("negative", 0)
            for item in recent
        ]
        
        variance = np.var(sentiments)
        momentum = self._calculate_momentum(symbol)
        volume = len(recent)
        
        # Predicted volatility (normalized)
        predicted_volatility = min(1.0, variance * 10)
        
        # Confidence based on data volume
        confidence = min(0.95, volume / 50.0)
        
        return VolatilityPrediction(
            symbol=symbol,
            predicted_volatility=predicted_volatility,
            confidence=confidence,
            time_horizon="1h",
            factors={
                "sentiment_variance": float(variance),
                "volume": volume,
                "momentum": float(momentum)
            },
            timestamp=datetime.utcnow()
        )
    
    async def get_current_signals(
        self,
        symbol: Optional[str] = None
    ) -> List[MarketSignal]:
        """
        Get current market signals
        
        Args:
            symbol: Filter by symbol (optional)
        
        Returns:
            List of current MarketSignal objects
        """
        if symbol:
            return [
                signal for signal in self.current_signals
                if signal.symbol == symbol.upper()
            ]
        
        return self.current_signals
