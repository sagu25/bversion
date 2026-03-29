import ZoneGISMap from './ZoneGISMap'

// Zone display names and rich info for non-technical audiences
export const ZONE_DISPLAY = { Z1: 'Zone 1', Z2: 'Zone 2', Z3: 'Zone 3' }

// ── Electrical schematic diagrams per zone ────────────────────────
function ZoneSchematic({ zoneId, isFault }) {
  const c  = isFault ? '#ff8c00' : '#00e87c'
  const c2 = '#00d4ff'
  const dim = '#2e5a8f'
  const bg  = 'rgba(6,11,20,0)'

  // Shared helpers
  const Node = ({ x, y, r = 5 }) => <circle cx={x} cy={y} r={r} fill="none" stroke={c2} strokeWidth={1.5} />
  const Bus  = ({ x1, y1, x2, y2 }) => <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={c2} strokeWidth={2.5} />
  const Wire = ({ x1, y1, x2, y2 }) => <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={c} strokeWidth={1.5} strokeDasharray="none" />
  const Lbl  = ({ x, y, text, col = dim, anchor = 'middle', size = 9 }) => (
    <text x={x} y={y} textAnchor={anchor} fontSize={size} fill={col}
      style={{ fontFamily: 'var(--font-mono)', letterSpacing: '0.04em' }}>{text}</text>
  )
  // Transformer symbol (two circles touching)
  const Xfmr = ({ x, y, big = false }) => {
    const r = big ? 11 : 8
    return (
      <g>
        <circle cx={x} cy={y - r} r={r} fill="none" stroke={c2} strokeWidth={1.8} />
        <circle cx={x} cy={y + r} r={r} fill="none" stroke={c2} strokeWidth={1.8} />
      </g>
    )
  }
  // Breaker symbol (small square with X)
  const Brk = ({ x, y, open = false }) => (
    <g>
      <rect x={x - 6} y={y - 6} width={12} height={12} fill="rgba(14,29,53,0.9)" stroke={open ? '#ff8c00' : c} strokeWidth={1.5} rx={1} />
      {open
        ? <line x1={x - 4} y1={y - 4} x2={x + 4} y2={y + 4} stroke="#ff8c00" strokeWidth={1.5} />
        : <line x1={x} y1={y - 4} x2={x} y2={y + 4} stroke={c} strokeWidth={1.5} />}
    </g>
  )
  // House / load icon
  const House = ({ x, y, size = 16 }) => (
    <g>
      <polygon points={`${x},${y - size * 0.5} ${x - size * 0.55},${y} ${x + size * 0.55},${y}`}
        fill="none" stroke={c} strokeWidth={1.3} />
      <rect x={x - size * 0.35} y={y} width={size * 0.7} height={size * 0.55}
        fill="none" stroke={c} strokeWidth={1.3} />
    </g>
  )
  // Office/tower icon
  const Office = ({ x, y, w = 12, h = 22 }) => (
    <g>
      <rect x={x - w / 2} y={y - h} width={w} height={h} fill="none" stroke={c} strokeWidth={1.3} />
      {[0.2, 0.45, 0.7].map(f => (
        <rect key={f} x={x - w * 0.3} y={y - h * f - 3} width={4} height={3}
          fill="none" stroke={c} strokeWidth={0.8} opacity={0.7} />
      ))}
    </g>
  )
  // Factory icon
  const Factory = ({ x, y }) => (
    <g>
      <rect x={x - 14} y={y - 14} width={28} height={14} fill="none" stroke={c} strokeWidth={1.3} />
      <rect x={x - 10} y={y - 26} width={6} height={13} fill="none" stroke={c} strokeWidth={1.2} />
      <rect x={x - 1}  y={y - 22} width={6} height={9}  fill="none" stroke={c} strokeWidth={1.2} />
      <rect x={x + 5}  y={y - 19} width={5} height={6}  fill="none" stroke={c} strokeWidth={1.2} />
    </g>
  )
  // Warehouse icon
  const Warehouse = ({ x, y }) => (
    <g>
      <rect x={x - 16} y={y - 10} width={32} height={10} fill="none" stroke={c} strokeWidth={1.3} />
      <path d={`M${x - 16},${y - 10} L${x},${y - 18} L${x + 16},${y - 10}`}
        fill="none" stroke={c} strokeWidth={1.3} />
    </g>
  )
  // Hospital icon
  const Hospital = ({ x, y }) => (
    <g>
      <rect x={x - 13} y={y - 20} width={26} height={20} fill="none" stroke={c} strokeWidth={1.3} />
      <line x1={x} y1={y - 17} x2={x} y2={y - 7} stroke={c} strokeWidth={2} />
      <line x1={x - 5} y1={y - 12} x2={x + 5} y2={y - 12} stroke={c} strokeWidth={2} />
    </g>
  )
  // Data centre icon
  const DataCentre = ({ x, y }) => (
    <g>
      {[0, 7, 14].map(dy => (
        <rect key={dy} x={x - 12} y={y - 22 + dy} width={24} height={5}
          fill="none" stroke={c} strokeWidth={1.2} rx={1} />
      ))}
      {[0, 7, 14].map(dy => (
        <circle key={dy} cx={x + 8} cy={y - 19 + dy} r={1.5} fill={c} opacity={0.8} />
      ))}
    </g>
  )
  // HV tower icon
  const Tower = ({ x, y }) => (
    <g>
      <line x1={x} y1={y - 30} x2={x - 10} y2={y} stroke={c2} strokeWidth={1.5} />
      <line x1={x} y1={y - 30} x2={x + 10} y2={y} stroke={c2} strokeWidth={1.5} />
      <line x1={x - 8} y1={y - 10} x2={x + 8} y2={y - 10} stroke={c2} strokeWidth={1.2} />
      <line x1={x - 12} y1={y - 20} x2={x + 12} y2={y - 20} stroke={c2} strokeWidth={1.2} />
      <line x1={x - 14} y1={y - 28} x2={x + 14} y2={y - 28} stroke={c2} strokeWidth={1.2} />
      <line x1={x} y1={y - 30} x2={x} y2={y} stroke={c2} strokeWidth={1} opacity={0.4} />
    </g>
  )
  // Fault badge
  const FaultBadge = ({ x, y }) => (
    <g>
      <polygon points={`${x},${y - 10} ${x - 9},${y + 4} ${x + 9},${y + 4}`}
        fill="rgba(255,140,0,0.15)" stroke="#ff8c00" strokeWidth={1.5} />
      <text x={x} y={y + 3} textAnchor="middle" fontSize={8} fill="#ff8c00" fontWeight="bold">!</text>
    </g>
  )

  // ── Z1: North Grid — Critical Infrastructure ──────────────────
  if (zoneId === 'Z1') return (
    <svg viewBox="0 0 380 175" style={{ width:'100%', height:'100%' }}>
      <rect width="380" height="175" fill="rgba(6,11,20,0.6)" />
      {/* HV source tower */}
      <Tower x={32} y={80} />
      <Lbl x={32} y={90} text="69kV" col={c2} size={8} />
      {/* HV bus left → transformer */}
      <Bus x1={46} y1={50} x2={80} y2={50} />
      <Lbl x={63} y={45} text="HV FEED" col={dim} size={7.5} />
      {/* Step-down transformer */}
      <line x1={80} y1={50} x2={80} y2={62} stroke={c2} strokeWidth={1.8} />
      <Xfmr x={80} y={80} big />
      <line x1={80} y1={98} x2={80} y2={110} stroke={c2} strokeWidth={1.8} />
      <Lbl x={80} y={58} text="69/11kV" col={c2} size={7.5} />
      {/* 11kV distribution bus */}
      <Bus x1={80} y1={110} x2={340} y2={110} />
      <Lbl x={100} y={122} text="11kV DISTRIBUTION BUS" col={dim} size={7.5} />
      {/* Breakers on bus */}
      <Brk x={130} y={110} />
      <Brk x={220} y={110} />
      <Brk x={310} y={110} />
      {/* Drop wires */}
      <Wire x1={130} y1={116} x2={130} y2={135} />
      <Wire x1={220} y1={116} x2={220} y2={135} />
      <Wire x1={310} y1={116} x2={310} y2={135} />
      {/* Load icons */}
      <Hospital x={130} y={155} />
      <DataCentre x={220} y={155} />
      <g>
        <rect x={297} y={135} width={26} height={20} fill="none" stroke={c} strokeWidth={1.3} />
        <line x1={303} y1={135} x2={303} y2={155} stroke={c} strokeWidth={0.8} opacity={0.5} />
        <line x1={309} y1={135} x2={309} y2={155} stroke={c} strokeWidth={0.8} opacity={0.5} />
        <line x1={315} y1={135} x2={315} y2={155} stroke={c} strokeWidth={0.8} opacity={0.5} />
        <circle cx={321} cy={140} r={2} fill={c} opacity={0.9} />
      </g>
      {/* Load labels */}
      <Lbl x={130} y={170} text="Hospital" col={c} size={8} />
      <Lbl x={220} y={170} text="Data Centre" col={c} size={8} />
      <Lbl x={310} y={170} text="Emergency Ctrl" col={c} size={8} />
      {/* Node dots on bus */}
      <Node x={130} y={110} r={3} />
      <Node x={220} y={110} r={3} />
      <Node x={310} y={110} r={3} />
      {/* Region label */}
      <Lbl x={190} y={14} text="NORTHERN CRITICAL INFRASTRUCTURE DISTRICT" col={dim} size={8} />
      <line x1={10} y1={18} x2={370} y2={18} stroke={dim} strokeWidth={0.5} opacity={0.4} />
    </svg>
  )

  // ── Z2: East Grid — Commercial & Residential ──────────────────
  if (zoneId === 'Z2') return (
    <svg viewBox="0 0 380 175" style={{ width:'100%', height:'100%' }}>
      <rect width="380" height="175" fill="rgba(6,11,20,0.6)" />
      {/* Grid source */}
      <rect x={8} y={42} width={30} height={20} fill="none" stroke={c2} strokeWidth={1.5} rx={2} />
      <Lbl x={23} y={56} text="GRID" col={c2} size={8} />
      <Lbl x={23} y={67} text="11kV" col={c2} size={7} />
      {/* HV wire → transformer */}
      <Bus x1={38} y1={52} x2={68} y2={52} />
      <line x1={68} y1={52} x2={68} y2={63} stroke={c2} strokeWidth={1.8} />
      <Xfmr x={68} y={80} />
      <line x1={68} y1={97} x2={68} y2={108} stroke={c2} strokeWidth={1.8} />
      <Lbl x={68} y={58} text="Smart Xfmr" col={dim} size={7} />
      <Lbl x={68} y={112} text="0.4kV" col={c2} size={7} />
      {/* Distribution bus */}
      <Bus x1={68} y1={108} x2={355} y2={108} />
      <Lbl x={190} y={120} text="0.4kV LOW-VOLTAGE BUS" col={dim} size={7.5} />
      {/* 5 branch drops — commercial + residential mix */}
      {[110, 175, 230, 285, 340].map((bx, i) => (
        <g key={bx}>
          <Node x={bx} y={108} r={3} />
          <Wire x1={bx} y1={108} x2={bx} y2={126} />
          {i === 0 && <Office x={bx} y={155} w={14} h={26} />}
          {i === 1 && <House  x={bx} y={152} size={20} />}
          {i === 2 && <Office x={bx} y={155} w={12} h={20} />}
          {i === 3 && <House  x={bx} y={152} size={18} />}
          {i === 4 && <House  x={bx} y={152} size={16} />}
        </g>
      ))}
      {/* Load labels */}
      <Lbl x={110} y={170} text="Office" col={c} size={8} />
      <Lbl x={175} y={170} text="Homes" col={c} size={8} />
      <Lbl x={230} y={170} text="Retail" col={c} size={8} />
      <Lbl x={285} y={170} text="Homes" col={c} size={8} />
      <Lbl x={340} y={170} text="Homes" col={c} size={8} />
      {/* Current labels on bus segments */}
      <Lbl x={140} y={103} text="I₁₂" col={dim} size={7} />
      <Lbl x={200} y={103} text="I₂₃" col={dim} size={7} />
      <Lbl x={257} y={103} text="I₃₄" col={dim} size={7} />
      <Lbl x={312} y={103} text="I₄₅" col={dim} size={7} />
      {/* Region label */}
      <Lbl x={190} y={14} text="EASTERN COMMERCIAL &amp; RESIDENTIAL DISTRICT" col={dim} size={8} />
      <line x1={10} y1={18} x2={370} y2={18} stroke={dim} strokeWidth={0.5} opacity={0.4} />
    </svg>
  )

  // ── Z3: West Grid — Industrial & Logistics (Fault zone) ───────
  return (
    <svg viewBox="0 0 380 175" style={{ width:'100%', height:'100%' }}>
      <rect width="380" height="175" fill="rgba(6,11,20,0.6)" />
      {/* HV source */}
      <rect x={8} y={42} width={30} height={20} fill="none" stroke={c2} strokeWidth={1.5} rx={2} />
      <Lbl x={23} y={56} text="GRID" col={c2} size={8} />
      <Lbl x={23} y={67} text="33kV" col={c2} size={7} />
      <Bus x1={38} y1={52} x2={68} y2={52} />
      {/* BRK-301 */}
      <line x1={68} y1={52} x2={80} y2={52} stroke={c2} strokeWidth={1.8} />
      <Brk x={90} y={52} open={isFault} />
      <Lbl x={90} y={42} text="BRK-301" col={isFault ? '#ff8c00' : c} size={7.5} />
      {isFault && <FaultBadge x={90} y={62} />}
      <line x1={96} y1={52} x2={118} y2={52} stroke={c2} strokeWidth={1.8} />
      {/* Transformer */}
      <line x1={118} y1={52} x2={118} y2={63} stroke={c2} strokeWidth={1.8} />
      <Xfmr x={118} y={80} big />
      <line x1={118} y1={97} x2={118} y2={108} stroke={c2} strokeWidth={1.8} />
      <Lbl x={118} y={58} text="33/11kV" col={dim} size={7} />
      {/* FDR-301 feeder controller */}
      <rect x={130} y={102} width={50} height={14} fill="rgba(14,29,53,0.9)" stroke={isFault ? '#ff8c00' : c2} strokeWidth={1.3} rx={2} />
      <Lbl x={155} y={112} text="FDR-301" col={isFault ? '#ff8c00' : c2} size={7.5} />
      <Bus x1={118} y1={108} x2={340} y2={108} />
      <Lbl x={230} y={120} text="11kV INDUSTRIAL BUS" col={dim} size={7.5} />
      {/* 3 industrial loads */}
      {[175, 255, 330].map((bx, i) => (
        <g key={bx}>
          <Node x={bx} y={108} r={3} />
          <Wire x1={bx} y1={108} x2={bx} y2={126} />
          {i === 0 && <Factory   x={bx} y={152} />}
          {i === 1 && <Warehouse x={bx} y={152} />}
          {i === 2 && <Factory   x={bx} y={152} />}
        </g>
      ))}
      <Lbl x={175} y={170} text="Manufacturing" col={c} size={8} />
      <Lbl x={255} y={170} text="Warehouse"     col={c} size={8} />
      <Lbl x={330} y={170} text="Logistics Hub" col={c} size={8} />
      {/* Fault banner */}
      {isFault && (
        <g>
          <rect x={145} y={22} width={220} height={14} rx={3}
            fill="rgba(255,140,0,0.12)" stroke="rgba(255,140,0,0.5)" strokeWidth={1} />
          <Lbl x={255} y={33} text="⚠  VOLTAGE FAULT — FEEDER INSTABILITY" col="#ff8c00" size={7.5} />
        </g>
      )}
      {/* Region label */}
      <Lbl x={190} y={14} text="WESTERN INDUSTRIAL &amp; LOGISTICS DISTRICT" col={dim} size={8} />
      <line x1={10} y1={18} x2={370} y2={18} stroke={dim} strokeWidth={0.5} opacity={0.4} />
    </svg>
  )
}

