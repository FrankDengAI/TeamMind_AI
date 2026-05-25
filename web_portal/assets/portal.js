const LANG_KEY = 'teammind_portal_lang';
const portalStorage = {
  getItem(key) {
    try {
      return window.localStorage?.getItem(key) || null;
    } catch {
      return null;
    }
  },
  setItem(key, value) {
    try {
      window.localStorage?.setItem(key, value);
    } catch {
      // Ignore blocked storage; language falls back for the current page.
    }
  },
};
const DEFAULT_LANG = portalStorage.getItem(LANG_KEY) || 'zh-CN';

const LAUNCH_ICON_TEACHER = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <rect x="4" y="4" width="7" height="7" rx="1.6" fill="#fff" fill-opacity="0.96"/>
  <rect x="13" y="4" width="7" height="7" rx="1.6" fill="#fff" fill-opacity="0.78"/>
  <rect x="4" y="13" width="7" height="7" rx="1.6" fill="#fff" fill-opacity="0.78"/>
  <rect x="13" y="13" width="7" height="7" rx="1.6" fill="#fff" fill-opacity="0.96"/>
</svg>`;

const LAUNCH_ICON_STUDENT = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <circle cx="12" cy="6.5" r="2.4" fill="#fff"/>
  <circle cx="6.5" cy="16.5" r="2.4" fill="#fff" opacity="0.92"/>
  <circle cx="17.5" cy="16.5" r="2.4" fill="#fff" opacity="0.92"/>
  <path d="M12 9v1.8M12 10.8 8 14.2M12 10.8l4 3.4" stroke="#fff" stroke-width="1.7" stroke-linecap="round"/>
</svg>`;

