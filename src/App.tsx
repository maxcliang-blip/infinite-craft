import { useState, useMemo } from 'react'
import type { Element } from './types'
import { baseElements, findRecipe } from './recipes'
import './App.css'

function App() {
  const [discovered, setDiscovered] = useState<Element[]>(baseElements)
  const [slot1, setSlot1] = useState<Element | null>(null)
  const [slot2, setSlot2] = useState<Element | null>(null)
  const [result, setResult] = useState<Element | null>(null)
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return discovered.filter(
      (el) => el.name.toLowerCase().includes(q) || el.id.includes(q)
    )
  }, [discovered, search])

  function handleSelect(el: Element) {
    if (!slot1) {
      setSlot1(el)
    } else if (!slot2) {
      setSlot2(el)
    } else {
      setSlot1(el)
      setSlot2(null)
      setResult(null)
    }
  }

  function handleCombine() {
    if (!slot1 || !slot2) return

    const newElement = findRecipe(slot1.id, slot2.id)

    if (newElement) {
      setResult(newElement)
      setDiscovered((prev) => {
        if (prev.some((el) => el.id === newElement.id)) return prev
        return [...prev, newElement]
      })
    } else {
      setResult({ id: 'nothing', name: 'Nothing', emoji: '💨' })
    }
  }

  function handleClear() {
    setSlot1(null)
    setSlot2(null)
    setResult(null)
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Elements</h2>
          <span className="count">{discovered.length}</span>
        </div>
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search"
        />
        <div className="element-list">
          {filtered.map((el) => (
            <button
              key={el.id}
              className={`element-chip ${slot1?.id === el.id || slot2?.id === el.id ? 'selected' : ''}`}
              onClick={() => handleSelect(el)}
            >
              <span className="emoji">{el.emoji}</span>
              <span className="name">{el.name}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="workspace">
        <h1>Infinite Craft</h1>

        <div className="crafting-area">
          <div className="slots">
            <div className={`slot ${slot1 ? 'filled' : ''}`} onClick={() => { setSlot1(null); setResult(null) }}>
              {slot1 ? (
                <>
                  <span className="emoji">{slot1.emoji}</span>
                  <span className="name">{slot1.name}</span>
                </>
              ) : (
                <span className="placeholder">Select element</span>
              )}
            </div>

            <span className="plus">+</span>

            <div className={`slot ${slot2 ? 'filled' : ''}`} onClick={() => { setSlot2(null); setResult(null) }}>
              {slot2 ? (
                <>
                  <span className="emoji">{slot2.emoji}</span>
                  <span className="name">{slot2.name}</span>
                </>
              ) : (
                <span className="placeholder">Select element</span>
              )}
            </div>
          </div>

          <div className="actions">
            <button
              className="combine-btn"
              disabled={!slot1 || !slot2}
              onClick={handleCombine}
            >
              Combine
            </button>
            <button className="clear-btn" onClick={handleClear}>
              Clear
            </button>
          </div>

          {result && (
            <div className={`result ${result.id === 'nothing' ? 'fail' : 'success'}`}>
              <span className="emoji">{result.emoji}</span>
              <span className="name">{result.name}</span>
              {result.id !== 'nothing' && (
                <span className="new-badge">New!</span>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
