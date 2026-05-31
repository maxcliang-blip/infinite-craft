export interface Element {
  id: string
  name: string
  emoji: string
}

export interface Recipe {
  first: string
  second: string
  result: Element
}
