import assert from 'node:assert/strict';
import { test } from 'node:test';
import { codexPluginSource, validateMarketplace } from './marketplace.mjs';

const validMarketplace = () => ({
  name: 'test-marketplace',
  version: '1.0.0',
  description: 'test',
  owner: { name: 'Test' },
  plugins: [{ name: 'local', source: './' }],
});

test('marketplace validation rejects invalid roots and plugin sources', () => {
  for (const value of [[], { ...validMarketplace(), plugins: '' }]) {
    assert.throws(() => validateMarketplace(value));
  }
  for (const source of [true, {}, { source: 'github' }, { source: 'url', url: '' }]) {
    const marketplace = validMarketplace();
    marketplace.plugins[0].source = source;
    assert.throws(() => validateMarketplace(marketplace));
  }
});

test('Codex source conversion preserves local and URL sources and maps GitHub repos', () => {
  assert.equal(codexPluginSource('local', './'), './');
  assert.deepEqual(
    codexPluginSource('github', { source: 'github', repo: 'owner/repo' }),
    { source: 'url', url: 'https://github.com/owner/repo.git' },
  );
  assert.deepEqual(
    codexPluginSource('url', { source: 'url', url: 'https://example.com/plugin.git' }),
    { source: 'url', url: 'https://example.com/plugin.git' },
  );
});
