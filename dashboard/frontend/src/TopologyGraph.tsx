import React, { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Billboard, Line } from '@react-three/drei';
import * as THREE from 'three';

// ─── Types ──────────────────────────────────────────────────
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

interface TopologyProps {
  pods: PodNode[];
  healingPod: string | null;
  onPodClick?: (pod: PodNode) => void;
}

// ─── Color Map — Charcoal Theme ─────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  healthy: '#4ade80',
  warning: '#facc15',
  critical: '#ef4444',
  healing: '#60a5fa',
  dead: '#444444',
};

const NS_COLORS: Record<string, string> = {
  netflix: '#ef4444',
  prime: '#3b82f6',
  'sentinels-system': '#a0a0a0',
};

// ─── Single Pod Node ────────────────────────────────────────
function PodSphere({ pod, isHealing, onClick }: {
  pod: PodNode; isHealing: boolean; onClick?: () => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const wireRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const color = STATUS_COLORS[pod.status] || STATUS_COLORS.healthy;
  const size = pod.namespace === 'sentinels-system' ? 0.45 : 0.3;

  useFrame(() => {
    if (!meshRef.current) return;

    // Gentle float
    meshRef.current.position.y = pod.y + Math.sin(Date.now() * 0.0008 + pod.x * 2) * 0.04;

    // Pulse for healing/critical
    if (isHealing || pod.status === 'critical') {
      const s = 1 + Math.sin(Date.now() * 0.004) * 0.12;
      meshRef.current.scale.setScalar(s);
    } else {
      meshRef.current.scale.setScalar(1);
    }

    // Glow
    if (glowRef.current) {
      const gs = isHealing ? 2.2 + Math.sin(Date.now() * 0.003) * 0.4 : hovered ? 1.8 : 1.4;
      glowRef.current.scale.setScalar(gs);
    }

    // Wireframe rotation
    if (wireRef.current) {
      wireRef.current.rotation.y += 0.003;
      wireRef.current.rotation.x += 0.001;
    }
  });

  return (
    <group position={[pod.x, pod.y, pod.z]}>
      {/* Outer glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={isHealing ? 0.15 : 0.04} />
      </mesh>

      {/* Tech wireframe overlay */}
      <mesh ref={wireRef}>
        <icosahedronGeometry args={[size * 1.3, 1]} />
        <meshBasicMaterial color={color} wireframe transparent opacity={isHealing ? 0.3 : 0.08} />
      </mesh>

      {/* Core sphere */}
      <mesh
        ref={meshRef}
        onClick={onClick}
        onPointerOver={() => { setHovered(true); document.body.style.cursor = 'pointer'; }}
        onPointerOut={() => { setHovered(false); document.body.style.cursor = 'default'; }}
      >
        <sphereGeometry args={[size, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isHealing ? 0.6 : hovered ? 0.35 : 0.15}
          roughness={0.4}
          metalness={0.6}
        />
      </mesh>

      {/* Label */}
      <Billboard position={[0, size + 0.22, 0]}>
        <Text
          fontSize={0.1}
          color={hovered ? '#ffffff' : '#888888'}
          anchorX="center"
          anchorY="bottom"
        >
          {pod.name.replace(/-[a-z0-9]{8,10}(-[a-z0-9]{5})?$/, '')}
        </Text>
      </Billboard>

      {/* Restart count */}
      {pod.restarts > 0 && (
        <Billboard position={[size + 0.12, 0, 0]}>
          <Text fontSize={0.08} color="#facc15" anchorX="left">
            x{pod.restarts}
          </Text>
        </Billboard>
      )}
    </group>
  );
}

// ─── Data Flow Particles ────────────────────────────────────
function DataFlowParticle({ from, to, speed, delay }: {
  from: [number, number, number]; to: [number, number, number]; speed: number; delay: number;
}) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (!ref.current) return;
    const t = ((Date.now() * speed * 0.001 + delay) % 1);
    ref.current.position.set(
      from[0] + (to[0] - from[0]) * t,
      from[1] + (to[1] - from[1]) * t + Math.sin(t * Math.PI) * 0.08,
      from[2] + (to[2] - from[2]) * t,
    );
    ref.current.material.opacity = Math.sin(t * Math.PI) * 0.6;
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.025, 8, 8]} />
      <meshBasicMaterial color="#ffffff" transparent opacity={0.3} />
    </mesh>
  );
}

