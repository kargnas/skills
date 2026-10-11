import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const scriptsDir = fileURLToPath(new URL('../skills/skill-manager/scripts/', import.meta.url));

// Runs the scanner's pure functions against a fake catalog, so the test needs no network.
const runPython = (body) => JSON.parse(execFileSync('uv', ['run', '--quiet', '--no-project', 'python', '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(scriptsDir)})
from scan_model_ids import build_pattern, classify, index_catalog
${body}
`], { encoding: 'utf8' }));

test('scanner matches whole versioned model IDs only', () => {
  const found = runPython(`
catalog = {"p": {"models": {k: {} for k in ["m-2", "vendor/m-2", "m-2-pro", "x2", "model-x2", "echo"]}}}
line = ("Use \`m-2\`, then vendor/m-2 or m-2-pro. Fallback: m-2. Also model-x2, echo, and m-2x. "
        "Pinned: m-2-2025-01-31 and m-2-20250131.")
print(json.dumps([[m.group(0), m.group(1)] for m in build_pattern(catalog).finditer(line)]))
`);
  assert.deepEqual(found, [
    ['m-2', 'm-2'],
    ['vendor/m-2', 'vendor/m-2'],
    ['m-2-pro', 'm-2-pro'],
    ['m-2', 'm-2'],
    ['model-x2', 'model-x2'],
    ['m-2-2025-01-31', 'm-2'],
    ['m-2-20250131', 'm-2'],
  ]);
});

test('scanner picks the newest same-output release from the origin catalog', () => {
  const newest = runPython(`
def m(i, d, out="text", **extra):
    return {"id": i, "family": "fam", "release_date": d, "modalities": {"output": [out]}, **extra}
catalog = {
    "origin": {"models": {
        "fam-1": m("fam-1", "2026-01-01"),
        "fam-2": m("fam-2", "2026-06-01"),
        "fam-2-custom": m("fam-2-custom", "2026-06-01"),
        "fam-9-image": m("fam-9-image", "2026-12-01", out="image"),
        "fam-latest-9": m("fam-latest-9", "2026-12-01"),
        "solo-1": {"id": "solo-1", "release_date": "2026-01-01"},
    }},
    "rehost": {"models": {
        "fam-1": m("fam-1", "2026-01-01", canonical_model_id="origin/fam-1"),
        "fam-8": m("fam-8", "2026-08-01", canonical_model_id="origin/fam-8"),
        "old-0": m("old-0", "2025-01-01"),
    }},
}
index = index_catalog(catalog)
out = {}
for model_id in ["fam-1", "fam-2", "old-0", "solo-1"]:
    result = classify(catalog, index, model_id)
    out[model_id] = None if result is None else [result[0], result[2]["id"]]
print(json.dumps(out))
`);
  assert.deepEqual(newest, {
    'fam-1': ['origin', 'fam-2'],
    'fam-2': ['origin', 'fam-2'],
    'old-0': ['origin', 'fam-2'],
    'solo-1': null,
  });
});
