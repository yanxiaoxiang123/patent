import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Global mock for localStorage
vi.stubGlobal('localStorage', {
  getItem: vi.fn((key: string) => {
    if (key === 'token') return 'mock_token'
    return null
  }),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
})

// Global mock for sessionStorage
vi.stubGlobal('sessionStorage', {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
})

// Mock window.matchMedia
vi.stubGlobal('matchMedia', vi.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn()
})))

// Mock ResizeObserver
vi.stubGlobal('ResizeObserver', vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
})))

// Mock fetch
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  body: null,
  headers: new Headers(),
  json: () => Promise.resolve({ success: true }),
  text: () => Promise.resolve('[DONE]')
})
