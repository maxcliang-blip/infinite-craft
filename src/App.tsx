import { useState, useRef, useCallback, useEffect } from 'react'
import type { Element } from './types'
import { baseElements, findRecipe } from './recipes'
import './App.css'

interface WorkspaceElement {
  id: string
  element: Element
  x: number
  y: number
}

function App() {
  const [discovered, setDiscovered] = useState<Element[]>(baseElements)
  const [workspaceElements, setWorkspaceElements] = useState<WorkspaceElement[]>([])
  const [dragging, setDragging] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const workspaceRef = useRef<HTMLDivElement>(null)
  const nextId = useRef(0)

  const addElement = useCallback((element: Element, x: number, y: number) => {
    const wEl: WorkspaceElement = {
      id: `w-${nextId.current++}`,
      element,
      x,
      y,
    }
    setWorkspaceElements((prev) => [...prev, wEl])
  }, [])

  const handleMouseDown = useCallback((e: React.MouseEvent, wElId: string) => {
    e.stopPropagation()
    e.preventDefault()
    const el = workspaceElements.find((w) => w.id === wElId)
    if (!el) return
    setDragging(wElId)
    setDragOffset({ x: e.clientX - el.x, y: e.clientY - el.y })
  }, [workspaceElements])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging) return
    setWorkspaceElements((prev) =>
      prev.map((w) =>
        w.id === dragging
          ? { ...w, x: e.clientX - dragOffset.x, y: e.clientY - dragOffset.y }
          : w
      )
    )
  }, [dragging, dragOffset])

  const combineElements = useCallback((draggedId: string, targetId: string) => {
    const dragged = workspaceElements.find((w) => w.id === draggedId)
    const target = workspaceElements.find((w) => w.id === targetId)
    if (!dragged || !target) return

    const result = findRecipe(dragged.element.id, target.element.id)
    if (result) {
      const midX = (dragged.x + target.x) / 2
      const midY = (dragged.y + target.y) / 2

      setWorkspaceElements((prev) =>
        prev.filter((w) => w.id !== draggedId && w.id !== targetId)
      )

      addElement(result, midX, midY)

      setDiscovered((prev) => {
        if (prev.some((el) => el.id === result.id)) return prev
        return [...prev, result]
      })
    }
  }, [workspaceElements, addElement])

  const handleMouseUp = useCallback(() => {
    if (!dragging || !workspaceRef.current) {
      setDragging(null)
      return
    }

    const dragged = workspaceElements.find((w) => w.id === dragging)
    if (!dragged) {
      setDragging(null)
      return
    }

    const draggedCenter = { x: dragged.x + 50, y: dragged.y + 20 }

    let closest: WorkspaceElement | null = null
    let closestDist = Infinity

    for (const other of workspaceElements) {
      if (other.id === dragging) continue
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
      combineElements(dragging, closest.id)
    } else {
      const rect = workspaceRef.current.getBoundingClientRect()
      const margin = 200
      if (
        dragged.y < -margin ||
        dragged.y > rect.height + margin ||
        dragged.x < -margin - (sidebarOpen ? 200 : 0) ||
        dragged.x > rect.width + margin
      ) {
        setWorkspaceElements((prev) => prev.filter((w) => w.id !== dragging))
      }
    }

    setDragging(null)
  }, [dragging, workspaceElements, combineElements, sidebarOpen])

  useEffect(() => {
    function handleGlobalMouseUp() {
      if (dragging) handleMouseUp()
    }
    window.addEventListener('mouseup', handleGlobalMouseUp)
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp)
  }, [dragging, handleMouseUp])

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
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? '✕' : '☰'}
          </button>
        </div>
      </header>

      {sidebarOpen && (
        <div className="sidebar">
          <div className="sidebar-content">
            {discovered.map((el) => (
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
          </div>
        </div>
      )}

      <div
        className="workspace"
        ref={workspaceRef}
        onMouseMove={handleMouseMove}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{ marginRight: sidebarOpen ? 200 : 0 }}
      >
        {workspaceElements.map((wEl) => (
          <div
            key={wEl.id}
            className={`workspace-element ${dragging === wEl.id ? 'dragging' : ''}`}
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
    </div>
  )
}

export default App