// ─── Connection Lines with Data Flow ────────────────────────
function ConnectionLines({ pods }: { pods: PodNode[] }) {
  const { lines, particles } = useMemo(() => {
    const lineData: [number, number, number][][] = [];
    const particleData: { from: [number, number, number]; to: [number, number, number]; speed: number; delay: number }[] = [];
    const podMap = new Map(pods.map(p => [p.id, p]));

    for (const pod of pods) {
      for (const connId of pod.connections) {
        const target = podMap.get(connId);
        if (target) {
          const from: [number, number, number] = [pod.x, pod.y, pod.z];
          const to: [number, number, number] = [target.x, target.y, target.z];
          lineData.push([from, to]);

          // Add 2 data flow particles per connection
          particleData.push({ from, to, speed: 0.3 + Math.random() * 0.2, delay: 0 });
          particleData.push({ from, to, speed: 0.3 + Math.random() * 0.2, delay: 0.5 });
        }
      }
    }
    return { lines: lineData, particles: particleData };
  }, [pods]);

  return (
    <>
      {lines.map((pts, i) => (
        <Line
          key={`line-${i}`}
          points={pts}
          color="#333333"
          lineWidth={1}
          transparent
          opacity={0.25}
        />
      ))}
      {particles.map((p, i) => (
        <DataFlowParticle key={`particle-${i}`} {...p} />
      ))}
    </>
  );
}

// ─── Background Stars ───────────────────────────────────────
function StarField() {
  const count = 300;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 25;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 25;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 25;
    }
    return pos;
  }, []);

  const ref = useRef<THREE.Points>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.005;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial color="#222222" size={0.02} transparent opacity={0.5} sizeAttenuation />
    </points>
  );
}

// ─── Namespace Ring ─────────────────────────────────────────
function NamespaceRing({ center, radius, label, color }: {
  center: [number, number, number]; radius: number; label: string; color: string;
}) {
  const points = useMemo(() => {
    const pts: [number, number, number][] = [];
    const segments = 80;
    for (let i = 0; i <= segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      pts.push([
        center[0] + Math.cos(angle) * radius,
        center[1] - 0.35,
        center[2] + Math.sin(angle) * radius,
      ]);
    }
    return pts;
  }, [center, radius]);

  return (
    <group>
      <Line points={points} color={color} lineWidth={1} transparent opacity={0.12} />
      <Billboard position={[center[0], center[1] - 0.65, center[2] + radius + 0.25]}>
        <Text fontSize={0.09} color={color} anchorX="center" letterSpacing={0.1}>
          {label.toUpperCase()}
        </Text>
      </Billboard>
    </group>
  );
}

// ─── Grid Floor ─────────────────────────────────────────────
function GridFloor() {
  return (
    <gridHelper
      args={[24, 48, '#1a1a1a', '#111111']}
      position={[0, -0.5, 0]}
    />
  );
}

