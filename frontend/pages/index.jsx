import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, TrendingDown, AlertCircle, Zap, Radio } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '../lib/useWebSocket';

export default function Dashboard() {
  const [sentimentData, setSentimentData] = useState([]);
  const [signals, setSignals] = useState([]);
  const [stats, setStats] = useState({
    articlesProcessed: 0,
    activeConnections: 0,
    averageLatency: 0
  });

  const { connected, messages } = useWebSocket('ws://localhost:8000/ws/sentiment');

  useEffect(() => {
    // Fetch initial stats
    fetch('http://localhost:8000/api/stats')
      .then(res => res.json())
      .then(data => {
        setStats({
          articlesProcessed: data.articles_processed_today,
          activeConnections: data.active_connections,
          averageLatency: data.average_latency_ms
        });
      });

    // Fetch initial signals
    fetch('http://localhost:8000/api/signals/current')
      .then(res => res.json())
      .then(data => setSignals(data));
  }, []);

  useEffect(() => {
    // Handle WebSocket messages
    if (messages.length > 0) {
      const latest = messages[messages.length - 1];
      
      if (latest.type === 'sentiment_update') {
        setSentimentData(prev => [...prev, ...latest.results].slice(-100));
        setSignals(latest.signals || []);
      }
    }
  }, [messages]);

  const getSentimentColor = (sentiment) => {
    if (sentiment === 'positive') return 'text-emerald-400';
    if (sentiment === 'negative') return 'text-rose-400';
    return 'text-amber-400';
  };

  const getSignalColor = (signal) => {
    if (signal === 'BUY') return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
    if (signal === 'SELL') return 'bg-rose-500/20 text-rose-400 border-rose-500/50';
    return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800/50 bg-black/40 backdrop-blur-xl">
        <div className="max-w-[1800px] mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-light tracking-tight mb-2">
                <span className="font-extralight text-gray-500">Neuro</span>
                <span className="font-normal bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Finance</span>
              </h1>
              <p className="text-sm text-gray-500 font-light tracking-wide">
                Real-time Financial Sentiment Intelligence
              </p>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-900/50 border border-gray-800">
                <Radio className={`w-4 h-4 ${connected ? 'text-emerald-400 animate-pulse' : 'text-gray-600'}`} />
                <span className="text-xs font-mono text-gray-400">
                  {connected ? 'LIVE' : 'DISCONNECTED'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="max-w-[1800px] mx-auto px-8 py-8">
        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={<Activity className="w-5 h-5" />}
            label="Articles Processed"
            value={stats.articlesProcessed.toLocaleString()}
            suffix="today"
            color="cyan"
          />
          <StatCard
            icon={<Zap className="w-5 h-5" />}
            label="Average Latency"
            value={stats.averageLatency.toFixed(1)}
            suffix="ms"
            color="blue"
          />
          <StatCard
            icon={<Radio className="w-5 h-5" />}
            label="Active Connections"
            value={stats.activeConnections}
            suffix="clients"
            color="emerald"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Market Signals - Left Column */}
          <div className="col-span-4 space-y-6">
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-800/50 p-6 shadow-2xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h2 className="text-lg font-medium">Market Signals</h2>
                  <p className="text-xs text-gray-500 font-mono">{signals.length} active</p>
                </div>
              </div>

              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                {signals.length === 0 ? (
                  <div className="text-center py-12 text-gray-600">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Waiting for signals...</p>
                  </div>
                ) : (
                  signals.map((signal, idx) => (
                    <SignalCard key={idx} signal={signal} delay={idx * 50} />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Sentiment Stream - Right Column */}
          <div className="col-span-8 space-y-6">
            {/* Sentiment Chart */}
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-800/50 p-6 shadow-2xl">
              <h2 className="text-lg font-medium mb-6">Sentiment Trends</h2>
              
              {sentimentData.length > 10 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={sentimentData.slice(-50)}>
                    <defs>
                      <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" opacity={0.3} />
                    <XAxis 
                      dataKey="timestamp" 
                      stroke="#4b5563"
                      tick={{ fill: '#6b7280', fontSize: 11 }}
                      tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                    />
                    <YAxis 
                      stroke="#4b5563"
                      tick={{ fill: '#6b7280', fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#111827',
                        border: '1px solid #1f2937',
                        borderRadius: '8px',
                        fontSize: '12px'
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="confidence"
                      stroke="#06b6d4"
                      strokeWidth={2}
                      fill="url(#sentimentGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-600">
                  <div className="text-center">
                    <Activity className="w-12 h-12 mx-auto mb-3 opacity-50 animate-pulse" />
                    <p className="text-sm">Building sentiment timeline...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Live Sentiment Feed */}
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-800/50 p-6 shadow-2xl">
              <h2 className="text-lg font-medium mb-6">Live Sentiment Stream</h2>
              
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {sentimentData.slice(-20).reverse().map((item, idx) => (
                  <SentimentCard key={idx} item={item} delay={idx * 30} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1f2937;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #374151;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #4b5563;
        }
      `}</style>
    </div>
  );
}

function StatCard({ icon, label, value, suffix, color }) {
  const colorClasses = {
    cyan: 'from-cyan-500/10 to-cyan-500/5 border-cyan-500/20',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/20',
    emerald: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/20'
  };

  return (
    <div 
      className={`bg-gradient-to-br ${colorClasses[color]} backdrop-blur-xl rounded-xl border p-6 shadow-lg
                  hover:scale-[1.02] transition-transform duration-300`}
      style={{ animation: 'fadeIn 0.5s ease-out' }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`text-${color}-400 opacity-80`}>{icon}</div>
      </div>
      <div className="space-y-1">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-light tracking-tight">{value}</span>
          <span className="text-sm text-gray-500 font-mono">{suffix}</span>
        </div>
        <p className="text-xs text-gray-500 tracking-wide">{label}</p>
      </div>
    </div>
  );
}

function SignalCard({ signal, delay }) {
  const Icon = signal.signal === 'BUY' ? TrendingUp : signal.signal === 'SELL' ? TrendingDown : Activity;
  
  return (
    <div 
      className={`p-4 rounded-xl border ${getSignalColor(signal.signal)} backdrop-blur-sm
                  hover:scale-[1.02] transition-all duration-300`}
      style={{ 
        animation: `slideInLeft 0.4s ease-out ${delay}ms backwards`
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5" />
          <div>
            <div className="font-mono text-sm font-medium">{signal.symbol}</div>
            <div className="text-xs opacity-70">{signal.signal}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-mono font-light">
            {(signal.strength * 100).toFixed(0)}%
          </div>
          <div className="text-xs opacity-70">strength</div>
        </div>
      </div>
      
      <div className="pt-3 border-t border-white/10">
        <div className="text-xs opacity-70 leading-relaxed">
          {signal.reasoning}
        </div>
      </div>
    </div>
  );
}

function SentimentCard({ item, delay }) {
  return (
    <div 
      className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/50 hover:bg-gray-800/50 
                 transition-all duration-300"
      style={{ 
        animation: `fadeIn 0.4s ease-out ${delay}ms backwards`
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            item.sentiment === 'positive' ? 'bg-emerald-400' :
            item.sentiment === 'negative' ? 'bg-rose-400' : 'bg-amber-400'
          } animate-pulse`} />
          <span className={`text-xs font-mono font-medium uppercase ${getSentimentColor(item.sentiment)}`}>
            {item.sentiment}
          </span>
        </div>
        <span className="text-xs text-gray-500 font-mono">
          {(item.confidence * 100).toFixed(0)}%
        </span>
      </div>
      
      <p className="text-sm text-gray-300 leading-relaxed line-clamp-2 mb-2">
        {item.text}
      </p>
      
      {item.entities && item.entities.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {item.entities.slice(0, 3).map((entity, idx) => (
            <span 
              key={idx}
              className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono"
            >
              {entity}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function getSentimentColor(sentiment) {
  if (sentiment === 'positive') return 'text-emerald-400';
  if (sentiment === 'negative') return 'text-rose-400';
  return 'text-amber-400';
}

function getSignalColor(signal) {
  if (signal === 'BUY') return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  if (signal === 'SELL') return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
}
