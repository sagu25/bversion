import { useEffect, useRef, useState, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const ZONE_CONFIG = {
  Z1: {
    center:   [51.5145, -0.1260],
    zoom:     13,
    color:    '#ff4d6d',
    gridSource: { pos:[51.530, -0.126], label:'National Grid · Substation A' },
    boundary: [[51.524,-0.148],[51.524,-0.104],[51.505,-0.104],[51.505,-0.148]],
    assets: [
      { pos:[51.518, -0.136], id:'BRK-110' },
      { pos:[51.512, -0.118], id:'FDR-110' },
    ],
    infrastructure: [
      { pos:[51.521,-0.128], icon:'✚', label:'Royal Hospital',     color:'#ff4d6d' },
      { pos:[51.516,-0.112], icon:'▣', label:'National Data Ctr',  color:'#00d4ff' },
      { pos:[51.509,-0.138], icon:'⚡', label:'Emergency Dispatch', color:'#ff9a3c' },
      { pos:[51.507,-0.115], icon:'🏛', label:'Gov. Command Ctr',  color:'#a855f7' },
    ],
  },
  Z2: {
    center:   [51.4990, -0.0740],
    zoom:     13,
    color:    '#ff9a3c',
    gridSource: { pos:[51.516, -0.040], label:'National Grid · Substation B' },
    boundary: [[51.510,-0.095],[51.510,-0.053],[51.488,-0.053],[51.488,-0.095]],
    assets: [
      { pos:[51.506,-0.082], id:'BRK-205' },
      { pos:[51.499,-0.071], id:'FDR-205' },
    ],
    infrastructure: [
      { pos:[51.507,-0.075], icon:'🏢', label:'Office Tower',      color:'#ff9a3c' },
      { pos:[51.502,-0.062], icon:'🏠', label:'Residential Area',  color:'#00e87c' },
      { pos:[51.492,-0.079], icon:'🛍', label:'Shopping Centre',   color:'#a855f7' },
      { pos:[51.496,-0.065], icon:'🏠', label:'Residential Block', color:'#00e87c' },
    ],
  },
  Z3: {
    center:   [51.5050, -0.1900],
    zoom:     13,
    color:    '#00d4ff',
    gridSource: { pos:[51.524,-0.190], label:'National Grid · Substation C' },
    boundary: [[51.518,-0.212],[51.518,-0.168],[51.492,-0.168],[51.492,-0.212]],
    assets: [
      { pos:[51.513,-0.200], id:'BRK-301' },
      { pos:[51.503,-0.183], id:'FDR-301' },
    ],
    infrastructure: [
      { pos:[51.515,-0.205], icon:'🏭', label:'Manufacturing Plant', color:'#00d4ff' },
      { pos:[51.507,-0.175], icon:'🏭', label:'Industrial Facility',  color:'#00d4ff' },
      { pos:[51.499,-0.194], icon:'📦', label:'Logistics Hub',        color:'#ff9a3c' },
      { pos:[51.495,-0.205], icon:'🏗', label:'Construction Depot',   color:'#6b8fa3' },
    ],
  },
}

function makeMarkerIcon(html) {
  return L.divIcon({ html, className: '', iconAnchor: [0, 0] })
}

export default function ZoneGISMap({ zoneId, isFault }) {
  const mapDivRef   = useRef(null)
  const mapRef      = useRef(null)
  const [svgLines, setSvgLines] = useState([])
  const [svgSize,  setSvgSize]  = useState({ w: 0, h: 0 })
  const cfg = ZONE_CONFIG[zoneId]

  // Convert all points to pixel coords and update SVG lines
  const refreshLines = useCallback(() => {
    const map = mapRef.current
    if (!map || !cfg) return

    const size = map.getSize()
    setSvgSize({ w: size.x, h: size.y })

    const toXY = (pos) => {
      const p = map.latLngToContainerPoint(L.latLng(pos[0], pos[1]))
      return [p.x, p.y]
    }

    const lines = []
    const brk = cfg.assets[0]
    const fdr = cfg.assets[1]

    // HV transmission: National Grid → BRK
    if (cfg.gridSource && brk) {
      lines.push({ from: toXY(cfg.gridSource.pos), to: toXY(brk.pos), type: 'hv' })
    }
    // Trunk: BRK → FDR
    if (brk && fdr) {
      lines.push({ from: toXY(brk.pos), to: toXY(fdr.pos), type: 'trunk' })
    }
    // Branches: FDR → each load
    if (fdr) {
      cfg.infrastructure.forEach(item => {
        lines.push({ from: toXY(fdr.pos), to: toXY(item.pos), type: 'branch' })
      })
    }
    setSvgLines(lines)
  }, [cfg])

  useEffect(() => {
    if (!cfg || !mapDivRef.current) return
    if (mapRef.current) { mapRef.current.remove(); mapRef.current = null }

    const map = L.map(mapDivRef.current, {
      center: cfg.center, zoom: cfg.zoom,
      zoomControl: true, attributionControl: false,
      scrollWheelZoom: true, dragging: true,
    })
    mapRef.current = map

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map)

    const zoneColor = isFault ? '#ff8c00' : cfg.color
    const brkColor  = isFault ? '#ff8c00' : zoneColor

    // ── DIV markers (always work) ──────────────────────────────
    // National Grid substation
    if (cfg.gridSource) {
      L.marker(cfg.gridSource.pos, {
        icon: makeMarkerIcon(`<div style="
          background:rgba(6,11,20,0.95);border:2px solid #f59e0b;border-radius:8px;
          padding:7px 12px;font-family:monospace;font-size:13px;font-weight:700;
          color:#f59e0b;white-space:nowrap;box-shadow:0 0 16px #f59e0b66;
        ">⚡ NATIONAL GRID<br/><span style="font-size:11px;opacity:0.75">${cfg.gridSource.label}</span></div>`),
      }).addTo(map)
    }

    // Asset markers
    cfg.assets.forEach(a => {
      const isBreaker = a.id.startsWith('BRK')
      const col = isBreaker ? brkColor : zoneColor
      L.marker(a.pos, {
        icon: makeMarkerIcon(`<div style="
          display:flex;align-items:center;gap:6px;
          background:rgba(6,11,20,0.92);border:2px solid ${col};border-radius:6px;
          padding:6px 12px;font-family:monospace;font-size:13px;font-weight:700;
          color:${col};white-space:nowrap;box-shadow:0 0 12px ${col}66;
        ">${isBreaker ? '⬡' : '◈'} ${a.id}</div>`),
      }).addTo(map)
    })

    // Infrastructure markers
    cfg.infrastructure.forEach(item => {
      L.marker(item.pos, {
        icon: makeMarkerIcon(`<div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <div style="
            background:rgba(6,11,20,0.88);border:1.5px solid ${item.color}77;border-radius:50%;
            width:36px;height:36px;display:flex;align-items:center;justify-content:center;
            font-size:18px;box-shadow:0 0 10px ${item.color}55;
          ">${item.icon}</div>
          <div style="
            background:rgba(6,11,20,0.85);color:${item.color};font-family:monospace;
            font-size:11px;font-weight:600;padding:2px 6px;border-radius:3px;white-space:nowrap;
          ">${item.label}</div>
        </div>`),
      }).addTo(map)
    })

    // Active fault badge
    if (isFault) {
      L.marker([cfg.boundary[0][0], cfg.boundary[0][1]], {
        icon: makeMarkerIcon(`<div style="
          color:#ff8c00;font-family:monospace;font-size:13px;font-weight:700;
          background:rgba(6,11,20,0.88);padding:5px 10px;border-radius:5px;
          border:1.5px solid #ff8c0077;white-space:nowrap;
        ">⚠ ACTIVE FAULT</div>`),
      }).addTo(map)
    }

    // Refresh lines on map move/zoom
    map.on('moveend zoomend move zoom', refreshLines)

    // Initial line draw after tiles load + size settles
    setTimeout(refreshLines, 150)

    return () => { map.remove(); mapRef.current = null; setSvgLines([]) }
  }, [zoneId, isFault, cfg, refreshLines])

  const zoneColor = cfg ? (isFault ? '#ff8c00' : cfg.color) : '#00d4ff'

  return (
    <div style={{ position:'relative', width:'100%', height:'100%', borderRadius:4, overflow:'hidden' }}>
      {/* Leaflet map — tiles + markers */}
      <div ref={mapDivRef} style={{ width:'100%', height:'100%' }} />

      {/* React SVG overlay — lines drawn here, guaranteed visible */}
      <svg
        style={{ position:'absolute', top:0, left:0, pointerEvents:'none', zIndex:999 }}
        width={svgSize.w} height={svgSize.h}
      >
        <defs>
          <filter id="glow-hv">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <filter id="glow-line">
            <feGaussianBlur stdDeviation="2" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {svgLines.map((ln, i) => {
          if (ln.type === 'hv') return (
            <g key={i} filter="url(#glow-hv)">
              <line x1={ln.from[0]} y1={ln.from[1]} x2={ln.to[0]} y2={ln.to[1]}
                stroke="#f59e0b" strokeWidth={6} opacity={0.25} />
              <line x1={ln.from[0]} y1={ln.from[1]} x2={ln.to[0]} y2={ln.to[1]}
                stroke="#f59e0b" strokeWidth={2.5} opacity={1} />
            </g>
          )
          if (ln.type === 'trunk') return (
            <g key={i} filter="url(#glow-line)">
              <line x1={ln.from[0]} y1={ln.from[1]} x2={ln.to[0]} y2={ln.to[1]}
                stroke={zoneColor} strokeWidth={6} opacity={0.2} />
              <line x1={ln.from[0]} y1={ln.from[1]} x2={ln.to[0]} y2={ln.to[1]}
                stroke={zoneColor} strokeWidth={2.5} opacity={1}
                strokeDasharray={isFault ? '10 5' : undefined} />
            </g>
          )
          return (
            <g key={i} filter="url(#glow-line)">
              <line x1={ln.from[0]} y1={ln.from[1]} x2={ln.to[0]} y2={ln.to[1]}
                stroke={zoneColor} strokeWidth={4} opacity={0.15} />
              <line x1={ln.from[0]} y1={ln.from[1]} x2={ln.to[0]} y2={ln.to[1]}
                stroke={zoneColor} strokeWidth={1.8} opacity={0.9}
                strokeDasharray="7 5" />
            </g>
          )
        })}
      </svg>
    </div>
  )
}
