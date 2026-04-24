import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import TopologyGraph, { generateDemoTopology } from './TopologyGraph';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import {
  Activity, Crosshair, ClipboardList, TrendingUp,
  Play, Loader2, Cpu, MemoryStick, AlertTriangle,
  Flame, Waves, RotateCcw, MapPin, Zap
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────
interface HealingEvent {
  id: string;
  timestamp: string;
  type: string;
  pod: string;
  namespace: string;
  anomaly_type?: string;
  anomaly_score?: number;
  policy_action?: string;
  recovery_time_ms?: number;
  result: string;
  anomaly_reason?: string;
  policy_reason?: string;
}

interface Scores {
  f1_score: number;
  mttd_seconds: number;
  mttr_seconds: number;
  recovery_rate: number;
  false_positive_rate: number;
  total_healing_actions: number;
  precision: number;
  recall: number;
  healing_by_type: Record<string, number>;
  healing_by_namespace: Record<string, number>;
}

interface PodNode {
  id: string;
  name: string;
  namespace: string;
  status: 'healthy' | 'warning' | 'critical' | 'healing' | 'dead';
  x: number;
  y: number;
  z: number;
  restarts: number;
  cpu: number;
  connections: string[];
}

// ─── API Layer ──────────────────────────────────────────────
const api = axios.create({ baseURL: 'http://localhost:5050' });

async function fetchScores(): Promise<Scores> {
  try {
    const res = await api.get('/api/scores');
    return res.data;
  } catch {
    return {
      f1_score: 0, mttd_seconds: 0, mttr_seconds: 0,
      recovery_rate: 0, false_positive_rate: 0,
      total_healing_actions: 0, precision: 0, recall: 0,
      healing_by_type: {}, healing_by_namespace: {},
    };
  }
}

async function fetchHealingLog(): Promise<HealingEvent[]> {
  try {
    const res = await axios.get('http://localhost:5000/api/healing-log', { params: { limit: 50 } });
    return Array.isArray(res.data) ? res.data : [];
  } catch {
    return [];
  }
}

async function simulateAttack(anomalyType: string, namespace: string, pod: string): Promise<HealingEvent> {
  const res = await axios.post('http://localhost:5000/api/simulate', {
    anomaly_type: anomalyType, namespace, pod,
  });
  return res.data;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── Attack Type Icons ──────────────────────────────────────
const ATTACK_ICONS: Record<string, React.ReactNode> = {
  high_cpu: <Cpu size={12} />,
  high_memory: <MemoryStick size={12} />,
  crash_loop: <AlertTriangle size={12} />,
  high_error_rate: <Flame size={12} />,
  traffic_spike: <Waves size={12} />,
};

// ─── Score Card Component ───────────────────────────────────
function ScoreCard({ scores }: { scores: Scores }) {
  return (
    <div className="card" style={{ flex: '0 0 auto' }}>
      <div className="card-header">
        <span className="header-label">
          <Activity size={14} />
          PERFORMANCE METRICS
        </span>
        <span className="badge live">LIVE</span>
      </div>
      <div className="card-body">
        <div className="scores-grid">
          <div className="score-item green">
            <div className="value">{(scores?.f1_score !== undefined ? scores.f1_score * 100 : 0).toFixed(1)}%</div>
            <div className="label">F1 Score</div>
          </div>
          <div className="score-item blue">
            <div className="value">{scores?.mttr_seconds?.toFixed(1) ?? '0.0'}s</div>
            <div className="label">MTTR</div>
          </div>
          <div className="score-item">
            <div className="value">{scores?.mttd_seconds?.toFixed(0) ?? '0'}s</div>
            <div className="label">MTTD</div>
          </div>
          <div className="score-item green">
            <div className="value">{(scores?.recovery_rate !== undefined ? scores.recovery_rate * 100 : 0).toFixed(1)}%</div>
            <div className="label">Recovery Rate</div>
          </div>
          <div className="score-item red">
            <div className="value">{(scores?.false_positive_rate !== undefined ? scores.false_positive_rate * 100 : 0).toFixed(1)}%</div>
            <div className="label">False Positive</div>
          </div>
          <div className="score-item yellow">
            <div className="value">{scores?.total_healing_actions ?? 0}</div>
            <div className="label">Total Heals</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Attack Launcher Component ──────────────────────────────
function AttackLauncher({ onAttack, isRunning }: {
  onAttack: (type: string, ns: string, pod: string) => void;
  isRunning: boolean;
}) {
  const [attackType, setAttackType] = useState('high_cpu');
  const [targetNs, setTargetNs] = useState('netflix');
  const [targetPod, setTargetPod] = useState('search-service');

  const podOptions: Record<string, string[]> = {
    netflix: ['api-gateway', 'user-service', 'content-service', 'streaming-service',
              'search-service', 'recommendation-service', 'payment-service', 'notification-service'],
    prime: ['primeos-monolith'],
  };

  return (
    <div className="card" style={{ flex: '0 0 auto' }}>
      <div className="card-header">
        <span className="header-label">
          <Crosshair size={14} />
          ATTACK LAUNCHER
        </span>
        <span className="badge chaos">CHAOS</span>
      </div>
      <div className="card-body">
        <div className="attack-controls">
          <select value={attackType} onChange={e => setAttackType(e.target.value)}>
            <option value="high_cpu">CPU Stress</option>
            <option value="high_memory">Memory Pressure</option>
            <option value="crash_loop">Crash Loop</option>
            <option value="high_error_rate">Error Spike</option>
            <option value="traffic_spike">Traffic Flood</option>
          </select>
          <select value={targetNs} onChange={e => {
            setTargetNs(e.target.value);
            setTargetPod(podOptions[e.target.value]?.[0] || '');
          }}>
            <option value="netflix">Netflix (Microservices)</option>
            <option value="prime">PrimeOS (Monolith)</option>
          </select>
          <select value={targetPod} onChange={e => setTargetPod(e.target.value)}>
            {(podOptions[targetNs] || []).map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <button
            className={`btn-attack ${isRunning ? 'active' : 'red'}`}
            onClick={() => onAttack(attackType, targetNs, targetPod)}
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <Loader2 size={14} className="spin" />
                HEALING IN PROGRESS
              </>
            ) : (
              <>
                <Play size={14} />
                LAUNCH ATTACK
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Healing Log Component ──────────────────────────────────
function HealingLog({ events }: { events: HealingEvent[] }) {
  return (
    <div className="card healing-log-card">
      <div className="card-header">
        <span className="header-label">
          <ClipboardList size={14} />
          HEALING AUDIT LOG
        </span>
        <span className="badge count">{events.length} EVENTS</span>
      </div>
      <div className="card-body">
        <div className="log-entries">
          {events.slice().reverse().map((event) => {
            const cls = event.type === 'healing_complete' && event.result === 'SUCCESS' ? 'success'
              : event.type === 'healing_complete' && event.result === 'FAILURE' ? 'failure'
              : event.type === 'safety_blocked' ? 'blocked'
              : event.type === 'false_positive_filtered' ? 'filtered'
              : 'simulation';

            return (
              <div key={event.id} className={`log-entry ${cls}`}>
                <span className="time">
                  {new Date(event.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                </span>
                <span className="action">{event.policy_action || event.type}</span>
                <span className="target" title={event.pod}>
                  {event.namespace}/{event.pod?.replace(/-[a-z0-9]{8,}-[a-z0-9]{5}$/, '')}
                </span>
                <span className="score" style={{
                  color: (event.anomaly_score ?? 0) < -0.3 ? '#ef4444' : '#4ade80'
                }}>
                  {event.anomaly_score !== undefined ? event.anomaly_score.toFixed(3) : '\u2014'}
                </span>
                <span className={`result ${cls}`}>
                  {event.recovery_time_ms ? `${(event.recovery_time_ms / 1000).toFixed(1)}s` : event.result}
                </span>
              </div>
            );
          })}
          {events.length === 0 && (
            <div className="empty-state">
              No healing events yet. Launch an attack to begin.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Anomaly Score Trend Chart ───────────────────────────────
function AnomalyTrend({ events }: { events: HealingEvent[] }) {
  const data = events.slice(-20).map((e, i) => ({
    idx: i,
    score: Math.abs(e.anomaly_score ?? 0),
    time: new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
  }));

  if (data.length < 2) return null;

  return (
    <div className="card" style={{ flex: '1 1 auto', minHeight: 0 }}>
      <div className="card-header">
        <span className="header-label">
          <TrendingUp size={14} />
          ANOMALY SCORE TREND
        </span>
      </div>
      <div className="card-body" style={{ padding: '4px 8px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ffffff" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#ffffff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="time" stroke="#444" fontSize={9} tickLine={false} axisLine={false} />
            <YAxis stroke="#444" fontSize={9} tickLine={false} axisLine={false} domain={[0, 1]} />
            <Tooltip
              contentStyle={{
                background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 6, fontSize: 10, color: '#a0a0a0'
              }}
              labelStyle={{ color: '#666' }}
            />
            <Area
              type="monotone" dataKey="score" stroke="#888"
              fill="url(#scoreGrad)" strokeWidth={1.5} dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── Main App ───────────────────────────────────────────────
export default function App() {
  const [scores, setScores] = useState<Scores>({
    f1_score: 0, mttd_seconds: 0, mttr_seconds: 0, recovery_rate: 0,
    false_positive_rate: 0, total_healing_actions: 0, precision: 0, recall: 0,
    healing_by_type: {}, healing_by_namespace: {},
  });
  const [healingLog, setHealingLog] = useState<HealingEvent[]>([]);
  const [pods, setPods] = useState<PodNode[]>(generateDemoTopology());
  const [healingPod, setHealingPod] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedPod, setSelectedPod] = useState<PodNode | null>(null);

  // Fetch scores periodically
  useEffect(() => {
    const load = async () => {
      const s = await fetchScores();
      setScores(s);
      const log = await fetchHealingLog();
      if (log.length > 0) setHealingLog(log);
    };
    load();
    const iv = setInterval(load, 10000);
    return () => clearInterval(iv);
  }, []);

  // Attack handler
  const handleAttack = useCallback(async (type: string, ns: string, pod: string) => {
    setIsRunning(true);

    // Visual: set target pod to critical
    setPods(prev => prev.map(p =>
      p.name === pod ? { ...p, status: 'critical' as const } : p
    ));

    try {
      const event = await simulateAttack(type, ns, pod);

      // Add event to local log immediately
      setHealingLog(prev => [...prev, event]);

      // Visual: healing animation
      const podId = `${ns}-${pod}`;
      setHealingPod(podId);
      setPods(prev => prev.map(p =>
        p.name === pod ? { ...p, status: 'healing' as const } : p
      ));

      // Wait 3s for healing animation, then recover
      await sleep(3000);

      setPods(prev => prev.map(p =>
        p.name === pod ? { ...p, status: 'healthy' as const, restarts: p.restarts + 1 } : p
      ));
      setHealingPod(null);

      // Refresh scores from metrics aggregator
      const s = await fetchScores();
      setScores(s);

      // Also refresh the full healing log from healer
      const log = await fetchHealingLog();
      if (log.length > 0) setHealingLog(log);
    } catch (error) {
      console.error('Attack simulation failed:', error);
      setPods(prev => prev.map(p =>
        p.name === pod ? { ...p, status: 'healthy' as const } : p
      ));
    } finally {
      setIsRunning(false);
    }
  }, []);

  return (
    <div className="dashboard">
      {/* ─── Top Bar ─── */}
      <div className="top-bar">
        <h1>
          <span className="pulse" />
          SENTINELS COMMAND CENTER
        </h1>
        <div className="status-pills">
          <div className="legend">
            <span className="legend-item"><span className="legend-dot healthy" /> Healthy</span>
            <span className="legend-item"><span className="legend-dot warning" /> Warning</span>
            <span className="legend-item"><span className="legend-dot critical" /> Critical</span>
            <span className="legend-item"><span className="legend-dot healing" /> Healing</span>
          </div>
          <span className="pill green">CONNECTED</span>
          <span className="pill white">v2.0.0</span>
        </div>
      </div>

      {/* ─── Main Grid ─── */}
      <div className="main-grid">
        {/* 3D Viewport */}
        <div className="card viewport-card">
          <TopologyGraph
            pods={pods}
            healingPod={healingPod}
            onPodClick={(pod) => setSelectedPod(pod)}
          />
          <div className="viewport-overlay">
            <button onClick={() => setPods(generateDemoTopology())}>
              <RotateCcw size={12} />
              Reset View
            </button>
            {selectedPod && (
              <button style={{ borderColor: 'rgba(255,255,255,0.2)', color: '#a0a0a0' }}>
                <MapPin size={12} />
                {selectedPod.name} ({selectedPod.status}) | CPU: {selectedPod.cpu?.toFixed(0) ?? '0'}%
              </button>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="right-panel">
          <ScoreCard scores={scores} />
          <AttackLauncher onAttack={handleAttack} isRunning={isRunning} />
          <AnomalyTrend events={healingLog} />
        </div>

        {/* Bottom: Healing Log */}
        <HealingLog events={healingLog} />
      </div>
    </div>
  );
}
