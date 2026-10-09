import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import http from 'node:http';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createInterface } from 'node:readline';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

test('preview WebSocket authenticates proxy connections without trusting cross-origin cookies', { timeout: 10000 }, async (t) => {
  const dir = await mkdtemp(path.join(tmpdir(), 'preview-server-test-'));
  const child = spawn(process.execPath, [fileURLToPath(new URL('../skills/dont-trust-my-ui-idea/scripts/server.cjs', import.meta.url))], {
    env: {
      ...Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('BRAINSTORM_'))),
      BRAINSTORM_DIR: dir,
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let errors = '';
  child.stderr.on('data', chunk => { errors += chunk; });
  t.after(async () => {
    if (child.exitCode === null && child.signalCode === null) {
      const exited = once(child, 'exit');
      child.kill();
      await exited;
    }
    await rm(dir, { recursive: true, force: true });
  });
  const info = await new Promise((resolve, reject) => {
    const lines = createInterface({ input: child.stdout });
    child.once('error', reject);
    child.once('exit', () => reject(new Error(errors || 'Preview exited before startup')));
    lines.on('line', line => {
      const data = JSON.parse(line);
      if (data.type === 'server-started') {
        lines.close();
        resolve(data);
      }
    });
  });
  const key = new URL(info.url).searchParams.get('key');
  const cookie = `brainstorm-key-${info.port}=${key}`;
  const localOrigin = `http://localhost:${info.port}`;
  const proxyOrigin = 'http://preview.orca.localhost:57028';

  function upgrade(requestPath, headers) {
    return new Promise((resolve, reject) => {
      const req = http.request({
        hostname: '127.0.0.1', port: info.port, path: requestPath,
        headers: {
          Host: `localhost:${info.port}`,
          Connection: 'Upgrade', Upgrade: 'websocket',
          'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==', 'Sec-WebSocket-Version': '13',
          ...headers,
        },
      });
      req.on('upgrade', (res, socket) => {
        socket.destroy();
        resolve(res.statusCode);
      });
      req.on('response', res => { res.resume(); resolve(res.statusCode); });
      req.on('error', error => error.code === 'ECONNRESET' ? resolve('rejected') : reject(error));
      req.setTimeout(2000, () => req.destroy(new Error('WebSocket handshake timed out')));
      req.end();
    });
  }

  await t.test('same-origin cookie and explicit key connections succeed', async () => {
    assert.equal(await upgrade('/', { Origin: localOrigin, Cookie: cookie }), 101);
    assert.equal(await upgrade(`/?key=${key}`, { Origin: localOrigin }), 101);
  });
  await t.test('a valid explicit key survives a proxy rewriting Host', async () => {
    assert.equal(await upgrade(`/?key=${key}`, { Origin: proxyOrigin }), 101);
  });
  await t.test('cross-origin cookies and forged forwarding headers remain rejected', async () => {
    assert.equal(await upgrade('/', { Origin: proxyOrigin, Cookie: cookie }), 'rejected');
    assert.equal(await upgrade('/', {
      Origin: proxyOrigin, Cookie: cookie,
      'X-Forwarded-Host': 'preview.orca.localhost:57028', 'X-Forwarded-Proto': 'http',
    }), 'rejected');
  });
  await t.test('missing, empty, and invalid keys cannot authenticate', async () => {
    assert.equal(await upgrade('/', { Origin: localOrigin }), 'rejected');
    for (const value of ['', 'invalid']) {
      assert.equal(await upgrade(`/?key=${value}`, { Origin: proxyOrigin, Cookie: cookie }), 'rejected');
    }
  });
});
