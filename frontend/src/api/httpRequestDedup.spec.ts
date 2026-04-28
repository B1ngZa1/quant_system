import { describe, it, expect } from 'vitest'
import { buildRequestKey } from './httpRequestDedup'

describe('buildRequestKey', () => {
  it('combines method, url, params and data for deduplication', () => {
    const key = buildRequestKey({
      method: 'get',
      url: '/api/v1/foo',
      params: { page: 1 },
      data: { x: 2 }
    })
    expect(key).toContain('get')
    expect(key).toContain('/api/v1/foo')
    expect(key).toContain('"page":1')
    expect(key).toContain('"x":2')
  })
})