const resources = {
  'zh-CN': {
    translation: {
      navProduct: '产品能力',
      navPricing: '定价',
      navWorkflow: '课堂流程',
      login: '登录',
      register: '注册',
      settings: '设置',
      language: '语言',
      languageHint: '英文使用 i18next 文案资源，繁体中文使用 opencc-js 公开库转换，避免手写转换规则。',
      brandLabel: '组队超脑 · TeamMind AI',
      brandKicker: '组队超脑 Classroom Runtime',
      pageTitle: '组队超脑 · TeamMind AI',
      heroBadge: 'AI 课堂协作分组平台',
      heroTitleA: '让每个课堂项目',
      heroTitleB: '像成熟团队一样协作',
      heroText: '组队超脑（TeamMind AI）从画像、候选组队、预沟通确认、任务分配、一周后调优到数据看板，帮助老师真实掌握每个小组的进度和参与度。',
      start: '开始使用',
      viewFlow: '查看流程',
      trustA: '画像驱动匹配',
      trustB: '候选组队确认',
      trustC: '任务与负载调优',
      trustD: '课堂过程性评价',
      liveTitle: '实时课堂指挥舱',
      metricA: '确认率',
      metricB: '完成率',
      metricC: '风险预警',
      flowTitle: 'AI 分组闭环',
      flowText: '画像匹配 -> 预沟通 -> 锁定团队 -> 任务分配 -> 周期调优 -> 数据看板',
      memberA: '学生画像已更新',
      memberB: '组内角色待确认',
      memberC: '任务反馈已进入调优池',
      sectionTitle: '为真实课堂设计，而不是只做一次自动分组',
      sectionText: '主流团队协作产品都会把自动建议、人类确认、过程数据和反馈闭环放在一起。组队超脑也遵循这个思路，让老师保留最终判断权，让学生有表达空间。',
      feature1Title: '班级健康度与 Copilot',
      feature1Text: '一屏掌握画像完成率、任务风险与待催办名单；自然语言问「谁该催、谁可能拖进度」。',
      feature2Title: '分组模板与多方案对比',
      feature2Text: '同质/异构/角色配额等 6 种策略，预览效果并排对比后再锁定正式分组。',
      feature3Title: '过程评价与任务模板',
      feature3Text: 'Rubric 量表打分、任务模板市场一键拆子任务，里程碑与组内看板同步进度。',
      feature4Title: '小组协作与超级报告',
      feature4Text: '组内频道、学生拖拽看板、一键催办站内通知；导出含健康摘要的超级分组 PDF。',
      modalTitleLogin: '选择你的身份后登录',
      modalTitleRegister: '选择你的身份后注册',
      modalText: '我们会根据身份进入不同工作台，避免学生和教师功能混在一起。',
      teacher: '我是教师',
      teacherText: '进入教师控制台，创建组队活动、管理确认期、分配任务并查看看板。',
      student: '我是学生',
      studentText: '进入学生端，填写画像、参与组队、确认角色、提交任务和反馈。',
      enterTeacher: '进入教师端',
      enterStudent: '进入学生端',
      teacherRegisterNote: '教师账号请由管理员预置',
      close: '关闭',
      launchTeacherTitle: '正在进入教师课堂指挥舱',
      launchStudentTitle: '正在进入学生协作空间',
      launchSubtitle: '正在为你准备本次课堂项目工作台，请稍候。',
      launchTeacherStepA: '连接本地课堂服务与权限会话',
      launchTeacherStepB: '读取班级、学生画像与组队活动数据库',
      launchTeacherStepC: '同步任务看板、风险预警和 AI 分组分析',
      launchTeacherStepD: '装载教师管理界面与实时课堂视图',
      launchStudentStepA: '连接学员工作台与身份会话',
      launchStudentStepB: '加载我的班级、活动和候选团队数据',
      launchStudentStepC: '同步画像标签、任务进度和社区消息',
      launchStudentStepD: '装载学生协作界面与个人项目空间',
      launchAlmost: '初始化完成，正在打开工作台...',
      footerLeft: '组队超脑 · TeamMind AI · 课堂协作操作系统',
      footerRight: '',
      classMode: '未来课堂实时运行中',
      classTitle: '第 4 周 · AI 产品原型课堂',
      teacherDesk: '教师指挥台',
      teacherDeskText: '确认分组、处理微调、追踪风险',
      studentPods: '学生协作舱',
      podA: 'A 组 · 原型设计',
      podB: 'B 组 · 数据分析',
      podC: 'C 组 · 汇报叙事',
      classTimeline: '课堂闭环节奏',
      timelineA: '画像',
      timelineB: '沟通',
      timelineC: '锁定',
      timelineD: '调优'
    }
  },
  en: {
    translation: {
      navProduct: 'Product',
      navPricing: 'Pricing',
      navWorkflow: 'Workflow',
      login: 'Log in',
      register: 'Sign up',
      settings: 'Settings',
      language: 'Language',
      languageHint: 'English uses i18next resources. Traditional Chinese uses the opencc-js public library instead of handwritten conversion rules.',
      brandLabel: 'TeamMind AI',
      brandKicker: 'TeamMind Classroom Runtime',
      pageTitle: 'TeamMind AI · Classroom Teaming',
      heroBadge: 'AI classroom teaming platform',
      heroTitleA: 'Turn every class project',
      heroTitleB: 'into real team collaboration',
      heroText: 'TeamMind AI connects profiling, candidate matching, pre-team communication, task assignment, weekly adjustment, and live dashboards so teachers can understand progress and engagement.',
      start: 'Get started',
      viewFlow: 'View workflow',
      trustA: 'Profile-driven matching',
      trustB: 'Candidate team confirmation',
      trustC: 'Task and workload adjustment',
      trustD: 'Process-based assessment',
      liveTitle: 'Live classroom command center',
      metricA: 'Confirm rate',
      metricB: 'Completion',
      metricC: 'Risk alerts',
      flowTitle: 'AI grouping loop',
      flowText: 'Profile match -> pre-talk -> lock team -> assign tasks -> weekly adjustment -> dashboard',
      memberA: 'Student profile updated',
      memberB: 'Team role awaiting confirmation',
      memberC: 'Task feedback entered adjustment pool',
      sectionTitle: 'Designed for real classrooms, not one-click grouping',
      sectionText: 'Modern collaboration products combine automated suggestions, human confirmation, process data, and feedback loops. TeamMind AI follows the same pattern while keeping teachers in control and giving students room to respond.',
      feature1Title: 'Class health & Copilot',
      feature1Text: 'See profile completion, task risks, and nudge lists; ask who is falling behind.',
      feature2Title: 'Grouping templates & compare',
      feature2Text: 'Six strategies with preview and side-by-side comparison before locking teams.',
      feature3Title: 'Rubric & task templates',
      feature3Text: 'Score with rubrics, apply task templates, milestones and team kanban.',
      feature4Title: 'Group chat & super report',
      feature4Text: 'Group channels, drag Kanban, in-app nudges, and PDF super group reports.',
      feature1Text: 'Students select active tags while the system combines interactions and task behavior into a composite profile.',
      feature2Title: 'Pre-team confirmation',
      feature2Text: 'Candidate teams discuss roles and task preferences before becoming official teams.',
      feature3Title: 'Task adjustment',
      feature3Text: 'After a week, progress, feedback, activity, and workload generate explainable adjustment suggestions.',
      feature4Title: 'Teaching dashboard',
      feature4Text: 'Teachers review completion, engagement, risks, feedback, and exports for coaching and grading.',
      modalTitleLogin: 'Choose your role to log in',
      modalTitleRegister: 'Choose your role to sign up',
      modalText: 'Each role opens a dedicated workspace so teacher and student workflows stay clear.',
      teacher: 'Teacher',
      teacherText: 'Open the teacher console to create activities, manage confirmations, assign tasks, and monitor dashboards.',
      student: 'Student',
      studentText: 'Open the student app to complete profiles, join teams, confirm roles, submit tasks, and give feedback.',
      enterTeacher: 'Open teacher console',
      enterStudent: 'Open student app',
      teacherRegisterNote: 'Teacher accounts should be provisioned by an administrator',
      close: 'Close',
      launchTeacherTitle: 'Opening the teacher command center',
      launchStudentTitle: 'Opening the student collaboration space',
      launchSubtitle: 'Preparing your classroom project workspace. Please wait.',
      launchTeacherStepA: 'Connecting classroom service and permission session',
      launchTeacherStepB: 'Loading classes, student profiles and activity database',
      launchTeacherStepC: 'Syncing task dashboard, risk alerts and AI grouping insights',
      launchTeacherStepD: 'Mounting teacher console and live classroom view',
      launchStudentStepA: 'Connecting student workspace and identity session',
      launchStudentStepB: 'Loading my classes, activities and candidate teams',
      launchStudentStepC: 'Syncing profile tags, task progress and community messages',
      launchStudentStepD: 'Mounting student collaboration workspace',
      launchAlmost: 'Initialization complete. Opening workspace...',
      footerLeft: 'TeamMind AI · Classroom collaboration operating system',
      footerRight: '',
      classMode: 'Future classroom live',
      classTitle: 'Week 4 · AI product prototype studio',
      teacherDesk: 'Teacher command desk',
      teacherDeskText: 'Confirm teams, resolve adjustments, track risks',
      studentPods: 'Student collaboration pods',
      podA: 'Team A · Prototype',
      podB: 'Team B · Data analysis',
      podC: 'Team C · Storytelling',
      classTimeline: 'Classroom loop',
      timelineA: 'Profile',
      timelineB: 'Talk',
      timelineC: 'Lock',
      timelineD: 'Adjust'
    }
  }
};

