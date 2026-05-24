#!/usr/bin/env node
/** 验证 template 中 t() 在 en 语言下是否仍含中文；并检查分组建议 / demo 映射 / 活动状态 */
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const files = [
  ['student', path.join(__dirname, '../web_embedded/assets/app.js'), 'STUDENT_I18N', 'STUDENT_TEXT_I18N'],
  ['admin', path.join(__dirname, '../web_embedded_admin/assets/app.js'), 'ADMIN_I18N', 'ADMIN_TEXT_I18N'],
];
const corePath = path.join(__dirname, '../web_embedded/assets/i18n-core.js');
const core = fs.readFileSync(corePath, 'utf8');

let failed = false;

for (const [name, file, sn, tn] of files) {
  const src = fs.readFileSync(file, 'utf8');
  const prefix = src.split('const http = axios.create')[0].replace(/^const \{ createApp[^\n]+\n/m, '');
  const templateMatch = src.match(/template:\s*`([\s\S]*?)\n  `,/);
  const template = templateMatch ? templateMatch[1] : '';
  const keys = [...new Set([...template.matchAll(/t\('([^']+)'\)/g)].map((m) => m[1]))];
  const sandbox = {
    window: {},
    Object,
    console,
    Vue: {},
    localStorage: { getItem: () => null, setItem: () => {} },
  };
  vm.createContext(sandbox);
  vm.runInContext(core + '\n' + prefix, sandbox);
  let structured, textI18n;
  try {
    structured = vm.runInContext(sn, sandbox);
    textI18n = vm.runInContext(tn, sandbox);
  } catch (e) {
    console.error(`\n=== ${name} ERROR loading i18n: ${e.message} ===`);
    failed = true;
    continue;
  }
  const t = sandbox.window.TeamMindI18n.createTranslator({
    structuredI18n: structured,
    textI18n,
    getLang: () => 'en',
    getOpenCC: () => null,
  });
  const bad = keys.filter((k) => /[\u4e00-\u9fff]/.test(String(t(k))));
  console.log(`\n=== ${name} ===`);
  console.log(`  t() keys: ${keys.length}`);
  console.log(`  still Chinese in en: ${bad.length}`);
  if (bad.length) {
    bad.forEach((k) => console.log(`    - ${k}`));
    failed = true;
  } else console.log('  OK all keys translate to English');
}

const helperSandbox = { window: {}, Object, console };
vm.createContext(helperSandbox);
vm.runInContext(core, helperSandbox);
const { formatGroupingAdvice, translateDemoText, translateBackendInsight, normalizeActivityStatus } =
  helperSandbox.window.TeamMindI18n;

const helperT = (key) => {
  const map = {
    '建议分为 %n% 组，人数分配为 %s%': 'Suggested %n% groups with sizes %s%',
    '系统建议分为 %n% 组，人数为 %s%。': 'System suggests %n% groups with sizes %s%.',
    暂无可分组学生: 'No students available for grouping',
  };
  return map[key] || key;
};

console.log('\n=== i18n-core helpers ===');
const advice = formatGroupingAdvice({ group_count: 3, sizes: [4, 4, 4] }, helperT);
if (!/Suggested 3 groups with sizes 4\/4\/4/.test(advice)) {
  console.log(`  FAIL formatGroupingAdvice: ${advice}`);
  failed = true;
} else console.log('  OK formatGroupingAdvice');

const demoTitle = translateDemoText('数字媒体技术 2401 班｜第 4 周产品原型项目组队', helperT, 'en', null);
if (/[\u4e00-\u9fff]/.test(demoTitle)) {
  console.log(`  FAIL translateDemoText: ${demoTitle}`);
  failed = true;
} else console.log(`  OK translateDemoText: ${demoTitle}`);

const insight = translateBackendInsight('建议分为 3 组，人数分配为 4/4/4', helperT);
if (/[\u4e00-\u9fff]/.test(insight)) {
  console.log(`  FAIL translateBackendInsight: ${insight}`);
  failed = true;
} else console.log(`  OK translateBackendInsight: ${insight}`);

if (normalizeActivityStatus('confirming') !== 'confirmation') {
  console.log('  FAIL normalizeActivityStatus confirming alias');
  failed = true;
} else console.log('  OK normalizeActivityStatus alias');

if (failed) process.exitCode = 1;
