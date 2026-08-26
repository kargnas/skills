#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { codexPluginSource, validateMarketplace } from './marketplace.mjs';

// Unlike opgginc/skills there is no CLI package here, so
// .claude-plugin/plugin.json is the single version source and everything
// else is derived from it.
const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const checkOnly = process.argv.includes('--check');

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

const pluginPath = join(repoRoot, '.claude-plugin', 'plugin.json');
const marketplacePath = join(repoRoot, '.claude-plugin', 'marketplace.json');
const codexMarketplacePath = join(repoRoot, '.agents', 'plugins', 'marketplace.json');
const plugin = readJson(pluginPath);
const version = plugin.version;
if (typeof version !== 'string' || !version) {
  throw new Error('.claude-plugin/plugin.json version must be a non-empty string');
}
const marketplace = readJson(marketplacePath);
validateMarketplace(marketplace, { root: repoRoot });
const marketplacePlugin = marketplace.plugins.find(({ name }) => name === plugin.name);

if (!marketplacePlugin) {
  throw new Error(`${plugin.name} entry missing from marketplace.json`);
}

// Codex discovers `.agents/plugins/marketplace.json` BEFORE `.claude-plugin/
// marketplace.json` and reads only the first hit, so the Codex manifest must
// list every plugin. Its plugin source schema is tagged local/url/git-subdir/
// npm — Claude's {"source":"github","repo":...} lands in Codex's Unsupported
// arm and that plugin entry is skipped with a warning only. Deriving the file
// here keeps the two schemas from drifting by hand.
const codexMarketplace = `${JSON.stringify(
  {
    name: marketplace.name,
    interface: { displayName: plugin.interface.displayName },
    plugins: marketplace.plugins.map(({ name, source, description, category }) => ({
      name,
      source: codexPluginSource(name, source),
      description,
      policy: { installation: 'AVAILABLE', authentication: 'ON_INSTALL' },
      category: category ?? 'development',
    })),
  },
  null,
  2,
)}\n`;

const drift = [];
if (marketplace.version !== version) drift.push('.claude-plugin/marketplace.json catalog');
if (marketplacePlugin.version !== version) {
  drift.push(`.claude-plugin/marketplace.json ${plugin.name}`);
}
try {
  if (readFileSync(codexMarketplacePath, 'utf8') !== codexMarketplace) {
    drift.push('.agents/plugins/marketplace.json');
  }
} catch {
  drift.push('.agents/plugins/marketplace.json (missing)');
}

if (checkOnly) {
  if (drift.length) {
    console.error(`metadata not synced with plugin.json (${version}): ${drift.join(', ')}`);
    process.exitCode = 1;
  } else {
    console.log(`plugin metadata matches plugin.json (${version})`);
  }
} else {
  // Claude Code caches explicit plugin versions, so every duplicated metadata
  // field must change with the plugin version or users keep stale skills.
  marketplace.version = version;
  marketplacePlugin.version = version;
  writeFileSync(marketplacePath, `${JSON.stringify(marketplace, null, 2)}\n`);
  mkdirSync(dirname(codexMarketplacePath), { recursive: true });
  writeFileSync(codexMarketplacePath, codexMarketplace);
  console.log(`synced plugin metadata to ${version}`);
}
