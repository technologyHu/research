#!/usr/bin/env node
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const runtimeRoot = path.join(skillRoot, 'runtime');
const require = createRequire(path.join(runtimeRoot, 'package.json'));
const lbug = require('@ladybugdb/core');
const manifest = JSON.parse(readFileSync(path.join(skillRoot, 'extensions.lock.json'), 'utf8'));
assert.equal(lbug.VERSION, manifest.coreVersion, 'Native database ABI differs from the extension lock.');
const db = new lbug.Database(':memory:', 64 * 1024 * 1024, true, false, 512 * 1024 * 1024);
const connection = new lbug.Connection(db);
async function query(sql) {
  const result = await connection.query(sql);
  try { return await result.getAll(); } finally { await result.close(); }
}
try {
  await query('LOAD EXTENSION fts');
  await query('LOAD EXTENSION vector');
  await query('CREATE NODE TABLE Documents(id STRING, body STRING, embedding FLOAT[3], PRIMARY KEY(id))');
  await query("CREATE (:Documents {id:'authentication', body:'authentication token validation', embedding:[1.0,0.0,0.0]})");
  await query("CREATE (:Documents {id:'invoice', body:'invoice billing payment', embedding:[0.0,1.0,0.0]})");
  await query("CALL CREATE_FTS_INDEX('Documents','documents_fts',['body'])");
  const fts = await query("CALL QUERY_FTS_INDEX('Documents','documents_fts','authentication') RETURN node.id AS id, score");
  assert.equal(fts[0]?.id, 'authentication', 'FTS did not find the matching document.');
  await query("CALL CREATE_VECTOR_INDEX('Documents','documents_vector','embedding', metric := 'cosine')");
  const vector = await query("CALL QUERY_VECTOR_INDEX('Documents','documents_vector',[1.0,0.0,0.0],1) RETURN node.id AS id, distance");
  assert.equal(vector[0]?.id, 'authentication', 'VECTOR did not find the nearest document.');
  console.log(JSON.stringify({ platform: `${process.platform}-${process.arch}`, database: lbug.VERSION, fullText: true, vector: true }));
} finally {
  await connection.close();
  await db.close();
}
