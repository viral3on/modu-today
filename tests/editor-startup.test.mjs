import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';

test('editor cold-starts when the runtime disallows CommonJS require of ES modules', () => {
  // Mirrors the Vercel loader restriction that previously crashed /api/editor.
  const script = `
    import assert from 'node:assert/strict';
    import {createHandler} from ${JSON.stringify(new URL('../api/editor.js', import.meta.url).href)};
    const handler = createHandler(() => { throw new Error('Unexpected GitHub request'); }, {});
    for (const [method, expected] of [['GET', 405], ['POST', 401]]) {
      const response = {
        headers: {},
        setHeader(name, value) { this.headers[name] = value; },
        status(code) { this.code = code; return this; },
        json(value) { this.body = value; }
      };
      await handler({method, headers: {origin: 'https://modu.today', 'content-type': 'application/json'}, body: {action: 'verify'}}, response);
      assert.equal(response.code, expected);
      assert.equal(response.headers['Cache-Control'], 'private, no-store');
      assert.equal(typeof response.body.error, 'string');
    }
  `;
  const result = spawnSync(process.execPath, ['--no-experimental-require-module', '--input-type=module', '--eval', script], {encoding: 'utf8', timeout: 15000});
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr || result.stdout);
});
