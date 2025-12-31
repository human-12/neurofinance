# NeuroFinance - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Platform
```bash
./start.sh
```
This will start all services using Docker Compose.

### Step 2: Access the Dashboard
Open your browser and navigate to:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Step 3: Test the System
```bash
python test_system.py
```

---

## 📡 WebSocket Connection Example

```javascript
// Connect to real-time sentiment feed
const ws = new WebSocket('ws://localhost:8000/ws/sentiment');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New sentiment update:', data);
};

// Subscribe to specific symbols
ws.send(JSON.stringify({
  type: 'subscribe',
  symbols: ['AAPL', 'GOOGL', 'TSLA']
}));
```

---

## 🔧 Common Commands

### Docker Management
```bash
# Start services
cd infrastructure && docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 API Endpoints

### GET /api/sentiment/analyze
Analyze sentiment of text
```bash
curl "http://localhost:8000/api/sentiment/analyze?text=Apple%20stock%20surges&source=test"
```

### GET /api/news/latest
Get latest financial news
```bash
curl "http://localhost:8000/api/news/latest?limit=10"
```

### GET /api/signals/current
Get current market signals
```bash
curl "http://localhost:8000/api/signals/current"
```

### GET /api/stats
Get platform statistics
```bash
curl "http://localhost:8000/api/stats"
```

---

## 🎯 Performance Targets

- **Latency**: <50ms per article
- **Throughput**: 100+ articles/second
- **Concurrent Users**: 1000+ WebSocket connections
- **Processing Volume**: 10M+ articles/day

---

## 🐛 Troubleshooting

### Backend not starting?
1. Check if port 8000 is available
2. Ensure Docker has enough memory (8GB+ recommended)
3. Check logs: `docker-compose logs backend`

### Frontend not connecting?
1. Verify backend is running: `curl http://localhost:8000/`
2. Check WebSocket URL in frontend config
3. Clear browser cache and reload

### Model loading slowly?
First run downloads FinBERT model (~500MB). Subsequent runs use cached model.

---

## 📚 Additional Resources

- [Full Documentation](README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Diagram](README.md#-system-architecture)
- [Contributing Guide](README.md#-contributing)

---

## 💡 Tips

1. **Performance**: Use GPU for 5-10x faster inference
2. **Production**: Add authentication and rate limiting
3. **Scaling**: Use Redis for distributed caching
4. **Monitoring**: Add Prometheus/Grafana for metrics

---

**Happy Trading! 📈**
