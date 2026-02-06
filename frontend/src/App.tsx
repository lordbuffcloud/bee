import { useEffect, useState } from 'react'

type Status = {
  heartbeat_running: boolean
  heartbeat_interval_sec: number
  risk_tolerance: number
  memory_goals: {
    goals: string[]
    before_tick: string | null
    tick_state: string | null
    after_tick: string | null
  }
  personality_summary: string
  evermem_enabled: boolean
  evermem_endpoint?: string | null
  evermem_group_id?: string | null
  last_tick?: string | null
}

export default function App() {
  const [status, setStatus] = useState<Status | null>(null)
  const [goals, setGoals] = useState<string[]>(['', '', ''])
  const [risk, setRisk] = useState(5)
  const [memoryQuery, setMemoryQuery] = useState('')
  const [memoryResults, setMemoryResults] = useState<any[]>([])
  const [memoryError, setMemoryError] = useState<string | null>(null)
  const [memoryLoading, setMemoryLoading] = useState(false)

  useEffect(() => {
    fetch('/api/status')
      .then((res) => res.json())
      .then((data) => {
        setStatus(data)
        setRisk(data.risk_tolerance)
        if (data.memory_goals?.goals?.length === 3) {
          setGoals(data.memory_goals.goals)
        }
      })
      .catch(() => null)
  }, [])

  const saveGoals = async () => {
    await fetch('/api/memory/goals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goals })
    })
  }

  const updateRisk = async () => {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ risk_tolerance: risk })
    })
  }

  const toggleHeartbeat = async () => {
    if (!status) return
    const endpoint = status.heartbeat_running ? '/api/heartbeat/stop' : '/api/heartbeat/start'
    await fetch(endpoint, { method: 'POST' })
    const next = await fetch('/api/status').then((res) => res.json())
    setStatus(next)
  }

  const searchMemory = async () => {
    if (!memoryQuery.trim()) return
    setMemoryLoading(true)
    setMemoryError(null)
    try {
      const res = await fetch('/api/evermem/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_query: memoryQuery, result_limit: 6 })
      })
      const data = await res.json()
      if (!data.ok) {
        throw new Error('Search failed')
      }
      const list = data.result?.memory_list ?? []
      setMemoryResults(Array.isArray(list) ? list : [])
    } catch (err) {
      setMemoryError('Unable to query EvermemOS right now.')
    } finally {
      setMemoryLoading(false)
    }
  }

  const lastTickLabel = status?.last_tick
    ? new Date(status.last_tick).toLocaleString()
    : 'Never'

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Binary Executive Engine</p>
          <h1>B.E.E. Hive Manager</h1>
          <p className="subtitle">
            Telegram-first agent with heartbeat, EvermemOS goals, and swarm-ready cognition.
          </p>
        </div>
        <div className="badge">Bee Core</div>
      </header>

      <section className="panel">
        <h2>Onboarding</h2>
        <ol className="steps">
          <li>Connect Telegram by setting `TELEGRAM_BOT_TOKEN` in `.env`.</li>
          <li>Provide `OPENAI_API_KEY` for the main model.</li>
          <li>Provide `ELEVENLABS_API_KEY` for voice output.</li>
        </ol>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Heartbeat</h2>
          <p className="meta">Interval: {status?.heartbeat_interval_sec ?? '?'} seconds</p>
          <p className="meta">Last tick: {lastTickLabel}</p>
          <button className="primary" onClick={toggleHeartbeat}>
            {status?.heartbeat_running ? 'Pause' : 'Start'} heartbeat
          </button>
        </div>

        <div className="panel">
          <h2>Risk Tolerance</h2>
          <p className="meta">1 = conservative, 10 = aggressive</p>
          <input
            type="range"
            min={1}
            max={10}
            value={risk}
            onChange={(e) => setRisk(Number(e.target.value))}
          />
          <button className="ghost" onClick={updateRisk}>Save risk level</button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>EvermemOS</h2>
          <span className={`status-pill ${status?.evermem_enabled ? 'ok' : 'off'}`}>
            {status?.evermem_enabled ? 'Connected' : 'Disabled'}
          </span>
        </div>
        <p className="meta">Endpoint: {status?.evermem_endpoint ?? 'Not configured'}</p>
        <p className="meta">Group: {status?.evermem_group_id ?? 'Default'}</p>
      </section>

      <section className="panel">
        <h2>Directive Goals (3)</h2>
        <div className="goals">
          {goals.map((goal, idx) => (
            <input
              key={idx}
              value={goal}
              placeholder={`Goal ${idx + 1}`}
              onChange={(e) => {
                const next = [...goals]
                next[idx] = e.target.value
                setGoals(next)
              }}
            />
          ))}
        </div>
        <button className="primary" onClick={saveGoals}>Save goals</button>
      </section>

      <section className="panel">
        <h2>Personality</h2>
        <p className="meta">{status?.personality_summary ?? 'Loading personality...'}</p>
      </section>

      <section className="panel">
        <h2>Memory Search</h2>
        <div className="form-row">
          <input
            type="text"
            placeholder="Search your EvermemOS memories"
            value={memoryQuery}
            onChange={(e) => setMemoryQuery(e.target.value)}
          />
          <button className="ghost" onClick={searchMemory} disabled={memoryLoading}>
            {memoryLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        {memoryError && <p className="error">{memoryError}</p>}
        <div className="memory-list">
          {memoryResults.map((item, idx) => (
            <article key={idx} className="memory-card">
              <h3>{item.title ?? `Memory ${idx + 1}`}</h3>
              <p>{item.content ?? 'No content returned.'}</p>
              {item.create_time && (
                <span className="stamp">
                  {new Date(item.create_time).toLocaleString()}
                </span>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