export const ZONE_INFO = {
  Z1: {
    display:     'Zone 1 — North Grid',
    region:      'Northern Critical Infrastructure District',
    type:        'Critical',
    typeColor:   '#ff4d6d',
    description: 'HIGHEST PRIORITY — directly powers hospitals, emergency response centres, and national data centres in the northern district. A fault here triggers an immediate P1 incident. Any action on this zone requires senior approval and strict safety protocols.',
    assets: [
      { id: 'BRK-110', type: 'Circuit Breaker',   role: 'Guards life-critical infrastructure. Breaker operation here must follow mandatory safety simulation — skipping this step is a serious violation that can cut power to hospitals and emergency services.' },
      { id: 'FDR-110', type: 'Feeder Controller', role: 'Maintains stable, uninterrupted power to hospitals, 999 emergency dispatch and government data centres. A restart here requires supervisor sign-off due to direct risk to human life.' },
    ],
  },
  Z2: {
    display:     'Zone 2 — East Grid',
    region:      'Eastern Commercial & Residential District',
    type:        'Sensitive',
    typeColor:   '#ff9a3c',
    description: 'Medium-priority zone covering the eastern commercial hub and residential areas — office towers, shopping centres and thousands of homes. Disruption here has wide public impact and must be handled with care.',
    assets: [
      { id: 'BRK-205', type: 'Circuit Breaker',   role: 'Protects the eastern grid from overloads during peak demand. Prevents a single fault from blacking out the entire commercial and residential district.' },
      { id: 'FDR-205', type: 'Feeder Controller', role: 'Balances electricity load across the eastern network in real time, preventing voltage drops and ensuring stable power for offices, shops and homes.' },
    ],
  },
  Z3: {
    display:     'Zone 3 — West Grid',
    region:      'Western Industrial & Logistics District',
    type:        'Operational',
    typeColor:   '#00d4ff',
    description: 'Lower-priority operational zone serving the western industrial corridor — manufacturing plants, warehouses and logistics hubs. This is the ACTIVE FAULT ZONE in the current scenario. The AI agent is authorised to investigate and restore it.',
    assets: [
      { id: 'BRK-301', type: 'Circuit Breaker',   role: 'Controls power isolation for the western industrial grid. The current voltage fault on this breaker is what the AI agent has been tasked to investigate and resolve.' },
      { id: 'FDR-301', type: 'Feeder Controller', role: 'Distributes power across the western industrial zone. It supports the manufacturing load but — unlike Zone 1 — a temporary restart here carries lower risk to public safety.' },
    ],
  },
}