const portalExtras = {
  'zh-CN': {
    languageShort: '语言',
    showcaseTitle: '不只是首页展示，而是一套真实课堂协作系统',
    showcaseText: '从 18 名高层次学生画像、10 条真实项目动态，到候选分组、预沟通、任务分配和过程看板，所有环节都能直接进入课堂试运行。',
    statStudents: '高层次学生画像',
    statPosts: '真实项目社区帖',
    statGroups: '候选小组演示',
    loopTitle: 'AI 课堂协作闭环',
    loopText: '每一步都保留学生表达空间和教师最终判断权。',
    loopA: '画像采集',
    loopB: '候选分组',
    loopC: '预沟通确认',
    loopD: '锁定团队',
    loopE: '任务分配',
    loopF: '周期调优',
    loopG: '数据看板',
    roleTitle: '角色雷达',
    roleText: '系统不是简单贴标签，而是把能力、偏好和任务需要连接起来。',
    roleDev: '技术开发',
    roleData: '数据支持',
    roleDesign: '设计执行',
    roleWrite: '文档汇报',
    roleCoord: '协调对接',
    previewTitle: '进入产品前，先看到真实工作台',
    teacherPreviewTitle: '教师课堂指挥舱',
    teacherPreviewText: '创建活动、处理微调、锁定团队、分配任务、监督风险。',
    studentPreviewTitle: '学生协作空间',
    studentPreviewText: '填写画像、确认角色、查看队友、更新任务、提交反馈。',
    pricingTitle: '简单透明的课堂定价',
    pricingText: '大部分功能永久免费；教师按班级规模与 AI 算力升级，学生不付费。',
    planFree: '免费版',
    planPro: '专业版',
    planPlus: '旗舰版',
    planPopular: '80% 教师选择',
    planCTA: '进入教师端升级',
    trialCTA: '新教师送 7 天 Pro 试用',
    trialClaim: '登录教师端后一键领取',
    planPerMonth: '/月',
    planFreeF1: '1 班级 · 健康度看板',
    planFreeF2: '6 种分组模板 + 预览',
    planFreeF3: '学生 Kanban · 20 AI 点',
    planProF1: '班级 Copilot + 一键催办',
    planProF2: '多方案对比 + 超级分组报告',
    planProF3: 'Rubric 过程评价 · 500 AI 点',
    planPlusF1: '多班大班',
    planPlusF2: '2000 AI 点',
    planPlusF3: 'PDF 不限',
  },
  en: {
    languageShort: 'Language',
    showcaseTitle: 'More than a landing page: a real classroom collaboration system',
    showcaseText: 'From 18 advanced student profiles and 10 project posts to candidate teams, pre-team confirmation, task assignment, and live dashboards, every step is ready for classroom pilots.',
    statStudents: 'Advanced student profiles',
    statPosts: 'Project community posts',
    statGroups: 'Candidate team demos',
    loopTitle: 'AI classroom collaboration loop',
    loopText: 'Every step keeps room for student response and teacher judgment.',
    loopA: 'Profile',
    loopB: 'Candidate match',
    loopC: 'Pre-talk',
    loopD: 'Lock team',
    loopE: 'Assign tasks',
    loopF: 'Adjust',
    loopG: 'Dashboard',
    roleTitle: 'Role radar',
    roleText: 'The system connects skills, preferences, and task needs instead of just attaching labels.',
    roleDev: 'Developer',
    roleData: 'Data analyst',
    roleDesign: 'Designer',
    roleWrite: 'Storyteller',
    roleCoord: 'Coordinator',
    previewTitle: 'Preview the real workspaces before logging in',
    teacherPreviewTitle: 'Teacher command center',
    teacherPreviewText: 'Create activities, resolve adjustments, lock teams, assign tasks, and monitor risks.',
    studentPreviewTitle: 'Student collaboration space',
    studentPreviewText: 'Complete profiles, confirm roles, review teammates, update tasks, and submit feedback.',
    pricingTitle: 'Simple classroom pricing',
    pricingText: 'Core features stay free for students. Teachers upgrade for AI credits and exports.',
    planFree: 'Free',
    planPro: 'Pro',
    planPlus: 'Plus',
    planPopular: 'Most popular',
    planCTA: 'Open teacher console',
    trialCTA: '7-day Pro trial for new teachers',
    trialClaim: 'Claim in the teacher console after sign-in',
    planPerMonth: '/mo',
    planFreeF1: '1 class · up to 30 students',
    planFreeF2: 'Full team formation workflow',
    planFreeF3: '20 AI credits/month',
    planProF1: 'Class Copilot + one-click nudges',
    planProF2: 'Scenario compare + super group PDF',
    planProF3: 'Rubric scoring · 500 AI credits',
    planProF2: '500 AI credits',
    planProF3: 'Export without watermark',
    planPlusF1: 'Multi-class & large cohorts',
    planPlusF2: '2000 AI credits',
    planPlusF3: 'Unlimited PDF reports',
  },
};

