import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createTypeScriptLoader } from './helpers/load-typescript.mjs';

const load = createTypeScriptLoader();
const { problemDisplayText } = load(new URL('../src/i18n/problemLabels.ts', import.meta.url));

test('problem names are shown in Korean outside the Chinese UI', () => {
  assert.equal(problemDisplayText('残留日文', 'ko'), '일본어 잔류');
  assert.equal(problemDisplayText('残留日文：おはよう', 'ko'), '일본어 잔류：おはよう');
  assert.equal(problemDisplayText('比日文长严格', 'ko'), '원문보다 김(엄격)');
  assert.equal(problemDisplayText('比日文长：1.6倍(12字符)', 'ko'), '원문보다 김：1.6배(12자)');
  assert.equal(problemDisplayText('语言不通-疑似中文：这个', 'ko'), '언어 이상-중국어 의심：这个');
  assert.equal(problemDisplayText('本无引号', 'ko'), '원문에 없는 따옴표');
  assert.equal(problemDisplayText('数字不符：10', 'ko'), '숫자 불일치：10');
  assert.equal(problemDisplayText('本有*符号', 'ko'), '* 기호 누락');
  assert.equal(problemDisplayText('本无 ♪ 译有 ♪', 'ko'), '원문에 없는 ♪, 번역에 ♪');
  assert.equal(problemDisplayText('GPT 사전 미사용: a---b', 'ko'), 'GPT 사전 미사용: a---b');
});

test('Chinese UI keeps stored names', () => {
  assert.equal(problemDisplayText('残留日文：おはよう', 'zh-CN'), '残留日文：おはよう');
});
