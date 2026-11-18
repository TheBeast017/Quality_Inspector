import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = '/api'

const CLASS_COLORS = {
  crazing: '#ef4444',
  inclusion: '#f97316',
  patches: '#eab308',
  pitted_surface: '#22c55e',
  'rolled-in_scale': '#06b6d4',
  scratches: '#8b5cf6'
}

const SEVERITY_COLORS = {
  minor: '#22c55e',
  moderate: '#eab308',
  major: '#f97316',
  critical: '#ef4444',
  unknown: '#6b7280'
}

function App() {
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [period, setPeriod] = useState('all')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchHistory()
    fetchAnalytics()
  }, [period])

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/history`)
      setHistory(res.data)
    } catch (e) {
      console.error('Failed to fetch history', e)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics`)
      setAnalytics(res.data)
    } catch (e) {
      console.error('Failed to fetch analytics', e)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setImage(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
      setError(null)
    }
  }

  const handleInspect = async () => {
    if (!image) return
    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', image)

    try {
      const res = await axios.post(`${API_BASE}/inspect`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(res.data)
      fetchHistory()
    } catch (e) {
      setError(e.response?.data?.detail || 'Inspection failed')
    } finally {
      setLoading(false)
    }
  }

  const drawCanvas = () => {
    if (!preview || !result) return null

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    img.src = preview

    return new Promise((resolve) => {
      img.onload = () => {
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        result.defects.forEach((defect) => {
          const [x1, y1, x2, y2] = defect.bbox
          const px1 = x1 * img.width
          const py1 = y1 * img.height
          const px2 = x2 * img.width
          const py2 = y2 * img.height

          const color = CLASS_COLORS[defect.class_name] || '#ef4444'

          // Draw mask if available
          if (defect.mask && defect.mask.length > 0) {
            ctx.beginPath()
            ctx.moveTo(defect.mask[0][0], defect.mask[0][1])
            defect.mask.forEach(([x, y]) => ctx.lineTo(x, y))
            ctx.closePath()
            ctx.fillStyle = color + '33'
            ctx.fill()
            ctx.strokeStyle = color
            ctx.lineWidth = 2
            ctx.stroke()
          }

          // Draw bbox
          ctx.strokeStyle = color
          ctx.lineWidth = 3
          ctx.strokeRect(px1, py1, px2 - px1, py2 - py1)

          // Label
          ctx.fillStyle = color
          ctx.font = '14px sans-serif'
          const label = `${defect.class_name} ${(defect.confidence * 100).toFixed(0)}%`
          ctx.fillText(label, px1, py1 - 5)
        })

        resolve(canvas)
      }
    })
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Industrial AI Inspection</h1>
        <div style={styles.status}>
          <span style={{
            ...styles.badge,
            background: result?.decision === 'PASS' ? '#22c55e' : result?.decision === 'REJECT' ? '#ef4444' : '#6b7280'
          }}>
            {result?.decision || '—'}
          </span>
        </div>
      </header>

      <main style={styles.main}>
        <section style={styles.uploadSection}>
          <div style={styles.dropZone}>
            <input type="file" accept="image/*" onChange={handleFileChange} style={styles.fileInput} />
            {preview ? (
              <div style={styles.previewWrapper}>
                {result ? (
                  <div style={styles.canvasWrapper}>
                    <CanvasRenderer preview={preview} result={result} />
                  </div>
                ) : (
                  <img src={preview} alt="Preview" style={styles.previewImg} />
                )}
              </div>
            ) : (
              <div style={styles.uploadPrompt}>
                <p>Drag & drop or click to upload an image</p>
                <p style={styles.hint}>JPG, PNG up to 10MB</p>
              </div>
            )}
          </div>

          <div style={styles.actions}>
            <button
              onClick={handleInspect}
              disabled={!image || loading}
              style={{ ...styles.button, opacity: !image || loading ? 0.5 : 1 }}
            >
              {loading ? 'Analyzing...' : 'Run Inspection'}
            </button>
            {error && <p style={styles.error}>{error}</p>}
          </div>
        </section>

        <aside style={styles.resultsPanel}>
          <h3 style={styles.sectionTitle}>Results</h3>
          {result ? (
            <div style={styles.resultsContent}>
              <div style={styles.summary}>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Defects Found</span>
                  <span style={styles.summaryValue}>{result.defects.length}</span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Processing Time</span>
                  <span style={styles.summaryValue}>{result.processing_time_ms.toFixed(1)} ms</span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Decision</span>
                  <span style={{
                    ...styles.summaryValue,
                    color: result.decision === 'PASS' ? '#22c55e' : '#ef4444',
                    fontWeight: 'bold'
                  }}>
                    {result.decision}
                  </span>
                </div>
              </div>

              {result.defects.length > 0 && (
                <div style={styles.defectsList}>
                  <h4 style={styles.subTitle}>Detected Defects</h4>
                  {result.defects.map((defect, idx) => (
                    <div key={idx} style={styles.defectCard}>
                      <div style={styles.defectHeader}>
                        <span style={{
                          ...styles.classBadge,
                          background: CLASS_COLORS[defect.class_name] || '#ef4444'
                        }}>
                          {defect.class_name}
                        </span>
                        <span style={{
                          ...styles.severityBadge,
                          background: SEVERITY_COLORS[defect.severity] || '#6b7280'
                        }}>
                          {defect.severity}
                        </span>
                      </div>
                      <div style={styles.defectDetails}>
                        <span>Confidence: {(defect.confidence * 100).toFixed(1)}%</span>
                        {defect.area_px && <span>Area: {defect.area_px.toFixed(0)} px²</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {result.defects.length === 0 && (
                <p style={styles.noDefects}>No defects detected — component passes inspection</p>
              )}
            </div>
          ) : (
            <p style={styles.emptyState}>Upload an image and run inspection to see results</p>
          )}
        </aside>
      </main>

      <section style={styles.historySection}>
        <div style={styles.historyHeader}>
          <h3 style={styles.sectionTitle}>Analysis Dashboard</h3>
          <div style={styles.periodTabs}>
            {['7d', 'all'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                style={{
                  ...styles.periodTab,
                  background: period === p ? '#2563eb' : '#fff',
                  color: period === p ? '#fff' : '#374151'
                }}
              >
                {p === '7d' ? 'Last 7 days' : 'All time'}
              </button>
            ))}
          </div>
        </div>

        {analytics ? (
          <div style={styles.analyticsGrid}>
            <div style={styles.kpiRow}>
              <div style={styles.kpiCard}>
                <span style={styles.kpiLabel}>Total Inspections</span>
                <span style={styles.kpiValue}>{analytics.total_inspections}</span>
              </div>
              <div style={styles.kpiCard}>
                <span style={styles.kpiLabel}>Total Defects</span>
                <span style={styles.kpiValue}>{analytics.total_defects}</span>
              </div>
              <div style={styles.kpiCard}>
                <span style={styles.kpiLabel}>Defect Rate</span>
                <span style={styles.kpiValue}>{analytics.defect_rate}/img</span>
              </div>
              <div style={styles.kpiCard}>
                <span style={styles.kpiLabel}>Reject Rate</span>
                <span style={{ ...styles.kpiValue, color: '#ef4444' }}>{analytics.reject_rate}%</span>
              </div>
              <div style={styles.kpiCard}>
                <span style={styles.kpiLabel}>Avg Time</span>
                <span style={styles.kpiValue}>{analytics.avg_processing_time_ms.toFixed(0)} ms</span>
              </div>
            </div>

            <div style={styles.chartCard}>
              <h4 style={styles.subTitle}>Defects by Class</h4>
              <BarChart data={analytics.defects_by_class} />
            </div>

            <div style={styles.chartCard}>
              <h4 style={styles.subTitle}>Defects by Severity</h4>
              <BarChart data={analytics.defects_by_severity} colorScale={SEVERITY_COLORS} />
            </div>

            <div style={styles.chartCard}>
              <h4 style={styles.subTitle}>Confidence Distribution</h4>
              <BarChart data={analytics.confidence_distribution} colors={['#6366f1', '#8b5cf6', '#f59e0b', '#ef4444']} />
            </div>

            <div style={styles.chartCard}>
              <h4 style={styles.subTitle}>PASS / REJECT Decisions</h4>
              <DonutChart data={analytics.decisions} />
            </div>
          </div>
        ) : (
          <p style={styles.emptyState}>Loading analytics...</p>
        )}
      </section>
    </div>
  )
}

function BarChart({ data, colorScale, colors }) {
  const entries = Object.entries(data).filter(([, v]) => v > 0)
  const maxVal = Math.max(...entries.map(([, v]) => Number(v)), 1)

  if (entries.length === 0) {
    return <p style={styles.emptyState}>No data yet</p>
  }

  return (
    <div style={styles.barChart}>
      {entries.map(([label, value], idx) => {
        const color = colors
          ? colors[idx % colors.length]
          : (colorScale ? colorScale[label] : '#2563eb')
        const pct = (Number(value) / maxVal) * 100
        return (
          <div key={label} style={styles.barRow}>
            <span style={styles.barLabel}>{label}</span>
            <div style={styles.barTrack}>
              <div style={{ ...styles.barFill, width: `${pct}%`, background: color || '#2563eb' }} />
            </div>
            <span style={styles.barValue}>{value}</span>
          </div>
        )
      })}
    </div>
  )
}

function DonutChart({ data }) {
  const entries = Object.entries(data).filter(([, v]) => Number(v) > 0)
  const total = entries.reduce((s, [, v]) => s + Number(v), 0) || 1
  const DONUT_COLORS = { PASS: '#22c55e', REJECT: '#ef4444' }

  if (entries.length === 0) {
    return <p style={styles.emptyState}>No data yet</p>
  }

  return (
    <div style={styles.donutWrap}>
      <div style={styles.donut}>
        {entries.map(([label, value], idx) => {
          const pct = (Number(value) / total) * 100
          const color = DONUT_COLORS[label] || '#6b7280'
          return (
            <div
              key={label}
              style={{
                ...styles.donutSlice,
                background: color,
                clipPath: `polygon(50% 50%, ${50 + 50 * Math.cos(2 * Math.PI * idx / entries.length)}% ${50 - 50 * Math.sin(2 * Math.PI * idx / entries.length)}%, ${50 + 50 * Math.cos(2 * Math.PI * (idx + 1) / entries.length)}% ${50 - 50 * Math.sin(2 * Math.PI * (idx + 1) / entries.length)}%)`
              }}
              title={`${label}: ${value} (${pct.toFixed(0)}%)`}
            />
          )
        })}
        <div style={styles.donutCenter}>
          <span style={styles.donutTotal}>{total}</span>
          <span style={styles.donutLabel}>decisions</span>
        </div>
      </div>
      <div style={styles.donutLegend}>
        {entries.map(([label, value]) => (
          <div key={label} style={styles.legendItem}>
            <span style={{ ...styles.legendDot, background: DONUT_COLORS[label] || '#6b7280' }} />
            <span>{label}</span>
            <span style={styles.legendValue}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function CanvasRenderer({ preview, result }) {
  const [canvas, setCanvas] = useState(null)

  useEffect(() => {
    const draw = async () => {
      const c = document.createElement('canvas')
      const ctx = c.getContext('2d')
      const img = new Image()
      img.src = preview
      img.onload = () => {
        c.width = img.width
        c.height = img.height
        ctx.drawImage(img, 0, 0)

        result.defects.forEach((defect) => {
          const [x1, y1, x2, y2] = defect.bbox
          const px1 = x1 * img.width
          const py1 = y1 * img.height
          const px2 = x2 * img.width
          const py2 = y2 * img.height

          const color = CLASS_COLORS[defect.class_name] || '#ef4444'

          if (defect.mask && defect.mask.length > 0) {
            ctx.beginPath()
            ctx.moveTo(defect.mask[0][0], defect.mask[0][1])
            defect.mask.forEach(([x, y]) => ctx.lineTo(x, y))
            ctx.closePath()
            ctx.fillStyle = color + '33'
            ctx.fill()
            ctx.strokeStyle = color
            ctx.lineWidth = 2
            ctx.stroke()
          }

          ctx.strokeStyle = color
          ctx.lineWidth = 3
          ctx.strokeRect(px1, py1, px2 - px1, py2 - py1)

          ctx.fillStyle = color
          ctx.font = '14px sans-serif'
          const label = `${defect.class_name} ${(defect.confidence * 100).toFixed(0)}%`
          ctx.fillText(label, px1, py1 - 5)
        })

        setCanvas(c)
      }
    }
    draw()
  }, [preview, result])

  if (!canvas) return <div style={styles.loadingCanvas}>Rendering...</div>

  return <canvas style={styles.resultCanvas} width={canvas.width} height={canvas.height} ref={(el) => { if (el && canvas) el.replaceWith(canvas) }} />
}

const styles = {
  container: { minHeight: '100vh', background: '#f5f5f5' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', background: '#fff', borderBottom: '1px solid #e5e7eb' },
  title: { fontSize: '20px', fontWeight: '600', color: '#111827' },
  status: { display: 'flex', gap: '12px' },
  badge: { padding: '4px 12px', borderRadius: '9999px', color: '#fff', fontSize: '14px', fontWeight: '500' },
  main: { display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px', padding: '24px', maxWidth: '1400px', margin: '0 auto' },
  uploadSection: { background: '#fff', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  dropZone: { border: '2px dashed #d1d5db', borderRadius: '8px', minHeight: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' },
  fileInput: { position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' },
  previewWrapper: { width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  previewImg: { maxWidth: '100%', maxHeight: '300px', borderRadius: '4px' },
  canvasWrapper: { width: '100%', height: '100%' },
  uploadPrompt: { textAlign: 'center', color: '#6b7280' },
  hint: { fontSize: '14px', marginTop: '8px' },
  actions: { display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' },
  button: { padding: '12px 24px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '16px', fontWeight: '500', cursor: 'pointer', transition: 'background 0.2s' },
  error: { color: '#ef4444', fontSize: '14px' },
  resultsPanel: { background: '#fff', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', height: 'fit-content', maxHeight: 'calc(100vh - 120px)', overflow: 'auto' },
  sectionTitle: { fontSize: '16px', fontWeight: '600', color: '#111827', marginBottom: '16px' },
  resultsContent: { display: 'flex', flexDirection: 'column', gap: '16px' },
  summary: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', padding: '16px', background: '#f9fafb', borderRadius: '8px' },
  summaryItem: { display: 'flex', flexDirection: 'column', gap: '4px' },
  summaryLabel: { fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' },
  summaryValue: { fontSize: '18px', fontWeight: '600', color: '#111827' },
  defectsList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  subTitle: { fontSize: '14px', fontWeight: '600', color: '#374151' },
  defectCard: { padding: '12px', background: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' },
  defectHeader: { display: 'flex', gap: '8px', marginBottom: '8px' },
  classBadge: { padding: '2px 8px', borderRadius: '4px', color: '#fff', fontSize: '12px', fontWeight: '500' },
  severityBadge: { padding: '2px 8px', borderRadius: '4px', color: '#fff', fontSize: '12px', fontWeight: '500' },
  defectDetails: { display: 'flex', gap: '16px', fontSize: '13px', color: '#4b5563' },
  noDefects: { textAlign: 'center', padding: '24px', color: '#22c55e', fontWeight: '500' },
  emptyState: { textAlign: 'center', padding: '24px', color: '#6b7280' },
  historySection: { padding: '24px', maxWidth: '1400px', margin: '0 auto' },
  historyHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  periodTabs: { display: 'flex', gap: '8px' },
  periodTab: { padding: '6px 16px', borderRadius: '6px', border: '1px solid #d1d5db', cursor: 'pointer', fontSize: '13px', fontWeight: '500' },
  analyticsGrid: { display: 'flex', flexDirection: 'column', gap: '16px' },
  kpiRow: { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' },
  kpiCard: { background: '#fff', borderRadius: '10px', padding: '16px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', gap: '6px' },
  kpiLabel: { fontSize: '11px', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' },
  kpiValue: { fontSize: '22px', fontWeight: '700', color: '#111827' },
  chartCard: { background: '#fff', borderRadius: '10px', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', gap: '12px' },
  barChart: { display: 'flex', flexDirection: 'column', gap: '10px' },
  barRow: { display: 'grid', gridTemplateColumns: '140px 1fr 40px', alignItems: 'center', gap: '12px' },
  barLabel: { fontSize: '13px', color: '#374151', textTransform: 'capitalize' },
  barTrack: { background: '#f3f4f6', borderRadius: '4px', height: '22px', overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: '4px', transition: 'width 0.4s ease' },
  barValue: { fontSize: '13px', fontWeight: '600', color: '#111827', textAlign: 'right' },
  donutWrap: { display: 'flex', alignItems: 'center', gap: '24px', justifyContent: 'center' },
  donut: { position: 'relative', width: '140px', height: '140px', borderRadius: '50%', background: '#f3f4f6', flexShrink: 0 },
  donutSlice: { position: 'absolute', inset: 0, borderRadius: '50%' },
  donutCenter: { position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' },
  donutTotal: { fontSize: '24px', fontWeight: '700', color: '#111827' },
  donutLabel: { fontSize: '11px', color: '#6b7280' },
  donutLegend: { display: 'flex', flexDirection: 'column', gap: '10px' },
  legendItem: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#374151' },
  legendDot: { width: '10px', height: '10px', borderRadius: '50%' },
  legendValue: { fontWeight: '600', color: '#111827', marginLeft: 'auto' },
  loadingCanvas: { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', color: '#6b7280' },
  resultCanvas: { maxWidth: '100%', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }
}

export default App