Object.entries(portalExtras).forEach(([lang, extra]) => {
  resources[lang].translation = { ...resources[lang].translation, ...extra };
});

const LANGUAGE_OPTIONS = [
  { code: 'zh-CN', label: '简体中文' },
  { code: 'zh-Hant', label: '繁體中文' },
  { code: 'en', label: 'English' },
  { code: 'ja', label: '日本語' },
  { code: 'ko', label: '한국어' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'es', label: 'Español' },
];

const localizedResources = {
  ja: {
    ...resources.en.translation,
    navProduct: '製品機能', navWorkflow: '授業フロー', login: 'ログイン', register: '登録', settings: '設定', language: '言語', languageShort: '言語',
    heroBadge: 'AI 教室コラボレーション・プラットフォーム', heroTitleA: 'すべての授業プロジェクトを', heroTitleB: '本物のチーム協働へ',
    heroText: 'TeamMind AI はプロフィール、候補チーム、事前確認、タスク配分、週次調整、ダッシュボードをつなぎます。',
    start: 'はじめる', viewFlow: '流れを見る', teacher: '教師', student: '学生', enterTeacher: '教師画面へ', enterStudent: '学生画面へ', close: '閉じる',
    launchTeacherTitle: '教師用コマンドセンターを準備中', launchStudentTitle: '学生用コラボ空間を準備中', launchSubtitle: '授業プロジェクトのワークスペースを初期化しています。', launchAlmost: '初期化完了。ワークスペースを開きます...',
    showcaseTitle: '公開ページ以上の、実際に使える授業協働システム', roleTitle: '役割レーダー', previewTitle: 'ログイン前にワークスペースを確認',
  },
  ko: {
    ...resources.en.translation,
    navProduct: '제품 기능', navWorkflow: '수업 흐름', login: '로그인', register: '가입', settings: '설정', language: '언어', languageShort: '언어',
    heroBadge: 'AI 수업 협업 팀빌딩 플랫폼', heroTitleA: '모든 수업 프로젝트를', heroTitleB: '진짜 팀 협업으로',
    heroText: 'TeamMind AI는 프로필, 후보 팀, 사전 확인, 과제 배정, 주간 조정, 대시보드를 연결합니다.',
    start: '시작하기', viewFlow: '흐름 보기', teacher: '교사', student: '학생', enterTeacher: '교사용으로 이동', enterStudent: '학생용으로 이동', close: '닫기',
    launchTeacherTitle: '교사용 지휘 센터 준비 중', launchStudentTitle: '학생 협업 공간 준비 중', launchSubtitle: '수업 프로젝트 작업 공간을 초기화하고 있습니다.', launchAlmost: '초기화 완료. 작업 공간을 여는 중...',
    showcaseTitle: '랜딩 페이지를 넘어 실제 수업 협업 시스템으로', roleTitle: '역할 레이더', previewTitle: '로그인 전 실제 작업 공간 미리보기',
  },
  fr: {
    ...resources.en.translation,
    navProduct: 'Produit', navWorkflow: 'Parcours', login: 'Connexion', register: 'Inscription', settings: 'Paramètres', language: 'Langue', languageShort: 'Langue',
    heroBadge: 'Plateforme IA de collaboration en classe', heroTitleA: 'Transformez chaque projet', heroTitleB: 'en vraie collaboration',
    heroText: 'TeamMind AI relie profils, équipes candidates, confirmation, tâches, ajustements hebdomadaires et tableaux de bord.',
    start: 'Commencer', viewFlow: 'Voir le parcours', teacher: 'Enseignant', student: 'Étudiant', enterTeacher: 'Espace enseignant', enterStudent: 'Espace étudiant', close: 'Fermer',
    launchTeacherTitle: 'Ouverture du centre enseignant', launchStudentTitle: 'Ouverture de l’espace étudiant', launchSubtitle: 'Préparation de votre espace de projet en classe.', launchAlmost: 'Initialisation terminée. Ouverture...',
    showcaseTitle: 'Plus qu’une vitrine : un système réel de collaboration en classe', roleTitle: 'Radar des rôles', previewTitle: 'Prévisualiser les espaces avant connexion',
  },
  de: {
    ...resources.en.translation,
    navProduct: 'Produkt', navWorkflow: 'Ablauf', login: 'Anmelden', register: 'Registrieren', settings: 'Einstellungen', language: 'Sprache', languageShort: 'Sprache',
    heroBadge: 'KI-Plattform für Teamarbeit im Unterricht', heroTitleA: 'Jedes Kursprojekt wird', heroTitleB: 'zu echter Teamarbeit',
    heroText: 'TeamMind AI verbindet Profile, Teamvorschläge, Bestätigung, Aufgaben, wöchentliche Anpassung und Dashboards.',
    start: 'Loslegen', viewFlow: 'Ablauf ansehen', teacher: 'Lehrkraft', student: 'Studierende', enterTeacher: 'Lehrbereich öffnen', enterStudent: 'Studierendenbereich öffnen', close: 'Schließen',
    launchTeacherTitle: 'Lehrbereich wird vorbereitet', launchStudentTitle: 'Lernbereich wird vorbereitet', launchSubtitle: 'Der Kurs-Projektarbeitsbereich wird initialisiert.', launchAlmost: 'Initialisierung abgeschlossen. Bereich wird geöffnet...',
    showcaseTitle: 'Mehr als eine Startseite: ein echtes Kollaborationssystem', roleTitle: 'Rollenradar', previewTitle: 'Arbeitsbereiche vor dem Login ansehen',
  },
  es: {
    ...resources.en.translation,
    navProduct: 'Producto', navWorkflow: 'Flujo', login: 'Iniciar sesión', register: 'Registrarse', settings: 'Ajustes', language: 'Idioma', languageShort: 'Idioma',
    heroBadge: 'Plataforma IA para colaboración en clase', heroTitleA: 'Convierte cada proyecto', heroTitleB: 'en colaboración real',
    heroText: 'TeamMind AI conecta perfiles, equipos candidatos, confirmación, tareas, ajustes semanales y paneles en vivo.',
    start: 'Empezar', viewFlow: 'Ver flujo', teacher: 'Docente', student: 'Estudiante', enterTeacher: 'Abrir docentes', enterStudent: 'Abrir estudiantes', close: 'Cerrar',
    launchTeacherTitle: 'Abriendo el centro docente', launchStudentTitle: 'Abriendo el espacio del estudiante', launchSubtitle: 'Preparando tu espacio de proyecto de clase.', launchAlmost: 'Inicialización completa. Abriendo...',
    showcaseTitle: 'Más que una página: un sistema real de colaboración en clase', roleTitle: 'Radar de roles', previewTitle: 'Vista previa antes de entrar',
  },
};

