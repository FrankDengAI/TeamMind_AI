/**
 * 启动屏即时 i18n（紧接在 #app-loading 后同步执行，不依赖 Vue / i18n-core 加载顺序）
 */
;(function () {
  const PACKS = {
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
  }

  function bootLang() {
    try {
      const q = new URLSearchParams(window.location.search).get('lang')
      if (q && q !== 'zh-CN') return q
      const app = localStorage.getItem('teammind_app_lang')
      const portal = localStorage.getItem('teammind_portal_lang')
      if (app && app !== 'zh-CN') return app
      if (portal && portal !== 'zh-CN') return portal
    } catch {
      // ignore
    }
    return 'zh-CN'
  }

  function applyBootInline() {
    const card = document.querySelector('.boot-card')
    if (!card) return bootLang()
    const variant = card.getAttribute('data-boot-variant') || 'student'
    const lang = bootLang()
    document.documentElement.lang = lang === 'zh-Hant' ? 'zh-Hant' : (lang === 'en' ? 'en' : 'zh-CN')
    if (lang === 'zh-CN') return lang
    const pack = PACKS[variant]?.[lang] || PACKS[variant]?.en
    if (!pack) return lang
    document.querySelectorAll('[data-i18n-boot]').forEach((el) => {
      const key = el.getAttribute('data-i18n-boot')
      if (key && pack[key] != null) el.textContent = pack[key]
    })
    return lang
  }

  function setBootLoadingChrome(active) {
    document.documentElement.classList.toggle('boot-loading', active)
  }

  applyBootInline()
  setBootLoadingChrome(true)
  window.teammindBootLang = bootLang
  window.teammindApplyBootInline = applyBootInline
  window.teammindSetBootLoadingChrome = setBootLoadingChrome
})()
