import type { Element, Recipe } from './types'

export const baseElements: Element[] = [
  { id: 'water', name: 'Water', emoji: '💧' },
  { id: 'fire', name: 'Fire', emoji: '🔥' },
  { id: 'earth', name: 'Earth', emoji: '🌍' },
  { id: 'wind', name: 'Wind', emoji: '💨' },
]

export const recipes: Recipe[] = [
  { first: 'water', second: 'fire', result: { id: 'steam', name: 'Steam', emoji: '♨️' } },
  { first: 'water', second: 'earth', result: { id: 'mud', name: 'Mud', emoji: '💩' } },
  { first: 'water', second: 'wind', result: { id: 'wave', name: 'Wave', emoji: '🌊' } },
  { first: 'fire', second: 'earth', result: { id: 'lava', name: 'Lava', emoji: '🌋' } },
  { first: 'fire', second: 'wind', result: { id: 'smoke', name: 'Smoke', emoji: '💨' } },
  { first: 'earth', second: 'wind', result: { id: 'dust', name: 'Dust', emoji: '✨' } },

  { first: 'water', second: 'steam', result: { id: 'cloud', name: 'Cloud', emoji: '☁️' } },
  { first: 'fire', second: 'water', result: { id: 'steam', name: 'Steam', emoji: '♨️' } },
  { first: 'steam', second: 'wind', result: { id: 'cloud', name: 'Cloud', emoji: '☁️' } },
  { first: 'cloud', second: 'water', result: { id: 'rain', name: 'Rain', emoji: '🌧️' } },
  { first: 'cloud', second: 'fire', result: { id: 'thunder', name: 'Thunder', emoji: '⚡' } },
  { first: 'rain', second: 'fire', result: { id: 'thunder', name: 'Thunder', emoji: '⚡' } },
  { first: 'rain', second: 'earth', result: { id: 'plant', name: 'Plant', emoji: '🌱' } },
  { first: 'plant', second: 'earth', result: { id: 'tree', name: 'Tree', emoji: '🌳' } },
  { first: 'plant', second: 'water', result: { id: 'algae', name: 'Algae', emoji: '🌿' } },
  { first: 'plant', second: 'fire', result: { id: 'ash', name: 'Ash', emoji: '🌫️' } },
  { first: 'tree', second: 'fire', result: { id: 'ash', name: 'Ash', emoji: '🌫️' } },
  { first: 'tree', second: 'earth', result: { id: 'forest', name: 'Forest', emoji: '🌲' } },
  { first: 'tree', second: 'tree', result: { id: 'forest', name: 'Forest', emoji: '🌲' } },

  { first: 'mud', second: 'fire', result: { id: 'brick', name: 'Brick', emoji: '🧱' } },
  { first: 'mud', second: 'wind', result: { id: 'dust', name: 'Dust', emoji: '✨' } },
  { first: 'lava', second: 'water', result: { id: 'obsidian', name: 'Obsidian', emoji: '⬛' } },
  { first: 'lava', second: 'earth', result: { id: 'volcano', name: 'Volcano', emoji: '🌋' } },
  { first: 'lava', second: 'wind', result: { id: 'obsidian', name: 'Obsidian', emoji: '⬛' } },
  { first: 'dust', second: 'fire', result: { id: 'gunpowder', name: 'Gunpowder', emoji: '💥' } },
  { first: 'dust', second: 'water', result: { id: 'mud', name: 'Mud', emoji: '💩' } },

  { first: 'obsidian', second: 'earth', result: { id: 'mountain', name: 'Mountain', emoji: '⛰️' } },
  { first: 'mountain', second: 'mountain', result: { id: 'mountain_range', name: 'Mountain Range', emoji: '🏔️' } },
  { first: 'ash', second: 'water', result: { id: 'mud', name: 'Mud', emoji: '💩' } },
  { first: 'ash', second: 'earth', result: { id: 'soil', name: 'Soil', emoji: '🌾' } },

  { first: 'brick', second: 'brick', result: { id: 'wall', name: 'Wall', emoji: '🧱' } },
  { first: 'wall', second: 'wall', result: { id: 'house', name: 'House', emoji: '🏠' } },
  { first: 'house', second: 'plant', result: { id: 'garden', name: 'Garden', emoji: '🏡' } },

  { first: 'wave', second: 'earth', result: { id: 'island', name: 'Island', emoji: '🏝️' } },
  { first: 'wave', second: 'wave', result: { id: 'ocean', name: 'Ocean', emoji: '🌊' } },
  { first: 'ocean', second: 'fire', result: { id: 'fog', name: 'Fog', emoji: '🌫️' } },

  { first: 'plant', second: 'plant', result: { id: 'forest', name: 'Forest', emoji: '🌲' } },
  { first: 'algae', second: 'fire', result: { id: 'smoke', name: 'Smoke', emoji: '💨' } },
]

export function findRecipe(a: string, b: string): Element | null {
  const recipe = recipes.find(
    (r) =>
      (r.first === a && r.second === b) || (r.first === b && r.second === a)
  )
  return recipe?.result ?? null
}

export function normalizeId(id: string): string {
  return id.toLowerCase().replace(/\s+/g, '_')
}
