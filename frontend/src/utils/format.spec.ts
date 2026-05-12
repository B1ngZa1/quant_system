import { describe, it, expect } from 'vitest'
import {
  formatMoney,
  formatNumber,
  formatVolume,
  formatPercent,
  getChangeColor,
  formatDate,
} from './format'

describe('formatMoney', () => {
  it('formats positive amount', () => {
    const result = formatMoney(1234.56)
    expect(result).toContain('1,234.56')
  })

  it('returns dash for null', () => {
    expect(formatMoney(null as unknown as number)).toBe('-')
  })

  it('returns dash for undefined', () => {
    expect(formatMoney(undefined as unknown as number)).toBe('-')
  })

  it('formats zero', () => {
    const result = formatMoney(0)
    expect(result).toContain('0.00')
  })
})

describe('formatNumber', () => {
  it('formats integer', () => {
    const result = formatNumber(12345)
    expect(result).toContain('12,345')
  })

  it('formats with decimals', () => {
    const result = formatNumber(12345.678, 2)
    expect(result).toContain('12,345.68')
  })

  it('returns dash for null', () => {
    expect(formatNumber(null as unknown as number)).toBe('-')
  })
})

describe('formatVolume', () => {
  it('formats 亿 for large volume', () => {
    const result = formatVolume(150000000)
    expect(result).toContain('亿')
  })

  it('formats 万 for medium volume', () => {
    const result = formatVolume(50000)
    expect(result).toContain('万')
  })

  it('formats small volume as string', () => {
    const result = formatVolume(500)
    expect(result).toBe('500')
  })
})

describe('formatPercent', () => {
  it('formats positive with + sign', () => {
    const result = formatPercent(0.0523)
    expect(result).toBe('+5.23%')
  })

  it('formats negative without extra sign', () => {
    const result = formatPercent(-0.031)
    expect(result).toBe('-3.10%')
  })

  it('formats without sign when withSign is false', () => {
    const result = formatPercent(0.05, 2, false)
    expect(result).toBe('5.00%')
  })

  it('returns dash for null', () => {
    expect(formatPercent(null as unknown as number)).toBe('-')
  })
})

describe('getChangeColor', () => {
  it('returns up for positive', () => {
    expect(getChangeColor(0.05)).toBe('up')
  })

  it('returns down for negative', () => {
    expect(getChangeColor(-0.02)).toBe('down')
  })

  it('returns neutral for zero', () => {
    expect(getChangeColor(0)).toBe('neutral')
  })
})

describe('formatDate', () => {
  it('formats date string to YYYY-MM-DD', () => {
    const result = formatDate('2024-01-15')
    expect(result).toBe('2024-01-15')
  })

  it('formats with HH:mm', () => {
    const d = new Date('2024-01-15T14:30:00')
    const result = formatDate(d, 'YYYY-MM-DD HH:mm')
    expect(result).toBe('2024-01-15 14:30')
  })

  it('returns dash for empty input', () => {
    expect(formatDate('')).toBe('-')
  })

  it('returns dash for null', () => {
    expect(formatDate(null as unknown as string)).toBe('-')
  })
})
