/**
 * 组队超脑（TeamMind AI）用户端 — 学员使用（默认由 5000 /student/ 托管）
 */
const TeamMindRuntime = (() => {
  const getStorage = () => {
    try {
      return window.localStorage || (typeof localStorage !== 'undefined' ? localStorage : null)
    } catch {
      return null
    }
  }
  const storage = {
    getItem(key) {
      try { return getStorage()?.getItem(key) || null } catch { return null }
    },
    setItem(key, value) {
      try { getStorage()?.setItem(key, value) } catch {}
    },
    removeItem(key) {
      try { getStorage()?.removeItem(key) } catch {}
    },
  }
  function showBootError(message) {
    if (typeof document === 'undefined') return
    const root = document.getElementById('app') || document.body
    root.innerHTML = `
      <main style="min-height:100vh;display:grid;place-items:center;padding:32px;background:#f8fafc;color:#0f172a;font-family:Segoe UI,Microsoft YaHei,sans-serif">
        <section style="max-width:560px;padding:28px;border:1px solid #fee2e2;border-radius:22px;background:#fff;box-shadow:0 20px 60px rgba(15,23,42,.12)">
          <h1 style="margin:0 0 12px;font-size:24px">学员端资源加载失败</h1>
          <p style="margin:0 0 14px;line-height:1.7;color:#475569">${message}</p>
          <p style="margin:0;color:#64748b">请检查网络/CDN 资源后刷新页面，或重新运行启动脚本。</p>
        </section>
      </main>
    `
  }
  return { storage, showBootError }
})()
const VueRuntime = window.Vue || (typeof Vue !== 'undefined' ? Vue : {})
const { createApp, ref, computed, onMounted, onUnmounted, watch, nextTick } = VueRuntime
if (typeof document !== 'undefined' && (!createApp || !window.axios || !window.ElementPlus)) {
  TeamMindRuntime.showBootError('Vue、Element Plus 或 axios 未能加载，应用无法启动。')
  throw new Error('TeamMind student runtime dependency missing')
}

const API_BASE = window.TEAMMIND_API_BASE || 'http://127.0.0.1:5000/api'
const ADMIN_PORTAL_URL = window.TEAMMIND_ADMIN_URL || 'http://127.0.0.1:5000/'
const APP_LANG_KEY = 'teammind_app_lang'
const VALID_APP_LANGS = new Set(['zh-CN', 'zh-Hant', 'en', 'ja', 'ko', 'fr', 'de', 'es'])
function resolveInitialAppLang() {
  try {
    const app = TeamMindRuntime.storage.getItem(APP_LANG_KEY)
    const portal = TeamMindRuntime.storage.getItem('teammind_portal_lang')
    const candidates = [app, portal].filter(Boolean)
    const nonZh = candidates.find((l) => l && l !== 'zh-CN')
    const pick = nonZh || app || portal || 'zh-CN'
    return VALID_APP_LANGS.has(pick) ? pick : 'zh-CN'
  } catch {
    return 'zh-CN'
  }
}
const DEFAULT_APP_LANG = resolveInitialAppLang()
const LANGUAGE_OPTIONS = [
  { code: 'zh-CN', label: '简体中文' },
  { code: 'zh-Hant', label: '繁體中文' },
  { code: 'en', label: 'English' },
  { code: 'ja', label: '日本語' },
  { code: 'ko', label: '한국어' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'es', label: 'Español' },
]

const NAV_ITEMS = [
  {
    key: 'classes',
    icon: '🏫',
    label: '我的班级',
    desc: '查看已加入班级，申请加入或退出课程班级。',
  },
  {
    key: 'profile',
    icon: '📝',
    label: '能力画像',
    desc: '先选择与你相关的标签，也可以补充一段简单介绍。',
  },
  {
    key: 'team',
    icon: '👥',
    label: '我的团队',
    desc: '查看所在小组、组内分工和队友任务进度。',
  },
  {
    key: 'tasks',
    icon: '✅',
    label: '我的任务',
    desc: '查看自己的任务、截止时间，并更新完成进度。',
  },
  {
    key: 'community',
    icon: '📚',
    label: '学习社区',
    desc: '发布学习兴趣、项目经验和资源分享。',
  },
  {
    key: 'messages',
    icon: '💬',
    label: '消息',
    desc: '和同学进行项目沟通与协作讨论。',
  },
]
const PAGE_KEYS = [...NAV_ITEMS.map((n) => n.key), 'account']

const STUDENT_I18N = {
  'zh-CN': {
    brandTitle: '组队超脑',
    brandShort: '组队超脑',
    brandEn: 'TeamMind AI',
    pageTitle: '组队超脑 · 学员端 | TeamMind AI',
    workspaceName: '学员工作台',
    loginTagline: '组队 · 任务 · 进度 · 沟通，一站式完成课程项目',
    loginFeatureA: '选择标签，快速生成适合你的项目角色建议',
    loginFeatureB: '在团队页查看队友进度，及时沟通协作',
    loginFeatureC: '在个人任务页更新子任务完成率，关注截止预警',
    loginTitle: '学员登录',
    loginSub: '注册或登录后开始使用',
    login: '登录',
    register: '注册',
    account: '账号',
    password: '密码',
    name: '姓名',
    adminHint: '老师/管理员请访问',
    adminBackend: '管理后台',
    switchToAdmin: '进入教师端',
    switchToAdminHint: '切换到教师视角管理分组、任务和看板',
    profileHome: '个人主页',
    logout: '退出登录',
    accountNavLabel: '个人主页',
    accountNavDesc: '设置头像、个人介绍和登录密码',
    language: '界面语言',
    languageShared: '此语言偏好与教师端共用；切换后会保存在当前浏览器。',
    profileCard: '个人资料',
    saveProfile: '保存资料',
    nav: {
      classes: ['我的班级', '查看已加入班级，申请加入或退出课程班级。'],
      profile: ['能力画像', '先选择与你相关的标签，也可以补充一段简单介绍。'],
      team: ['我的团队', '查看所在小组、组内分工和队友任务进度。'],
      tasks: ['我的任务', '查看自己的任务、截止时间，并更新完成进度。'],
      community: ['学习社区', '发布学习兴趣、项目经验和资源分享。'],
      messages: ['消息', '和同学进行项目沟通与协作讨论。'],
    },
  },
  en: {
    brandTitle: 'TeamMind AI',
    brandShort: 'TeamMind AI',
    brandEn: 'TeamMind AI',
    pageTitle: 'TeamMind AI · Student',
    workspaceName: 'Student Workspace',
    loginTagline: 'Teams, tasks, progress and communication in one project workspace',
    loginFeatureA: 'Choose tags and get project role suggestions quickly',
    loginFeatureB: 'Review teammate progress and communicate in time',
    loginFeatureC: 'Update task progress and watch deadline alerts',
    loginTitle: 'Student Login',
    loginSub: 'Sign up or log in to get started',
    login: 'Log in',
    register: 'Sign up',
    account: 'Account',
    password: 'Password',
    name: 'Name',
    adminHint: 'Teachers/admins should use',
    adminBackend: 'Admin Console',
    switchToAdmin: 'Open Teacher App',
    switchToAdminHint: 'Switch to the teacher view for groups, tasks and dashboards.',
    profileHome: 'Profile',
    logout: 'Log out',
    accountNavLabel: 'Profile',
    accountNavDesc: 'Set avatar, bio and password',
    language: 'Language',
    languageShared: 'This preference is shared with the teacher workspace in the current browser.',
    profileCard: 'Profile',
    saveProfile: 'Save profile',
    nav: {
      classes: ['My Classes', 'View joined classes and request to join or leave.'],
      profile: ['Ability Profile', 'Choose related tags and optionally add a short introduction.'],
      team: ['My Team', 'Review your group, role assignment and teammate progress.'],
      tasks: ['My Tasks', 'Review tasks, deadlines and update progress.'],
      community: ['Learning Community', 'Share interests, project experience and resources.'],
      messages: ['Messages', 'Discuss projects and collaboration with classmates.'],
    },
  },
}

Object.assign(STUDENT_I18N, {
  'zh-Hant': {
    ...STUDENT_I18N['zh-CN'],
    workspaceName: '學員工作台',
    language: '介面語言',
    languageShared: '此語言偏好與教師端共用；切換後會保存在目前瀏覽器。',
    profileCard: '個人資料',
    saveProfile: '保存資料',
    nav: {
      classes: ['我的班級', '查看已加入班級，申請加入或退出課程班級。'],
      profile: ['能力畫像', '先選擇與你相關的標籤，也可以補充一段簡單介紹。'],
      team: ['我的團隊', '查看所在小組、組內分工和隊友任務進度。'],
      tasks: ['我的任務', '查看自己的任務、截止時間，並更新完成進度。'],
      community: ['學習社群', '發布學習興趣、專案經驗和資源分享。'],
      messages: ['訊息', '和同學進行專案溝通與協作討論。'],
    },
  },
  ja: {
    ...STUDENT_I18N.en,
    workspaceName: '学生ワークスペース',
    language: '言語',
    languageShared: 'この設定は教師用ワークスペースと共有されます。',
    profileCard: 'プロフィール',
    saveProfile: '保存',
    nav: {
      classes: ['マイクラス', '参加済みクラスを確認し、参加・退出を申請します。'],
      profile: ['能力プロフィール', '関連タグを選び、短い自己紹介を追加できます。'],
      team: ['マイチーム', 'チーム、役割、メンバー進捗を確認します。'],
      tasks: ['マイタスク', 'タスク、期限、進捗を確認します。'],
      community: ['学習コミュニティ', '興味、経験、資料を共有します。'],
      messages: ['メッセージ', 'クラスメートとプロジェクトを相談します。'],
    },
  },
  ko: {
    ...STUDENT_I18N.en,
    workspaceName: '학생 워크스페이스',
    language: '언어',
    languageShared: '이 설정은 교사용 워크스페이스와 공유됩니다.',
    profileCard: '프로필',
    saveProfile: '저장',
    nav: {
      profile: ['역량 프로필', '관련 태그를 선택하고 짧은 소개를 추가할 수 있습니다.'],
      team: ['내 팀', '팀, 역할, 팀원 진행 상황을 확인합니다.'],
      tasks: ['내 작업', '작업, 마감일, 진행률을 확인합니다.'],
      community: ['학습 커뮤니티', '관심사, 경험, 자료를 공유합니다.'],
      messages: ['메시지', '동료와 프로젝트 협업을 논의합니다.'],
    },
  },
  fr: {
    ...STUDENT_I18N.en,
    workspaceName: 'Espace étudiant',
    language: 'Langue',
    languageShared: 'Ce choix est partagé avec l’espace enseignant.',
    profileCard: 'Profil',
    saveProfile: 'Enregistrer',
    nav: {
      profile: ['Profil de compétences', 'Choisissez des tags et ajoutez une courte présentation.'],
      team: ['Mon équipe', 'Consultez votre équipe, rôle et progression des membres.'],
      tasks: ['Mes tâches', 'Consultez les tâches, échéances et progression.'],
      community: ['Communauté', 'Partagez intérêts, expériences et ressources.'],
      messages: ['Messages', 'Discutez du projet avec vos camarades.'],
    },
  },
  de: {
    ...STUDENT_I18N.en,
    workspaceName: 'Lernbereich',
    language: 'Sprache',
    languageShared: 'Diese Einstellung wird mit dem Lehrbereich geteilt.',
    profileCard: 'Profil',
    saveProfile: 'Speichern',
    nav: {
      profile: ['Kompetenzprofil', 'Wählen Sie Tags und ergänzen Sie optional eine kurze Vorstellung.'],
      team: ['Mein Team', 'Team, Rolle und Fortschritt der Mitglieder ansehen.'],
      tasks: ['Meine Aufgaben', 'Aufgaben, Fristen und Fortschritt ansehen.'],
      community: ['Lern-Community', 'Interessen, Erfahrungen und Ressourcen teilen.'],
      messages: ['Nachrichten', 'Projektarbeit mit Kommilitonen besprechen.'],
    },
  },
  es: {
    ...STUDENT_I18N.en,
    workspaceName: 'Espacio del estudiante',
    language: 'Idioma',
    languageShared: 'Esta preferencia se comparte con el espacio docente.',
    profileCard: 'Perfil',
    saveProfile: 'Guardar',
    nav: {
      profile: ['Perfil de habilidades', 'Elige etiquetas y añade una breve presentación.'],
      team: ['Mi equipo', 'Consulta equipo, rol y progreso de compañeros.'],
      tasks: ['Mis tareas', 'Consulta tareas, plazos y progreso.'],
      community: ['Comunidad', 'Comparte intereses, experiencias y recursos.'],
      messages: ['Mensajes', 'Habla del proyecto con tus compañeros.'],
    },
  },
})

const STUDENT_TEXT_I18N = {
  en: {
    学员登录: 'Student Login',
    登录: 'Log in',
    注册: 'Sign up',
    姓名: 'Name',
    账号: 'Account',
    密码: 'Password',
    学员工作台: 'Student Workspace',
    能力画像: 'Ability Profile',
    我的团队: 'My Team',
    我的任务: 'My Tasks',
    学习社区: 'Learning Community',
    消息: 'Messages',
    个人主页: 'Profile',
    退出登录: 'Log out',
    先完成你的项目名片: 'Complete Your Project Card First',
    我的项目标签: 'My Project Tags',
    知识维度: 'Knowledge',
    技能维度: 'Skills',
    协作维度: 'Collaboration',
    自由描述: 'Free Description',
    主动标签: 'Active Tags',
    提交并生成综合画像: 'Submit and Generate Profile',
    我的协作画像: 'My Collaboration Profile',
    适合以下角色方向: 'Recommended Role Directions',
    当前活动团队: 'Current Activity Team',
    '队友进度（全员可见）': 'Teammate Progress (Visible to All)',
    截止预警: 'Deadline Alerts',
    我的子任务: 'My Subtasks',
    子任务: 'Subtask',
    分配依据: 'Assignment Reason',
    截止: 'Deadline',
    风险: 'Risk',
    进度: 'Progress',
    操作: 'Actions',
    完成: 'Complete',
    反馈: 'Feedback',
    发布学习动态: 'Post Learning Update',
    会话列表: 'Conversations',
    聊天: 'Chat',
    发送: 'Send',
    个人资料: 'Profile',
    修改密码: 'Change Password',
    当前密码: 'Current Password',
    新密码: 'New Password',
    确认新密码: 'Confirm New Password',
    保存资料: 'Save Profile',
    头像链接: 'Avatar URL',
    个人介绍: 'Bio',
    '研究方向 / 项目兴趣': 'Research / Project Interest',
    可协作时间: 'Availability',
    作品集链接: 'Portfolio URL',
    'GitHub / 实验室主页': 'GitHub / Lab Page',
    主页主题: 'Theme',
    研究兴趣: 'Research Interest',
    作品链接: 'Portfolio',
    代码主页: 'Code Page',
    界面语言: 'Language',
  },
}

