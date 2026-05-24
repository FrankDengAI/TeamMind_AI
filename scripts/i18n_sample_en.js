#!/usr/bin/env node
/** 在 Node 中加载 app.js 的 i18n 常量，抽样验证 en 翻译 */
const fs = require('fs');
const vm = require('vm');

function loadI18n(file) {
  const src = fs.readFileSync(file, 'utf8');
  const prefix = src.split('const http = axios.create')[0];
  const sandbox = { window: {}, Object, console };
  vm.createContext(sandbox);
  vm.runInContext(prefix, sandbox);
  const isStudent = file.includes('web_embedded\\assets') || file.includes('web_embedded/assets');
  const structured = isStudent ? sandbox.STUDENT_I18N : sandbox.ADMIN_I18N;
  const text = isStudent ? sandbox.STUDENT_TEXT_I18N : sandbox.ADMIN_TEXT_I18N;
  const templateMatch = src.match(/template:\s*`([\s\S]*?)\n  `,/);
  const template = templateMatch ? templateMatch[1] : '';
  const keys = [...template.matchAll(/t\('([^']+)'\)/g)].map((m) => m[1]);
  const t = sandbox.window.TeamMindI18n
    ? sandbox.window.TeamMindI18n.createTranslator({
        structuredI18n: structured,
        textI18n: text,
        getLang: () => 'en',
        getOpenCC: () => null,
      })
    : (k) => k;
  const samples = [...new Set(keys)].slice(0, 40);
  const stillChinese = samples.filter((k) => /[\u4e00-\u9fff]/.test(t(k)));
  return { file, totalKeys: new Set(keys).size, stillChinese };
}

for (const file of process.argv.slice(2)) {
  const r = loadI18n(file);
  console.log(`\n${file}`);
  console.log(`  unique t() keys in template: ${r.totalKeys}`);
  console.log(`  sample untranslated (of first 40 unique): ${r.stillChinese.length}`);
  if (r.stillChinese.length) console.log('  ', r.stillChinese.slice(0, 12).join(' | '));
}
