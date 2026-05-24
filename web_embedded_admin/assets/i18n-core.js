/**
 * TeamMind 嵌入式 UI 通用 i18n 工具（学生端 / 教师端共用）
 */
;(function (global) {
  const DEMO_CONTENT_I18N = {
    en: {
      '人工智能 2401 班': 'AI 2401 Class',
      '软件工程 2402 班': 'Software Engineering 2402 Class',
      '数据科学 2301 班': 'Data Science 2301 Class',
      '数字媒体技术 2401 班': 'Digital Media Technology 2401 Class',
      'AI 产品创新实践': 'AI Product Innovation Practice',
      '软件工程综合实训': 'Software Engineering Capstone',
      '数据智能项目实践': 'Data Intelligence Project Practice',
      '交互媒体设计实践': 'Interactive Media Design Practice',
      '第 4 周产品原型项目组队': 'Week 4 Product Prototype Teaming',
      '第二学期课程设计': 'Second Semester Course Design',
      '期末展示自由组队': 'Final Showcase Free Teaming',
      '数据可视化专题项目': 'Data Visualization Project',
      '交互媒体创意工作坊': 'Interactive Media Creative Workshop',
      '当前班级': 'Current Class',
      '未识别班级': 'Unknown Class',
      '未命名活动': 'Untitled Activity',
      '技术开发': 'Technical Development',
      '设计执行': 'Design Execution',
      '协调对接': 'Coordination',
      '数据支持': 'Data Support',
      '质量审核': 'Quality Review',
      '创意策划': 'Creative Planning',
      '文案撰写': 'Documentation',
      '执行落地': 'Execution',
      '对外对接': 'External Liaison',
    },
    ja: {
      '人工智能 2401 班': 'AI 2401 クラス',
      '软件工程 2402 班': 'ソフトウェア工学 2402 クラス',
      '数据科学 2301 班': 'データサイエンス 2301 クラス',
      '数字媒体技术 2401 班': 'デジタルメディア技術 2401 クラス',
      'AI 产品创新实践': 'AI プロダクト創造実践',
      '软件工程综合实训': 'ソフトウェア工学総合演習',
      '数据智能项目实践': 'データインテリジェンスプロジェクト実践',
      '交互媒体设计实践': 'インタラクティブメディアデザイン実践',
      '第 4 周产品原型项目组队': '第4週プロトタイプチーム編成',
      '第二学期课程设计': '第2学期コースデザイン',
      '期末展示自由组队': '期末展示フリー編成',
      '数据可视化专题项目': 'データ可視化プロジェクト',
      '交互媒体创意工作坊': 'インタラクティブメディアワークショップ',
      '当前班级': '現在のクラス',
      '未识别班级': '不明なクラス',
      '未命名活动': '名称未設定の活動',
      '技术开发': '技術開発',
      '设计执行': 'デザイン実行',
      '协调对接': '調整連携',
      '数据支持': 'データ支援',
      '质量审核': '品質レビュー',
      '创意策划': 'クリエイティブ企画',
      '文案撰写': 'ドキュメント作成',
      '执行落地': '実行推進',
      '对外对接': '外部連携',
    },
  }

  const ACTIVITY_STATUS_ALIASES = {
    confirming: 'confirmation',
  }

  function lookupTextTranslation(original, target) {
    if (!target || !original) return original
    if (target[original]) return target[original]
    const compact = String(original).replace(/\s+/g, ' ').trim()
    if (target[compact]) return target[compact]
    const countSuffix = compact.match(/^(.+?)(\s*\(\d+\))$/)
    if (countSuffix && target[countSuffix[1]]) return `${target[countSuffix[1]]}${countSuffix[2]}`
    return original
  }

  function resolveStructured(bundle, key) {
    if (!bundle || key == null) return undefined
    if (Object.prototype.hasOwnProperty.call(bundle, key)) {
      const value = bundle[key]
      if (value != null && typeof value !== 'object') return value
    }
    return undefined
  }

  function createTranslator({ structuredI18n, textI18n, getLang, getOpenCC }) {
    return function t(key) {
      const lang = getLang()
      const zhBundle = structuredI18n['zh-CN'] || {}
      const activeBundle = structuredI18n[lang] || zhBundle
      const structured = resolveStructured(activeBundle, key)
      if (structured !== undefined) return structured

      const zhStructured = resolveStructured(zhBundle, key)
      const baseText = zhStructured !== undefined ? zhStructured : String(key)

      if (lang === 'zh-CN') return baseText

      if (lang === 'zh-Hant') {
        const converter = getOpenCC?.()
        if (converter) return converter(baseText)
      }

      const dict = textI18n[lang] || textI18n.en || {}
      const translated = lookupTextTranslation(baseText, dict)
      if (translated !== baseText) return translated

      if (lang !== 'en') {
        const enDict = textI18n.en || {}
        const enTranslated = lookupTextTranslation(baseText, enDict)
        if (enTranslated !== baseText) return enTranslated
      }

      return baseText
    }
  }

  function initOpenCC() {
    if (!global.OpenCC?.Converter) return null
    try {
      return global.OpenCC.Converter({ from: 'cn', to: 'tw' })
    } catch {
      return null
    }
  }

  function normalizeActivityStatus(status) {
    const key = String(status || '')
    return ACTIVITY_STATUS_ALIASES[key] || key
  }

  function formatGroupingAdvice(advice, t) {
    if (!advice || !advice.sizes?.length) return t('暂无可分组学生')
    const sizes = advice.sizes.join('/')
    return t('建议分为 %n% 组，人数分配为 %s%')
      .replace('%n%', String(advice.group_count ?? advice.sizes.length))
      .replace('%s%', sizes)
  }

  function translateDemoText(text, t, lang, getOpenCC) {
    if (text == null || text === '') return ''
    const raw = String(text)
    if (lang === 'zh-CN') return raw

    const demoDict = DEMO_CONTENT_I18N[lang] || DEMO_CONTENT_I18N.en || {}
    if (demoDict[raw]) return demoDict[raw]

    const parts = raw.split(/[｜|]/)
    if (parts.length === 2) {
      const left = translateDemoText(parts[0], t, lang, getOpenCC)
      const right = translateDemoText(parts[1], t, lang, getOpenCC)
      return `${left}｜${right}`
    }

    const viaT = t(raw)
    if (viaT !== raw) return viaT

    if (lang === 'zh-Hant') {
      const converter = getOpenCC?.()
      if (converter) return converter(raw)
    }

    const enDict = DEMO_CONTENT_I18N.en || {}
    if (enDict[raw]) return enDict[raw]
    if (lang !== 'en') return enDict[raw] || raw
    return raw
  }

  function translateBackendInsight(text, t, lang = 'en', getOpenCC) {
    if (text == null || text === '') return ''
    const raw = String(text).trim()

    const patterns = [
      {
        re: /^系统建议分为 (\d+) 组，人数为 ([0-9/]+)。$/,
        tpl: (m) => t('系统建议分为 %n% 组，人数为 %s%。').replace('%n%', m[1]).replace('%s%', m[2]),
      },
      {
        re: /^建议分为 (\d+) 组，人数分配为 ([0-9/]+)$/,
        tpl: (m) => t('建议分为 %n% 组，人数分配为 %s%').replace('%n%', m[1]).replace('%s%', m[2]),
      },
      {
        re: /^最大组与最小组人数差为 (\d+)，可降低组间工作量不均。$/,
        tpl: (m) => t('最大组与最小组人数差为 %n%，可降低组间工作量不均。').replace('%n%', m[1]),
      },
      {
        re: /^默认参考每组 (\d+) 人，符合 10-20 人班级的小组项目组织方式。$/,
        tpl: (m) => t('默认参考每组 %n% 人，符合 10-20 人班级的小组项目组织方式。').replace('%n%', m[1]),
      },
      {
        re: /^当前班级人数适合进行均匀项目分组。$/,
        tpl: () => t('当前班级人数适合进行均匀项目分组。'),
      },
      {
        re: /^当前暂无可分组学生。$/,
        tpl: () => t('当前暂无可分组学生。'),
      },
      {
        re: /^暂无可分组学生$/,
        tpl: () => t('暂无可分组学生'),
      },
      {
        re: /^人数较少的小组需要老师关注任务拆分，避免承担同等任务量。$/,
        tpl: () => t('人数较少的小组需要老师关注任务拆分，避免承担同等任务量。'),
      },
      {
        re: /^已为活动“(.+?)”生成 (\d+) 个候选小组，平均均衡度 ([\d.]+)。$/,
        tpl: (m) => t('已为活动“%t%”生成 %n% 个候选小组，平均均衡度 %s%。')
          .replace('%t%', translateDemoText(m[1], t, lang, getOpenCC))
          .replace('%n%', m[2])
          .replace('%s%', m[3]),
      },
    ]

    for (const { re, tpl } of patterns) {
      const m = raw.match(re)
      if (m) return tpl(m)
    }

    const translated = t(raw)
    return translated !== raw ? translated : raw
  }

  global.TeamMindI18n = {
    lookupTextTranslation,
    createTranslator,
    initOpenCC,
    DEMO_CONTENT_I18N,
    ACTIVITY_STATUS_ALIASES,
    normalizeActivityStatus,
    formatGroupingAdvice,
    translateDemoText,
    translateBackendInsight,
  }
})(window)