Object.assign(STUDENT_TEXT_I18N.en, {
  我的班级: 'My Classes',
  '加入班级后，老师创建课程项目时会按班级范围生成均匀分组。加入和退出都需要老师审批，避免小组范围混乱。': 'After joining a class, teacher-created course projects are grouped within that class. Join and leave requests require teacher approval to keep grouping clear.',
  刷新: 'Refresh',
  '已加入 / 待审批班级': 'Joined / Pending Classes',
  '退出申请通过前，你仍会保留在当前班级成员名单中。': 'Before a leave request is approved, you remain in the current class roster.',
  '还没有加入任何班级，可以在右侧申请。': 'You have not joined any class yet. Apply on the right.',
  课程信息待补充: 'Course info pending',
  申请退出: 'Request Leave',
  可加入班级: 'Available Classes',
  '提交申请后，等待任课老师或管理员审批。': 'After submitting, wait for teacher/admin approval.',
  '申请说明（可选，例如我是本课程学生）': 'Request note (optional, e.g. I am enrolled in this course)',
  未设置课程: 'No course set',
  'AI 分析': 'AI Analysis',
  审批中: 'Pending',
  申请加入: 'Apply to Join',
  我的申请记录: 'My Request History',
  班级: 'Class',
  类型: 'Type',
  加入: 'Join',
  退出: 'Leave',
  状态: 'Status',
  说明: 'Note',
  老师备注: 'Teacher Note',
  暂无申请记录: 'No request history',
  班级活动: 'Class Activities',
  '选择你所属的班级，查看该班当前组队活动；也可以为这个班级发起一个活动。': 'Choose one of your classes to view its team activities. You can also start an activity for this class.',
  选择班级: 'Select Class',
  当前班级: 'Current Class',
  '活动标题，如：期末展示自由组队': 'Activity title, e.g. final showcase free teaming',
  学生自由组队: 'Student Free Teaming',
  任务驱动自动组队: 'Task-driven Auto Grouping',
  创建到该班级: 'Create in This Class',
  '活动说明/任务需求（可选）': 'Activity notes / task requirements (optional)',
  活动: 'Activity',
  方式: 'Mode',
  操作: 'Actions',
  '查看/参与': 'View / Join',
  当前班级暂无活动: 'No activities in this class',
  任务驱动组队: 'Task-driven Grouping',
  自由组队: 'Free Teaming',
  待参与: 'Not Joined',
  已参与: 'Joined',
  参与活动: 'Join Activity',
  同步当前标签: 'Sync Current Tags',
  查看活动: 'View Activity',
  '老师已发起新的组队活动，请选择是否参与。': 'A teacher has started a new team activity. Choose whether to join.',
  '选择几个与你相关的标签，系统会整理出适合你的角色方向。也可以补充一段自我介绍，让建议更准确。': 'Choose tags related to you, and the system will suggest suitable roles. You can also add a short introduction for better advice.',
  '先按维度快速圈出特点，再用自由描述补充细节。': 'Pick your strengths by dimension first, then add details in free text.',
  '① 主动标签': '1. Active Tags',
  '点击标签选中/取消；自定义标签可选。仅选主动标签也可提交，自由描述为补充项。': 'Click tags to select/deselect. Custom tags are optional. Active tags alone are enough; free text is supplementary.',
  '你熟悉的课程、理论和领域方向': 'Courses, theories and domain areas you know',
  '你能承担的工具、方法和执行任务': 'Tools, methods and execution tasks you can handle',
  '你在团队里的沟通、推进和配合方式': 'How you communicate, drive work and collaborate in a team',
  搜索或下拉选择知识标签: 'Search or select knowledge tags',
  搜索或下拉选择技能标签: 'Search or select skill tags',
  搜索或下拉选择协作标签: 'Search or select collaboration tags',
  自定义标签: 'Custom tag',
  '自定义标签（可选）': 'Custom tag (optional)',
  '没有合适标签时，可以补一个最能代表你的关键词。': 'If no tag fits, add one keyword that best represents you.',
  添加: 'Add',
  已选: 'Selected',
  '② 自由描述': '2. Free Description',
  '可选。DeepSeek 会结合主动标签分析自由文本；不填写时仅依据已选标签生成画像。': 'Optional. DeepSeek analyzes free text with active tags; if empty, the profile is generated from selected tags.',
  '③ 简历上传': '3. Resume Upload',
  '上传 PDF / DOC / DOCX 简历，系统会提取经历并融合已选标签生成画像。': 'Upload a PDF / DOC / DOCX resume. The system extracts your experience and combines it with selected tags.',
  '已选择：': 'Selected: ',
  选择简历文件: 'Choose Resume File',
  '支持 PDF、DOC、DOCX；若解析失败，可回到自由描述手动补充。': 'PDF, DOC and DOCX are supported. If parsing fails, use free text to add details manually.',
  解析简历并生成画像: 'Parse Resume and Generate Profile',
  请先选择简历文件: 'Please choose a resume file first',
  简历画像已生成: 'Resume profile generated',
  '我的协作画像': 'My Collaboration Profile',
  '根据你的主动标签、学习互动和任务表现生成，仅展示正向角色建议': 'Generated from active tags, learning interactions and task performance; only positive role suggestions are shown.',
  多角色方向: 'Multiple Role Directions',
  我的团队: 'My Team',
  当前活动团队: 'Current Activity Team',
  队友进度: 'Teammate Progress',
  我的任务: 'My Tasks',
  创建一个组内任务: 'Create a Team Task',
  任务名称: 'Task Name',
  任务描述: 'Task Description',
  创建任务: 'Create Task',
  学习社区: 'Learning Community',
  发布学习动态: 'Post Learning Update',
  评论: 'Comments',
  收起评论: 'Hide Comments',
  查看评论: 'View Comments',
  同学: 'Classmate',
  '暂无评论，欢迎补充观点。': 'No comments yet. Add your thoughts.',
  '写下你的评论，补充经验或组队想法': 'Write a comment, share experience or teaming ideas',
  提交评论: 'Submit Comment',
  评论不能为空: 'Comment cannot be empty',
  评论已发布: 'Comment posted',
  会话列表: 'Conversations',
  聊天: 'Chat',
  发送: 'Send',
  账号安全: 'Account Security',
  修改密码: 'Change Password',
  当前密码: 'Current Password',
  新密码: 'New Password',
  确认新密码: 'Confirm New Password',
  可选: 'Optional',
  个标签: 'tags',
  你选择的标签: 'Your Selected Tags',
  学习互动标签: 'Learning Interaction Tags',
  给你的建议: 'Suggestions for You',
  暂无当前组队活动: 'No active team activity',
  '老师创建并发布组队活动后，这里会显示参与入口和队伍信息。': 'After a teacher creates and publishes a team activity, the join entry and team information will appear here.',
  参与本次活动: 'Join This Activity',
  同步我的标签: 'Sync My Tags',
  未参与: 'Not Joined',
  组队大厅: 'Team Lobby',
  队伍名称: 'Team Name',
  '队伍说明 / 想找什么伙伴': 'Team note / desired teammates',
  创建我的队伍: 'Create My Team',
  队伍暂未填写说明: 'No team description yet',
  申请加入: 'Apply to Join',
  退出队伍: 'Leave Team',
  '给队长留言（可选）': 'Message the leader (optional)',
  等待老师汇总并发布分组: 'Waiting for Teacher to Publish Groups',
  '你已参与本次活动。系统会结合本次标签、历史互动和任务需求生成队伍，老师发布后这里会显示你的团队。': 'You have joined this activity. The system will generate teams using tags, history and task requirements; your team will appear after the teacher publishes it.',
  自由组队进行中: 'Free Teaming in Progress',
  '可以继续创建、申请或调整队伍。老师锁定后会进入正式团队页。': 'You can continue creating, applying to or adjusting teams. After the teacher locks them, this becomes the formal team page.',
  预沟通确认候选团队还未最终锁定: 'Pre-communication Confirmation: Candidate Team Not Final',
  '预沟通确认：候选团队还未最终锁定': 'Pre-communication Confirmation: Candidate Team Not Final',
  '请先和候选队友沟通，确认大家是否接受当前角色定位和后续任务方向；如不合适，可以提交微调申请给老师。': 'Communicate with candidate teammates first. Confirm whether everyone accepts current roles and task direction; submit an adjustment request if needed.',
  候选匹配依据: 'Candidate Matching Basis',
  AI候选团队分析: 'AI Candidate Team Analysis',
  'AI 候选团队分析': 'AI Candidate Team Analysis',
  确认率: 'Confirmation Rate',
  微调申请: 'Adjustment Requests',
  待确认: 'Pending Confirmation',
  我: 'Me',
  暂未填写个人介绍: 'No bio yet',
  发消息沟通: 'Message',
  '希望承担/调整的角色（可选）': 'Preferred / adjusted role (optional)',
  '希望承担或避免的任务（可选）': 'Tasks to take or avoid (optional)',
  '沟通备注 / 微调原因': 'Communication note / adjustment reason',
  接受当前团队与角色: 'Accept Current Team and Role',
  提交微调申请: 'Submit Adjustment Request',
  '这是候选团队，老师锁定后会进入正式分工。': 'This is a candidate team. It becomes formal after teacher locking.',
  '只展示本次活动对应的团队和队友任务进度，历史小组不会混在这里。': 'Only this activity team and teammate progress are shown here; historical groups are not mixed in.',
  中的角色: 'role in',
  每30秒自动刷新团队数据: 'Auto refreshes team data every 30 seconds',
  '每 30 秒自动刷新团队数据': 'Auto refreshes team data every 30 seconds',
  本组组队依据: 'Team Grouping Basis',
  AI团队协作建议: 'AI Team Collaboration Advice',
  'AI 团队协作建议': 'AI Team Collaboration Advice',
  团队完成率: 'Team Completion',
  预警: 'Alerts',
  全组任务互相可见: 'All Team Tasks (Visible to Everyone)',
  '全组任务（互相可见）': 'All Team Tasks (Visible to Everyone)',
  '老师分配的任务和同学主动创建的任务都会显示在这里，方便互相了解、协作和调整。': 'Teacher-assigned tasks and student-created tasks are shown here for transparency, collaboration and adjustment.',
  我想创建任务: 'I Want to Create a Task',
  负责人: 'Owner',
  任务: 'Task',
  最后消息: 'Last Message',
  未读: 'Unread',
  打开: 'Open',
  我想做的任务: 'Tasks I Want to Do',
  '你可以主动创建并认领自己想做的任务。创建后会进入小组任务列表，队友和老师都能看到。': 'You can create and claim tasks you want to do. They will appear in the team task list for teammates and teachers.',
  任务说明: 'Task Note',
  '为什么想做 / 需要什么协助': 'Why you want it / help needed',
  难度: 'Difficulty',
  预计工时: 'Estimated Hours',
  截止日期: 'Due Date',
  选择日期: 'Select Date',
  创建并认领任务: 'Create and Claim Task',
  全组任务动态: 'Team Task Updates',
  '这里展示你所在小组的所有任务，包含老师分配和同学主动创建的任务。': 'All tasks in your group are shown here, including teacher-assigned and student-created tasks.',
  暂无小组任务: 'No team tasks yet',
  标题可选: 'Title (optional)',
  '标题（可选）': 'Title (optional)',
  选择帖子标签: 'Select post tags',
  匿名发布: 'Post anonymously',
  发布: 'Post',
  学习动态: 'Learning Update',
  点赞: 'Like',
  收藏: 'Favorite',
  发消息: 'Message',
  同学: 'Classmate',
  任务驱动: 'Task-driven',
  '（我）': ' (Me)',
  用户: 'User',
  人: 'members',
  未命名活动: 'Untitled Activity',
  优势明显: 'Strong advantage',
  基础良好: 'Solid foundation',
  可继续提升: 'Room to grow',
  建议补强: 'Needs strengthening',
  知识方向: 'Knowledge Focus',
  擅长任务: 'Strong Tasks',
  协作方式: 'Collaboration Style',
  课程主题: 'Course topic',
  实践执行: 'Hands-on execution',
  课程学习: 'Course learning',
  '资料整理、实践执行、成果表达': 'Documentation, execution and presentation',
  '沟通配合、稳定推进': 'Communication and steady progress',
  '适合在团队中围绕「%k%」参与方案推进，可优先尝试「%r%」等角色方向，并结合「%s%」完成具体任务。': 'In a team, focus on "%k%" for planning; try roles like "%r%" and apply "%s%" to concrete tasks.',
  '你在「%t%」方向有可用于组队匹配的基础。': 'You have team-matching foundations in "%t%".',
  '适合优先参与「%t%」等任务。': 'Well suited for tasks such as "%t%".',
  '团队协作中可以发挥「%t%」相关特点。': 'In teamwork you can leverage strengths in "%t%".',
  '建议你在后续项目中优先尝试「%r%」相关任务，也可以根据小组需要灵活切换；继续通过社区分享、组内沟通和任务提交完善自己的学习画像。': 'Try "%r%" tasks in upcoming projects and adapt as the team needs; keep improving your profile through community posts, team communication and task submissions.',
  知: 'K',
  技: 'S',
  协: 'C',
  标: 'T',
  '正在读取主动标签...': 'Reading active tags...',
  '正在分析自由描述与学习行为...': 'Analyzing free text and learning behavior...',
  '正在融合知识、技能、协作特征...': 'Combining knowledge, skills and collaboration traits...',
  '正在生成适合的角色方向...': 'Generating suitable role directions...',
  '正在整理给你的建议...': 'Preparing suggestions for you...',
  '计算完成，正在刷新画像...': 'Calculation complete, refreshing profile...',
  '请按老师要求参与本次组队活动。': 'Follow your teacher\'s instructions for this team activity.',
  角色待定: 'Role TBD',
  '个：': ':',
  '候选匹配依据：': 'Candidate matching basis:',
  '分析：': 'Analysis:',
  同意: 'Approve',
  拒绝: 'Reject',
  确定: 'OK',
  取消: 'Cancel',
  确认操作: 'Confirm',
  头像: 'Avatar',
  '可选：例如计算机专业，熟悉 Python 与前端...': 'Optional: e.g. CS major, familiar with Python and frontend...',
  '如：技术开发、文档汇报、协调对接': 'e.g. development, documentation, coordination',
  '如：愿意做原型；不适合后端；需要同伴协助数据分析': 'e.g. willing to prototype; not suited for backend; need help with data analysis',
  '如果不接受当前安排，请说明原因；接受时也可以写给老师和队友的备注。': 'If you do not accept the arrangement, explain why; you may also leave notes for the teacher and teammates when accepting.',
  你在: 'Your role in',
  '本组组队依据：': 'Team grouping basis:',
  '暂无小组任务。老师分配或同学创建后会显示。': 'No team tasks yet. They appear after teacher assignment or peer creation.',
  '如：整理用户访谈问题、实现登录页原型、完成数据清洗': 'e.g. interview questions, login prototype, data cleaning',
  '简单说明你准备做什么、产出是什么': 'Briefly describe what you will do and deliver',
  '例如：我擅长前端，想负责页面实现；需要队友提供接口字段': 'e.g. I am good at frontend and want to build pages; need API fields from teammates',
  '系统按你的能力与偏好分配子任务。请更新完成百分比；逾期或滞后会在上方预警，队友在团队页可见你的进度。': 'Subtasks are assigned by ability and preference. Update completion %; overdue items alert above and teammates see your progress on the team page.',
  '暂无任务。加入小组并由老师分配任务后显示。': 'No tasks yet. Shown after joining a group and teacher assignment.',
  '暂无小组任务。': 'No team tasks yet.',
  '分享项目经验、兴趣方向、学习资料或组队想法；点赞、收藏、评论会形成你的被动画像标签。': 'Share project experience, interests, resources or teaming ideas; likes, favorites and comments build passive profile tags.',
  '写下你感兴趣的方向、正在做的项目、想寻找的队友...': 'Write interests, current projects, teammates you are looking for...',
  '暂无会话，可在学习社区中给同学发消息': 'No conversations yet. Message classmates from the community.',
  输入消息: 'Type a message',
  '学员账号：': 'Student account:',
  未填写: 'Not set',
  '头像支持图片链接；留空时会自动使用姓名首字作为头像。': 'Avatar accepts an image URL; if empty, the first letter of your name is used.',
  个人标题: 'Headline',
  '如：数据分析 / 智慧教育方向研究生': 'e.g. Data analysis / smart education graduate student',
  '写一句你的项目兴趣、擅长方向或希望承担的角色': 'One line about project interests, strengths or preferred role',
  '如：学习分析、智能教育、大模型应用': 'e.g. learning analytics, smart education, LLM applications',
  '如：每周 6-8 小时，周三/周末可开会': 'e.g. 6-8 hours/week, meetings Wed/weekends',
  'Aurora 极光': 'Aurora',
  'Ocean 海蓝': 'Ocean',
  'Sunrise 晨光': 'Sunrise',
  '新密码至少 6 位，保存后下次登录生效。': 'New password must be at least 6 characters; takes effect on next login.',
  正在计算适合你的角色方向: 'Calculating suitable role directions for you',
  '系统正在综合主动标签、自由描述、被动标签与任务表现，稍等片刻。': 'Combining active tags, free text, passive tags and task performance. Please wait.',
  '建议分为 %n% 组，人数分配为 %s%': 'Suggested %n% groups with sizes %s%',
  暂无可分组学生: 'No students available for grouping',
  '系统建议分为 %n% 组，人数为 %s%。': 'System suggests %n% groups with sizes %s%.',
  '最大组与最小组人数差为 %n%，可降低组间工作量不均。': 'Max/min group size gap is %n%; consider reducing workload imbalance.',
  '默认参考每组 %n% 人，符合 10-20 人班级的小组项目组织方式。': 'Default reference: %n% per group, suitable for 10-20 student class projects.',
  '当前班级人数适合进行均匀项目分组。': 'Current class size suits balanced project grouping.',
  '当前暂无可分组学生。': 'No students available for grouping currently.',
  '人数较少的小组需要老师关注任务拆分，避免承担同等任务量。': 'Smaller groups need task splitting to avoid equal workload burden.',
  '已为活动“%t%”生成 %n% 个候选小组，平均均衡度 %s%。': 'Generated %n% candidate groups for activity "%t%" with average balance %s%.',
  '分析：': 'Analysis: ',
  未命名活动: 'Untitled Activity',
  请求失败: 'Request failed',
  请填写账号和密码: 'Please enter account and password',
  登录成功: 'Signed in successfully',
  '请完整填写姓名、账号和密码': 'Please fill in name, account and password',
  '密码至少 6 位': 'Password must be at least 6 characters',
  '注册成功，请先填写画像': 'Registered. Please complete your profile first.',
  '登录状态已失效，请重新登录': 'Session expired. Please sign in again.',
  个人资料已保存: 'Profile saved',
  请填写旧密码和新密码: 'Please enter current and new password',
  两次输入的新密码不一致: 'New passwords do not match',
  密码已修改: 'Password updated',
  '请至少选择主动标签，或输入 50 字以上自由描述': 'Select at least one active tag, or enter 50+ characters of free text',
  'AI 画像已生成': 'AI profile generated',
  '画像已生成，请等待老师分组': 'Profile generated. Wait for teacher grouping.',
  帖子内容至少10字: 'Post content must be at least 10 characters',
  '帖子内容至少 10 字': 'Post content must be at least 10 characters',
  已发布: 'Posted',
  已收藏: 'Favorited',
  已点赞: 'Liked',
  请先选择一个已加入的班级: 'Select a class you have joined first',
  请填写活动标题: 'Please enter an activity title',
  '班级活动已创建，同班同学可以看到': 'Class activity created; classmates can see it',
  '已提交加入班级申请，等待老师审批': 'Join request submitted; awaiting teacher approval',
  已提交退出申请: 'Leave request submitted',
  已参与本次组队活动: 'Joined this team activity',
  本次活动标签已更新: 'Activity tags updated',
  请填写队伍名称: 'Please enter a team name',
  队伍已创建: 'Team created',
  已发送加入申请: 'Join request sent',
  已同意申请: 'Request approved',
  已拒绝申请: 'Request rejected',
  已退出队伍: 'Left the team',
  请先填写希望调整的原因: 'Please explain why you want an adjustment',
  已确认当前候选团队与角色: 'Confirmed candidate team and role',
  已提交微调申请: 'Adjustment request submitted',
  '请先加入或锁定一个小组，再创建任务': 'Join or lock a group before creating tasks',
  请填写任务名称: 'Please enter a task name',
  '任务已创建，队友和老师都可以看到': 'Task created; visible to teammates and teacher',
  进度已保存: 'Progress saved',
  请填写反馈原因: 'Please enter feedback',
  任务反馈已提交: 'Task feedback submitted',
  学习动态: 'Learning update',
  还没有设置个人标题: 'No headline set yet',
  '完善头像和个人介绍，让同学更容易认识你。': 'Add an avatar and bio so classmates can get to know you.',
  '填写你的研究方向、项目兴趣或想探索的问题': 'Add research interests, project topics or questions you want to explore',
  管理员请使用: 'Admins please use:',
  加载失败: 'Load failed',
  '请说明任务过重、不适配或需要协助的原因，老师会在调优时看到：': 'Explain if the task is too heavy, a poor fit, or you need help (visible to the teacher during adjustment):',
  '分配依据：': 'Assignment basis: ',
  '退出班级需要老师审批，审批通过后你将不再参与该班级后续分组。确定提交申请？': 'Leaving a class requires teacher approval. You will not join future groupings in that class. Submit request?',
  申请退出班级: 'Request to leave class',
  '退出后需要重新创建或申请加入队伍，确定继续吗？': 'You must create or apply to a team again after leaving. Continue?',
  退出队伍: 'Leave team',
  '确认后老师会看到你接受当前候选团队与角色，是否继续？': 'Your teacher will see that you accept this candidate team and role. Continue?',
  确认候选团队: 'Confirm candidate team',
})

