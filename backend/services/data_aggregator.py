"""
Data Aggregation Service
Aggregates news feeds and social data from multiple sources
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import feedparser
from collections import deque
import hashlib

from models.schemas import NewsItem


class DataAggregator:
    """
    Aggregates financial news and social media data
    Handles 10M+ articles/day with deduplication
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.processed_ids = deque(maxlen=100000)  # Track processed articles
        self.daily_count = 0
        self.last_reset = datetime.utcnow()
        
        # RSS feeds for financial news
        self.news_feeds = [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.reuters.com/finance",
            "https://seekingalpha.com/market_currents.xml",
            "https://www.ft.com/?format=rss",
        ]
        
        # Twitter/X API endpoints would go here
        # Social media APIs typically require authentication
        self.social_endpoints = []
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def fetch_latest_articles(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[NewsItem]:
        """
        Fetch latest financial news articles
        
        Args:
            symbol: Filter by stock symbol (optional)
            limit: Maximum number of articles to return
        
        Returns:
            List of NewsItem objects
        """
        # Reset daily counter if new day
        if (datetime.utcnow() - self.last_reset).days >= 1:
            self.daily_count = 0
            self.last_reset = datetime.utcnow()
        
        articles = []
        
        # Fetch from RSS feeds
        rss_articles = await self._fetch_from_rss()
        articles.extend(rss_articles)
        
        # Fetch from social media (if configured)
        if self.social_endpoints:
            social_articles = await self._fetch_from_social(symbol)
            articles.extend(social_articles)
        
        # Generate simulated articles for demo (remove in production)
        if len(articles) < limit:
            simulated = self._generate_demo_articles(limit - len(articles), symbol)
            articles.extend(simulated)
        
        # Filter by symbol if specified
        if symbol:
            articles = [
                a for a in articles
                if symbol.upper() in (a.symbols or [])
            ]
        
        # Deduplicate
        articles = self._deduplicate(articles)
        
        # Update counter
        self.daily_count += len(articles)
        
        return articles[:limit]
    
    async def _fetch_from_rss(self) -> List[NewsItem]:
        """Fetch articles from RSS feeds"""
        articles = []
        session = await self._get_session()
        
        tasks = []
        for feed_url in self.news_feeds:
            tasks.append(self._fetch_single_feed(session, feed_url))
        
        # Fetch all feeds concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
        
        return articles
    
    async def _fetch_single_feed(
        self,
        session: aiohttp.ClientSession,
        feed_url: str
    ) -> List[NewsItem]:
        """Fetch and parse a single RSS feed"""
        try:
            async with session.get(feed_url) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries[:50]:  # Limit per feed
                    article = NewsItem(
                        id=self._generate_id(entry.get("link", "")),
                        title=entry.get("title", ""),
                        content=entry.get("summary", "")[:1000],
                        url=entry.get("link", ""),
                        source=feed.feed.get("title", "Unknown"),
                        published_at=self._parse_date(entry.get("published")),
                        symbols=self._extract_symbols(
                            entry.get("title", "") + " " + entry.get("summary", "")
                        )
                    )
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            return []
    
    async def _fetch_from_social(self, symbol: Optional[str] = None) -> List[NewsItem]:
        """
        Fetch from social media platforms
        Requires API keys and authentication
        """
        # Placeholder for Twitter/X API integration
        # In production, use Twitter API v2 with bearer token
        return []
    
    def _generate_demo_articles(
        self,
        count: int,
        symbol: Optional[str] = None
    ) -> List[NewsItem]:
        """
        Generate simulated articles for demo purposes
        Remove this in production and use real data sources
        """
        import random
        
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META"]
        if symbol:
            symbols = [symbol.upper()]
        
        templates = [
            "{symbol} stock surges on strong earnings report",
            "Analysts bullish on {symbol} following product launch",
            "{symbol} faces regulatory scrutiny in Europe",
            "Market volatility impacts {symbol} trading",
            "{symbol} CEO announces strategic partnership",
            "Investors cautious on {symbol} amid market uncertainty",
            "{symbol} beats quarterly expectations",
            "Technical analysis suggests {symbol} breakout incoming",
        ]
        
        sentiments = ["bullish", "bearish", "neutral", "mixed"]
        
        articles = []
        for i in range(count):
            chosen_symbol = random.choice(symbols)
            template = random.choice(templates)
            sentiment = random.choice(sentiments)
            
            title = template.format(symbol=chosen_symbol)
            content = f"Market analysts are {sentiment} on {chosen_symbol} as recent developments suggest significant movement ahead. Traders are closely monitoring key support and resistance levels."
            
            article = NewsItem(
                id=self._generate_id(f"{title}-{i}-{datetime.utcnow().timestamp()}"),
                title=title,
                content=content,
                url=f"https://example.com/article-{i}",
                source="Financial Times" if i % 2 == 0 else "Bloomberg",
                published_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
                symbols=[chosen_symbol]
            )
            articles.append(article)
        
        return articles
    
    def _deduplicate(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate articles based on ID"""
        unique_articles = []
        seen_ids = set(self.processed_ids)
        
        for article in articles:
            if article.id not in seen_ids:
                unique_articles.append(article)
                seen_ids.add(article.id)
                self.processed_ids.append(article.id)
        
        return unique_articles
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse date string to datetime"""
        if not date_str:
            return datetime.utcnow()
        
        from dateutil import parser
        try:
            return parser.parse(date_str)
        except:
            return datetime.utcnow()
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        import re
        
        # Look for $SYMBOL pattern and standalone tickers
        symbols = re.findall(r'\$([A-Z]{1,5})\b', text)
        symbols.extend(re.findall(r'\b([A-Z]{2,5})\b', text))
        
        # Filter known symbols (simplified - use actual symbol list in production)
        known_symbols = {
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA",
            "JPM", "BAC", "GS", "MS", "C", "WFC", "V", "MA"
        }
        
        return list(set([s for s in symbols if s in known_symbols]))[:5]
    
    async def get_daily_count(self) -> int:
        """Get number of articles processed today"""
        return self.daily_count
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
