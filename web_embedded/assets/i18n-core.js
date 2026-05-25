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

  /** 画像标签、角色方向、分类名等（与 tag_catalog 一致） */
  const TAG_LEXICON_I18N = {
    en: {
      综合推荐: 'Overall recommendation',
      技能标签: 'Skill tags',
      协作标签: 'Collaboration tags',
      画像匹配: 'Profile match',
      基础推荐: 'Basic recommendation',
      系统开发支持: 'System development support',
      界面与体验设计: 'UI & experience design',
      数据分析支持: 'Data analysis support',
      资料整理与汇报: 'Documentation & reporting',
      产品与方案策划: 'Product & solution planning',
      项目协作成员: 'Project collaborator',
      产品设计: 'Product design',
      测试验证: 'Testing & QA',
      其他: 'Other',
      学历层级: 'Education level',
      学科领域: 'Academic field',
      理论方向: 'Theory area',
      应用领域: 'Application domain',
      编程语言: 'Programming language',
      开发能力: 'Development skills',
      数据能力: 'Data skills',
      AI能力: 'AI skills',
      设计能力: 'Design skills',
      表达产出: 'Communication output',
      工具平台: 'Tools & platforms',
      偏好角色: 'Preferred role',
      沟通风格: 'Communication style',
      协作风格: 'Collaboration style',
      团队经验: 'Team experience',
      时间投入: 'Time commitment',
      本科: "Bachelor's",
      硕士: "Master's",
      博士: 'PhD',
      计算机科学: 'Computer Science',
      人工智能: 'Artificial Intelligence',
      数据科学: 'Data Science',
      设计学: 'Design',
      经管: 'Business & Management',
      工程管理: 'Engineering Management',
      教育技术: 'Educational Technology',
      数字媒体: 'Digital Media',
      数字媒体技术: 'Digital Media Technology',
      机器学习: 'Machine Learning',
      深度学习: 'Deep Learning',
      自然语言处理: 'Natural Language Processing',
      计算机视觉: 'Computer Vision',
      统计学: 'Statistics',
      数据库原理: 'Database Systems',
      数据库: 'Database',
      计算机网络: 'Computer Networks',
      操作系统: 'Operating Systems',
      算法与数据结构: 'Algorithms & Data Structures',
      软件工程: 'Software Engineering',
      人机交互: 'Human-Computer Interaction',
      用户研究: 'User Research',
      产品规划: 'Product Planning',
      项目管理: 'Project Management',
      金融科技: 'FinTech',
      智慧医疗: 'Smart Healthcare',
      智慧教育: 'Smart Education',
      前端开发: 'Frontend Development',
      后端开发: 'Backend Development',
      全栈开发: 'Full-stack Development',
      'API设计': 'API Design',
      测试与调试: 'Testing & Debugging',
      数据清洗: 'Data Cleaning',
      数据分析: 'Data Analysis',
      数据可视化: 'Data Visualization',
      模型训练: 'Model Training',
      'Prompt设计': 'Prompt Engineering',
      'UI设计': 'UI Design',
      'UX流程设计': 'UX Workflow Design',
      原型设计: 'Prototyping',
      'PPT汇报': 'Slide Presentations',
      文案撰写: 'Copywriting',
      调研报告: 'Research Reports',
      云服务部署: 'Cloud Deployment',
      '组长/负责人': 'Team Lead',
      技术开发: 'Technical Development',
      设计执行: 'Design Execution',
      数据支持: 'Data Support',
      产品策划: 'Product Planning',
      文档汇报: 'Documentation & Reporting',
      资料调研: 'Research Support',
      测试验收: 'Testing & QA',
      执行落地: 'Execution',
      协调对接: 'Coordination',
      主动沟通: 'Proactive Communication',
      安静执行: 'Quiet Execution',
      及时反馈: 'Timely Feedback',
      擅长会议沟通: 'Strong in Meetings',
      严谨细致: 'Detail-oriented',
      灵活创新: 'Flexible & Innovative',
      乐于分享: 'Enjoys Sharing',
      计划性强: 'Strong Planning',
      抗压能力强: 'Resilient Under Pressure',
      愿意辅导同伴: 'Mentors Teammates',
      暂无团队项目经验: 'No team project experience yet',
      '1-2次团队项目': '1-2 team projects',
      '3次以上团队项目': '3+ team projects',
      时间投入充足: 'High time commitment',
      时间投入适中: 'Moderate time commitment',
      碎片时间协作: 'Fragmented schedule collaboration',
      质量审核: 'Quality Review',
      创意策划: 'Creative Planning',
      对外对接: 'External Liaison',
      暂无数据: 'No data',
      积极: 'Active',
      一般: 'Moderate',
      需关注: 'Needs attention',
      已逾期: 'Overdue',
      紧急: 'Urgent',
      预警: 'At risk',
      滞后: 'Behind',
      正常: 'On track',
      较多元: 'Diverse',
      待细化: 'To be refined',
      待补充: 'To be added',
      未指定: 'Unspecified',
      未设置截止日期: 'No deadline set',
      '按轮询均衡分配，保证每人承担子任务': 'Round-robin assignment for fair subtask distribution',
      '当前班级教师为免费版，使用规则解析；教师开通 Pro 后自动启用 DeepSeek': 'Your class uses rule-based parsing on the free plan; DeepSeek activates when the teacher upgrades to Pro.',
      '加入班级后，将跟随任课教师的 AI 套餐': 'After joining a class, you follow the teacher\'s AI plan.',
      '当前为规则解析，教师开通 Pro 后全班自动启用 DeepSeek': 'Rule-based parsing now; DeepSeek for the whole class when the teacher upgrades to Pro.',
      '学生自由组队，老师已锁定为正式队伍': 'Student free teaming; teacher locked as formal team.',
      成员进度预警: 'Member progress alert',
      '候选分组已结合成员画像、角色偏好、技能标签和任务目标进行互补匹配。': 'Candidate groups match profiles, role preferences, skill tags and task goals.',
      '班级绑定活动会自动限定在本班 active 成员中，避免跨班级误分配。': 'Class-bound activities only include active members of this class.',
      '小组人数按班级规模尽量均匀，降低组间协作负载差异。': 'Group sizes are balanced to reduce workload gaps between teams.',
      '画像缺失或标签过少的学生可能降低匹配精度。': 'Students with missing profiles or few tags may reduce matching accuracy.',
      '进入预沟通阶段后，优先收集学生对角色和任务偏好的反馈。': 'During pre-communication, collect feedback on roles and task preferences first.',
      '锁定前重点查看均衡度偏低的小组。': 'Before locking, review groups with lower balance scores.',
      '若组内角色重复较多，建议老师在预沟通阶段引导重新认领职责。': 'If roles overlap, guide members to reclaim responsibilities during pre-communication.',
      '先确认每位成员的首选角色，再把任务拆成技术、产品、数据、文档与汇报子任务。': 'Confirm preferred roles first, then split into tech, product, data, documentation and presentation subtasks.',
      关注低画像完整度成员: 'Watch members with incomplete profiles',
      要求小组在锁定前提交一次角色确认: 'Require a role confirmation before locking',
      '查看每组 AI 分析': 'Review AI analysis per group',
      处理微调申请: 'Handle adjustment requests',
      锁定正式团队后再分配任务: 'Assign tasks after locking formal teams',
      '先按人数均匀分组，再结合画像进行角色互补。': 'Group by even headcount first, then complement roles using profiles.',
      '建议分组后保留预沟通阶段，让学生确认角色与任务偏好。': 'Keep a pre-communication phase so students confirm roles and task preferences.',
      检查未录入画像学生: 'Check students without profiles',
      发布活动后提醒学生同步标签: 'Remind students to sync tags after publishing',
      锁定前处理微调申请: 'Resolve adjustment requests before locking',
      暂无显著技能标签: 'No notable skill tags yet',
      需求调研: 'Requirements research',
      原型设计: 'Prototyping',
      文献综述: 'Literature review',
      实验设计: 'Experiment design',
      论文撰写: 'Paper writing',
      方案策划: 'Planning',
      物料设计: 'Material design',
      宣传推广: 'Promotion',
      现场执行: 'On-site execution',
      产品开发: 'Product development',
      科研报告: 'Research report',
      活动策划: 'Event planning',
      测试验收: 'Testing & acceptance',
      产品设计: 'Product design',
      '完成一个可演示的 AI 产品低保真原型': 'Build a demonstrable AI product low-fidelity prototype',
    },
  }

  const AI_PREVIEW_SUFFIX_RE = /[ …]*[（(]升级\s*Pro[^）)]*[）)]\s*$/u

  function stripAiPreviewSuffix(text) {
    return String(text || '').replace(AI_PREVIEW_SUFFIX_RE, '').trim()
  }

  function aiPreviewSuffix(lang, t) {
    if (lang === 'zh-CN') return ' …（升级 Pro 查看完整 AI 分析）'
    if (lang === 'zh-Hant') return ' …（升級 Pro 查看完整 AI 分析）'
    const viaT = t?.('升级 Pro 查看完整 AI 分析')
    return viaT && viaT !== '升级 Pro 查看完整 AI 分析' ? ` … (${viaT})` : ' … (Upgrade to Pro for full AI analysis)'
  }

  const DYNAMIC_SEGMENT_I18N = {
    en: {
      major_coverage: 'Covers %n% major areas (%tags%)',
      skill_tags_count: '%n% skill tags, group skill average %s%',
      role_direction: '%n% role directions (%roles%), collaboration average %s%',
      knowledge_balance: 'Knowledge average %s%, well-balanced overall',
      task_tag_match: 'Task tags matched %a%/%b% (%tags%)',
      task_role_match: 'Task roles matched %a%/%b% (%roles%)',
      role_pref_match: 'Role preference "%pref%" matches required role "%role%"',
      skill_fit: 'Skill score %s% fits difficulty level %d%',
      workload: 'Current workload %h%h; load balancing considered',
      task_difficulty_assign: 'Level-%d% task assigned to member with fewest hours (%h%h committed) for balance',
      group_summary: '%name%: %n% members, skill average %s%, suitable for pre-communication',
      role_coverage: 'Role coverage: %roles%',
      skill_coverage: 'Skill tags: %skills%',
      score_triple: 'Knowledge / skill / collaboration averages: %k% / %s% / %c%',
      overdue_days: 'Overdue by %n% day(s) — act now',
      urgent_days: '%n% day(s) left, only %p%% complete',
      risk_deadline: 'May miss deadline (%n% day(s) left)',
      behind_schedule: 'Behind schedule — speed up or ask for help',
      on_track: '%n% day(s) left, on track',
    },
  }

  function segText(lang, key, vars = {}) {
    const tpl = (DYNAMIC_SEGMENT_I18N[lang] || DYNAMIC_SEGMENT_I18N.en || {})[key] || key
    return Object.entries(vars).reduce((s, [k, v]) => s.replace(`%${k}%`, String(v)), tpl)
  }

  function translateProfileLexicon(text, lang, t, getOpenCC) {
    if (text == null || text === '') return ''
    const raw = String(text)
    if (lang === 'zh-CN') return raw

    const dict = TAG_LEXICON_I18N[lang] || TAG_LEXICON_I18N.en || {}
    const demoDict = DEMO_CONTENT_I18N[lang] || DEMO_CONTENT_I18N.en || {}

    const translateOne = (term) => {
      const trimmed = String(term || '').trim()
      if (!trimmed) return trimmed
      const viaDict = lookupTextTranslation(trimmed, dict)
      if (viaDict !== trimmed) return viaDict
      if (demoDict[trimmed]) return demoDict[trimmed]
      if (t) {
        const viaT = t(trimmed)
        if (viaT !== trimmed) return viaT
      }
      if (lang !== 'en') {
        const enDict = TAG_LEXICON_I18N.en || {}
        const viaEn = lookupTextTranslation(trimmed, enDict)
        if (viaEn !== trimmed) return viaEn
        if (DEMO_CONTENT_I18N.en?.[trimmed]) return DEMO_CONTENT_I18N.en[trimmed]
      }
      if (lang === 'zh-Hant' && getOpenCC) {
        const converter = getOpenCC()
        if (converter) return converter(trimmed)
      }
      return trimmed
    }

    const parts = raw.split(/[、,，]/).map((s) => s.trim()).filter(Boolean)
    if (parts.length > 1) {
      const sep = (lang === 'zh-CN' || lang === 'zh-Hant') ? '、' : ', '
      return parts.map(translateOne).join(sep)
    }
    return translateOne(raw)
  }

  function localizeTagCatalog(catalog, lang, t, getOpenCC) {
    if (!catalog || lang === 'zh-CN') return catalog
    const mapList = (list) => (list || []).map((tag) => ({
      ...tag,
      displayName: translateProfileLexicon(tag.name, lang, t, getOpenCC),
      displayCategory: translateProfileLexicon(tag.category || '其他', lang, t, getOpenCC),
    }))
    return {
      knowledge: mapList(catalog.knowledge),
      skill: mapList(catalog.skill),
      collab: mapList(catalog.collab),
    }
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

  function applyFullInsightPatterns(raw, t, lang, getOpenCC) {
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
        re: /^已为活动[“"](.+?)[”"]生成 (\d+) 个候选小组[，,]?\s*平均均衡度 ([\d.]+)。?$/,
        tpl: (m) => t('已为活动“%t%”生成 %n% 个候选小组，平均均衡度 %s%。')
          .replace('%t%', translateDemoText(m[1], t, lang, getOpenCC))
          .replace('%n%', m[2])
          .replace('%s%', m[3]),
      },
      {
        re: /^第(\d+)组$/,
        tpl: (m) => (lang === 'en' ? `Group ${m[1]}` : lang === 'zh-Hant' ? `第${m[1]}組` : `第${m[1]}组`),
      },
      {
        re: /^(.+?)共 (\d+) 人，技能均分 ([\d.]+)，适合进入预沟通确认。$/,
        tpl: (m) => segText(lang, 'group_summary', { name: translateDemoText(m[1], t, lang, getOpenCC), n: m[2], s: m[3] }),
      },
      {
        re: /^角色覆盖：(.+?)。$/,
        tpl: (m) => segText(lang, 'role_coverage', { roles: translateProfileLexicon(m[1], lang, t, getOpenCC) }),
      },
      {
        re: /^技能标签覆盖：(.+?)。$/,
        tpl: (m) => segText(lang, 'skill_coverage', { skills: translateProfileLexicon(m[1], lang, t, getOpenCC) }),
      },
      {
        re: /^知识\/技能\/协作均分为 ([\d.]+)\/([\d.]+)\/([\d.]+)。$/,
        tpl: (m) => segText(lang, 'score_triple', { k: m[1], s: m[2], c: m[3] }),
      },
      {
        re: /^已超期 (\d+) 天，请立即处理$/,
        tpl: (m) => segText(lang, 'overdue_days', { n: m[1] }),
      },
      {
        re: /^剩余 (\d+) 天，进度仅 (\d+)%$/,
        tpl: (m) => segText(lang, 'urgent_days', { n: m[1], p: m[2] }),
      },
      {
        re: /^预计难以按期完成（剩余 (\d+) 天）$/,
        tpl: (m) => segText(lang, 'risk_deadline', { n: m[1] }),
      },
      {
        re: /^剩余 (\d+) 天，进展正常$/,
        tpl: (m) => segText(lang, 'on_track', { n: m[1] }),
      },
    ]
    for (const { re, tpl } of patterns) {
      const m = raw.match(re)
      if (m) return tpl(m)
    }
    return null
  }

  function applySegmentPatterns(raw, t, lang, getOpenCC) {
    const lex = (s) => translateProfileLexicon(s, lang, t, getOpenCC)
    const patterns = [
      {
        re: /^专业方向覆盖 (\d+) 类（(.+?)）$/,
        tpl: (m) => segText(lang, 'major_coverage', { n: m[1], tags: lex(m[2]) }),
      },
      {
        re: /^技能标签共 (\d+) 项，组内技能均分 ([\d.]+)$/,
        tpl: (m) => segText(lang, 'skill_tags_count', { n: m[1], s: m[2] }),
      },
      {
        re: /^角色方向 (\d+) 类（(.+?)），协作均分 ([\d.]+)$/,
        tpl: (m) => segText(lang, 'role_direction', { n: m[1], roles: lex(m[2]), s: m[3] }),
      },
      {
        re: /^基础方向均分 ([\d.]+)，整体搭配较均衡$/,
        tpl: (m) => segText(lang, 'knowledge_balance', { s: m[1] }),
      },
      {
        re: /^任务标签匹配 (\d+)\/(\d+)（(.+?)）$/,
        tpl: (m) => segText(lang, 'task_tag_match', { a: m[1], b: m[2], tags: lex(m[3]) }),
      },
      {
        re: /^任务角色匹配 (\d+)\/(\d+)（(.+?)）$/,
        tpl: (m) => segText(lang, 'task_role_match', { a: m[1], b: m[2], roles: lex(m[3]) }),
      },
      {
        re: /^角色偏好「(.+?)」与任务要求「(.+?)」匹配$/,
        tpl: (m) => segText(lang, 'role_pref_match', { pref: lex(m[1]), role: lex(m[2]) }),
      },
      {
        re: /^实操能力 ([\d.]+) 与难度 (\d+) 级适配$/,
        tpl: (m) => segText(lang, 'skill_fit', { s: m[1], d: m[2] }),
      },
      {
        re: /^角色偏好「(.+?)」与任务要求「(.+?)」匹配；当前累计工时 ([\d.]+)h，兼顾负载均衡$/,
        tpl: (m) => `${segText(lang, 'role_pref_match', { pref: lex(m[1]), role: lex(m[2]) })}; ${segText(lang, 'workload', { h: m[3] })}`,
      },
      {
        re: /^实操能力 ([\d.]+) 与难度 (\d+) 级适配；当前累计工时 ([\d.]+)h，兼顾负载均衡$/,
        tpl: (m) => `${segText(lang, 'skill_fit', { s: m[1], d: m[2] })}; ${segText(lang, 'workload', { h: m[3] })}`,
      },
      {
        re: /^任务难度 (\d+) 级，按当前累计工时最少者分配（已承担 ([\d.]+)h），保障工作量均衡$/,
        tpl: (m) => segText(lang, 'task_difficulty_assign', { d: m[1], h: m[2] }),
      },
    ]
    for (const { re, tpl } of patterns) {
      const m = raw.match(re)
      if (m) return tpl(m)
    }
    return null
  }

  function translateParenContent(text, lang, t, getOpenCC) {
    if (!text || !/[（）]/.test(text)) return text
    return String(text).replace(/（([^）]+)）/g, (_, inner) => {
      const innerTr = translateProfileLexicon(inner, lang, t, getOpenCC)
      if (lang === 'zh-CN' || lang === 'zh-Hant') return `（${innerTr}）`
      return ` (${innerTr})`
    })
  }

  function translateSegment(seg, t, lang, getOpenCC) {
    const raw = String(seg || '').trim()
    if (!raw) return raw
    const full = applyFullInsightPatterns(raw, t, lang, getOpenCC)
    if (full) return full
    const partial = applySegmentPatterns(raw, t, lang, getOpenCC)
    if (partial) return partial
    const dict = TAG_LEXICON_I18N[lang] || TAG_LEXICON_I18N.en || {}
    if (dict[raw]) return dict[raw]
    const viaT = t(raw)
    if (viaT !== raw) return viaT
    let out = translateProfileLexicon(raw, lang, t, getOpenCC)
    return translateParenContent(out, lang, t, getOpenCC)
  }

  function normalizeCnListCommas(text) {
    return String(text || '').replace(/,\s*/g, '、')
  }

  function translateAppDynamicText(text, t, lang = 'en', getOpenCC) {
    if (text == null || text === '') return ''
    const raw = normalizeCnListCommas(String(text).trim())
    if (lang === 'zh-CN') return String(text).trim()

    const assignBasis = raw.match(/^([\s\S]+?)\n?【分配依据】([\s\S]+)$/)
    if (assignBasis) {
      const head = translateAppDynamicText(assignBasis[1].trim(), t, lang, getOpenCC)
      const basis = translateSegment(assignBasis[2].trim(), t, lang, getOpenCC)
      const label = lang === 'en' ? 'Assignment basis: ' : t('分配依据：')
      return `${head}\n${label}${basis}`
    }

    const full = applyFullInsightPatterns(raw, t, lang, getOpenCC)
    if (full) return full

    if (raw.includes('；')) {
      const sep = lang === 'zh-Hant' ? '；' : '; '
      return raw.split('；').map((s) => translateSegment(s, t, lang, getOpenCC)).join(sep)
    }

    let out = translateSegment(raw, t, lang, getOpenCC)
    if (lang === 'zh-Hant' && getOpenCC && out === raw) {
      const converter = getOpenCC()
      if (converter) return converter(raw)
    }
    return out
  }

  function formatInsightForUi(text, t, lang = 'en', getOpenCC) {
    if (text == null || text === '') return ''
    const raw = String(text)
    if (lang === 'zh-CN') return raw
    const hadPreview = AI_PREVIEW_SUFFIX_RE.test(raw)
    const core = stripAiPreviewSuffix(raw)
    let out = translateAppDynamicText(core, t, lang, getOpenCC)
    if (hadPreview) out += aiPreviewSuffix(lang, t)
    return out
  }

  function translateBackendInsight(text, t, lang = 'en', getOpenCC) {
    return formatInsightForUi(text, t, lang, getOpenCC)
  }

  const BOOT_SCREEN_I18N = {
    student: {
      en: {
        kicker: 'TeamMind · Classroom Runtime',
        title: 'Opening student collaboration workspace',
        subtitle: 'Preparing your classroom project workspace. Please wait.',
        step1: 'Connecting student workspace and session',
        step2: 'Loading classes, activities and candidate teams',
        step3: 'Syncing profile tags, task progress and messages',
        step4: 'Loading student UI and personal project space',
        foot: 'The workspace will open automatically when ready',
      },
      'zh-Hant': {
        kicker: '組隊超腦 · Classroom Runtime',
        title: '正在進入學生協作空間',
        subtitle: '正在為你準備本次課堂專案工作台，請稍候。',
        step1: '連接學員工作台與身分會話',
        step2: '載入我的班級、活動和候選團隊資料',
        step3: '同步畫像標籤、任務進度和社群訊息',
        step4: '裝載學生協作介面與個人專案空間',
        foot: '初始化完成後將自動開啟工作台',
      },
    },
    teacher: {
      en: {
        kicker: 'TeamMind · Classroom Runtime',
        title: 'Opening teacher command center',
        subtitle: 'Preparing your classroom project workspace. Please wait.',
        step1: 'Connecting classroom service and permission session',
        step2: 'Loading classes, student profiles and activity data',
        step3: 'Syncing task dashboard, risk alerts and AI grouping',
        step4: 'Loading teacher console and live classroom view',
        foot: 'The workspace will open automatically when ready',
      },
      'zh-Hant': {
        kicker: '組隊超腦 · Classroom Runtime',
        title: '正在進入教師課堂指揮艙',
        subtitle: '正在為你準備本次課堂專案工作台，請稍候。',
        step1: '連接本地課堂服務與權限會話',
        step2: '讀取班級、學生畫像與組隊活動資料庫',
        step3: '同步任務看板、風險預警和 AI 分組分析',
        step4: '裝載教師管理介面與即時課堂視圖',
        foot: '初始化完成後將自動開啟工作台',
      },
    },
  }

  function getStoredAppLang() {
    try {
      const urlLang = new URLSearchParams(window.location.search).get('lang')
      if (urlLang && urlLang !== 'zh-CN') return urlLang
      const app = localStorage.getItem('teammind_app_lang')
      const portal = localStorage.getItem('teammind_portal_lang')
      const candidates = [app, portal].filter(Boolean)
      const nonZh = candidates.find((l) => l && l !== 'zh-CN')
      if (nonZh) return nonZh
      return app || portal || 'zh-CN'
    } catch {
      return 'zh-CN'
    }
  }

  function applyBootScreenI18n(variant = 'student') {
    if (typeof window.teammindApplyBootInline === 'function') {
      window.teammindApplyBootInline()
      return
    }
    const lang = getStoredAppLang()
    document.documentElement.lang = lang === 'zh-Hant' ? 'zh-Hant' : (lang === 'en' ? 'en' : 'zh-CN')
    if (lang === 'zh-CN') return
    const pack = BOOT_SCREEN_I18N[variant]?.[lang] || BOOT_SCREEN_I18N[variant]?.en
    if (!pack) return
    document.querySelectorAll('[data-i18n-boot]').forEach((el) => {
      const key = el.getAttribute('data-i18n-boot')
      if (key && pack[key] != null) el.textContent = pack[key]
    })
  }

  function hideBootScreen() {
    const el = document.getElementById('app-loading')
    if (!el) return
    el.classList.add('boot-hidden')
    el.setAttribute('aria-hidden', 'true')
    document.documentElement.classList.remove('boot-loading')
    if (typeof window.teammindSetBootLoadingChrome === 'function') {
      window.teammindSetBootLoadingChrome(false)
    }
  }

  global.TeamMindI18n = {
    lookupTextTranslation,
    createTranslator,
    initOpenCC,
    DEMO_CONTENT_I18N,
    TAG_LEXICON_I18N,
    ACTIVITY_STATUS_ALIASES,
    normalizeActivityStatus,
    formatGroupingAdvice,
    translateDemoText,
    translateBackendInsight,
    formatInsightForUi,
    translateAppDynamicText,
    translateProfileLexicon,
    localizeTagCatalog,
    stripAiPreviewSuffix,
    BOOT_SCREEN_I18N,
    getStoredAppLang,
    applyBootScreenI18n,
    hideBootScreen,
  }
})(window)