// ─── Main 3D Topology ──────────────────────────────────────
export default function TopologyGraph({ pods, healingPod, onPodClick }: TopologyProps) {
  return (
    <Canvas
      camera={{ position: [0, 5, 9], fov: 50 }}
      gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.2 }}
      style={{ width: '100%', height: '100%', background: '#0d0d0d' }}
    >
      {/* 3-Point Lighting Setup */}
      <ambientLight intensity={0.25} color="#ffffff" />
      {/* Key light — warm white from top-right */}
      <directionalLight position={[5, 8, 5]} intensity={0.6} color="#ffffff" />
      {/* Fill light — cool from left */}
      <pointLight position={[-6, 4, -4]} intensity={0.3} color="#8888ff" />
      {/* Rim light — subtle backlight */}
      <pointLight position={[0, 2, -8]} intensity={0.2} color="#ffffff" />

      {/* Environment */}
      <GridFloor />
      <StarField />
      <fog attach="fog" args={['#0d0d0d', 12, 25]} />

      {/* Namespace rings */}
      <NamespaceRing center={[-2, 0, 0]} radius={2.5} label="netflix" color="#ef4444" />
      <NamespaceRing center={[3, 0, 0]} radius={1.5} label="prime" color="#3b82f6" />
      <NamespaceRing center={[0, 0, -3]} radius={1.8} label="sentinels" color="#888888" />

      {/* Connections + data flow */}
      <ConnectionLines pods={pods} />

      {/* Pod nodes */}
      {pods.map((pod) => (
        <PodSphere
          key={pod.id}
          pod={pod}
          isHealing={healingPod === pod.id}
          onClick={() => onPodClick?.(pod)}
        />
      ))}

      {/* Camera controls */}
      <OrbitControls
        enableDamping dampingFactor={0.05}
        minDistance={3} maxDistance={16}
        maxPolarAngle={Math.PI / 2 + 0.2}
        autoRotate autoRotateSpeed={0.2}
      />
    </Canvas>
  );
}

// ─── Generate Demo Topology ─────────────────────────────────
export function generateDemoTopology(): PodNode[] {
  const netflixServices = [
    'api-gateway', 'user-service', 'content-service', 'streaming-service',
    'search-service', 'recommendation-service', 'payment-service', 'notification-service',
  ];

  const pods: PodNode[] = [];

  // Netflix pods (circle on the left)
  netflixServices.forEach((svc, i) => {
    const angle = (i / netflixServices.length) * Math.PI * 2;
    pods.push({
      id: `netflix-${svc}`,
      name: svc,
      namespace: 'netflix',
      status: 'healthy',
      x: -2 + Math.cos(angle) * 1.8,
      y: 0,
      z: Math.sin(angle) * 1.8,
      restarts: 0,
      cpu: Math.random() * 40 + 10,
      connections: i === 0 ? netflixServices.slice(1).map(s => `netflix-${s}`) : [`netflix-api-gateway`],
    });
  });

  // Netflix frontend
  pods.push({
    id: 'netflix-frontend',
    name: 'netflix-frontend',
    namespace: 'netflix',
    status: 'healthy',
    x: -2, y: 1.2, z: 0,
    restarts: 0, cpu: 15,
    connections: ['netflix-api-gateway'],
  });

  // Prime pods
  pods.push({
    id: 'prime-backend',
    name: 'primeos-monolith',
    namespace: 'prime',
    status: 'healthy',
    x: 3, y: 0, z: 0,
    restarts: 0, cpu: 35,
    connections: [],
  });

  pods.push({
    id: 'prime-frontend',
    name: 'prime-frontend',
    namespace: 'prime',
    status: 'healthy',
    x: 3, y: 1.0, z: 0.8,
    restarts: 0, cpu: 12,
    connections: ['prime-backend'],
  });

  // SENTINELS core
  pods.push({
    id: 'sentinels-healer',
    name: 'healer-agent',
    namespace: 'sentinels-system',
    status: 'healthy',
    x: 0, y: 0.5, z: -3,
    restarts: 0, cpu: 25,
    connections: ['netflix-api-gateway', 'prime-backend'],
  });

  pods.push({
    id: 'sentinels-metrics',
    name: 'metrics-aggregator',
    namespace: 'sentinels-system',
    status: 'healthy',
    x: 1.2, y: 0.3, z: -3.5,
    restarts: 0, cpu: 18,
    connections: ['sentinels-healer'],
  });

  pods.push({
    id: 'sentinels-opa',
    name: 'opa-server',
    namespace: 'sentinels-system',
    status: 'healthy',
    x: -1.2, y: 0.3, z: -3.5,
    restarts: 0, cpu: 10,
    connections: ['sentinels-healer'],
  });

  return pods;
}
