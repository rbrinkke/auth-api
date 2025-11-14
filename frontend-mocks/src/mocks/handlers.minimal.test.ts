/**
 * MINIMAL TEST - Verify MSW setup works
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Create a simple test handler with FULL URL
const testHandlers = [
  http.post('http://localhost/test', () => {
    return HttpResponse.json({ success: true }, { status: 200 });
  }),
];

const server = setupServer(...testHandlers);

beforeAll(() => {
  server.listen();
});

afterAll(() => {
  server.close();
});

describe('MSW Setup Test', () => {
  it('should intercept requests with full URL', async () => {
    const response = await fetch('http://localhost/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: true }),
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toEqual({ success: true });
  });
});