Object.entries(localizedResources).forEach(([lang, translation]) => {
  resources[lang] = { translation };
});

let currentMode = 'login';
let openCCConverter = null;
let settingsOpen = false;
let lastModalTrigger = null;
let launchTimer = null;

function showPortalError(message) {
  const root = document.getElementById('app') || document.body;
  root.innerHTML = `
    <main style="min-height:100vh;display:grid;place-items:center;padding:32px;background:#f8fafc;color:#0f172a;font-family:Segoe UI,Microsoft YaHei,sans-serif">
      <section style="max-width:560px;padding:28px;border:1px solid #fee2e2;border-radius:22px;background:#fff;box-shadow:0 20px 60px rgba(15,23,42,.12)">
        <h1 style="margin:0 0 12px;font-size:24px">页面资源加载失败</h1>
        <p style="margin:0 0 14px;line-height:1.7;color:#475569">${message}</p>
        <p style="margin:0;color:#64748b">请检查网络/CDN 资源后刷新页面，或使用本地启动脚本重新启动服务。</p>
      </section>
    </main>
  `;
}

async function initI18n() {
  if (!window.i18next?.init) {
    showPortalError('i18next 国际化资源未加载，门户暂时无法初始化。');
    return;
  }
  await i18next.init({
    lng: DEFAULT_LANG === 'zh-Hant' ? 'zh-CN' : DEFAULT_LANG,
    fallbackLng: 'zh-CN',
    resources,
  });
  if (window.OpenCC?.Converter) {
    openCCConverter = OpenCC.Converter({ from: 'cn', to: 'tw' });
  }
  applyPageTitle();
  render();
  renderCanvas();
}

function t(key) {
  const raw = i18next.t(key);
  const lang = portalStorage.getItem(LANG_KEY) || DEFAULT_LANG;
  if (lang === 'zh-Hant' && openCCConverter) return openCCConverter(raw);
  return raw;
}

function applyPageTitle() {
  document.title = t('pageTitle') || 'TeamMind AI';
}

function syncAppLangPreference(lang) {
  portalStorage.setItem(LANG_KEY, lang);
  try {
    window.localStorage?.setItem('teammind_app_lang', lang);
  } catch {
    // Ignore blocked storage; portal language still applies for this session.
  }
}

function setLang(lang) {
  syncAppLangPreference(lang);
  i18next.changeLanguage(lang === 'zh-Hant' ? 'zh-CN' : lang).then(() => {
    applyPageTitle();
    render();
  });
}

function currentLang() {
  return portalStorage.getItem(LANG_KEY) || DEFAULT_LANG;
}

function openRoleModal(mode) {
  currentMode = mode;
  lastModalTrigger = document.activeElement;
  const modal = document.querySelector('.role-modal');
  modal?.removeAttribute('hidden');
  modal?.setAttribute('aria-hidden', 'false');
  document.querySelector('.modal-title').textContent = t(mode === 'login' ? 'modalTitleLogin' : 'modalTitleRegister');
  document.querySelector('[data-action="close"]')?.focus();
}

function closeRoleModal() {
  const modal = document.querySelector('.role-modal');
  modal?.setAttribute('hidden', '');
  modal?.setAttribute('aria-hidden', 'true');
  lastModalTrigger?.focus?.();
}

