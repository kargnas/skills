#!/usr/bin/env node
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export function codexPluginSource(name, source) {
  if (typeof source === 'string' && source) return source;
  if (source?.source === 'github' && typeof source.repo === 'string' && source.repo) {
    return { source: 'url', url: `https://github.com/${source.repo}.git` };
  }
  if (source?.source === 'url' && typeof source.url === 'string' && source.url) {
    return { source: 'url', url: source.url };
  }
  throw new Error(`plugin ${name} has an invalid source: ${JSON.stringify(source)}`);
}

export function validateMarketplace(marketplace, { root } = {}) {
  if (!marketplace || typeof marketplace !== 'object' || Array.isArray(marketplace)) {
    throw new Error('marketplace root must be an object');
  }
  for (const field of ['name', 'version', 'description']) {
    if (typeof marketplace[field] !== 'string' || !marketplace[field]) {
      throw new Error(`marketplace ${field} must be a non-empty string`);
    }
  }
  if (!marketplace.owner || typeof marketplace.owner.name !== 'string') {
    throw new Error('marketplace owner.name must be a string');
  }
  if (!Array.isArray(marketplace.plugins)) {
    throw new Error('marketplace plugins must be an array');
  }
  for (const plugin of marketplace.plugins) {
    if (!plugin || typeof plugin.name !== 'string' || !plugin.name) {
      throw new Error('marketplace plugin name must be a non-empty string');
    }
    codexPluginSource(plugin.name, plugin.source);
    if (root && typeof plugin.source === 'string' && !existsSync(join(root, plugin.source))) {
      throw new Error(`plugin ${plugin.name} source directory not found: ${plugin.source}`);
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const root = join(dirname(fileURLToPath(import.meta.url)), '..');
  const marketplace = JSON.parse(
    readFileSync(join(root, '.claude-plugin', 'marketplace.json'), 'utf8'),
  );
  validateMarketplace(marketplace, { root });
  console.log('marketplace.json is valid');
}