STUDENT_TEXT_I18N.ja = {
  ...(STUDENT_TEXT_I18N.ja || {}),
  '建议分为 %n% 组，人数分配为 %s%': '%n% グループ、人数配分 %s% を推奨',
  暂无可分组学生: 'グループ分けできる学生がいません',
  '系统建议分为 %n% 组，人数为 %s%。': 'システムは %n% グループ、人数 %s% を推奨しています。',
  '最大组与最小组人数差为 %n%，可降低组间工作量不均。': '最大グループと最小グループの人数差は %n% です。作業量の偏りを抑えられます。',
  '默认参考每组 %n% 人，符合 10-20 人班级的小组项目组织方式。': '標準では各グループ %n% 人を参考にし、10-20 人規模のクラスプロジェクトに適しています。',
  '当前班级人数适合进行均匀项目分组。': '現在のクラス人数は均等なプロジェクト分けに適しています。',
  '当前暂无可分组学生。': '現在グループ分けできる学生がいません。',
  '人数较少的小组需要老师关注任务拆分，避免承担同等任务量。': '人数の少ないグループは、同じ作業量にならないよう教師がタスク分割を確認してください。',
  '已为活动“%t%”生成 %n% 个候选小组，平均均衡度 %s%。': '活動「%t%」に対して %n% 個の候補グループを生成しました。平均バランスは %s% です。',
  '分析：': '分析：',
}

;['zh-Hant', 'ja', 'ko', 'fr', 'de', 'es'].forEach((lang) => {
  STUDENT_TEXT_I18N[lang] = { ...STUDENT_TEXT_I18N.en, ...(STUDENT_TEXT_I18N[lang] || {}) }
})

const STUDENT_DYNAMIC_I18N = {
  'zh-CN': {
    status: {
      active: '已加入', pending: '待审批', approved: '已通过', rejected: '已拒绝',
      draft: '草稿', collecting: '收集中', grouping: '分组中', confirmation: '确认中',
      confirming: '确认中', preview: '预览中', tasking: '任务中', adjusting: '调整中',
      published: '已发布', locked: '已锁定', completed: '已完成', joined: '已参与',
    },
  },
  'zh-Hant': {
    status: {
      active: '已加入', pending: '待審批', approved: '已通過', rejected: '已拒絕',
      draft: '草稿', collecting: '收集中', grouping: '分組中', confirmation: '確認中',
      confirming: '確認中', preview: '預覽中', tasking: '任務中', adjusting: '調整中',
      published: '已發布', locked: '已鎖定', completed: '已完成', joined: '已參與',
    },
  },
  en: {
    status: {
      active: 'Active', pending: 'Pending', approved: 'Approved', rejected: 'Rejected',
      draft: 'Draft', collecting: 'Collecting', grouping: 'Grouping', confirmation: 'Confirming',
      confirming: 'Confirming', preview: 'Preview', tasking: 'Tasking', adjusting: 'Adjusting',
      published: 'Published', locked: 'Locked', completed: 'Completed', joined: 'Joined',
    },
  },
  ja: {
    status: {
      active: '参加中', pending: '保留中', approved: '承認済み', rejected: '却下済み',
      draft: '下書き', collecting: '収集中', grouping: '編成中', confirmation: '確認中',
      confirming: '確認中', preview: 'プレビュー', tasking: 'タスク中', adjusting: '調整中',
      published: '公開済み', locked: 'ロック済み', completed: '完了', joined: '参加済み',
    },
  },
  ko: {
    status: {
      active: '활성', pending: '대기 중', approved: '승인됨', rejected: '거절됨',
      draft: '초안', collecting: '수집 중', grouping: '편성 중', confirmation: '확인 중',
      confirming: '확인 중', preview: '미리보기', tasking: '작업 중', adjusting: '조정 중',
      published: '게시됨', locked: '잠김', completed: '완료', joined: '참여함',
    },
  },
  fr: {
    status: {
      active: 'Actif', pending: 'En attente', approved: 'Approuvé', rejected: 'Refusé',
      draft: 'Brouillon', collecting: 'Collecte', grouping: 'Regroupement', confirmation: 'Confirmation',
      confirming: 'Confirmation', preview: 'Aperçu', tasking: 'Tâches', adjusting: 'Ajustement',
      published: 'Publié', locked: 'Verrouillé', completed: 'Terminé', joined: 'Inscrit',
    },
  },
  de: {
    status: {
      active: 'Aktiv', pending: 'Ausstehend', approved: 'Genehmigt', rejected: 'Abgelehnt',
      draft: 'Entwurf', collecting: 'Sammeln', grouping: 'Gruppierung', confirmation: 'Bestätigung',
      confirming: 'Bestätigung', preview: 'Vorschau', tasking: 'Aufgabenphase', adjusting: 'Anpassung',
      published: 'Veröffentlicht', locked: 'Gesperrt', completed: 'Abgeschlossen', joined: 'Teilgenommen',
    },
  },
  es: {
    status: {
      active: 'Activo', pending: 'Pendiente', approved: 'Aprobado', rejected: 'Rechazado',
      draft: 'Borrador', collecting: 'Recopilando', grouping: 'Agrupando', confirmation: 'Confirmación',
      confirming: 'Confirmando', preview: 'Vista previa', tasking: 'Tareas', adjusting: 'Ajuste',
      published: 'Publicado', locked: 'Bloqueado', completed: 'Completado', joined: 'Inscrito',
    },
  },
}

function lookupTextTranslation(original, target) {
  if (!target) return original
  if (target[original]) return target[original]
  const compact = original.replace(/\s+/g, ' ').trim()
  if (target[compact]) return target[compact]
  const countSuffix = compact.match(/^(.+?)(\s*\(\d+\))$/)
  if (countSuffix && target[countSuffix[1]]) return `${target[countSuffix[1]]}${countSuffix[2]}`
  return original
}

let studentOpenCCConverter = null
function getStudentOpenCC() {
  if (studentOpenCCConverter === null && window.TeamMindI18n) {
    studentOpenCCConverter = window.TeamMindI18n.initOpenCC() || false
  }
  return studentOpenCCConverter || null
}

const FALLBACK_TAG_CATALOG = {
  knowledge: [
    { id: 'field_cs', name: '计算机科学', category: '学科领域', weights: { knowledge: 0.85, skill: 0.35, collab: 0 } },
    { id: 'field_ai', name: '人工智能', category: '学科领域', weights: { knowledge: 0.9, skill: 0.35, collab: 0 } },
    { id: 'field_data', name: '数据科学', category: '学科领域', weights: { knowledge: 0.85, skill: 0.45, collab: 0 } },
    { id: 'field_design', name: '设计学', category: '学科领域', weights: { knowledge: 0.65, skill: 0.45, collab: 0.1 } },
    { id: 'field_business', name: '经管', category: '学科领域', weights: { knowledge: 0.65, skill: 0.25, collab: 0.2 } },
    { id: 'theory_ml', name: '机器学习', category: '理论方向', weights: { knowledge: 0.9, skill: 0.35, collab: 0 } },
    { id: 'theory_database', name: '数据库', category: '理论方向', weights: { knowledge: 0.82, skill: 0.35, collab: 0 } },
    { id: 'theory_se', name: '软件工程', category: '理论方向', weights: { knowledge: 0.8, skill: 0.35, collab: 0.1 } },
  ],
  skill: [
    { id: 'skill_python', name: 'Python', category: '编程语言', weights: { knowledge: 0.15, skill: 0.95, collab: 0 } },
    { id: 'skill_java', name: 'Java', category: '编程语言', weights: { knowledge: 0.1, skill: 0.9, collab: 0 } },
    { id: 'skill_js', name: 'JavaScript', category: '编程语言', weights: { knowledge: 0.1, skill: 0.9, collab: 0 } },
    { id: 'skill_frontend', name: '前端开发', category: '开发能力', weights: { knowledge: 0.1, skill: 0.9, collab: 0.05 } },
    { id: 'skill_backend', name: '后端开发', category: '开发能力', weights: { knowledge: 0.1, skill: 0.9, collab: 0.05 } },
    { id: 'skill_data_analysis', name: '数据分析', category: '数据能力', weights: { knowledge: 0.15, skill: 0.9, collab: 0.05 } },
    { id: 'skill_ui', name: 'UI设计', category: '设计能力', weights: { knowledge: 0.1, skill: 0.85, collab: 0.15 } },
    { id: 'tool_git', name: 'Git', category: '工具平台', weights: { knowledge: 0.05, skill: 0.8, collab: 0.15 } },
  ],
  collab: [
    { id: 'role_leader', name: '组长/负责人', category: '偏好角色', weights: { knowledge: 0.15, skill: 0.2, collab: 0.95 } },
    { id: 'role_dev', name: '技术开发', category: '偏好角色', weights: { knowledge: 0.05, skill: 0.75, collab: 0.35 } },
    { id: 'role_data', name: '数据支持', category: '偏好角色', weights: { knowledge: 0.2, skill: 0.7, collab: 0.35 } },
    { id: 'role_writer', name: '文档汇报', category: '偏好角色', weights: { knowledge: 0.25, skill: 0.55, collab: 0.45 } },
    { id: 'style_proactive', name: '主动沟通', category: '沟通风格', weights: { knowledge: 0, skill: 0.1, collab: 0.95 } },
    { id: 'style_detail', name: '严谨细致', category: '协作风格', weights: { knowledge: 0.15, skill: 0.25, collab: 0.8 } },
    { id: 'style_creative', name: '灵活创新', category: '协作风格', weights: { knowledge: 0.15, skill: 0.35, collab: 0.75 } },
    { id: 'style_share', name: '乐于分享', category: '协作风格', weights: { knowledge: 0.05, skill: 0.1, collab: 0.85 } },
  ],
}

const http = axios.create({ baseURL: API_BASE, timeout: 30000 })

/** setup 外工具函数使用的翻译器（setup 内会赋值） */
let studentUiT = (key) => key
let studentGetLang = () => 'zh-CN'
let studentGetOpenCCFn = () => null