// SVG illustrations — exported so hover tooltip can reuse them
export function ZoneIllustration({ zoneId, color }) {
  // Z1 — Critical / Hospital (most sensitive)
  if (zoneId === 'Z1') return (
    <svg viewBox="0 0 160 100" width="160" height="100">
      {/* Main hospital building */}
      <rect x="28" y="32" width="104" height="64" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      {/* Hospital cross — vertical */}
      <rect x="68" y="10" width="24" height="52" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      {/* Hospital cross — horizontal */}
      <rect x="52" y="24" width="56" height="24" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      {/* Plus sign inside cross */}
      <line x1="80" y1="18" x2="80" y2="40" stroke={color} strokeWidth="3" opacity="0.8"/>
      <line x1="68" y1="30" x2="92" y2="30" stroke={color} strokeWidth="3" opacity="0.8"/>
      {/* Entrance */}
      <rect x="68" y="72" width="24" height="24" fill="none" stroke={color} strokeWidth="2"/>
      {/* Windows */}
      <rect x="36" y="44" width="14" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="56" y="44" width="10" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="94" y="44" width="10" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="110" y="44" width="14" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="36" y="62" width="14" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="110" y="62" width="14" height="12" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      {/* Emergency siren */}
      <circle cx="20" cy="20" r="8" fill="none" stroke={color} strokeWidth="1.5" opacity="0.7"/>
      <line x1="20" y1="12" x2="20" y2="8" stroke={color} strokeWidth="2" opacity="0.7"/>
      <line x1="26" y1="14" x2="29" y2="11" stroke={color} strokeWidth="2" opacity="0.7"/>
      <line x1="28" y1="20" x2="32" y2="20" stroke={color} strokeWidth="2" opacity="0.7"/>
      {/* Ground */}
      <line x1="5" y1="96" x2="155" y2="96" stroke={color} strokeWidth="1.5" opacity="0.4"/>
    </svg>
  )

  // Z2 — Sensitive / City skyline (commercial & residential)
  if (zoneId === 'Z2') return (
    <svg viewBox="0 0 160 100" width="160" height="100">
      {/* Tall central tower */}
      <rect x="58" y="14" width="28" height="82" fill="none" stroke={color} strokeWidth="2.5" rx="1"/>
      {/* Antenna */}
      <line x1="72" y1="14" x2="72" y2="6" stroke={color} strokeWidth="1.5"/>
      <circle cx="72" cy="5" r="2" fill={color}/>
      {/* Left building */}
      <rect x="18" y="38" width="36" height="58" fill="none" stroke={color} strokeWidth="2" rx="1"/>
      {/* Right building */}
      <rect x="90" y="28" width="38" height="68" fill="none" stroke={color} strokeWidth="2" rx="1"/>
      {/* Window grids — central */}
      {[22,32,42,52,62,72,82].map(y => [62,75].map(x => (
        <rect key={`${x}-${y}`} x={x} y={y} width="7" height="5" fill="none" stroke={color} strokeWidth="1" opacity="0.6" rx="0.5"/>
      )))}
      {/* Window grids — left */}
      {[44,54,64,74].map(y => [22,32,42].map(x => (
        <rect key={`l${x}-${y}`} x={x} y={y} width="7" height="5" fill="none" stroke={color} strokeWidth="1" opacity="0.6" rx="0.5"/>
      )))}
      {/* Window grids — right */}
      {[34,44,54,64,74].map(y => [93,103,113].map(x => (
        <rect key={`r${x}-${y}`} x={x} y={y} width="7" height="5" fill="none" stroke={color} strokeWidth="1" opacity="0.6" rx="0.5"/>
      )))}
      {/* Ground */}
      <line x1="5" y1="96" x2="155" y2="96" stroke={color} strokeWidth="1.5" opacity="0.4"/>
    </svg>
  )

  // Z3 — Operational / Factory (industrial, least sensitive)
  return (
    <svg viewBox="0 0 160 100" width="160" height="100">
      {/* Factory building */}
      <rect x="20" y="52" width="120" height="44" fill="none" stroke={color} strokeWidth="2.5" rx="2"/>
      {/* Smokestacks */}
      <rect x="32" y="24" width="14" height="30" fill="none" stroke={color} strokeWidth="2"/>
      <rect x="57" y="12" width="14" height="42" fill="none" stroke={color} strokeWidth="2"/>
      <rect x="82" y="18" width="14" height="36" fill="none" stroke={color} strokeWidth="2"/>
      {/* Smoke puffs */}
      <circle cx="39" cy="20" r="5" fill="none" stroke={color} strokeWidth="1.5" opacity="0.5"/>
      <circle cx="64" cy="8"  r="5" fill="none" stroke={color} strokeWidth="1.5" opacity="0.5"/>
      <circle cx="89" cy="14" r="5" fill="none" stroke={color} strokeWidth="1.5" opacity="0.5"/>
      {/* Door */}
      <rect x="67" y="72" width="16" height="24" fill="none" stroke={color} strokeWidth="2"/>
      {/* Windows */}
      <rect x="28" y="62" width="12" height="10" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="48" y="62" width="12" height="10" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="95" y="62" width="12" height="10" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      <rect x="115" y="62" width="12" height="10" fill="none" stroke={color} strokeWidth="1.5" rx="1"/>
      {/* Fault warning triangle */}
      <polygon points="140,55 150,72 130,72" fill="none" stroke={color} strokeWidth="1.8" opacity="0.8"/>
      <text x="140" y="70" textAnchor="middle" fontSize="10" fill={color} fontWeight="bold" opacity="0.9">!</text>
      {/* Ground */}
      <line x1="5" y1="96" x2="155" y2="96" stroke={color} strokeWidth="1.5" opacity="0.4"/>
    </svg>
  )
}

