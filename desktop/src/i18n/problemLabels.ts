/**
 * 문제 검사 이름(problem_common의 저장값)은 캐시·설정·필터와 호환되도록 중국어 그대로 저장한다.
 * 화면에는 UI 언어가 중국어가 아니면 한국어 이름으로 바꿔 보여 준다(표시 전용).
 */
const KO_LABELS: Array<[string, string]> = [
  ['比日文长严格', '원문보다 김(엄격)'],
  ['比日文长', '원문보다 김'],
  ['语言不通-疑似中文', '언어 이상-중국어 의심'],
  ['语言不通-非GBK', '언어 이상-GBK 밖 문자'],
  ['语言不通', '언어 이상'],
  ['词频过高', '글자 반복 과다'],
  ['标点错漏', '문장부호 오류'],
  ['本无括号', '원문에 없는 괄호'],
  ['本无引号', '원문에 없는 따옴표'],
  ['本无韩文', '원문에 없는 한글'],
  ['残留日文', '일본어 잔류'],
  ['原文输出', '원문 그대로 출력'],
  ['丢失换行', '줄바꿈 누락'],
  ['多加换行', '줄바꿈 추가'],
  ['字典使用', '사전 미적용'],
  ['引入英文', '영어 유입'],
  ['缺控制符', '제어 문자 누락'],
  ['独白男他', "독백 '他'"],
  ['单句过长', '문장 너무 김'],
  ['数字不符', '숫자 불일치'],
  ['翻译失败', '번역 실패'],
];

const KO_SYMBOLS: Record<string, string> = { '括号': '괄호', '引号': '따옴표', '符号': ' 기호' };

function koSymbol(text: string): string {
  return Object.entries(KO_SYMBOLS).reduce((acc, [zh, ko]) => acc.split(zh).join(ko), text);
}

/** 문제 이름 하나 또는 문제 항목 하나(예: `残留日文：おはよう`)를 표시용으로 바꾼다. */
export function problemDisplayText(text: string, language: string): string {
  const value = String(text ?? '');
  if (!value || language.toLowerCase().startsWith('zh')) return value;
  for (const [zh, ko] of KO_LABELS) {
    if (value.startsWith(zh)) return ko + value.slice(zh.length).replace(/^：(.*?)倍\((\d+)字符\)$/, '：$1배($2자)');
  }
  // 本无 X 译有 Y / 本有 X 译无 Y (원문-번역 대응 검사)
  let m = /^本无 (.+) 译有 (.+)$/.exec(value);
  if (m) return `원문에 없는 ${m[1]}, 번역에 ${m[2]}`;
  m = /^本有 (.+) 译无 (.+)$/.exec(value);
  if (m) return `원문의 ${m[1]}, 번역에 ${m[2]} 없음`;
  m = /^本无(.+)$/.exec(value);
  if (m) return `원문에 없는 ${koSymbol(m[1])}`;
  m = /^本有(.+)$/.exec(value);
  if (m) return `${koSymbol(m[1])} 누락`;
  return value;
}