http.interceptors.request.use((cfg) => {
  const t = TeamMindRuntime.storage.getItem('tf_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})
function isStudentAuthFailure(err) {
  const status = err.response?.status
  if (status === 401) return true
  if (status !== 422) return false
  const url = String(err.config?.url || '')
  return url.includes('/auth/me') || (!url.includes('/profile/parse') && !url.includes('/profile/resume'))
}

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (!isStudentAuthFailure(err)) {
      const errText = err.response?.data?.error || err.message || '请求失败'
      ElementPlus?.ElMessage?.error(
        window.TeamMindI18n?.translateAppDynamicText?.(errText, studentGetLang(), studentUiT, studentGetOpenCCFn()) || errText
      )
    }
    if (isStudentAuthFailure(err)) {
      TeamMindRuntime.storage.removeItem('tf_token')
      TeamMindRuntime.storage.removeItem('tf_user')
      window.dispatchEvent(new CustomEvent('teammind-auth-expired'))
    }
    return Promise.reject(err)
  }
)

function safeJsonStorage(key, fallback = null) {
  try {
    return JSON.parse(TeamMindRuntime.storage.getItem(key) || 'null') || fallback
  } catch {
    TeamMindRuntime.storage.removeItem(key)
    return fallback
  }
}

function studentConfirm(message, title) {
  const box = ElementPlus.ElMessageBox || ElementPlus.MessageBox
  const confirmTitle = title
    ? (window.TeamMindI18n?.translateAppDynamicText?.(title, studentGetLang(), studentUiT, studentGetOpenCCFn()) || studentUiT(title))
    : studentUiT('确认操作')
  const confirmMessage = window.TeamMindI18n?.translateAppDynamicText?.(message, studentGetLang(), studentUiT, studentGetOpenCCFn()) || studentUiT(message) || message
  if (box?.confirm) {
    return box.confirm(confirmMessage, confirmTitle, {
      type: 'warning',
      confirmButtonText: studentUiT('确定'),
      cancelButtonText: studentUiT('取消'),
    })
  }
  return window.confirm(`${confirmTitle}\n\n${confirmMessage}`) ? Promise.resolve() : Promise.reject('cancel')
}

function rejectAdminAccount(userData) {
  if (userData?.user?.role === 'admin') {
    ElementPlus.ElMessage.warning({ message: `${t('管理员请使用')}${ADMIN_PORTAL_URL}`, duration: 5000 })
    return true
  }
  return false
}

function scorePct(v) {
  return Math.min(100, Math.round((Number(v) || 0) * 10))
}

function scoreStyle(v, color) {
  return {
    '--pct': `${scorePct(v)}%`,
    '--score-color': color,
  }
}

function scoreLevel(v) {
  const n = Number(v) || 0
  if (n >= 8) return studentUiT('优势明显')
  if (n >= 6) return studentUiT('基础良好')
  if (n >= 4) return studentUiT('可继续提升')
  return studentUiT('建议补强')
}

function userInitial(name) {
  return (name || '?').charAt(0).toUpperCase()
}

function userAvatar(u) {
  return u?.avatar_url || ''
}

function activityDisplayTitle(activity) {
  if (!activity) return ''
  const rawTitle = activity.title || ''
  if (window.TeamMindI18n?.translateDemoText) {
    if (rawTitle) {
      return window.TeamMindI18n.translateDemoText(rawTitle, studentUiT, studentGetLang(), studentGetOpenCCFn())
    }
    const className = activity.classroom?.name || studentUiT('当前班级')
    const title = studentUiT('未命名活动')
    return window.TeamMindI18n.translateDemoText(`${className}｜${title}`, studentUiT, studentGetLang(), studentGetOpenCCFn())
  }
  const className = activity.classroom?.name || studentUiT('当前班级')
  const title = activity.title || studentUiT('未命名活动')
  return title.startsWith(`${className}｜`) ? title : `${className}｜${title}`
}

function demoImageFallback(event) {
  event.target.onerror = null
  event.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="100%25" height="100%25" fill="%23eef2ff"/><text x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%234f46e5" font-family="Arial" font-size="28">TeamMind Classroom</text></svg>'
}

function riskTagType(level) {
  const map = { critical: 'danger', warning: 'warning', normal: 'success', done: 'info' }
  return map[level] || 'info'
}

function formatDeadline(iso) {
  if (!iso) return '—'
  try { return iso.slice(0, 10) } catch (e) { return iso }
}

function mergeTagCatalog(primary, extra) {
  const out = { knowledge: [], skill: [], collab: [] }
  ;['knowledge', 'skill', 'collab'].forEach((dimension) => {
    const seen = new Set()
    ;[primary?.[dimension] || [], extra?.[dimension] || []].flat().forEach((tag) => {
      if (!tag?.name || seen.has(tag.name)) return
      seen.add(tag.name)
      out[dimension].push(tag)
    })
  })
  return out
}

function profileTags(profile, dimension = null) {
  const tags = [...(profile?.active_tags || []), ...(profile?.passive_tags || [])]
  const seen = new Set()
  return tags.filter((tag) => {
    if (!tag?.name || seen.has(tag.name)) return false
    if (dimension && tag.dimension !== dimension) return false
    seen.add(tag.name)
    return true
  })
}

function tagNames(profile, dimension, limit = 4) {
  return profileTags(profile, dimension).slice(0, limit).map((tag) => tag.name)
}

function phraseOrFallback(names, fallback) {
  const joined = names.length ? names.join('、') : fallback
  if (window.TeamMindI18n?.translateProfileLexicon) {
    return window.TeamMindI18n.translateProfileLexicon(joined, studentGetLang(), studentUiT, studentGetOpenCCFn())
  }
  return joined
}

function uniquePush(list, name, source = '画像匹配') {
  const clean = String(name || '').trim()
  if (clean && !list.some((item) => item.name === clean)) list.push({ name: clean, source })
}

function roleCandidates(profile) {
  const roles = []
  uniquePush(roles, profile?.pref_role, '综合推荐')
  profileTags(profile, 'collab').forEach((tag) => {
    if ((tag.category || '').includes('角色') || ['文档汇报', '产品策划', '数据支持', '技术开发', '设计执行', '资料调研', '测试验收', '协调对接', '执行落地'].includes(tag.name)) {
      uniquePush(roles, tag.name, '协作标签')
    }
  })

  const skillNames = tagNames(profile, 'skill', 8)
  const skillRoleMap = [
    [['前端开发', 'JavaScript', 'TypeScript', 'UI设计', 'UX流程设计', '原型设计'], '界面与体验设计'],
    [['后端开发', 'Java', 'Python', 'SQL', 'API设计'], '系统开发支持'],
    [['数据分析', '数据清洗', '数据可视化', '模型训练'], '数据分析支持'],
    [['文案撰写', 'PPT汇报', '调研报告'], '资料整理与汇报'],
    [['产品规划', '用户研究', 'Prompt设计'], '产品与方案策划'],
  ]
  skillRoleMap.forEach(([keys, role]) => {
    if (keys.some((key) => skillNames.includes(key))) uniquePush(roles, role, '技能标签')
  })

  if (!roles.length) uniquePush(roles, '项目协作成员', '基础推荐')
  return roles.slice(0, 5)
}

function roleTitle(profile) {
  return roleCandidates(profile)[0]?.name || '项目协作成员'
}

function roleSummary(profile) {
  const roles = roleCandidates(profile).slice(0, 3).map((item) => item.name)
  const skills = phraseOrFallback(tagNames(profile, 'skill', 3), studentUiT('实践执行'))
  const knowledge = phraseOrFallback(tagNames(profile, 'knowledge', 2), profile?.field || studentUiT('课程主题'))
  const tpl = studentUiT('适合在团队中围绕「%k%」参与方案推进，可优先尝试「%r%」等角色方向，并结合「%s%」完成具体任务。')
  const roleText = window.TeamMindI18n?.translateProfileLexicon
    ? window.TeamMindI18n.translateProfileLexicon(roles.join('、'), studentGetLang(), studentUiT, studentGetOpenCCFn())
    : roles.join('、')
  return tpl.replace('%k%', knowledge).replace('%r%', roleText).replace('%s%', skills)
}

function positiveInsights(profile) {
  const knowledge = phraseOrFallback(tagNames(profile, 'knowledge', 4), profile?.field || studentUiT('课程学习'))
  const skills = phraseOrFallback(tagNames(profile, 'skill', 4), studentUiT('资料整理、实践执行、成果表达'))
  const collab = phraseOrFallback(tagNames(profile, 'collab', 4), studentUiT('沟通配合、稳定推进'))
  return [
    {
      icon: '📚',
      title: studentUiT('知识方向'),
      text: studentUiT('你在「%t%」方向有可用于组队匹配的基础。').replace('%t%', knowledge),
    },
    {
      icon: '🛠️',
      title: studentUiT('擅长任务'),
      text: studentUiT('适合优先参与「%t%」等任务。').replace('%t%', skills),
    },
    {
      icon: '🤝',
      title: studentUiT('协作方式'),
      text: studentUiT('团队协作中可以发挥「%t%」相关特点。').replace('%t%', collab),
    },
  ]
}

function profileSuggestion(profile) {
  const roles = roleCandidates(profile).slice(0, 3).map((item) => item.name).join('、')
  const roleText = window.TeamMindI18n?.translateProfileLexicon
    ? window.TeamMindI18n.translateProfileLexicon(roles, studentGetLang(), studentUiT, studentGetOpenCCFn())
    : roles
  return studentUiT('建议你在后续项目中优先尝试「%r%」相关任务，也可以根据小组需要灵活切换；继续通过社区分享、组内沟通和任务提交完善自己的学习画像。').replace('%r%', roleText)
}

function tagDimensionClass(tag, fallback = 'skill') {
  return `badge-${tag?.dimension || fallback}`
}

function buildAccountForm(u = {}) {
  return {
    name: u?.name || '',
    avatar_url: u?.avatar_url || '',
    bio: u?.bio || '',
    headline: u?.headline || '',
    portfolio_url: u?.portfolio_url || '',
    github_url: u?.github_url || '',
    research_interest: u?.research_interest || '',
    availability: u?.availability || '',
    display_theme: u?.display_theme || 'aurora',
  }
}

const App = {
  setup() {
    const page = ref('login')
    const user = ref(safeJsonStorage('tf_user'))
    const token = ref(TeamMindRuntime.storage.getItem('tf_token') || '')
    const loading = ref(false)
    const tab = ref('login')
    const loginForm = ref({ account: '', password: '' })
    const regForm = ref({ name: '', account: '', password: '' })
    const rawText = ref('')
    const profile = ref(null)
    const profileLlmHint = ref('')
    const history = ref([])
    const tagCatalog = ref({ knowledge: [], skill: [], collab: [] })
    const activeTags = ref([])
    const customTag = ref('')
    const profileTab = ref('tags')
    const resumeFile = ref(null)
    const calculating = ref(false)
    const calculateProgress = ref(0)
    const calculateText = ref('')
    const communityFeed = ref([])
    const postForm = ref({ title: '', content: '', tags: [], is_anonymous: false })
    const postMedia = ref([])
    const commentInputs = ref({})
    const expandedComments = ref({})
    const conversations = ref([])
    const messages = ref([])
    const chatTargetId = ref(null)
    const chatConversationId = ref(null)
    const chatInput = ref('')
    const accountForm = ref(buildAccountForm(user.value))
    const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })
    const language = ref(STUDENT_I18N[DEFAULT_APP_LANG] ? DEFAULT_APP_LANG : 'zh-CN')
    const groups = ref([])
    const personal = ref({})
    const availableClasses = ref([])
    const myClassData = ref({ memberships: [], requests: [] })
    const classRequestMessage = ref('')
    const selectedStudentClassId = ref(null)
    const classActivities = ref([])
    const classActivityForm = ref({
      title: '',
      mode: 'free_team',
      group_size: 4,
      task_goal: '',
      description: '',
    })
    const groupId = ref(null)
    const teamDashboard = ref(null)
    const activities = ref([])
    const selectedActivityId = ref(null)
    const activityTeams = ref([])
    const teamForm = ref({ name: '', description: '', desired_tags: [] })
    const joinMessage = ref('')
    const confirmationForm = ref({ preferred_role: '', reason: '', task_preferences: '', message: '' })
    const taskCreateForm = ref({
      task_name: '',
      description: '',
      reason: '',
      difficulty: 3,
      estimated_hours: 2,
      deadline: '',
    })
    let refreshTimer = null
    let calcTimer = null
    let calcStartedAt = 0

    const isLoggedIn = computed(() => !!token.value && user.value?.role === 'user')
    const t = window.TeamMindI18n
      ? window.TeamMindI18n.createTranslator({
          structuredI18n: STUDENT_I18N,
          textI18n: STUDENT_TEXT_I18N,
          getLang: () => language.value,
          getOpenCC: getStudentOpenCC,
        })
      : (key) => STUDENT_I18N[language.value]?.[key] || STUDENT_I18N['zh-CN'][key] || key
    studentUiT = t
    studentGetLang = () => language.value
    studentGetOpenCCFn = getStudentOpenCC
    const displayDemoText = (text) => {
      void language.value
      if (text == null || text === '') return ''
      return window.TeamMindI18n?.translateDemoText(String(text), t, language.value, getStudentOpenCC()) || String(text)
    }
    const formatGroupingAdviceText = (advice) => {
      void language.value
      if (!advice) return ''
      return window.TeamMindI18n?.formatGroupingAdvice(advice, t) || ''
    }
    const formatInsightText = (text) => {
      void language.value
      if (text == null || text === '') return ''
      return window.TeamMindI18n?.formatInsightForUi?.(String(text), t, language.value, getStudentOpenCC())
        || window.TeamMindI18n?.translateAppDynamicText?.(String(text), t, language.value, getStudentOpenCC())
        || String(text)
    }
    const formatDynamicText = formatInsightText
    const studentDynamicPack = computed(() => STUDENT_DYNAMIC_I18N[language.value] || STUDENT_DYNAMIC_I18N.en)
    const formatActivityStatus = (status) => {
      void language.value
      if (status == null || status === '') return '—'
      const normalized = window.TeamMindI18n?.normalizeActivityStatus
        ? window.TeamMindI18n.normalizeActivityStatus(status)
        : status
      return studentDynamicPack.value.status?.[normalized] || studentDynamicPack.value.status?.[status] || String(status)
    }
    const localizedRoleSummary = computed(() => {
      void language.value
      return roleSummary(profile.value)
    })
    const localizedPositiveInsights = computed(() => {
      void language.value
      return positiveInsights(profile.value)
    })
    const localizedProfileSuggestion = computed(() => {
      void language.value
      return profileSuggestion(profile.value)
    })
    function translateProfileText(text) {
      void language.value
      if (text == null || text === '') return ''
      if (window.TeamMindI18n?.translateProfileLexicon) {
        return window.TeamMindI18n.translateProfileLexicon(text, language.value, t, getStudentOpenCC())
      }
      return String(text)
    }
    const displayTagCatalog = computed(() => {
      void language.value
      return window.TeamMindI18n?.localizeTagCatalog?.(
        tagCatalog.value,
        language.value,
        t,
        getStudentOpenCC(),
      ) || tagCatalog.value
    })
    const tagIcon = (tag, fallback = 'skill') => {
      void language.value
      const dim = tag?.dimension || fallback
      if (language.value === 'en') {
        return { knowledge: 'K', skill: 'S', collab: 'C' }[dim] || '·'
      }
      const collab = language.value === 'zh-Hant' ? '協' : '协'
      return { knowledge: '知', skill: '技', collab }[dim] || '标'
    }
    const localizedRoleCandidates = computed(() => {
      void language.value
      if (!profile.value) return []
      return roleCandidates(profile.value).map((role) => ({
        ...role,
        name: translateProfileText(role.name),
        source: translateProfileText(role.source),
      }))
    })
    const navItems = computed(() => NAV_ITEMS.map((item) => {
      const translated = STUDENT_I18N[language.value]?.nav?.[item.key]
        || STUDENT_I18N.en?.nav?.[item.key]
        || STUDENT_I18N['zh-CN'].nav[item.key]
      return { ...item, label: translated?.[0] || item.label, desc: translated?.[1] || item.desc }
    }))
    const currentNav = computed(() => {
      if (page.value === 'account') return { label: t('accountNavLabel'), desc: t('accountNavDesc') }
      return navItems.value.find((n) => n.key === page.value) || navItems.value[0]
    })
    const personalAlerts = computed(() => personal.value.alerts || [])
    const currentActivity = computed(() => activities.value.find((a) => a.id === selectedActivityId.value) || activities.value[0] || null)
    const myGroup = computed(() => currentActivity.value?.my_group || groups.value[0] || null)
    const myParticipant = computed(() => currentActivity.value?.my_participant || null)
    const myConfirmation = computed(() => currentActivity.value?.my_confirmation || null)
    const isConfirmationStage = computed(() => ['preview', 'confirming', 'grouping'].includes(currentActivity.value?.status))
    const confirmationSummary = computed(() => myGroup.value?.confirmation_summary || currentActivity.value?.confirmation_summary || null)
    const myRoom = computed(() => {
      const uid = user.value?.id
      return activityTeams.value.find((room) => (room.member_ids || []).includes(uid)) || null
    })
    const myTeamRole = computed(() => {
      if (!teamDashboard.value?.members || !user.value) return null
      const m = teamDashboard.value.members.find((x) => x.user?.id === user.value.id)
      return m?.team_role || null
    })
    const teammates = computed(() => {
      if (!teamDashboard.value?.members) return []
      return teamDashboard.value.members.filter((m) => m.user?.id !== user.value?.id)
    })
    const candidateMembers = computed(() => myGroup.value?.members || [])
    const myClassMemberships = computed(() => myClassData.value.memberships || [])
    const activeClassMemberships = computed(() => myClassMemberships.value.filter((m) => m.status === 'active'))
    const myClassRequests = computed(() => myClassData.value.requests || [])
    const selectedStudentClass = computed(() => activeClassMemberships.value.find((m) => m.class_id === selectedStudentClassId.value) || activeClassMemberships.value[0] || null)

    function setAuth(data) {
      if (rejectAdminAccount(data)) return
      token.value = data.token
      user.value = data.user
      accountForm.value = buildAccountForm(data.user)
      TeamMindRuntime.storage.setItem('tf_token', data.token)
      TeamMindRuntime.storage.setItem('tf_user', JSON.stringify(data.user))
      page.value = 'profile'
      window.removeEventListener('hashchange', onHashChange)
      window.addEventListener('hashchange', onHashChange)
      if (window.location.hash !== '#profile') window.location.hash = 'profile'
      nextTick(updateDocumentTitle)
    }

    function clearStaleAdminSession() {
      if (user.value?.role === 'admin') {
        token.value = ''
        user.value = null
        TeamMindRuntime.storage.removeItem('tf_token')
        TeamMindRuntime.storage.removeItem('tf_user')
        page.value = 'login'
      }
    }

    async function doLogin() {
      if (!loginForm.value.account.trim() || !loginForm.value.password) {
        return ElementPlus.ElMessage.warning(t('请填写账号和密码'))
      }
      loading.value = true
      try {
        const { data } = await http.post('/auth/login', loginForm.value)
        if (rejectAdminAccount(data)) return
        setAuth(data)
        ElementPlus.ElMessage.success(t('登录成功'))
        await Promise.all([loadHistory(), loadTagCatalog()])
      } finally { loading.value = false }
    }

    async function doRegister() {
      if (!regForm.value.name.trim() || !regForm.value.account.trim() || !regForm.value.password) {
        return ElementPlus.ElMessage.warning(t('请完整填写姓名、账号和密码'))
      }
      if (regForm.value.password.length < 6) {
        return ElementPlus.ElMessage.warning(t('密码至少 6 位'))
      }
      loading.value = true
      try {
        const { data } = await http.post('/auth/register', regForm.value)
        setAuth(data)
        ElementPlus.ElMessage.success(t('注册成功，请先填写画像'))
        await Promise.all([loadHistory(), loadTagCatalog()])
      } finally { loading.value = false }
    }

    function logout() {
      stopRefresh()
      stopCalcProgress()
      token.value = ''
      user.value = null
      TeamMindRuntime.storage.removeItem('tf_token')
      TeamMindRuntime.storage.removeItem('tf_user')
      page.value = 'login'
      if (window.location.hash) window.location.hash = ''
      updateDocumentTitle()
    }

    function handleAuthExpired() {
      if (!token.value && !user.value) return
      stopRefresh()
      token.value = ''
      user.value = null
      page.value = 'login'
      ElementPlus.ElMessage.warning(t('登录状态已失效，请重新登录'))
    }

    async function loadMe() {
      const { data } = await http.get('/auth/me')
      user.value = data
      accountForm.value = buildAccountForm(data)
      TeamMindRuntime.storage.setItem('tf_user', JSON.stringify(data))
    }

    async function loadProfileLlmStatus() {
      try {
        const { data } = await http.get('/profile/llm-status')
        profileLlmHint.value = data.llm_available ? '' : (data.hint || '')
      } catch {
        profileLlmHint.value = ''
      }
    }

    async function saveAccount() {
      loading.value = true
      try {
        const { data } = await http.put('/auth/me', accountForm.value)
        user.value = data
        accountForm.value = buildAccountForm(data)
        TeamMindRuntime.storage.setItem('tf_user', JSON.stringify(data))
        ElementPlus.ElMessage.success(t('个人资料已保存'))
      } finally { loading.value = false }
    }

    async function changePassword() {
      if (!passwordForm.value.old_password || !passwordForm.value.new_password) {
        return ElementPlus.ElMessage.warning(t('请填写旧密码和新密码'))
      }
      if (passwordForm.value.new_password.length < 6) {
        return ElementPlus.ElMessage.warning('新密码至少 6 位')
      }
      if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
        return ElementPlus.ElMessage.warning(t('两次输入的新密码不一致'))
      }
      loading.value = true
      try {
        await http.post('/auth/change-password', {
          old_password: passwordForm.value.old_password,
          new_password: passwordForm.value.new_password,
        })
        passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
        ElementPlus.ElMessage.success(t('密码已修改'))
      } finally { loading.value = false }
    }

    function startCalcProgress() {
      stopCalcProgress()
      calculating.value = true
      calcStartedAt = Date.now()
      calculateProgress.value = 8
      const steps = [
        t('正在读取主动标签...'),
        t('正在分析自由描述与学习行为...'),
        t('正在融合知识、技能、协作特征...'),
        t('正在生成适合的角色方向...'),
        t('正在整理给你的建议...'),
      ]
      let idx = 0
      calculateText.value = steps[idx]
      calcTimer = setInterval(() => {
        idx = Math.min(idx + 1, steps.length - 1)
        calculateText.value = steps[idx]
        calculateProgress.value = Math.min(92, calculateProgress.value + 14 + Math.round(Math.random() * 8))
      }, 650)
    }

    function finishCalcProgress() {
      calculateText.value = t('计算完成，正在刷新画像...')
      calculateProgress.value = 100
      const wait = Math.max(500, 1600 - (Date.now() - calcStartedAt))
      setTimeout(() => {
        calculating.value = false
        stopCalcProgress()
      }, wait)
    }

    function stopCalcProgress() {
      if (calcTimer) { clearInterval(calcTimer); calcTimer = null }
    }

    async function loadHistory() {
      const { data } = await http.get('/profile/history')
      history.value = data
      if (data?.length) profile.value = data[0]
    }

    async function loadTagCatalog() {
      try {
        const { data } = await http.get('/profile/tags/catalog')
        const hasTags = data && ['knowledge', 'skill', 'collab'].some((k) => (data[k] || []).length)
        tagCatalog.value = hasTags ? mergeTagCatalog(data, FALLBACK_TAG_CATALOG) : FALLBACK_TAG_CATALOG
      } catch (e) {
        tagCatalog.value = FALLBACK_TAG_CATALOG
      }
    }

    function isTagSelected(name) {
      return activeTags.value.some((x) => x.name === name)
    }

    function groupedTags(dimension) {
      void language.value
      return (displayTagCatalog.value[dimension] || []).reduce((acc, tag) => {
        const category = tag.displayCategory || tag.category || translateProfileText('其他')
        if (!acc[category]) acc[category] = []
        acc[category].push(tag)
        return acc
      }, {})
    }

    function hotTags(dimension) {
      void language.value
      return (displayTagCatalog.value[dimension] || []).slice(0, 12)
    }

    function tagNamesByDimension(dimension) {
      return activeTags.value.filter((x) => x.dimension === dimension).map((x) => x.name)
    }

    function setTagsForDimension(dimension, names) {
      const selected = new Set(names)
      activeTags.value = activeTags.value.filter((x) => x.dimension !== dimension || x.custom)
      ;(tagCatalog.value[dimension] || []).forEach((tag) => {
        if (selected.has(tag.name) && !activeTags.value.some((x) => x.name === tag.name)) {
          activeTags.value.push({ ...tag, dimension, level: 2 })
        }
      })
    }

    function toggleTag(tag, dimension) {
      const idx = activeTags.value.findIndex((x) => x.name === tag.name)
      if (idx >= 0) {
        activeTags.value.splice(idx, 1)
      } else {
        activeTags.value.push({ ...tag, dimension, level: 2 })
      }
    }

    function addCustomTag(dimension = 'skill') {
      const name = customTag.value.trim()
      if (!name) return
      activeTags.value.push({ name, dimension, level: 2, custom: true })
      customTag.value = ''
    }

    async function parseText() {
      const text = rawText.value.trim()
      if (!activeTags.value.length && text.length < 50) {
        return ElementPlus.ElMessage.warning(t('请至少选择主动标签，或输入 50 字以上自由描述'))
      }
      loading.value = true
      startCalcProgress()
      try {
        const { data } = await http.post('/profile/submit', { raw_text: text, active_tags: activeTags.value })
        profile.value = data.profile
        if (data.llm_hint) profileLlmHint.value = data.llm_hint
        else if (!profileLlmHint.value) profileLlmHint.value = ''
        ElementPlus.ElMessage.success(data.llm_mode === 'deepseek' ? t('AI 画像已生成') : t('画像已生成，请等待老师分组'))
        await loadHistory()
        finishCalcProgress()
      } catch (e) {
        calculating.value = false
        stopCalcProgress()
        throw e
      } finally { loading.value = false }
    }

    function onResumeFile(e) {
      resumeFile.value = (e.target.files || [])[0] || null
    }

    async function parseResume() {
      if (!resumeFile.value) return ElementPlus.ElMessage.warning(t('请先选择简历文件'))
      const fd = new FormData()
      fd.append('resume_file', resumeFile.value)
      fd.append('active_tags', JSON.stringify(activeTags.value))
      loading.value = true
      startCalcProgress()
      try {
        const { data } = await http.post('/profile/resume', fd)
        profile.value = data.profile
        ElementPlus.ElMessage.success(t('简历画像已生成'))
        await loadHistory()
        finishCalcProgress()
      } catch (e) {
        calculating.value = false
        stopCalcProgress()
        throw e
      } finally { loading.value = false }
    }

    async function loadFeed() {
      const { data } = await http.get('/community/feed')
      communityFeed.value = data.items || []
    }

    function onPostMedia(e) {
      postMedia.value = Array.from(e.target.files || [])
    }

    async function createPost() {
      if (postForm.value.content.length < 10) return ElementPlus.ElMessage.warning(t('帖子内容至少 10 字'))
      const fd = new FormData()
      fd.append('title', postForm.value.title)
      fd.append('content', postForm.value.content)
      fd.append('tags', JSON.stringify(postForm.value.tags.map((name) => ({ name }))))
      fd.append('is_anonymous', postForm.value.is_anonymous ? 'true' : 'false')
      postMedia.value.forEach((f) => fd.append('media', f))
      loading.value = true
      try {
        await http.post('/community/posts', fd)
        ElementPlus.ElMessage.success(t('已发布'))
        postForm.value = { title: '', content: '', tags: [], is_anonymous: false }
        postMedia.value = []
        await loadFeed()
      } finally { loading.value = false }
    }

    async function interactPost(post, type) {
      await http.post(`/community/posts/${post.id}/${type}`)
      ElementPlus.ElMessage.success(type === 'favorite' ? t('已收藏') : t('已点赞'))
      await loadFeed()
      await loadHistory()
    }

    async function toggleComments(post) {
      if (expandedComments.value[post.id]) {
        expandedComments.value = { ...expandedComments.value, [post.id]: false }
        return
      }
      const { data } = await http.get(`/community/posts/${post.id}`)
      post.comments = data.comments || []
      post.stats = data.stats || post.stats
      expandedComments.value = { ...expandedComments.value, [post.id]: true }
    }

    async function submitComment(post) {
      const content = (commentInputs.value[post.id] || '').trim()
      if (!content) return ElementPlus.ElMessage.warning(t('评论不能为空'))
      await http.post(`/community/posts/${post.id}/comment`, { content })
      commentInputs.value = { ...commentInputs.value, [post.id]: '' }
      const { data } = await http.get(`/community/posts/${post.id}`)
      post.comments = data.comments || []
      post.stats = data.stats || post.stats
      expandedComments.value = { ...expandedComments.value, [post.id]: true }
      ElementPlus.ElMessage.success(t('评论已发布'))
      await loadHistory()
    }

    async function loadConversations() {
      const { data } = await http.get('/chat/conversations')
      conversations.value = data
    }

    async function openConversation(conv) {
      chatConversationId.value = conv.id
      chatTargetId.value = conv.other_user_id
      const { data } = await http.get(`/chat/conversations/${conv.id}/messages`)
      messages.value = data
      await http.post(`/chat/conversations/${conv.id}/read`)
    }

    async function startChat(targetId) {
      const { data } = await http.post('/chat/conversations', { target_user_id: targetId })
      await loadConversations()
      await openConversation(data)
      page.value = 'messages'
    }

    async function sendMessage() {
      if (!chatConversationId.value || !chatInput.value.trim()) return
      const { data } = await http.post(`/chat/conversations/${chatConversationId.value}/messages`, { content: chatInput.value })
      messages.value.push(data)
      chatInput.value = ''
      await loadConversations()
      await loadHistory()
    }

    async function loadGroups() {
      if (currentActivity.value?.my_group) {
        groups.value = [currentActivity.value.my_group]
        groupId.value = currentActivity.value.my_group.id
        return
      }
      const { data } = await http.get('/group/list')
      groups.value = data
      if (data.length) {
        if (!groupId.value || !data.some((g) => g.id === groupId.value)) groupId.value = data[0].id
      } else {
        groupId.value = null
        teamDashboard.value = null
      }
    }

    async function loadStudentClasses() {
      const [all, mine] = await Promise.all([
        http.get('/classes'),
        http.get('/classes/my'),
      ])
      availableClasses.value = all.data || []
      myClassData.value = mine.data || { memberships: [], requests: [] }
      if (!activeClassMemberships.value.some((m) => m.class_id === selectedStudentClassId.value)) {
        selectedStudentClassId.value = activeClassMemberships.value[0]?.class_id || null
      }
      if (selectedStudentClassId.value) await loadClassActivities(selectedStudentClassId.value)
      else classActivities.value = []
    }

    async function loadClassActivities(classId = selectedStudentClassId.value) {
      if (!classId) {
        classActivities.value = []
        return
      }
      selectedStudentClassId.value = classId
      const { data } = await http.get(`/classes/${classId}/activities`)
      classActivities.value = data || []
    }

    async function createClassActivity() {
      const classId = selectedStudentClassId.value
      if (!classId) return ElementPlus.ElMessage.warning(t('请先选择一个已加入的班级'))
      if (!classActivityForm.value.title.trim()) return ElementPlus.ElMessage.warning(t('请填写活动标题'))
      loading.value = true
      try {
        await http.post(`/classes/${classId}/activities`, classActivityForm.value)
        ElementPlus.ElMessage.success(t('班级活动已创建，同班同学可以看到'))
        classActivityForm.value = { title: '', mode: 'free_team', group_size: 4, task_goal: '', description: '' }
        await Promise.all([loadClassActivities(classId), loadActivities()])
      } finally { loading.value = false }
    }

    async function requestJoinClass(cls) {
      if (!cls) return
      loading.value = true
      try {
        await http.post(`/classes/${cls.id}/join-request`, { message: classRequestMessage.value })
        classRequestMessage.value = ''
        ElementPlus.ElMessage.success(t('已提交加入班级申请，等待老师审批'))
        await loadStudentClasses()
      } finally { loading.value = false }
    }

    async function requestLeaveClass(item) {
      const cls = item?.classroom
      if (!cls) return
      try {
        await studentConfirm('退出班级需要老师审批，审批通过后你将不再参与该班级后续分组。确定提交申请？', '申请退出班级')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.post(`/classes/${cls.id}/leave-request`, { message: classRequestMessage.value })
        classRequestMessage.value = ''
        ElementPlus.ElMessage.success(t('已提交退出申请'))
        await loadStudentClasses()
      } finally { loading.value = false }
    }

    async function loadActivities() {
      const { data } = await http.get('/team-activities/active')
      activities.value = data
      if (!selectedActivityId.value && data.length) selectedActivityId.value = data[0].id
      const active = currentActivity.value
      if (active?.my_group) {
        groups.value = [active.my_group]
        groupId.value = active.my_group.id
      } else {
        await loadGroups()
      }
      if (active?.mode === 'free_team') await loadActivityTeams()
      else activityTeams.value = []
    }

    async function joinActivity(activity = currentActivity.value) {
      if (!activity) return
      loading.value = true
      try {
        await http.post(`/team-activities/${activity.id}/join`, { active_tags: activeTags.value })
        ElementPlus.ElMessage.success(t('已参与本次组队活动'))
        await loadActivities()
      } finally { loading.value = false }
    }

    async function syncActivityTags(activity = currentActivity.value) {
      if (!activity?.my_participant) return joinActivity(activity)
      loading.value = true
      try {
        await http.put(`/team-activities/${activity.id}/tags`, { active_tags: activeTags.value })
        ElementPlus.ElMessage.success(t('本次活动标签已更新'))
        await loadActivities()
      } finally { loading.value = false }
    }

    async function loadActivityTeams() {
      const activity = currentActivity.value
      if (!activity) return
      const { data } = await http.get(`/team-activities/${activity.id}/teams`)
      activityTeams.value = data
    }

    async function createTeamRoom() {
      const activity = currentActivity.value
      if (!activity) return
      if (!teamForm.value.name.trim()) return ElementPlus.ElMessage.warning(t('请填写队伍名称'))
      loading.value = true
      try {
        await http.post(`/team-activities/${activity.id}/teams`, teamForm.value)
        teamForm.value = { name: '', description: '', desired_tags: [] }
        ElementPlus.ElMessage.success(t('队伍已创建'))
        await loadActivityTeams()
      } finally { loading.value = false }
    }

    async function requestJoinTeam(room) {
      const activity = currentActivity.value
      if (!activity || !room) return
      loading.value = true
      try {
        await http.post(`/team-activities/${activity.id}/teams/${room.id}/join-request`, { message: joinMessage.value })
        joinMessage.value = ''
        ElementPlus.ElMessage.success(t('已发送加入申请'))
        await loadActivityTeams()
      } finally { loading.value = false }
    }

    async function handleJoinRequest(req, action) {
      const activity = currentActivity.value
      if (!activity) return
      loading.value = true
      try {
        await http.post(`/team-activities/${activity.id}/requests/${req.id}/${action}`)
        ElementPlus.ElMessage.success(action === 'approve' ? t('已同意申请') : t('已拒绝申请'))
        await loadActivityTeams()
      } finally { loading.value = false }
    }

    async function leaveTeamRoom(room = myRoom.value) {
      const activity = currentActivity.value
      if (!activity || !room) return
      try {
        await studentConfirm('退出后需要重新创建或申请加入队伍，确定继续吗？', '退出队伍')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.post(`/team-activities/${activity.id}/teams/${room.id}/leave`)
        ElementPlus.ElMessage.success(t('已退出队伍'))
        await loadActivityTeams()
      } finally { loading.value = false }
    }

    async function submitTeamConfirmation(accept = true) {
      const activity = currentActivity.value
      if (!activity || !myGroup.value) return
      if (!accept && !confirmationForm.value.reason.trim()) {
        return ElementPlus.ElMessage.warning(t('请先填写希望调整的原因'))
      }
      if (accept) {
        try {
          await studentConfirm('确认后老师会看到你接受当前候选团队与角色，是否继续？', '确认候选团队')
        } catch {
          return
        }
      }
      loading.value = true
      try {
        await http.post(`/team-activities/${activity.id}/confirm`, {
          accept_team: accept,
          accept_role: accept,
          preferred_role: confirmationForm.value.preferred_role || myConfirmation.value?.preferred_role || myTeamRole.value || '',
          task_preferences: confirmationForm.value.task_preferences,
          reason: confirmationForm.value.reason,
          message: confirmationForm.value.message,
        })
        ElementPlus.ElMessage.success(accept ? t('已确认当前候选团队与角色') : t('已提交微调申请'))
        confirmationForm.value = { preferred_role: '', reason: '', task_preferences: '', message: '' }
        await loadActivities()
        await loadGroups()
      } finally { loading.value = false }
    }

    async function loadPersonal() {
      const { data } = await http.get('/board/personal')
      personal.value = data
    }

    async function createStudentTask() {
      const gid = groupId.value || myGroup.value?.id || personal.value.groups?.[0]?.id
      if (!gid) return ElementPlus.ElMessage.warning(t('请先加入或锁定一个小组，再创建任务'))
      if (!taskCreateForm.value.task_name.trim()) return ElementPlus.ElMessage.warning(t('请填写任务名称'))
      loading.value = true
      try {
        await http.post('/task/create', {
          ...taskCreateForm.value,
          group_id: gid,
        })
        ElementPlus.ElMessage.success(t('任务已创建，队友和老师都可以看到'))
        taskCreateForm.value = { task_name: '', description: '', reason: '', difficulty: 3, estimated_hours: 2, deadline: '' }
        await loadPersonal()
        if (page.value === 'team') await loadTeamDashboard()
      } finally { loading.value = false }
    }

    async function loadTeamDashboard() {
      if (!groupId.value) {
        teamDashboard.value = null
        return
      }
      try {
        const { data } = await http.get(`/board/team/${groupId.value}/dashboard`)
        teamDashboard.value = data
      } catch (e) {
        teamDashboard.value = null
      }
    }

    async function updateProgress(taskId, progress) {
      loading.value = true
      try {
        await http.post(`/task/${taskId}/progress`, { progress, submit_status: 'on_time' })
        ElementPlus.ElMessage.success(t('进度已保存'))
        await loadPersonal()
        if (page.value === 'team') await loadTeamDashboard()
      } finally { loading.value = false }
    }

    async function submitTaskFeedback(task) {
      const message = window.prompt(t('请说明任务过重、不适配或需要协助的原因，老师会在调优时看到：'), '')
      if (message === null) return
      if (!message.trim()) return ElementPlus.ElMessage.warning(t('请填写反馈原因'))
      const expected = window.prompt('你希望如何调整？例如：拆分任务、换负责人、延后截止、需要同伴协助。', '')
      loading.value = true
      try {
        await http.post(`/task/${task.id}/feedback`, {
          feedback_type: 'needs_help',
          message,
          expected_adjustment: expected || '',
          workload: 4,
        })
        ElementPlus.ElMessage.success(t('任务反馈已提交'))
        await loadPersonal()
      } finally { loading.value = false }
    }

    function startRefresh() {
      stopRefresh()
      if (page.value === 'team' && groupId.value) {
        refreshTimer = setInterval(loadTeamDashboard, 30000)
      }
    }

    function stopRefresh() {
      if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
    }

    function updateDocumentTitle() {
      const base = t('pageTitle')
      if (!isLoggedIn.value) {
        document.title = base
        return
      }
      const current = navItems.value.find((item) => item.key === page.value)
      document.title = current ? `${base} · ${current.label}` : base
    }

    function go(p, pushHash = true) {
      if (!PAGE_KEYS.includes(p)) p = 'profile'
      if (!pushHash && page.value === p) return
      page.value = p
      if (pushHash && window.location.hash !== `#${p}`) {
        window.location.hash = p
      }
      updateDocumentTitle()
      stopRefresh()
      if (p === 'profile') {
        loadHistory()
        loadProfileLlmStatus()
      }
      if (p === 'classes') loadStudentClasses()
      if (p === 'team') { loadActivities().then(() => loadGroups()).then(() => { loadTeamDashboard(); startRefresh() }) }
      if (p === 'tasks') loadPersonal()
      if (p === 'community') loadFeed()
      if (p === 'messages') loadConversations()
      if (p === 'account') loadMe()
    }

    function setLanguage(lang) {
      language.value = STUDENT_I18N[lang] ? lang : 'zh-CN'
      TeamMindRuntime.storage.setItem(APP_LANG_KEY, language.value)
      TeamMindRuntime.storage.setItem('teammind_portal_lang', language.value)
      document.documentElement.lang = language.value
      updateDocumentTitle()
      try {
        const u = new URL(window.location.href)
        if (language.value === 'zh-CN') u.searchParams.delete('lang')
        else u.searchParams.set('lang', language.value)
        window.history.replaceState(null, '', u.pathname + u.search + u.hash)
      } catch {
        // ignore
      }
      globalThis.teammindApplyBootInline?.()
      globalThis.TeamMindI18n?.applyBootScreenI18n?.('student')
    }

    function onHashChange() {
      const key = window.location.hash.replace('#', '')
      if (PAGE_KEYS.includes(key)) go(key, false)
    }

    onMounted(() => {
      setLanguage(language.value)
      globalThis.teammindApplyBootInline?.()
      globalThis.TeamMindI18n?.applyBootScreenI18n?.('student')
      globalThis.TeamMindI18n?.hideBootScreen?.()
      window.addEventListener('teammind-auth-expired', handleAuthExpired)
      clearStaleAdminSession()
      if (isLoggedIn.value) {
        const key = window.location.hash.replace('#', '')
        page.value = PAGE_KEYS.includes(key) ? key : 'profile'
        window.addEventListener('hashchange', onHashChange)
        loadHistory()
        loadTagCatalog()
        loadStudentClasses()
        loadActivities()
        if (page.value === 'classes') loadStudentClasses()
        if (page.value === 'team') go('team', false)
        if (page.value === 'tasks') loadPersonal()
        if (page.value === 'community') loadFeed()
        if (page.value === 'messages') loadConversations()
        if (page.value === 'account') loadMe()
      }
    })

    onUnmounted(() => {
      stopRefresh()
      window.removeEventListener('hashchange', onHashChange)
      window.removeEventListener('teammind-auth-expired', handleAuthExpired)
    })

    return {
      NAV_ITEMS, navItems, page, user, isLoggedIn, loading, tab, loginForm, regForm,
      rawText, profile, profileLlmHint, history, groups, personal, groupId, teamDashboard,
      availableClasses, myClassData, myClassMemberships, myClassRequests, classRequestMessage,
      selectedStudentClassId, selectedStudentClass, activeClassMemberships, classActivities, classActivityForm,
      activities, selectedActivityId, currentActivity, myParticipant, myConfirmation, isConfirmationStage, confirmationSummary,
      activityTeams, teamForm, joinMessage, myRoom, confirmationForm, candidateMembers,
      tagCatalog, displayTagCatalog, activeTags, customTag, profileTab, resumeFile, calculating, calculateProgress, calculateText,
      communityFeed, postForm, postMedia, commentInputs, expandedComments,
      conversations, messages, chatTargetId, chatConversationId, chatInput,
      currentNav, personalAlerts, myGroup, myTeamRole, teammates,
      language, LANGUAGE_OPTIONS, t, setLanguage,
      ADMIN_PORTAL_URL, scorePct, scoreStyle, scoreLevel, userInitial, userAvatar, activityDisplayTitle, displayDemoText, formatGroupingAdviceText, formatDynamicText, formatInsightText, formatActivityStatus, demoImageFallback, riskTagType, formatDeadline,
      roleTitle, roleCandidates, roleSummary, positiveInsights, profileSuggestion,
      localizedRoleSummary, localizedPositiveInsights, localizedProfileSuggestion, localizedRoleCandidates, translateProfileText,
      tagDimensionClass, tagIcon,
      accountForm, passwordForm, taskCreateForm, doLogin, doRegister, logout, loadMe, saveAccount, changePassword, parseText, parseResume, onResumeFile, updateProgress, submitTaskFeedback, createStudentTask, loadTeamDashboard, go,
      loadStudentClasses, loadClassActivities, createClassActivity, requestJoinClass, requestLeaveClass,
      loadActivities, joinActivity, syncActivityTags, loadActivityTeams, createTeamRoom, requestJoinTeam, handleJoinRequest, leaveTeamRoom,
      submitTeamConfirmation,
      isTagSelected, groupedTags, hotTags, tagNamesByDimension, setTagsForDimension,
      toggleTag, addCustomTag, createPost, onPostMedia, interactPost, toggleComments, submitComment, openConversation, startChat, sendMessage,
    }
  },
  template: `
    <div v-if="!isLoggedIn" class="login-page">
      <div class="login-brand">
        <h1>{{ t('brandTitle') }}</h1>
        <p class="brand-en">{{ t('brandEn') }}</p>
        <p class="tagline">{{ t('loginTagline') }}</p>
        <ul class="features">
          <li>{{ t('loginFeatureA') }}</li>
          <li>{{ t('loginFeatureB') }}</li>
          <li>{{ t('loginFeatureC') }}</li>
        </ul>
        <a class="role-switch-card" :href="ADMIN_PORTAL_URL">
          <span>🧑‍🏫</span>
          <strong>{{ t('switchToAdmin') }}</strong>
          <small>{{ t('switchToAdminHint') }}</small>
        </a>
      </div>
      <div class="login-panel">
        <div class="login-card">
          <el-select v-model="language" size="small" style="width:140px;margin-bottom:16px" @change="setLanguage">
            <el-option v-for="item in LANGUAGE_OPTIONS" :key="item.code" :label="item.label" :value="item.code" />
          </el-select>
          <div class="card-title">{{ t('loginTitle') }}</div>
          <p class="card-sub">{{ t('loginSub') }}</p>
          <el-tabs v-model="tab" stretch>
            <el-tab-pane :label="t('login')" name="login">
              <el-form label-position="top">
                <el-form-item :label="t('account')"><el-input v-model="loginForm.account" size="large" /></el-form-item>
                <el-form-item :label="t('password')"><el-input v-model="loginForm.password" type="password" show-password size="large" @keyup.enter="doLogin" /></el-form-item>
                <el-button type="primary" :loading="loading" @click="doLogin" size="large" style="width:100%">{{ t('login') }}</el-button>
              </el-form>
            </el-tab-pane>
            <el-tab-pane :label="t('register')" name="register">
              <el-form label-position="top">
                <el-form-item :label="t('name')"><el-input v-model="regForm.name" size="large" /></el-form-item>
                <el-form-item :label="t('account')"><el-input v-model="regForm.account" size="large" /></el-form-item>
                <el-form-item :label="t('password')"><el-input v-model="regForm.password" type="password" show-password size="large" /></el-form-item>
                <el-button type="primary" :loading="loading" @click="doRegister" size="large" style="width:100%">{{ t('register') }}</el-button>
              </el-form>
            </el-tab-pane>
          </el-tabs>
          <p class="login-footer">{{ t('adminHint') }} <a :href="ADMIN_PORTAL_URL" target="_blank">{{ t('adminBackend') }}</a></p>
          <a class="login-switch-link" :href="ADMIN_PORTAL_URL">🧑‍🏫 {{ t('switchToAdmin') }}</a>
        </div>
      </div>
    </div>

    <div v-else class="layout">
      <aside class="aside">
        <div class="logo">
          <div class="logo-title">{{ t('brandShort') }}</div>
          <div class="logo-sub">{{ t('workspaceName') }}</div>
        </div>
        <nav class="nav-list">
          <a v-for="n in navItems" :key="n.key" class="nav-item" :class="{active: page===n.key}" @click="go(n.key)">
            <span class="nav-icon">{{ n.icon }}</span><span>{{ n.label }}</span>
          </a>
        </nav>
        <div class="aside-switch">
          <a :href="ADMIN_PORTAL_URL">
            <span>🧑‍🏫</span>
            <strong>{{ t('switchToAdmin') }}</strong>
          </a>
        </div>
      </aside>
      <div class="main">
        <header class="header">
          <div>
            <div class="page-title">{{ currentNav.label }}</div>
            <div class="page-desc">{{ currentNav.desc }}</div>
          </div>
          <div class="header-actions">
            <el-select v-model="language" size="small" style="width:132px" @change="setLanguage">
              <el-option v-for="item in LANGUAGE_OPTIONS" :key="item.code" :label="item.label" :value="item.code" />
            </el-select>
            <a class="top-switch-button" :href="ADMIN_PORTAL_URL">🧑‍🏫 {{ t('switchToAdmin') }}</a>
            <el-dropdown trigger="click">
              <div class="user-chip clickable">
                <div class="avatar">
                  <img v-if="userAvatar(user)" :src="userAvatar(user)" :alt="t('头像')" />
                  <span v-else>{{ userInitial(user?.name) }}</span>
                </div>
                <span class="user-name">{{ user?.name }}</span>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="go('account')">{{ t('profileHome') }}</el-dropdown-item>
                  <el-dropdown-item divided @click="logout">{{ t('logout') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </header>
        <main class="content">
          <template v-if="page==='classes'">
            <div class="activity-board">
              <div class="activity-board-main">
                <span class="activity-pill">Classroom</span>
                <h2>{{ t('我的班级') }}</h2>
                <p>{{ t('加入班级后，老师创建课程项目时会按班级范围生成均匀分组。加入和退出都需要老师审批，避免小组范围混乱。') }}</p>
              </div>
              <el-button @click="loadStudentClasses">{{ t('刷新') }}</el-button>
            </div>

            <div class="class-student-grid">
              <div class="card">
                <div class="card-header">
                  <div>
                    <h3>{{ t('已加入 / 待审批班级') }}</h3>
                    <p class="hint">{{ t('退出申请通过前，你仍会保留在当前班级成员名单中。') }}</p>
                  </div>
                </div>
                <div v-if="!myClassMemberships.length" class="empty-note">{{ t('还没有加入任何班级，可以在右侧申请。') }}</div>
                <div v-for="m in myClassMemberships" :key="m.id" class="student-class-card">
                  <div>
                    <strong>{{ displayDemoText(m.classroom?.name) || (t('班级') + m.class_id) }}</strong>
                    <p>{{ displayDemoText(m.classroom?.course_name || m.classroom?.major) || t('课程信息待补充') }}</p>
                  </div>
                  <div class="student-class-actions">
                    <el-tag :type="m.status==='active'?'success':'warning'">{{ formatActivityStatus(m.status) }}</el-tag>
                    <el-button v-if="m.status==='active'" size="small" plain @click="requestLeaveClass(m)">{{ t('申请退出') }}</el-button>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div>
                    <h3>{{ t('可加入班级') }}</h3>
                    <p class="hint">{{ t('提交申请后，等待任课老师或管理员审批。') }}</p>
                  </div>
                </div>
                <el-input v-model="classRequestMessage" :placeholder="t('申请说明（可选，例如我是本课程学生）')" style="margin-bottom:12px" />
                <div v-for="c in availableClasses" :key="c.id" class="student-class-card">
                  <div>
                    <strong>{{ displayDemoText(c.name) }}</strong>
                    <p>{{ displayDemoText(c.course_name || c.major) || (t('未设置课程') + ' ·') }} {{ c.member_count || 0 }}/{{ c.max_students || 20 }} {{ t('人') }}</p>
                    <small class="hint">{{ formatGroupingAdviceText(c.grouping_advice) }}</small>
                    <small v-if="c.grouping_advice?.ai_analysis" class="hint">AI {{ t('分析：') }} {{ formatInsightText(c.grouping_advice.ai_analysis.summary) }}</small>
                  </div>
                  <div class="student-class-actions">
                    <el-tag v-if="c.my_membership" :type="c.my_membership.status==='active'?'success':'warning'">{{ formatActivityStatus(c.my_membership.status) }}</el-tag>
                    <el-tag v-else-if="c.my_pending_request" type="warning">{{ t('审批中') }}</el-tag>
                    <el-button v-else size="small" type="primary" @click="requestJoinClass(c)">{{ t('申请加入') }}</el-button>
                  </div>
                </div>
              </div>
            </div>

            <div class="card">
              <h3>{{ t('我的申请记录') }}</h3>
              <el-table :data="myClassRequests" stripe :empty-text="t('暂无申请记录')">
                <el-table-column :label="t('班级')"><template #default="{row}">{{ displayDemoText(row.classroom?.name) || row.class_id }}</template></el-table-column>
                <el-table-column :label="t('类型')" width="90"><template #default="{row}">{{ row.request_type==='join' ? t('加入') : t('退出') }}</template></el-table-column>
                <el-table-column :label="t('状态')" width="100"><template #default="{row}"><el-tag size="small">{{ formatActivityStatus(row.status) }}</el-tag></template></el-table-column>
                <el-table-column :label="t('说明')"><template #default="{row}">{{ formatDynamicText(row.message) || '—' }}</template></el-table-column>
                <el-table-column :label="t('老师备注')"><template #default="{row}">{{ formatDynamicText(row.reviewed_note) || '—' }}</template></el-table-column>
              </el-table>
            </div>

            <div class="card">
              <div class="card-header">
                <div>
                  <h3>{{ t('班级活动') }}</h3>
                  <p class="hint">{{ t('选择你所属的班级，查看该班当前组队活动；也可以为这个班级发起一个活动。') }}</p>
                </div>
                <el-select v-model="selectedStudentClassId" :placeholder="t('选择班级')" style="width:260px" @change="loadClassActivities">
                  <el-option v-for="m in activeClassMemberships" :key="m.class_id" :label="displayDemoText(m.classroom?.name) || (t('班级') + m.class_id)" :value="m.class_id" />
                </el-select>
              </div>
              <div v-if="selectedStudentClass" class="student-class-activity-create">
                <el-input v-model="classActivityForm.title" :placeholder="t('活动标题，如：期末展示自由组队')" />
                <el-select v-model="classActivityForm.mode" style="width:160px">
                  <el-option :label="t('学生自由组队')" value="free_team" />
                  <el-option :label="t('任务驱动自动组队')" value="task_auto" />
                </el-select>
                <el-input-number v-model="classActivityForm.group_size" :min="2" :max="8" />
                <el-button type="primary" @click="createClassActivity">{{ t('创建到该班级') }}</el-button>
              </div>
              <el-input v-if="selectedStudentClass" v-model="classActivityForm.task_goal" type="textarea" :rows="2" :placeholder="t('活动说明/任务需求（可选）')" style="margin-bottom:12px" />
              <el-table :data="classActivities" stripe :empty-text="t('当前班级暂无活动')">
                <el-table-column :label="t('活动')" min-width="180"><template #default="{row}">{{ activityDisplayTitle(row) }}</template></el-table-column>
                <el-table-column :label="t('班级')" min-width="140"><template #default="{row}">{{ displayDemoText(selectedStudentClass?.classroom?.name || row.classroom?.name) || t('当前班级') }}</template></el-table-column>
                <el-table-column :label="t('方式')" width="130"><template #default="{row}">{{ row.mode==='task_auto' ? t('任务驱动') : t('自由组队') }}</template></el-table-column>
                <el-table-column :label="t('状态')" width="100"><template #default="{row}">{{ formatActivityStatus(row.status) }}</template></el-table-column>
                <el-table-column :label="t('操作')" width="120">
                  <template #default="{row}">
                    <el-button size="small" type="primary" plain @click="selectedActivityId=row.id; go('team')">{{ t('查看/参与') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>

          <template v-if="page==='profile'">
            <div v-if="currentActivity" class="activity-hero-card">
              <div>
                <span class="activity-pill">{{ currentActivity.mode==='task_auto' ? t('任务驱动组队') : t('自由组队') }}</span>
                <h3>{{ activityDisplayTitle(currentActivity) }}</h3>
                <p>{{ formatDynamicText(currentActivity.task_goal || currentActivity.description) || t('老师已发起新的组队活动，请选择是否参与。') }}</p>
              </div>
              <div class="activity-hero-actions">
                <el-tag :type="myParticipant ? 'success' : 'warning'">{{ myParticipant ? t('已参与') : t('待参与') }}</el-tag>
                <el-button type="primary" @click="myParticipant ? syncActivityTags() : joinActivity()">{{ myParticipant ? t('同步当前标签') : t('参与活动') }}</el-button>
                <el-button plain @click="go('team')">{{ t('查看活动') }}</el-button>
              </div>
            </div>
            <div class="theory-panel">
              <h4>{{ t('先完成你的项目名片') }}</h4>
              <p>{{ t('选择几个与你相关的标签，系统会整理出适合你的角色方向。也可以补充一段自我介绍，让建议更准确。') }}</p>
              <p v-if="profileLlmHint" class="hint" style="margin-top:8px;color:#b45309">{{ formatDynamicText(profileLlmHint) }}</p>
            </div>
            <div class="card profile-tag-card">
              <div class="profile-card-head">
                <div class="profile-card-title">
                  <span class="profile-title-icon">🏷️</span>
                  <div>
                    <h3>{{ t('我的项目标签') }}</h3>
                    <p class="hint">{{ t('先按维度快速圈出特点，再用自由描述补充细节。') }}</p>
                  </div>
                </div>
                <div class="profile-step-mini">
                  <span>{{ t('① 主动标签') }}</span>
                  <span>{{ t('② 自由描述') }}</span>
                </div>
              </div>
              <el-tabs v-model="profileTab">
                <el-tab-pane :label="t('① 主动标签')" name="tags">
                  <p class="hint">{{ t('点击标签选中/取消；自定义标签可选。仅选主动标签也可提交，自由描述为补充项。') }}</p>
                  <div class="tag-section dimension-knowledge">
                    <div class="tag-section-head">
                      <div class="dimension-title">
                        <span class="dimension-icon">📚</span>
                        <div><h4>{{ t('知识维度') }}</h4><small>{{ t('你熟悉的课程、理论和领域方向') }}</small></div>
                      </div>
                      <span>{{ (tagCatalog.knowledge||[]).length }} {{ t('个标签') }}</span>
                    </div>
                    <el-select :key="'knowledge-' + language" :model-value="tagNamesByDimension('knowledge')" multiple filterable clearable :placeholder="t('搜索或下拉选择知识标签')" class="tag-select" @change="(names)=>setTagsForDimension('knowledge', names)">
                      <el-option-group v-for="(items, category) in groupedTags('knowledge')" :key="category" :label="category">
                        <el-option v-for="tag in items" :key="tag.id" :label="tag.displayName || tag.name" :value="tag.name" />
                      </el-option-group>
                    </el-select>
                    <div class="tag-picker">
                      <el-tag v-for="tag in hotTags('knowledge')" :key="tag.id" :type="isTagSelected(tag.name)?'primary':'info'" effect="plain" class="pick-tag" @click="toggleTag(tag,'knowledge')">{{ tag.displayName || tag.name }}</el-tag>
                    </div>
                  </div>
                  <div class="tag-section dimension-skill">
                    <div class="tag-section-head">
                      <div class="dimension-title">
                        <span class="dimension-icon">🛠️</span>
                        <div><h4>{{ t('技能维度') }}</h4><small>{{ t('你能承担的工具、方法和执行任务') }}</small></div>
                      </div>
                      <span>{{ (tagCatalog.skill||[]).length }} {{ t('个标签') }}</span>
                    </div>
                    <el-select :key="'skill-' + language" :model-value="tagNamesByDimension('skill')" multiple filterable clearable :placeholder="t('搜索或下拉选择技能标签')" class="tag-select" @change="(names)=>setTagsForDimension('skill', names)">
                      <el-option-group v-for="(items, category) in groupedTags('skill')" :key="category" :label="category">
                        <el-option v-for="tag in items" :key="tag.id" :label="tag.displayName || tag.name" :value="tag.name" />
                      </el-option-group>
                    </el-select>
                    <div class="tag-picker">
                      <el-tag v-for="tag in hotTags('skill')" :key="tag.id" :type="isTagSelected(tag.name)?'primary':'info'" effect="plain" class="pick-tag" @click="toggleTag(tag,'skill')">{{ tag.displayName || tag.name }}</el-tag>
                    </div>
                  </div>
                  <div class="tag-section dimension-collab">
                    <div class="tag-section-head">
                      <div class="dimension-title">
                        <span class="dimension-icon">🤝</span>
                        <div><h4>{{ t('协作维度') }}</h4><small>{{ t('你在团队里的沟通、推进和配合方式') }}</small></div>
                      </div>
                      <span>{{ (tagCatalog.collab||[]).length }} {{ t('个标签') }}</span>
                    </div>
                    <el-select :key="'collab-' + language" :model-value="tagNamesByDimension('collab')" multiple filterable clearable :placeholder="t('搜索或下拉选择协作标签')" class="tag-select" @change="(names)=>setTagsForDimension('collab', names)">
                      <el-option-group v-for="(items, category) in groupedTags('collab')" :key="category" :label="category">
                        <el-option v-for="tag in items" :key="tag.id" :label="tag.displayName || tag.name" :value="tag.name" />
                      </el-option-group>
                    </el-select>
                    <div class="tag-picker">
                      <el-tag v-for="tag in hotTags('collab')" :key="tag.id" :type="isTagSelected(tag.name)?'primary':'info'" effect="plain" class="pick-tag" @click="toggleTag(tag,'collab')">{{ tag.displayName || tag.name }}</el-tag>
                    </div>
                  </div>
                  <div class="custom-tag-panel">
                    <span class="custom-tag-icon">✨</span>
                    <div>
                      <strong>{{ t('自定义标签（可选）') }}</strong>
                      <p>{{ t('没有合适标签时，可以补一个最能代表你的关键词。') }}</p>
                    </div>
                    <el-input v-model="customTag" :placeholder="t('自定义标签（可选）')" />
                    <el-button @click="addCustomTag('skill')">{{ t('添加') }}</el-button>
                  </div>
                  <div class="selected-tags-panel">
                    <strong>{{ t('已选') }} {{ activeTags.length }} {{ t('个：') }}</strong>
                    <div class="selected-tags-list">
                      <el-tag v-for="tag in activeTags" :key="tag.name" closable @close="activeTags=activeTags.filter(x=>x.name!==tag.name)" :class="['selected-tag', tagDimensionClass(tag)]">
                        <span class="tag-chip-icon">{{ tagIcon(tag) }}</span>{{ translateProfileText(tag.name) }}
                      </el-tag>
                    </div>
                  </div>
                </el-tab-pane>
                <el-tab-pane :label="t('② 自由描述')" name="text">
                  <p class="hint">{{ t('可选。DeepSeek 会结合主动标签分析自由文本；不填写时仅依据已选标签生成画像。') }}</p>
                  <el-input v-model="rawText" type="textarea" :rows="8" maxlength="800" show-word-limit :placeholder="t('可选：例如计算机专业，熟悉 Python 与前端...')" />
                </el-tab-pane>
                <el-tab-pane :label="t('③ 简历上传')" name="resume">
                  <p class="hint">{{ t('上传 PDF / DOC / DOCX 简历，系统会提取经历并融合已选标签生成画像。') }}</p>
                  <div class="custom-tag-panel">
                    <span class="custom-tag-icon">📄</span>
                    <div>
                      <strong>{{ resumeFile ? (t('已选择：') + resumeFile.name) : t('选择简历文件') }}</strong>
                      <p>{{ t('支持 PDF、DOC、DOCX；若解析失败，可回到自由描述手动补充。') }}</p>
                    </div>
                    <input type="file" accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" @change="onResumeFile" />
                    <el-button type="primary" plain :disabled="!resumeFile" :loading="loading" @click="parseResume">{{ t('解析简历并生成画像') }}</el-button>
                  </div>
                </el-tab-pane>
              </el-tabs>
              <el-button type="primary" :loading="loading" @click="parseText" size="large" style="margin-top:16px">{{ t('提交并生成综合画像') }}</el-button>
            </div>
            <div v-if="profile" class="card profile-result-card">
              <div class="profile-result-head">
                <div>
                  <h3>{{ t('我的协作画像') }}</h3>
                  <p class="hint">{{ t('根据你的主动标签、学习互动和任务表现生成，仅展示正向角色建议') }}</p>
                </div>
                <el-tag type="success" size="large">{{ t('多角色方向') }}</el-tag>
              </div>
              <div class="role-hero">
                <div class="role-badge">{{ t('适合以下角色方向') }}</div>
                <div class="role-options">
                  <div v-for="(role, idx) in localizedRoleCandidates" :key="role.name + '-' + idx" class="role-option" :class="'rank-' + idx">
                    <span class="role-rank">{{ idx + 1 }}</span>
                    <strong>{{ role.name }}</strong>
                    <small>{{ role.source }}</small>
                  </div>
                </div>
                <p>{{ localizedRoleSummary }}</p>
              </div>
              <div class="profile-insight-grid role-insight-grid">
                <div class="profile-insight role-insight" v-for="item in localizedPositiveInsights" :key="item.title">
                  <div class="insight-icon">{{ item.icon }}</div>
                  <h4>{{ item.title }}</h4>
                  <p>{{ item.text }}</p>
                </div>
              </div>
              <div class="profile-insight-grid">
                <div class="profile-insight" v-if="profile.active_tags?.length">
                  <h4>{{ t('你选择的标签') }}</h4>
                  <span v-for="tag in profile.active_tags" :key="tag.name" class="ability-badge" :class="tagDimensionClass(tag)">
                    <b>{{ tagIcon(tag) }}</b>{{ translateProfileText(tag.name) }}
                  </span>
                </div>
                <div class="profile-insight" v-if="profile.passive_tags?.length">
                  <h4>{{ t('学习互动标签') }}</h4>
                  <span v-for="tag in profile.passive_tags" :key="tag.name" class="ability-badge passive" :class="tagDimensionClass(tag)">
                    <b>{{ tagIcon(tag) }}</b>{{ translateProfileText(tag.name) }}
                  </span>
                </div>
              </div>
              <div class="student-suggestion">
                <strong>{{ t('给你的建议') }}</strong>
                <p>{{ localizedProfileSuggestion }}</p>
              </div>
            </div>
          </template>

          <template v-if="page==='team'">
            <div v-if="!activities.length" class="card">
              <el-empty :description="t('暂无当前组队活动')">
                <template #default><p class="hint">{{ t('老师创建并发布组队活动后，这里会显示参与入口和队伍信息。') }}</p></template>
              </el-empty>
            </div>
            <template v-else>
              <div class="activity-board">
                <div class="activity-board-main">
                  <span class="activity-pill">{{ currentActivity?.mode==='task_auto' ? t('任务驱动自动组队') : t('学生自由组队') }}</span>
                  <h2>{{ activityDisplayTitle(currentActivity) }}</h2>
                  <p>{{ formatDynamicText(currentActivity?.task_goal || currentActivity?.description) || t('请按老师要求参与本次组队活动。') }}</p>
                  <div class="activity-board-actions">
                    <el-button v-if="!myParticipant" type="primary" @click="joinActivity()">{{ t('参与本次活动') }}</el-button>
                    <el-button v-else type="primary" plain @click="syncActivityTags()">{{ t('同步我的标签') }}</el-button>
                    <el-tag :type="myParticipant ? 'success' : 'warning'">{{ myParticipant ? t('已参与') : t('未参与') }}</el-tag>
                    <el-tag>{{ formatActivityStatus(currentActivity?.status) }}</el-tag>
                  </div>
                </div>
                <el-select v-model="selectedActivityId" style="width:260px" @change="loadActivities">
                  <el-option v-for="a in activities" :key="a.id" :label="activityDisplayTitle(a)" :value="a.id" />
                </el-select>
              </div>

              <div v-if="currentActivity?.mode==='free_team' && myParticipant" class="card">
                <div class="card-header"><h3>{{ t('组队大厅') }}</h3><el-button @click="loadActivityTeams">{{ t('刷新') }}</el-button></div>
                <div v-if="!myRoom" class="free-create-box">
                  <el-input v-model="teamForm.name" :placeholder="t('队伍名称')" />
                  <el-input v-model="teamForm.description" :placeholder="t('队伍说明 / 想找什么伙伴')" />
                  <el-button type="primary" @click="createTeamRoom">{{ t('创建我的队伍') }}</el-button>
                </div>
                <div class="free-room-grid">
                  <div v-for="room in activityTeams" :key="room.id" class="free-room-card" :class="{mine: room.id===myRoom?.id}">
                    <div class="room-head">
                      <strong>{{ room.name }}</strong>
                      <el-tag size="small">{{ (room.member_ids||[]).length }} {{ t('人') }}</el-tag>
                    </div>
                    <p>{{ room.description || t('队伍暂未填写说明') }}</p>
                    <div class="room-members">
                      <el-tag v-for="m in room.members||[]" :key="m.id" size="small">{{ m.name }}</el-tag>
                    </div>
                    <template v-if="room.leader_id===user?.id">
                      <div v-for="req in room.pending_requests||[]" :key="req.id" class="join-request">
                        <span>{{ req.user?.name || req.user_id }} {{ t('申请加入') }}</span>
                        <el-button size="small" type="success" @click="handleJoinRequest(req,'approve')">{{ t('同意') }}</el-button>
                        <el-button size="small" @click="handleJoinRequest(req,'reject')">{{ t('拒绝') }}</el-button>
                      </div>
                    </template>
                    <div v-if="!myRoom && room.leader_id!==user?.id" class="join-box">
                      <el-input v-model="joinMessage" size="small" :placeholder="t('给队长留言（可选）')" />
                      <el-button size="small" type="primary" @click="requestJoinTeam(room)">{{ t('申请加入') }}</el-button>
                    </div>
                    <el-button v-if="room.id===myRoom?.id" size="small" plain @click="leaveTeamRoom(room)">{{ t('退出队伍') }}</el-button>
                  </div>
                </div>
              </div>

              <div v-if="currentActivity?.mode==='task_auto' && myParticipant && !myGroup" class="waiting-card">
                <div class="waiting-orbit"></div>
                <h3>{{ t('等待老师汇总并发布分组') }}</h3>
                <p>{{ t('你已参与本次活动。系统会结合本次标签、历史互动和任务需求生成队伍，老师发布后这里会显示你的团队。') }}</p>
              </div>

              <div v-if="currentActivity?.mode==='free_team' && myParticipant && currentActivity.status!=='locked'" class="waiting-card small">
                <h3>{{ t('自由组队进行中') }}</h3>
                <p>{{ t('可以继续创建、申请或调整队伍。老师锁定后会进入正式团队页。') }}</p>
              </div>

              <div v-if="currentActivity?.mode==='task_auto' && myGroup && isConfirmationStage" class="card confirm-panel">
                <div class="card-header">
                  <div>
                    <h3>{{ t('预沟通确认：候选团队还未最终锁定') }}</h3>
                    <p class="hint">{{ t('请先和候选队友沟通，确认大家是否接受当前角色定位和后续任务方向；如不合适，可以提交微调申请给老师。') }}</p>
                  </div>
                  <el-tag :type="myConfirmation?.status==='accepted' ? 'success' : (myConfirmation?.status==='adjust_requested' ? 'warning' : 'info')">
                    {{ formatActivityStatus(myConfirmation?.status || 'pending') }}
                  </el-tag>
                </div>
                <p v-if="myGroup.complement_note" class="explain-banner">{{ t('候选匹配依据：') }} {{ formatInsightText(myGroup.complement_note) }}</p>
                <div v-if="myGroup.ai_analysis" class="student-ai-card">
                  <strong>{{ t('AI 候选团队分析') }}</strong>
                  <p>{{ formatInsightText(myGroup.ai_analysis.summary) }}</p>
                  <span v-for="x in myGroup.ai_analysis.recommendations||[]" :key="x">{{ formatInsightText(x) }}</span>
                </div>
                <div class="summary-pills" v-if="confirmationSummary">
                  <span class="pill">{{ t('确认率') }} {{ confirmationSummary.accept_rate }}</span>
                  <span class="pill warn" v-if="confirmationSummary.adjust_requested">{{ t('微调申请') }} {{ confirmationSummary.adjust_requested }}</span>
                  <span class="pill">{{ t('待确认') }} {{ confirmationSummary.pending }}</span>
                </div>
                <div class="member-grid">
                  <div v-for="m in candidateMembers" :key="m.id" class="member-card" :class="{me: m.id===user?.id}">
                    <div class="member-head">
                      <div class="member-avatar">{{ userInitial(m.name) }}</div>
                      <div>
                        <strong>{{ m.name }}{{ m.id===user?.id ? t('（我）') : '' }}</strong>
                        <div class="hint">{{ m.bio ? formatDynamicText(m.bio) : t('暂未填写个人介绍') }}</div>
                      </div>
                    </div>
                    <el-button v-if="m.id!==user?.id" size="small" plain @click="startChat(m.id)">{{ t('发消息沟通') }}</el-button>
                  </div>
                </div>
                <el-form label-position="top" class="confirm-form">
                  <el-form-item :label="t('希望承担/调整的角色（可选）')">
                    <el-input v-model="confirmationForm.preferred_role" :placeholder="translateProfileText(myConfirmation?.preferred_role || myTeamRole) || t('如：技术开发、文档汇报、协调对接')" />
                  </el-form-item>
                  <el-form-item :label="t('希望承担或避免的任务（可选）')">
                    <el-input v-model="confirmationForm.task_preferences" :placeholder="t('如：愿意做原型；不适合后端；需要同伴协助数据分析')" />
                  </el-form-item>
                  <el-form-item :label="t('沟通备注 / 微调原因')">
                    <el-input v-model="confirmationForm.reason" type="textarea" :rows="3" :placeholder="t('如果不接受当前安排，请说明原因；接受时也可以写给老师和队友的备注。')" />
                  </el-form-item>
                  <div class="toolbar-row">
                    <el-button type="primary" :loading="loading" @click="submitTeamConfirmation(true)">{{ t('接受当前团队与角色') }}</el-button>
                    <el-button type="warning" plain :loading="loading" @click="submitTeamConfirmation(false)">{{ t('提交微调申请') }}</el-button>
                  </div>
                </el-form>
              </div>

              <template v-if="myGroup">
              <div class="theory-panel supervision">
                <h4>{{ t('当前活动团队') }}</h4>
                <p>{{ isConfirmationStage ? t('这是候选团队，老师锁定后会进入正式分工。') : t('只展示本次活动对应的团队和队友任务进度，历史小组不会混在这里。') }}</p>
              </div>
              <div class="card highlight-card" v-if="myTeamRole">
                <p>{{ t('你在') }} <strong>{{ myGroup?.group_name }}</strong> {{ t('中的角色') }}</p>
                <el-tag type="primary" size="large">{{ translateProfileText(myTeamRole) }}</el-tag>
              </div>
              <div class="card toolbar-row" v-if="groups.length > 1">
                <el-select v-model="groupId" @change="loadTeamDashboard" style="width:220px">
                  <el-option v-for="g in groups" :key="g.id" :label="g.group_name" :value="g.id" />
                </el-select>
                <el-button @click="loadTeamDashboard">{{ t('刷新') }}</el-button>
                <span class="hint">{{ t('每 30 秒自动刷新团队数据') }}</span>
              </div>
              <template v-if="teamDashboard">
                <p v-if="teamDashboard.grouping_explain" class="explain-banner">{{ t('本组组队依据：') }} {{ formatDynamicText(teamDashboard.grouping_explain) }}</p>
                <div v-if="teamDashboard.group?.ai_analysis" class="student-ai-card">
                  <strong>{{ t('AI 团队协作建议') }}</strong>
                  <p>{{ formatDynamicText(teamDashboard.group.ai_analysis.summary) }}</p>
                  <span v-for="x in teamDashboard.group.ai_analysis.recommendations||[]" :key="x">{{ formatDynamicText(x) }}</span>
                </div>
                <div class="summary-pills">
                  <span class="pill">{{ t('团队完成率') }} {{ teamDashboard.summary?.completion_rate }}</span>
                  <span class="pill warn" v-if="teamDashboard.summary?.warning_risks">{{ t('预警') }} {{ teamDashboard.summary.warning_risks }}</span>
                </div>
                <div class="card">
                  <h3>{{ t('队友进度（全员可见）') }}</h3>
                  <div class="member-grid">
                    <div v-for="m in teamDashboard.members" :key="m.user?.id" class="member-card" :class="{me: m.user?.id===user?.id}">
                      <div class="member-head">
                        <div class="member-avatar">{{ userInitial(m.user?.name) }}</div>
                        <div>
                          <strong>{{ m.user?.name }}{{ m.user?.id===user?.id ? t('（我）') : '' }}</strong>
                          <div style="font-size:12px;color:#64748b">{{ m.team_role ? translateProfileText(m.team_role) : t('角色待定') }}</div>
                        </div>
                        <el-tag size="small" :type="m.engagement?.engagement_level==='low'?'danger':'success'">{{ formatDynamicText(m.engagement?.engagement_label) }}</el-tag>
                      </div>
                      <el-progress :percentage="m.engagement?.avg_progress||0" />
                    </div>
                  </div>
                </div>
                <div class="card">
                  <div class="card-header">
                    <div>
                      <h3>{{ t('全组任务（互相可见）') }}</h3>
                      <p class="hint">{{ t('老师分配的任务和同学主动创建的任务都会显示在这里，方便互相了解、协作和调整。') }}</p>
                    </div>
                    <el-button type="primary" plain @click="go('tasks')">{{ t('我想创建任务') }}</el-button>
                  </div>
                  <el-table v-if="(teamDashboard.tasks||[]).length" :data="teamDashboard.tasks" stripe>
                    <el-table-column :label="t('任务')" min-width="160"><template #default="{row}">{{ formatDynamicText(row.task_name) }}</template></el-table-column>
                    <el-table-column :label="t('负责人')" width="120">
                      <template #default="{row}">
                        {{ (teamDashboard.members||[]).find(m=>m.user?.id===row.assignee_id)?.user?.name || (t('用户') + row.assignee_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column :label="t('说明')" min-width="220"><template #default="{row}"><span class="explain-text">{{ formatDynamicText(row.assign_reason || row.description) || '—' }}</span></template></el-table-column>
                    <el-table-column :label="t('截止')" width="110"><template #default="{row}">{{ formatDeadline(row.deadline) }}</template></el-table-column>
                    <el-table-column :label="t('进度')" width="160"><template #default="{row}"><el-progress :percentage="row.progress||0" /></template></el-table-column>
                    <el-table-column :label="t('状态')" width="100"><template #default="{row}"><el-tag size="small">{{ formatActivityStatus(row.status) }}</el-tag></template></el-table-column>
                  </el-table>
                  <el-empty v-else :description="t('暂无小组任务。老师分配或同学创建后会显示。')" />
                </div>
              </template>
              </template>
            </template>
          </template>

          <template v-if="page==='tasks'">
            <div class="card">
              <div class="card-header">
                <div>
                  <h3>{{ t('我想做的任务') }}</h3>
                  <p class="hint">{{ t('你可以主动创建并认领自己想做的任务。创建后会进入小组任务列表，队友和老师都能看到。') }}</p>
                </div>
              </div>
              <el-form label-position="top" class="student-task-form">
                <el-form-item :label="t('任务名称')"><el-input v-model="taskCreateForm.task_name" :placeholder="t('如：整理用户访谈问题、实现登录页原型、完成数据清洗')" /></el-form-item>
                <el-form-item :label="t('任务说明')"><el-input v-model="taskCreateForm.description" type="textarea" :rows="3" :placeholder="t('简单说明你准备做什么、产出是什么')" /></el-form-item>
                <el-form-item :label="t('为什么想做 / 需要什么协助')"><el-input v-model="taskCreateForm.reason" type="textarea" :rows="2" :placeholder="t('例如：我擅长前端，想负责页面实现；需要队友提供接口字段')" /></el-form-item>
                <div class="task-form-grid">
                  <el-form-item :label="t('难度')"><el-input-number v-model="taskCreateForm.difficulty" :min="1" :max="5" /></el-form-item>
                  <el-form-item :label="t('预计工时')"><el-input-number v-model="taskCreateForm.estimated_hours" :min="0.5" :max="80" :step="0.5" /></el-form-item>
                  <el-form-item :label="t('截止日期')"><el-date-picker v-model="taskCreateForm.deadline" value-format="YYYY-MM-DD" type="date" :placeholder="t('选择日期')" style="width:100%" /></el-form-item>
                </div>
                <el-button type="primary" :loading="loading" @click="createStudentTask">{{ t('创建并认领任务') }}</el-button>
              </el-form>
            </div>
            <div v-if="personalAlerts.length" class="card alert-list">
              <h3>{{ t('截止预警') }}</h3>
              <div v-for="a in personalAlerts" :key="a.task_id" class="alert-item" :class="a.level">
                <strong>{{ formatDynamicText(a.task_name) }}</strong> — {{ formatDynamicText(a.message) }}
              </div>
            </div>
            <div class="card">
              <h3>{{ t('我的子任务') }}</h3>
              <p class="hint">{{ t('系统按你的能力与偏好分配子任务。请更新完成百分比；逾期或滞后会在上方预警，队友在团队页可见你的进度。') }}</p>
              <el-table v-if="(personal.tasks||[]).length" :data="personal.tasks" stripe>
                <el-table-column :label="t('子任务')" min-width="140"><template #default="{row}">{{ formatDynamicText(row.task_name) }}</template></el-table-column>
                <el-table-column :label="t('分配依据')" min-width="200">
                  <template #default="{row}"><span class="explain-text">{{ formatDynamicText(row.assign_reason) || '—' }}</span></template>
                </el-table-column>
                <el-table-column :label="t('截止')" width="110"><template #default="{row}">{{ formatDeadline(row.deadline) }}</template></el-table-column>
                <el-table-column :label="t('风险')" width="80"><template #default="{row}"><el-tag v-if="row.risk" :type="riskTagType(row.risk.level)" size="small">{{ formatDynamicText(row.risk.label) }}</el-tag></template></el-table-column>
                <el-table-column :label="t('进度')" min-width="140"><template #default="{row}"><el-progress :percentage="row.progress||0" /></template></el-table-column>
                <el-table-column :label="t('操作')" width="180">
                  <template #default="{row}">
                    <el-button size="small" @click="updateProgress(row.id, Math.min(100,(row.progress||0)+10))">+10%</el-button>
                    <el-button size="small" type="primary" plain @click="updateProgress(row.id, 100)">{{ t('完成') }}</el-button>
                    <el-button size="small" type="warning" plain @click="submitTaskFeedback(row)">{{ t('反馈') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else :description="t('暂无任务。加入小组并由老师分配任务后显示。')" />
            </div>
            <div class="card">
              <h3>{{ t('全组任务动态') }}</h3>
              <p class="hint">{{ t('这里展示你所在小组的所有任务，包含老师分配和同学主动创建的任务。') }}</p>
              <el-table v-if="(personal.team_tasks||[]).length" :data="personal.team_tasks" stripe>
                <el-table-column :label="t('任务')" min-width="150"><template #default="{row}">{{ formatDynamicText(row.task_name) }}</template></el-table-column>
                <el-table-column :label="t('负责人')" width="110"><template #default="{row}">{{ row.assignee_id===user?.id ? t('我') : (t('用户') + row.assignee_id) }}</template></el-table-column>
                <el-table-column :label="t('说明')" min-width="220"><template #default="{row}"><span class="explain-text">{{ formatDynamicText(row.assign_reason || row.description) || '—' }}</span></template></el-table-column>
                <el-table-column :label="t('截止')" width="110"><template #default="{row}">{{ formatDeadline(row.deadline) }}</template></el-table-column>
                <el-table-column :label="t('进度')" width="150"><template #default="{row}"><el-progress :percentage="row.progress||0" /></template></el-table-column>
              </el-table>
              <el-empty v-else :description="t('暂无小组任务。')" />
            </div>
          </template>

          <template v-if="page==='community'">
            <div class="card">
              <h3>{{ t('发布学习动态') }}</h3>
              <p class="hint">{{ t('分享项目经验、兴趣方向、学习资料或组队想法；点赞、收藏、评论会形成你的被动画像标签。') }}</p>
              <el-input v-model="postForm.title" :placeholder="t('标题（可选）')" style="margin-bottom:8px" />
              <el-input v-model="postForm.content" type="textarea" :rows="4" maxlength="2000" show-word-limit :placeholder="t('写下你感兴趣的方向、正在做的项目、想寻找的队友...')" />
              <el-select v-model="postForm.tags" multiple filterable :placeholder="t('选择帖子标签')" style="width:100%;margin-top:8px">
                <el-option v-for="tag in [...tagCatalog.knowledge,...tagCatalog.skill,...tagCatalog.collab]" :key="tag.id" :label="translateProfileText(tag.name)" :value="tag.name" />
              </el-select>
              <div style="display:flex;align-items:center;gap:12px;margin-top:10px">
                <input type="file" multiple accept="image/*,video/mp4" @change="onPostMedia" />
                <el-switch v-model="postForm.is_anonymous" :active-text="t('匿名发布')" />
                <el-button type="primary" :loading="loading" @click="createPost">{{ t('发布') }}</el-button>
              </div>
            </div>
            <div v-for="p in communityFeed" :key="p.id" class="card community-card">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <h3>{{ p.title ? formatDynamicText(p.title) : t('学习动态') }}</h3>
                <span class="hint">{{ p.author }}</span>
              </div>
              <p>{{ p.content }}</p>
              <div v-if="p.media?.length" style="display:flex;gap:8px;flex-wrap:wrap">
                <template v-for="m in p.media" :key="m.url">
                  <img v-if="m.type==='image'" :src="m.url" style="max-width:180px;border-radius:10px" @error="demoImageFallback" />
                  <video v-else controls :src="m.url" style="max-width:260px;border-radius:10px"></video>
                </template>
              </div>
              <div style="margin-top:8px"><el-tag v-for="tag in p.tags" :key="tag.name" style="margin:3px">{{ translateProfileText(tag.name) }}</el-tag></div>
              <div style="margin-top:12px;display:flex;gap:8px">
                <el-button size="small" @click="interactPost(p, 'like')">{{ t('点赞') }} {{ p.stats?.likes || 0 }}</el-button>
                <el-button size="small" @click="interactPost(p, 'favorite')">{{ t('收藏') }} {{ p.stats?.favorites || 0 }}</el-button>
                <el-button size="small" @click="toggleComments(p)">{{ expandedComments[p.id] ? t('收起评论') : t('查看评论') }} {{ p.stats?.comments || 0 }}</el-button>
                <el-button v-if="p.user_id && p.user_id!==user?.id" size="small" type="primary" plain @click="startChat(p.user_id)">{{ t('发消息') }}</el-button>
              </div>
              <div v-if="expandedComments[p.id]" class="comment-panel" style="margin-top:12px;border-top:1px solid #e5e7eb;padding-top:12px">
                <div v-if="(p.comments||[]).length" style="display:grid;gap:8px;margin-bottom:10px">
                  <div v-for="c in p.comments" :key="c.id" style="background:#f8fafc;border-radius:10px;padding:10px">
                    <strong>{{ c.author || t('同学') }}</strong>
                    <p style="margin:4px 0 0">{{ c.content }}</p>
                  </div>
                </div>
                <el-empty v-else :description="t('暂无评论，欢迎补充观点。')" />
                <div style="display:flex;gap:8px;margin-top:10px">
                  <el-input v-model="commentInputs[p.id]" :placeholder="t('写下你的评论，补充经验或组队想法')" @keyup.enter="submitComment(p)" />
                  <el-button type="primary" :loading="loading" @click="submitComment(p)">{{ t('提交评论') }}</el-button>
                </div>
              </div>
            </div>
          </template>

          <template v-if="page==='messages'">
            <div class="card">
              <h3>{{ t('会话列表') }}</h3>
              <el-table :data="conversations" :empty-text="t('暂无会话，可在学习社区中给同学发消息')">
                <el-table-column :label="t('同学')"><template #default="{row}">{{ row.other_user?.name || (t('用户') + row.other_user_id) }}</template></el-table-column>
                <el-table-column :label="t('最后消息')"><template #default="{row}">{{ row.last_message?.content || '—' }}</template></el-table-column>
                <el-table-column :label="t('未读')" width="80"><template #default="{row}"><el-tag v-if="row.unread">{{ row.unread }}</el-tag></template></el-table-column>
                <el-table-column :label="t('操作')" width="120"><template #default="{row}"><el-button size="small" @click="openConversation(row)">{{ t('打开') }}</el-button></template></el-table-column>
              </el-table>
            </div>
            <div v-if="chatConversationId" class="card">
              <h3>{{ t('聊天') }}</h3>
              <div style="max-height:360px;overflow:auto;border:1px solid #e5e7eb;border-radius:12px;padding:12px">
                <div v-for="m in messages" :key="m.id" :style="{textAlign:m.sender_id===user?.id?'right':'left',margin:'8px 0'}">
                  <span style="display:inline-block;background:#f1f5f9;padding:8px 12px;border-radius:12px">{{ m.content }}</span>
                </div>
              </div>
              <div style="display:flex;gap:8px;margin-top:12px">
                <el-input v-model="chatInput" :placeholder="t('输入消息')" @keyup.enter="sendMessage" />
                <el-button type="primary" @click="sendMessage">{{ t('发送') }}</el-button>
              </div>
            </div>
          </template>

          <template v-if="page==='account'">
            <div class="account-hero">
              <div class="account-avatar-lg">
                <img v-if="userAvatar(user)" :src="userAvatar(user)" :alt="t('头像')" />
                <span v-else>{{ userInitial(user?.name) }}</span>
              </div>
              <div>
                <h2>{{ user?.name }}</h2>
                <p class="profile-headline">{{ user?.headline || t('还没有设置个人标题') }}</p>
                <p>{{ user?.bio || t('完善头像和个人介绍，让同学更容易认识你。') }}</p>
                <el-tag>{{ t('学员账号：') }} {{ user?.account }}</el-tag>
                <el-tag type="success" v-if="user?.availability">{{ formatDynamicText(user.availability) }}</el-tag>
              </div>
            </div>
            <div class="profile-showcase">
              <div class="showcase-item"><b>{{ t('研究兴趣') }}</b><span>{{ user?.research_interest || t('填写你的研究方向、项目兴趣或想探索的问题') }}</span></div>
              <div class="showcase-item"><b>{{ t('作品链接') }}</b><a v-if="user?.portfolio_url" :href="user.portfolio_url" target="_blank">Portfolio</a><span v-else>{{ t('未填写') }}</span></div>
              <div class="showcase-item"><b>{{ t('代码主页') }}</b><a v-if="user?.github_url" :href="user.github_url" target="_blank">GitHub / Lab</a><span v-else>{{ t('未填写') }}</span></div>
            </div>
            <div class="account-grid">
              <div class="card">
                <h3>{{ t('language') }}</h3>
                <p class="hint">{{ t('languageShared') }}</p>
                <el-select v-model="language" style="width:100%" @change="setLanguage">
                  <el-option v-for="item in LANGUAGE_OPTIONS" :key="item.code" :label="item.label" :value="item.code" />
                </el-select>
              </div>
              <div class="card">
                <h3>{{ t('profileCard') }}</h3>
                <p class="hint">{{ t('头像支持图片链接；留空时会自动使用姓名首字作为头像。') }}</p>
                <el-form label-position="top">
                  <el-form-item :label="t('姓名')"><el-input v-model="accountForm.name" maxlength="64" /></el-form-item>
                  <el-form-item :label="t('个人标题')"><el-input v-model="accountForm.headline" maxlength="120" :placeholder="t('如：数据分析 / 智慧教育方向研究生')" /></el-form-item>
                  <el-form-item :label="t('头像链接')"><el-input v-model="accountForm.avatar_url" placeholder="https://..." maxlength="512" /></el-form-item>
                  <el-form-item :label="t('个人介绍')"><el-input v-model="accountForm.bio" type="textarea" :rows="4" maxlength="240" show-word-limit :placeholder="t('写一句你的项目兴趣、擅长方向或希望承担的角色')" /></el-form-item>
                  <el-form-item :label="t('研究方向 / 项目兴趣')"><el-input v-model="accountForm.research_interest" maxlength="240" :placeholder="t('如：学习分析、智能教育、大模型应用')" /></el-form-item>
                  <el-form-item :label="t('可协作时间')"><el-input v-model="accountForm.availability" maxlength="120" :placeholder="t('如：每周 6-8 小时，周三/周末可开会')" /></el-form-item>
                  <el-form-item :label="t('作品集链接')"><el-input v-model="accountForm.portfolio_url" placeholder="https://..." maxlength="512" /></el-form-item>
                  <el-form-item :label="t('GitHub / 实验室主页')"><el-input v-model="accountForm.github_url" placeholder="https://..." maxlength="512" /></el-form-item>
                  <el-form-item :label="t('主页主题')"><el-select v-model="accountForm.display_theme" style="width:100%"><el-option :label="t('Aurora 极光')" value="aurora" /><el-option :label="t('Ocean 海蓝')" value="ocean" /><el-option :label="t('Sunrise 晨光')" value="sunrise" /></el-select></el-form-item>
                  <el-button type="primary" :loading="loading" @click="saveAccount">{{ t('saveProfile') }}</el-button>
                </el-form>
              </div>
              <div class="card">
                <h3>{{ t('修改密码') }}</h3>
                <p class="hint">{{ t('新密码至少 6 位，保存后下次登录生效。') }}</p>
                <el-form label-position="top">
                  <el-form-item :label="t('当前密码')"><el-input v-model="passwordForm.old_password" type="password" show-password /></el-form-item>
                  <el-form-item :label="t('新密码')"><el-input v-model="passwordForm.new_password" type="password" show-password /></el-form-item>
                  <el-form-item :label="t('确认新密码')"><el-input v-model="passwordForm.confirm_password" type="password" show-password @keyup.enter="changePassword" /></el-form-item>
                  <el-button type="primary" plain :loading="loading" @click="changePassword">{{ t('修改密码') }}</el-button>
                </el-form>
              </div>
            </div>
          </template>
        </main>
      </div>

      <el-dialog v-model="calculating" width="420px" :close-on-click-modal="false" :show-close="false" class="calc-dialog">
        <div class="calc-box">
          <div class="calc-orbit">
            <span></span><span></span><span></span>
          </div>
          <h3>{{ t('正在计算适合你的角色方向') }}</h3>
          <p>{{ calculateText }}</p>
          <el-progress :percentage="calculateProgress" :stroke-width="12" striped striped-flow />
          <div class="calc-tips">{{ t('系统正在综合主动标签、自由描述、被动标签与任务表现，稍等片刻。') }}</div>
        </div>
      </el-dialog>
    </div>
  `,
}

function bootApp() {
  const root = document.getElementById('app')
  if (!root || typeof Vue === 'undefined') return
  try {
    const app = createApp(App)
    if (typeof ElementPlus !== 'undefined') app.use(ElementPlus)
    app.mount('#app')
  } catch (e) {
    root.innerHTML = '<p>加载失败: ' + (e.message || e) + '</p>'
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootApp)
else bootApp()
