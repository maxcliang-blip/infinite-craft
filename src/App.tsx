import { useState, useRef, useCallback, useEffect } from 'react'
import type { Element } from './types'
import { baseElements, findRecipe } from './recipes'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || ''

const DISCOVERED_KEY = 'infinite-craft-discovered'

interface WorkspaceElement {
  id: string
  element: Element
  x: number
  y: number
}

interface AiResult {
  name: string
  emoji: string
  id: string
}

function App() {
  const [discovered, setDiscovered] = useState<Element[]>(() => {
    try {
      const saved = localStorage.getItem(DISCOVERED_KEY)
      if (saved) {
        const parsed = JSON.parse(saved) as Element[]
        if (parsed.length > 0) return parsed
      }
    } catch {}
    return baseElements
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [workspaceElements, setWorkspaceElements] = useState<WorkspaceElement[]>([])
  const [dragging, setDragging] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [combining, setCombining] = useState<string | null>(null)
  const [showChangelog, setShowChangelog] = useState(false)
  const workspaceRef = useRef<HTMLDivElement>(null)
  const nextId = useRef(0)
  const draggingRef = useRef<string | null>(null)
  const dragOffsetRef = useRef({ x: 0, y: 0 })
  const dragElRef = useRef<HTMLElement | null>(null)

  const addElement = useCallback((element: Element, x: number, y: number) => {
    const wEl: WorkspaceElement = {
      id: `w-${nextId.current++}`,
      element,
      x,
      y,
    }
    setWorkspaceElements((prev) => [...prev, wEl])
  }, [])

  const callAiCombine = useCallback(async (first: Element, second: Element): Promise<AiResult | null> => {
    try {
      const resp = await fetch(`${API_URL}/api/combine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first: first.name, second: second.name }),
      })

      if (!resp.ok) return null
      return await resp.json()
    } catch {
      return null
    }
  }, [])

  const handleMouseDown = useCallback((e: React.MouseEvent, wElId: string) => {
    e.stopPropagation()
    const el = workspaceElements.find((w) => w.id === wElId)
    if (!el) return

    const offsetX = e.clientX - el.x
    const offsetY = e.clientY - el.y

    draggingRef.current = wElId
    dragOffsetRef.current = { x: offsetX, y: offsetY }
    setDragging(wElId)

    const domEl = document.querySelector(`.workspace-element[data-id="${wElId}"]`) as HTMLElement
    if (domEl) {
      dragElRef.current = domEl
      domEl.style.transition = 'none'
      domEl.style.willChange = 'transform'
      domEl.style.zIndex = '100'
    }
  }, [workspaceElements])

  useEffect(() => {
    let mouseX = 0
    let mouseY = 0

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX
      mouseY = e.clientY
      if (!draggingRef.current || !dragElRef.current) return
      const orig = workspaceElements.find(w => w.id === draggingRef.current)
      if (!orig) return
      const dx = e.clientX - dragOffsetRef.current.x - orig.x
      const dy = e.clientY - dragOffsetRef.current.y - orig.y
      dragElRef.current.style.transform = `translate(${dx}px, ${dy}px)`
    }

    const handleMouseUp = async () => {
      const wElId = draggingRef.current
      if (!wElId) {
        draggingRef.current = null
        dragElRef.current = null
        setDragging(null)
        return
      }

      const dragged = workspaceElements.find((w) => w.id === wElId)
      if (!dragged) {
        draggingRef.current = null
        dragElRef.current = null
        setDragging(null)
        return
      }

      const finalX = mouseX - dragOffsetRef.current.x
      const finalY = mouseY - dragOffsetRef.current.y

      const draggedCenter = { x: finalX + 50, y: finalY + 20 }

      let closest: WorkspaceElement | null = null
      let closestDist = Infinity

      for (const other of workspaceElements) {
        if (other.id === wElId) continue
        const otherCenter = { x: other.x + 50, y: other.y + 20 }
        const dist = Math.sqrt(
          (draggedCenter.x - otherCenter.x) ** 2 +
          (draggedCenter.y - otherCenter.y) ** 2
        )
        if (dist < 60 && dist < closestDist) {
          closest = other
          closestDist = dist
        }
      }

      if (closest) {
        setCombining(wElId)

        let result: AiResult | null = null
        const aiResult = await callAiCombine(dragged.element, closest.element)

        if (aiResult) {
          result = aiResult
        } else {
          const staticResult = findRecipe(dragged.element.id, closest.element.id)
          if (staticResult) {
            result = { name: staticResult.name, emoji: staticResult.emoji, id: staticResult.id }
          }
        }

        if (result) {
          const midX = (dragged.x + closest.x) / 2
          const midY = (dragged.y + closest.y) / 2

          setWorkspaceElements((prev) =>
            prev.filter((w) => w.id !== wElId && w.id !== closest!.id)
          )

          addElement({ name: result.name, emoji: result.emoji, id: result.id }, midX, midY)

          setDiscovered((prev) => {
            if (prev.some((el) => el.id === result!.id)) return prev
            return [...prev, { name: result!.name, emoji: result!.emoji, id: result!.id }]
          })
        }

        setCombining(null)
      } else {
        if (!workspaceRef.current) return
        const rect = workspaceRef.current.getBoundingClientRect()
        const margin = 200
        if (
          finalY < -margin ||
          finalY > rect.height + margin ||
          finalX < -margin - (sidebarOpen ? 200 : 0) ||
          finalX > rect.width + margin
        ) {
          setWorkspaceElements((prev) => prev.filter((w) => w.id !== wElId))
        }
      }

      draggingRef.current = null
      dragElRef.current = null
      setDragging(null)
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    window.addEventListener('mouseup', handleMouseUp)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [workspaceElements, callAiCombine, addElement, sidebarOpen])

  const handleSidebarDragStart = useCallback((e: React.DragEvent, el: Element) => {
    e.dataTransfer.setData('application/json', JSON.stringify(el))
    e.dataTransfer.effectAllowed = 'copy'
  }, [])

  const handleSidebarDragEnd = useCallback(() => {}, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()

    const data = e.dataTransfer.getData('application/json')
    if (!data) return

    const el: Element = JSON.parse(data)
    if (!workspaceRef.current) return

    const rect = workspaceRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left - 50
    const y = e.clientY - rect.top - 20
    addElement(el, x, y)
  }, [addElement])

  const handleDoubleClick = useCallback((e: React.MouseEvent, wElId: string) => {
    e.stopPropagation()
    const wEl = workspaceElements.find((w) => w.id === wElId)
    if (!wEl) return
    addElement({ ...wEl.element }, wEl.x + 20, wEl.y + 20)
  }, [workspaceElements, addElement])

  return (
    <div className="app">
      <header className="header">
        <h1>Infinite Craft</h1>
        <div className="header-right">
          <span className="discovery-count">{discovered.length} / ???</span>
          <button className="header-btn" onClick={() => setShowChangelog(true)}>
            Changelog
          </button>
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? '✕' : '☰'}
          </button>
        </div>
      </header>

      {sidebarOpen && (
        <div className="sidebar">
          <div className="sidebar-search">
            <input
              type="text"
              className="search-input"
              placeholder="Search elements..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="sidebar-content">
            {discovered
              .filter((el) =>
                el.name.toLowerCase().includes(searchQuery.toLowerCase())
              )
              .map((el) => (
                <div
                  key={el.id}
                  className="sidebar-element"
                  draggable
                  onDragStart={(e) => handleSidebarDragStart(e, el)}
                  onDragEnd={handleSidebarDragEnd}
                >
                  <span className="emoji">{el.emoji}</span>
                  <span className="name">{el.name}</span>
                </div>
              ))}
            {searchQuery && discovered.filter((el) =>
              el.name.toLowerCase().includes(searchQuery.toLowerCase())
            ).length === 0 && (
              <div className="no-results">No elements found</div>
            )}
          </div>
        </div>
      )}

      <div
        className="workspace"
        ref={workspaceRef}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{ marginRight: sidebarOpen ? 200 : 0 }}
      >
        {workspaceElements.map((wEl) => (
          <div
            key={wEl.id}
            data-id={wEl.id}
            className={`workspace-element ${dragging === wEl.id ? 'dragging' : ''} ${combining === wEl.id ? 'combining' : ''}`}
            style={{ left: wEl.x, top: wEl.y, zIndex: dragging === wEl.id ? 100 : 1 }}
            onMouseDown={(e) => handleMouseDown(e, wEl.id)}
            onDoubleClick={(e) => handleDoubleClick(e, wEl.id)}
          >
            <span className="emoji">{wEl.element.emoji}</span>
            <span className="name">{wEl.element.name}</span>
          </div>
        ))}

        {workspaceElements.length === 0 && (
          <div className="workspace-hint">
            Drag an element here to start crafting
          </div>
        )}
      </div>

      {workspaceElements.length > 0 && (
        <button className="clear-all" onClick={() => setWorkspaceElements([])}>
          Clear all
        </button>
      )}

      {showChangelog && (
        <div className="overlay" onClick={() => setShowChangelog(false)}>
          <div className="changelog" onClick={(e) => e.stopPropagation()}>
            <div className="changelog-header">
              <h2>Changelog</h2>
              <button className="close-btn" onClick={() => setShowChangelog(false)}>✕</button>
            </div>
            <div className="changelog-body">
              <div className="changelog-version">
                <span className="version-tag">v1.2.3</span>
                <span className="version-date">2026-06-03</span>
              </div>
              <div className="changelog-section">
                <h3>Dragging Improvements</h3>
                <ul>
                  <li>Direct DOM manipulation — no React re-renders during drag</li>
                  <li>GPU-accelerated via CSS transform</li>
                  <li>Window-level mouse tracking for consistent movement</li>
                  <li>Smoother shadow and cursor transitions</li>
                </ul>
              </div>

              <div className="changelog-version changelog-version-prev">
                <span className="version-tag">v1.2.2</span>
                <span className="version-date">2026-06-03</span>
              </div>
              <div className="changelog-section">
                <h3>Frontend</h3>
                <ul>
                  <li>React + TypeScript app with Vite</li>
                  <li>Drag-and-drop elements from sidebar to workspace</li>
                  <li>Drag elements on canvas to combine them</li>
                  <li>Double-click to duplicate elements</li>
                  <li>Collapsible sidebar</li>
                </ul>
              </div>
              <div className="changelog-section">
                <h3>Backend</h3>
                <ul>
                  <li>FastAPI + OpenRouter AI for dynamic element generation</li>
                  <li>SQLite database for persistent recipe caching</li>
                  <li>47 static recipes for instant responses</li>
                  <li>AI results cached — subsequent combos are instant</li>
                </ul>
              </div>
              <div className="changelog-section">
                <h3>Game</h3>
                <ul>
                  <li>4 base elements: Water, Fire, Earth, Wind</li>
                  <li>Infinite AI-powered combinations</li>
                  <li>Element discovery tracking</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
