import { describe, it, expect, beforeEach } from 'vitest'
import { storage } from './storage'

describe('storage.local', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('sets and gets a value', () => {
    storage.local.set('test-key', { name: 'test' })
    const result = storage.local.get('test-key')
    expect(result).toEqual({ name: 'test' })
  })

  it('returns default value for missing key', () => {
    const result = storage.local.get('nonexistent', 'default')
    expect(result).toBe('default')
  })

  it('returns null default when not specified', () => {
    const result = storage.local.get('nonexistent')
    expect(result).toBeNull()
  })

  it('removes a key', () => {
    storage.local.set('test-key', 'value')
    storage.local.remove('test-key')
    expect(storage.local.get('test-key')).toBeNull()
  })

  it('clears all keys', () => {
    storage.local.set('key1', 'a')
    storage.local.set('key2', 'b')
    storage.local.clear()
    expect(storage.local.get('key1')).toBeNull()
    expect(storage.local.get('key2')).toBeNull()
  })

  it('handles JSON parse errors gracefully', () => {
    localStorage.setItem('bad-json', '{invalid')
    const result = storage.local.get('bad-json', 'fallback')
    expect(result).toBe('fallback')
  })
})

describe('storage.session', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('sets and gets a value', () => {
    storage.session.set('session-key', 123)
    expect(storage.session.get('session-key')).toBe(123)
  })

  it('returns default value for missing key', () => {
    expect(storage.session.get('missing', [])).toEqual([])
  })

  it('removes a key', () => {
    storage.session.set('session-key', 'val')
    storage.session.remove('session-key')
    expect(storage.session.get('session-key')).toBeNull()
  })
})