function launchSteps(role) {
  const prefix = role === 'teacher' ? 'launchTeacherStep' : 'launchStudentStep';
  return ['A', 'B', 'C', 'D'].map((item) => t(`${prefix}${item}`));
}

function appendLangToUrl(url, lang) {
  if (!lang || lang === 'zh-CN') return url
  try {
    const u = new URL(url, window.location.origin)
    u.searchParams.set('lang', lang)
    return `${u.pathname}${u.search}${u.hash}`
  } catch {
    const sep = url.includes('?') ? '&' : '?'
    return `${url}${sep}lang=${encodeURIComponent(lang)}`
  }
}

function openLaunchOverlay(role, url) {
  const lang = currentLang()
  syncAppLangPreference(lang)
  const targetUrl = appendLangToUrl(url, lang)
  window.clearTimeout(launchTimer)
  closeRoleModal();
  const existing = document.querySelector('.launch-overlay');
  existing?.remove();
  const steps = launchSteps(role);
  const overlay = document.createElement('section');
  overlay.className = 'launch-overlay';
  overlay.setAttribute('aria-live', 'polite');
  overlay.innerHTML = `
    <div class="launch-shell ${role}">
      <div class="launch-orbit" aria-hidden="true">
        <span></span><span></span><span></span>
      </div>
      <div class="launch-card">
        <div class="launch-mark">
          <span>${role === 'teacher' ? LAUNCH_ICON_TEACHER : LAUNCH_ICON_STUDENT}</span>
        </div>
        <p class="launch-kicker">${t('brandKicker')}</p>
        <h2>${t(role === 'teacher' ? 'launchTeacherTitle' : 'launchStudentTitle')}</h2>
        <p class="launch-subtitle">${t('launchSubtitle')}</p>
        <div class="launch-progress"><span></span></div>
        <div class="launch-steps">
          ${steps.map((step, index) => `<div class="launch-step ${index === 0 ? 'active' : ''}"><b>0${index + 1}</b><span>${step}</span></div>`).join('')}
        </div>
        <div class="launch-foot">
          <span class="launch-pulse"></span>
          <strong>${steps[0]}</strong>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  requestAnimationFrame(() => overlay.classList.add('show'));
  const foot = overlay.querySelector('.launch-foot strong');
  overlay.querySelectorAll('.launch-step').forEach((step, index) => {
    window.setTimeout(() => {
      overlay.querySelectorAll('.launch-step').forEach((item, inner) => item.classList.toggle('active', inner <= index));
      if (foot) foot.textContent = steps[index];
    }, 260 + index * 380);
  });
  window.setTimeout(() => {
    if (foot) foot.textContent = t('launchAlmost');
    overlay.classList.add('ready');
  }, 1660);
  launchTimer = window.setTimeout(() => {
    window.location.href = targetUrl;
  }, 2050);
}

function render() {
  document.documentElement.lang = currentLang() === 'en' ? 'en' : currentLang();
  document.getElementById('app').innerHTML = `
    <aside class="settings-rail" aria-label="${t('settings')}">
      <button class="rail-button" data-action="toggle-settings" title="${t('settings')}" aria-expanded="${settingsOpen}">⚙</button>
    </aside>
    <section class="settings-panel" ${settingsOpen ? '' : 'hidden'} aria-live="polite">
      <h3>${t('settings')}</h3>
      <p>${t('languageHint')}</p>
      <div class="language-grid">
        ${LANGUAGE_OPTIONS.map((item) => languageButton(item.code, item.label)).join('')}
      </div>
    </section>

    <header class="topbar">
      <div class="brand"><span class="brand-mark"></span><span>${t('brandLabel')}</span></div>
      <nav class="nav">
        <a href="#product">${t('navProduct')}</a>
        <a href="#pricing">${t('navPricing')}</a>
        <a href="#workflow">${t('navWorkflow')}</a>
      </nav>
      <div class="actions">
        ${languageSelect()}
        <button data-action="login">${t('login')}</button>
        <button class="primary" data-action="register">${t('register')}</button>
      </div>
    </header>

    <main>
      <section class="hero">
        <div>
          <span class="eyebrow">${t('heroBadge')}</span>
          <h1><span class="gradient-text">${t('heroTitleA')}</span><br />${t('heroTitleB')}</h1>
          <p class="hero-copy">${t('heroText')}</p>
          <div class="hero-actions">
            <button class="primary" data-action="login">${t('start')}</button>
            <a class="button" href="#workflow">${t('viewFlow')}</a>
          </div>
          <div class="trust-row">
            <span>${t('trustA')}</span><span>${t('trustB')}</span><span>${t('trustC')}</span><span>${t('trustD')}</span>
          </div>
        </div>
        <div class="product-orbit" aria-label="${t('liveTitle')}">
          <div class="classroom-glow"></div>
          <div class="dashboard-card">
            <div class="screen-head">
              <span class="eyebrow">${t('classMode')}</span>
              <span class="live-dot">LIVE</span>
            </div>
            <h3 class="class-title">${t('classTitle')}</h3>
            <div class="classroom-map">
              <div class="teacher-console">
                <strong>${t('teacherDesk')}</strong>
                <span>${t('teacherDeskText')}</span>
              </div>
              <div class="seat-grid">
                ${Array.from({ length: 28 }, (_, i) => `<span class="seat ${i % 7 === 0 ? 'active' : ''}"></span>`).join('')}
              </div>
            </div>
            <div class="metrics">
              <div class="metric"><strong>86%</strong><span>${t('metricA')}</span></div>
              <div class="metric"><strong>72%</strong><span>${t('metricB')}</span></div>
              <div class="metric"><strong>5</strong><span>${t('metricC')}</span></div>
            </div>
            <div class="flow-card">
              <div class="flow-card-head">
                <h4>${t('classTimeline')}</h4>
                <span>${t('flowTitle')}</span>
              </div>
              <div class="timeline-steps">
                <b>${t('timelineA')}</b><b>${t('timelineB')}</b><b>${t('timelineC')}</b><b>${t('timelineD')}</b>
              </div>
              <div class="flow-line"><span></span></div>
            </div>
            <div class="pod-title">${t('studentPods')}</div>
            <div class="team-list">
              ${teamItem(t('podA'))}
              ${teamItem(t('podB'))}
              ${teamItem(t('podC'))}
            </div>
          </div>
        </div>
      </section>

      <section class="section" id="product">
        <div class="section-head">
          <h2>${t('sectionTitle')}</h2>
          <p>${t('sectionText')}</p>
        </div>
        <div class="feature-grid" id="workflow">
          ${feature('01', t('feature1Title'), t('feature1Text'))}
          ${feature('02', t('feature2Title'), t('feature2Text'))}
          ${feature('03', t('feature3Title'), t('feature3Text'))}
          ${feature('04', t('feature4Title'), t('feature4Text'))}
        </div>
      </section>

      <section class="section pricing-section" id="pricing">
        <div class="section-head">
          <h2>${t('pricingTitle')}</h2>
          <p>${t('pricingText')}</p>
        </div>
        <div class="pricing-grid" id="pricing-grid">
          <article class="pricing-card"><h3>${t('planFree')}</h3><p class="price">¥0</p><ul><li>${t('planFreeF1')}</li><li>${t('planFreeF2')}</li><li>${t('planFreeF3')}</li></ul></article>
          <article class="pricing-card popular"><span class="pricing-badge">${t('planPopular')}</span><h3>${t('planPro')}</h3><p class="price">¥49<small>${t('planPerMonth')}</small></p><ul><li>${t('planProF1')}</li><li>${t('planProF2')}</li><li>${t('planProF3')}</li></ul><a class="button primary" href="/admin/#billing">${t('planCTA')}</a></article>
          <article class="pricing-card"><h3>${t('planPlus')}</h3><p class="price">¥129<small>${t('planPerMonth')}</small></p><ul><li>${t('planPlusF1')}</li><li>${t('planPlusF2')}</li><li>${t('planPlusF3')}</li></ul><a class="button" href="/admin/#billing">${t('planCTA')}</a></article>
        </div>
        <p class="pricing-trial"><a href="/admin/">${t('trialCTA')}</a> · ${t('trialClaim')}</p>
      </section>

      <section class="section showcase-section">
        <div class="section-head">
          <span class="eyebrow">${t('loopTitle')}</span>
          <h2>${t('showcaseTitle')}</h2>
          <p>${t('showcaseText')}</p>
        </div>
        <div class="stat-strip">
          ${statCard('18', t('statStudents'))}
          ${statCard('10', t('statPosts'))}
          ${statCard('5', t('statGroups'))}
        </div>
        <div class="loop-rail" aria-label="${t('loopTitle')}">
          ${['loopA', 'loopB', 'loopC', 'loopD', 'loopE', 'loopF', 'loopG'].map((key, index) => loopStep(index + 1, t(key))).join('')}
        </div>
        <div class="showcase-grid">
          <article class="radar-card">
            <h3>${t('roleTitle')}</h3>
            <p>${t('roleText')}</p>
            <div class="role-radar">
              ${roleCard('01', t('roleDev'), '92%')}
              ${roleCard('02', t('roleData'), '88%')}
              ${roleCard('03', t('roleDesign'), '84%')}
              ${roleCard('04', t('roleWrite'), '79%')}
              ${roleCard('05', t('roleCoord'), '86%')}
            </div>
          </article>
          <article class="preview-card">
            <h3>${t('previewTitle')}</h3>
            <div class="preview-grid">
              ${previewCard('Teacher', t('teacherPreviewTitle'), t('teacherPreviewText'))}
              ${previewCard('Student', t('studentPreviewTitle'), t('studentPreviewText'))}
            </div>
          </article>
        </div>
      </section>
    </main>

    <footer><span>${t('footerLeft')}</span>${t('footerRight') ? `<span>${t('footerRight')}</span>` : ''}</footer>

    <section class="role-modal" role="dialog" aria-modal="true" aria-hidden="true" aria-labelledby="role-modal-title" hidden>
      <div class="modal-card">
        <div class="modal-head">
          <div>
            <h3 class="modal-title" id="role-modal-title">${t('modalTitleLogin')}</h3>
            <p>${t('modalText')}</p>
          </div>
          <button data-action="close">${t('close')}</button>
        </div>
        <div class="role-grid">
          <article class="role-card">
            <h4>${t('teacher')}</h4>
            <p>${t('teacherText')}</p>
            <div class="role-actions">
              <a class="button primary launch-link" href="/admin/" data-launch-role="teacher" data-launch-url="/admin/">${t('enterTeacher')}</a>
              <span class="button">${t('teacherRegisterNote')}</span>
            </div>
          </article>
          <article class="role-card">
            <h4>${t('student')}</h4>
            <p>${t('studentText')}</p>
            <div class="role-actions">
              <a class="button primary launch-link" href="/student/" data-launch-role="student" data-launch-url="/student/">${t('enterStudent')}</a>
            </div>
          </article>
        </div>
      </div>
    </section>
  `;
  bindEvents();
}

function languageButton(lang, label) {
  return `<button class="${currentLang() === lang ? 'active' : ''}" data-lang="${lang}">${label}</button>`;
}

function languageSelect() {
  const current = LANGUAGE_OPTIONS.find((item) => item.code === currentLang()) || LANGUAGE_OPTIONS[0];
  return `
    <label class="top-language">
      <span>${t('languageShort')}</span>
      <select data-lang-select aria-label="${t('language')}">
        ${LANGUAGE_OPTIONS.map((item) => `<option value="${item.code}" ${item.code === current.code ? 'selected' : ''}>${item.label}</option>`).join('')}
      </select>
    </label>
  `;
}

function feature(index, title, text) {
  return `<article class="feature-card"><b>${index}</b><h3>${title}</h3><p>${text}</p></article>`;
}

function teamItem(text) {
  return `<div class="team-member"><span>${text}</span><span class="pulse"></span></div>`;
}

function statCard(num, label) {
  return `<div class="portal-stat"><strong>${num}</strong><span>${label}</span></div>`;
}

function loopStep(num, label) {
  return `<div class="loop-step"><b>${String(num).padStart(2, '0')}</b><span>${label}</span></div>`;
}

function roleCard(index, label, score) {
  return `<div class="role-chip"><span>${index}</span><strong>${label}</strong><em>${score}</em></div>`;
}

function previewCard(kind, title, text) {
  return `<div class="workspace-preview"><b>${kind}</b><strong>${title}</strong><span>${text}</span></div>`;
}

function bindEvents() {
  document.querySelectorAll('[data-action="login"]').forEach((el) => el.addEventListener('click', () => openRoleModal('login')));
  document.querySelectorAll('[data-action="register"]').forEach((el) => el.addEventListener('click', () => openRoleModal('register')));
  document.querySelectorAll('.launch-link').forEach((el) => {
    el.addEventListener('click', (event) => {
      event.preventDefault();
      const lang = currentLang();
      syncAppLangPreference(lang);
      const url = el.dataset.launchUrl || el.getAttribute('href');
      window.location.href = appendLangToUrl(url, lang);
    });
  });
  document.querySelector('[data-action="close"]')?.addEventListener('click', closeRoleModal);
  document.querySelector('.role-modal')?.addEventListener('click', (event) => {
    if (event.target.classList.contains('role-modal')) closeRoleModal();
  });
  document.onkeydown = (event) => {
    if (event.key === 'Escape' && !document.querySelector('.role-modal')?.hasAttribute('hidden')) {
      closeRoleModal();
    }
  };
  document.querySelector('[data-action="toggle-settings"]')?.addEventListener('click', () => {
    const panel = document.querySelector('.settings-panel');
    if (!panel) return;
    settingsOpen = !settingsOpen;
    panel.toggleAttribute('hidden', !settingsOpen);
    document.querySelector('[data-action="toggle-settings"]')?.setAttribute('aria-expanded', String(settingsOpen));
  });
  document.querySelectorAll('[data-lang]').forEach((el) => el.addEventListener('click', () => setLang(el.dataset.lang)));
  document.querySelector('[data-lang-select]')?.addEventListener('change', (event) => setLang(event.target.value));
}

function renderCanvas() {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const particles = Array.from({ length: 82 }, () => ({
    x: Math.random(),
    y: Math.random(),
    vx: (Math.random() - 0.5) * 0.0007,
    vy: (Math.random() - 0.5) * 0.0007,
    r: 1 + Math.random() * 2.6,
  }));

  function resize() {
    canvas.width = window.innerWidth * window.devicePixelRatio;
    canvas.height = window.innerHeight * window.devicePixelRatio;
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
  }

  function frame() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    ctx.clearRect(0, 0, w, h);
    particles.forEach((p, i) => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > 1) p.vx *= -1;
      if (p.y < 0 || p.y > 1) p.vy *= -1;
      const x = p.x * w;
      const y = p.y * h;
      ctx.beginPath();
      ctx.fillStyle = i % 3 === 0 ? 'rgba(34,211,238,.55)' : 'rgba(196,181,253,.42)';
      ctx.arc(x, y, p.r, 0, Math.PI * 2);
      ctx.fill();
      for (let j = i + 1; j < particles.length; j += 1) {
        const q = particles[j];
        const dx = x - q.x * w;
        const dy = y - q.y * h;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 130) {
          ctx.strokeStyle = `rgba(125, 211, 252, ${0.12 * (1 - dist / 130)})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(q.x * w, q.y * h);
          ctx.stroke();
        }
      }
    });
    requestAnimationFrame(frame);
  }

  resize();
  window.addEventListener('resize', resize);
  frame();
}

initI18n();