export default function ZoneInfoModal({ zoneId, zones, assets, onClose }) {
  if (!zoneId) return null
  const info   = ZONE_INFO[zoneId]
  if (!info) return null
  const zState  = zones?.[zoneId] || {}
  const isFault = zState.health === 'FAULT'
  const faultMsg = zState.fault || null

  return (
    <div className="zone-modal-overlay" onClick={onClose}>
      <div className="zone-modal zone-modal-horizontal" onClick={e => e.stopPropagation()}>

        {/* Close */}
        <button className="zone-modal-close" onClick={onClose}>✕</button>

        {/* COL 1 — GIS map */}
        <div className="zmc-schematic">
          <div className="zmc-col-label">GIS ZONE MAP</div>
          <div className="zmc-schematic-inner">
            <ZoneGISMap zoneId={zoneId} isFault={isFault} />
          </div>
        </div>

        {/* Divider */}
        <div className="zmc-divider" />

        {/* COL 2 — Zone info */}
        <div className="zmc-info">
          <div className="zmc-col-label">ZONE OVERVIEW</div>

          {/* Illustration + name */}
          <div className="zmc-illus-row">
            <div className="zone-modal-illustration-sm" style={{ borderColor: info.typeColor + '44', background: info.typeColor + '0d' }}>
              <ZoneIllustration zoneId={zoneId} color={info.typeColor} />
            </div>
            <div>
              <div className="zone-modal-name">{info.display}</div>
              <div className="zone-modal-badges">
                <span className="zone-modal-type" style={{ borderColor: info.typeColor + '80', color: info.typeColor, background: info.typeColor + '18' }}>
                  {info.type} Zone
                </span>
                <span className={`zone-modal-status ${isFault ? 'zms-fault' : 'zms-ok'}`}>
                  {isFault ? '⚠ FAULT ACTIVE' : '✓ HEALTHY'}
                </span>
              </div>
            </div>
          </div>

          {/* Active fault alert */}
          {isFault && faultMsg && (
            <div className="zone-modal-fault-alert">
              <div className="zmfa-title">⚡ Active Fault Detected</div>
              <div className="zmfa-msg">{faultMsg}</div>
              <div className="zmfa-impact">
                The AI agent has been tasked to investigate and restore this zone.
                TARE is monitoring all commands issued against this zone in real time.
              </div>
            </div>
          )}

          {/* Description */}
          <div className="zone-modal-section-label" style={{ marginTop: 14 }}>What is this zone?</div>
          <p className="zone-modal-desc">{info.description}</p>
        </div>

        {/* Divider */}
        <div className="zmc-divider" />

        {/* COL 3 — Assets */}
        <div className="zmc-assets">
          <div className="zmc-col-label">ASSETS IN THIS ZONE</div>
          {info.assets.map(a => {
            const ast = assets?.[a.id]
            return (
              <div key={a.id} className="zone-modal-asset">
                <div className="zma-header">
                  <span className="zma-id">{a.id}</span>
                  <span className="zma-type">{a.type}</span>
                  {ast && (
                    <span className={`zma-state ${ast.state === 'OPEN' || ast.state === 'RESTARTING' ? 'zma-warn' : 'zma-ok'}`}>
                      {ast.state}
                    </span>
                  )}
                </div>
                <p className="zma-role">{a.role}</p>
              </div>
            )
          })}
        </div>

      </div>
    </div>
  )
}
