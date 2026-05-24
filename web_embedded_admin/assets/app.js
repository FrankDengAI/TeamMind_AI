/**
 * 组队超脑（TeamMind Admin）— 管理后台（5000）
 */
const TeamMindAdminRuntime = (() => {
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
          <h1 style="margin:0 0 12px;font-size:24px">教师端资源加载失败</h1>
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
  TeamMindAdminRuntime.showBootError('Vue、Element Plus 或 axios 未能加载，应用无法启动。')
  throw new Error('TeamMind admin runtime dependency missing')
}

const API_BASE = window.TEAMMIND_API_BASE || '/api'
const STUDENT_PORTAL_URL = window.TEAMMIND_STUDENT_URL || '/student/'
const APP_LANG_KEY = 'teammind_app_lang'
const DEFAULT_APP_LANG = TeamMindAdminRuntime.storage.getItem(APP_LANG_KEY) || TeamMindAdminRuntime.storage.getItem('teammind_portal_lang') || 'zh-CN'
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
  { key: 'classes', icon: '🏫', label: '班级管理', desc: '创建班级、维护成员、审批学生加入或退出申请' },
  { key: 'workbench', icon: '🎯', label: '组队活动中心', desc: '创建一次具体活动，再选择自动分组或学生自由组队' },
  { key: 'users', icon: '👤', label: '学员与画像', desc: '查看学员标签、角色建议和分组参考信息' },
  { key: 'community', icon: '📚', label: '社区管理', desc: '查看学习社区帖子、富媒体内容和互动数据，必要时隐藏不合适内容' },
  { key: 'export', icon: '📥', label: '数据导出', desc: '导出分组依据、任务分配与进度报告，支撑教学研究与答辩' },
  { key: 'settings', icon: '⚙️', label: '系统设置', desc: '默认每组人数、调优周期与项目任务模板' },
]
const PAGE_KEYS = [...NAV_ITEMS.map((n) => n.key), 'account']

const ADMIN_I18N = {
  'zh-CN': {
    brandTitle: '组队超脑',
    brandShort: '组队超脑',
    brandEn: 'TeamMind Admin',
    pageTitle: '组队超脑 · 管理后台 | TeamMind Admin',
    workspaceName: '管理控制台',
    loginTitle: '管理员登录',
    loginSub: '登录后按步骤完成分组、分工和进度跟踪',
    loginTagline: '班级项目分组、任务分配与进度管理',
    studentAccess: '端口 5000 · 学员请访问 /student/ 学生端',
    switchToStudent: '跳转学生端',
    switchToStudentHint: '以学生视角查看画像、组队、任务和社区',
    account: '账号',
    password: '密码',
    loginButton: '登 录',
    demoHint: '默认 admin / admin123 · 演示脚本见 README',
    refresh: '刷新',
    profileHome: '个人主页',
    logout: '退出登录',
    accountNavLabel: '个人主页',
    accountNavDesc: '设置头像、管理员信息和登录密码',
    language: '界面语言',
    languageShared: '教师端和学生端共用此语言偏好；切换后会保存在当前浏览器。',
    settingsTitle: '系统设置',
    defaultGroupSize: '默认每组人数（建议4或5）',
    adjustDays: '调优周期(天)',
    save: '保存',
    nav: {
      classes: ['班级管理', '创建班级、维护成员、审批学生加入或退出申请'],
      workbench: ['组队活动中心', '创建一次具体活动，再选择自动分组或学生自由组队'],
      users: ['学员与画像', '查看学员标签、角色建议和分组参考信息'],
      community: ['社区管理', '查看学习社区帖子、富媒体内容和互动数据，必要时隐藏不合适内容'],
      export: ['数据导出', '导出分组依据、任务分配与进度报告，支撑教学研究与答辩'],
      settings: ['系统设置', '默认每组人数、调优周期与项目任务模板'],
    },
  },
  en: {
    brandTitle: 'TeamMind Admin',
    brandShort: 'TeamMind',
    brandEn: 'TeamMind Admin',
    pageTitle: 'TeamMind Admin · Console',
    workspaceName: 'Admin Console',
    loginTitle: 'Admin Login',
    loginSub: 'Log in to manage grouping, roles and progress step by step.',
    loginTagline: 'Class project grouping, task assignment and progress management',
    studentAccess: 'Port 5000 · Students should use /student/',
    switchToStudent: 'Open Student App',
    switchToStudentHint: 'View profiles, teams, tasks and community as a student.',
    account: 'Account',
    password: 'Password',
    loginButton: 'Log in',
    demoHint: 'Default admin / admin123 · See README for demo scripts',
    refresh: 'Refresh',
    profileHome: 'Profile',
    logout: 'Log out',
    accountNavLabel: 'Profile',
    accountNavDesc: 'Set avatar, admin info and password',
    language: 'Language',
    languageShared: 'This preference is shared by teacher and student workspaces in the current browser.',
    settingsTitle: 'System Settings',
    defaultGroupSize: 'Default group size (4 or 5 recommended)',
    adjustDays: 'Adjustment cycle (days)',
    save: 'Save',
    nav: {
      classes: ['Class Management', 'Create classes, manage members and review join/leave requests.'],
      workbench: ['Team Activity Center', 'Create an activity, then choose auto grouping or student free teaming.'],
      users: ['Students & Profiles', 'Review student tags, suggested roles and grouping signals.'],
      community: ['Community Management', 'Review posts, rich media and interaction data.'],
      export: ['Data Export', 'Export grouping reasons, task assignment and progress reports.'],
      settings: ['System Settings', 'Default group size, adjustment cycle and task templates.'],
    },
  },
}

Object.assign(ADMIN_I18N, {
  'zh-Hant': {
    ...ADMIN_I18N['zh-CN'],
    workspaceName: '管理控制台',
    language: '介面語言',
    languageShared: '教師端和學生端共用此語言偏好；切換後會保存在目前瀏覽器。',
    settingsTitle: '系統設定',
    defaultGroupSize: '預設每組人數（建議4或5）',
    adjustDays: '調整週期(天)',
    nav: {
      classes: ['班級管理', '建立班級、維護成員、審批學生加入或退出申請'],
      workbench: ['組隊活動中心', '建立一次具體活動，再選擇自動分組或學生自由組隊'],
      users: ['學員與畫像', '查看學員標籤、角色建議和分組參考資訊'],
      community: ['社群管理', '查看學習社群貼文、富媒體內容和互動資料'],
      export: ['資料匯出', '匯出分組依據、任務分配與進度報告'],
      settings: ['系統設定', '預設每組人數、調整週期與專案任務模板'],
    },
  },
  ja: {
    ...ADMIN_I18N.en,
    workspaceName: '管理コンソール',
    language: '言語',
    languageShared: 'この設定は教師用・学生用ワークスペースで共有されます。',
    settingsTitle: 'システム設定',
    defaultGroupSize: '既定のグループ人数（4 または 5 推奨）',
    adjustDays: '調整サイクル（日）',
    save: '保存',
    refresh: '更新',
    profileHome: 'プロフィール',
    logout: 'ログアウト',
    nav: {
      classes: ['クラス管理', 'クラス作成、メンバー管理、参加/退出申請の承認。'],
      workbench: ['チーム活動センター', '活動を作成し、自動編成または自由編成を選択します。'],
      users: ['学生とプロフィール', 'タグ、役割提案、編成参考情報を確認します。'],
      community: ['コミュニティ管理', '投稿、メディア、交流データを確認します。'],
      export: ['データ出力', '編成根拠、タスク、進捗レポートを出力します。'],
      settings: ['システム設定', 'グループ人数、調整周期、タスクテンプレート。'],
    },
  },
  ko: {
    ...ADMIN_I18N.en,
    workspaceName: '관리 콘솔',
    language: '언어',
    languageShared: '이 설정은 교사용 및 학생용 워크스페이스에서 공유됩니다.',
    settingsTitle: '시스템 설정',
    defaultGroupSize: '기본 그룹 인원(4 또는 5 권장)',
    adjustDays: '조정 주기(일)',
    save: '저장',
    refresh: '새로고침',
    profileHome: '프로필',
    logout: '로그아웃',
    nav: {
      workbench: ['팀 활동 센터', '활동을 만들고 자동 편성 또는 자유 팀 구성을 선택합니다.'],
      users: ['학생 및 프로필', '학생 태그, 역할 제안, 편성 정보를 확인합니다.'],
      community: ['커뮤니티 관리', '게시글, 미디어, 상호작용 데이터를 검토합니다.'],
      export: ['데이터 내보내기', '편성 근거, 작업 배정, 진행 보고서를 내보냅니다.'],
      settings: ['시스템 설정', '기본 인원, 조정 주기, 작업 템플릿.'],
    },
  },
  fr: {
    ...ADMIN_I18N.en,
    workspaceName: 'Console enseignant',
    language: 'Langue',
    languageShared: 'Ce choix est partagé entre les espaces enseignant et étudiant.',
    settingsTitle: 'Paramètres système',
    defaultGroupSize: 'Taille de groupe par défaut (4 ou 5 conseillé)',
    adjustDays: 'Cycle d’ajustement (jours)',
    save: 'Enregistrer',
    refresh: 'Actualiser',
    profileHome: 'Profil',
    logout: 'Se déconnecter',
    nav: {
      workbench: ['Centre des activités', 'Créez une activité puis choisissez le regroupement automatique ou libre.'],
      users: ['Étudiants et profils', 'Consultez les tags, rôles suggérés et signaux de regroupement.'],
      community: ['Communauté', 'Modérez les publications, médias et interactions.'],
      export: ['Export des données', 'Exportez les regroupements, tâches et rapports de progression.'],
      settings: ['Paramètres système', 'Taille des groupes, cycle et modèles de tâches.'],
    },
  },
  de: {
    ...ADMIN_I18N.en,
    workspaceName: 'Admin-Konsole',
    language: 'Sprache',
    languageShared: 'Diese Einstellung gilt für Lehr- und Lernbereich in diesem Browser.',
    settingsTitle: 'Systemeinstellungen',
    defaultGroupSize: 'Standardgruppengröße (4 oder 5 empfohlen)',
    adjustDays: 'Anpassungszyklus (Tage)',
    save: 'Speichern',
    refresh: 'Aktualisieren',
    profileHome: 'Profil',
    logout: 'Abmelden',
    nav: {
      workbench: ['Team-Aktivitätszentrum', 'Aktivität erstellen und automatische oder freie Teambildung wählen.'],
      users: ['Studierende & Profile', 'Tags, Rollenvorschläge und Gruppensignale prüfen.'],
      community: ['Community-Verwaltung', 'Beiträge, Medien und Interaktionen prüfen.'],
      export: ['Datenexport', 'Gruppen, Aufgaben und Fortschrittsberichte exportieren.'],
      settings: ['Systemeinstellungen', 'Gruppengröße, Anpassungszyklus und Aufgabenvorlagen.'],
    },
  },
  es: {
    ...ADMIN_I18N.en,
    workspaceName: 'Consola docente',
    language: 'Idioma',
    languageShared: 'Esta preferencia se comparte entre docente y estudiante en este navegador.',
    settingsTitle: 'Configuración del sistema',
    defaultGroupSize: 'Tamaño de grupo predeterminado (4 o 5 recomendado)',
    adjustDays: 'Ciclo de ajuste (días)',
    save: 'Guardar',
    refresh: 'Actualizar',
    profileHome: 'Perfil',
    logout: 'Cerrar sesión',
    nav: {
      workbench: ['Centro de actividades', 'Cree una actividad y elija agrupación automática o libre.'],
      users: ['Estudiantes y perfiles', 'Revise etiquetas, roles sugeridos y señales de agrupación.'],
      community: ['Gestión de comunidad', 'Revise publicaciones, medios e interacciones.'],
      export: ['Exportar datos', 'Exporte agrupaciones, tareas e informes de progreso.'],
      settings: ['Configuración', 'Tamaño de grupo, ciclo de ajuste y plantillas.'],
    },
  },
})

const ADMIN_TEXT_I18N = {
  en: {
    管理员: 'Admin',
    管理员账号: 'Admin account',
    管理控制台: 'Admin Console',
    组队活动中心: 'Team Activity Center',
    创建组队活动: 'Create Team Activity',
    活动列表: 'Activity List',
    活动标题: 'Activity Title',
    '课程/场景': 'Course / Scenario',
    组队方式: 'Grouping Mode',
    任务驱动自动组队: 'Task-driven Auto Grouping',
    学生自由组队: 'Student Free Teaming',
    每组人数: 'Group Size',
    '任务需求/组队说明': 'Task Requirement / Grouping Notes',
    建议角色: 'Suggested Roles',
    关键标签: 'Key Tags',
    创建活动: 'Create Activity',
    '暂无活动，先创建一个组队活动。': 'No activities yet. Create one first.',
    参与人数: 'Participants',
    已生成小组: 'Generated Groups',
    自由队伍: 'Free Teams',
    确认率: 'Confirmation Rate',
    参与学生: 'Participants',
    候选分组结果: 'Candidate Groups',
    预沟通确认与微调申请: 'Pre-talk Confirmation & Adjustment Requests',
    学员与画像: 'Students & Profiles',
    学员画像详情: 'Student Profile Details',
    学习社区帖子: 'Community Posts',
    数据导出: 'Data Export',
    导出画像: 'Export Profiles',
    导出分组: 'Export Groups',
    导出任务: 'Export Tasks',
    '支持导出画像、分组、任务数据；报告导出需先选择已生成报告的小组。': 'Export profiles, groups and tasks. Report export requires a group with a generated report.',
    选择报告小组: 'Select Report Group',
    '导出报告 PDF': 'Export Report PDF',
    请先选择有报告的小组: 'Select a group with a report first',
    个人资料: 'Profile',
    账号安全: 'Account Security',
    修改密码: 'Change Password',
    当前密码: 'Current Password',
    新密码: 'New Password',
    确认新密码: 'Confirm New Password',
    保存资料: 'Save Profile',
    姓名: 'Name',
    个人标题: 'Headline',
    头像链接: 'Avatar URL',
    个人介绍: 'Bio',
    '教学/研究方向': 'Teaching / Research Area',
    可联系时间: 'Availability',
    课程主页: 'Course Page',
    公开主页: 'Public Page',
    主页主题: 'Theme',
    计算规则说明: 'Scoring Rules',
    评分来源拆解: 'Score Breakdown',
    标签证据: 'Tag Evidence',
    主动标签: 'Active Tags',
    被动标签: 'Passive Tags',
    结构化解析: 'Structured Parsing',
    学历: 'Degree',
    '专业/方向': 'Major / Field',
    偏好角色: 'Preferred Role',
    画像时间: 'Profile Time',
    操作: 'Actions',
    刷新: 'Refresh',
    保存: 'Save',
    隐藏: 'Hide',
    恢复: 'Restore',
  },
}

Object.assign(ADMIN_TEXT_I18N.en, {
  班级管理: 'Class Management',
  '先维护班级和成员，再在组队活动中选择班级范围。学生加入或退出班级都需要老师审批，避免分组范围混乱。': 'Maintain classes and members first, then choose a class scope when creating team activities. Student join/leave requests require teacher approval to keep grouping clear.',
  班级数: 'Classes',
  班级学生: 'Class Students',
  待审批: 'Pending',
  建议组数: 'Suggested Groups',
  班级列表: 'Class List',
  '暂无班级，请先创建。': 'No classes yet. Create one first.',
  未设置课程: 'No course set',
  人: 'students',
  组: 'groups',
  人参与: 'participants',
  未识别班级: 'Unknown class',
  未命名活动: 'Untitled Activity',
  确认: 'Confirm',
  确定: 'OK',
  取消: 'Cancel',
  赞: 'Likes ',
  藏: 'Fav ',
  评: 'Cmt ',
  审批: 'requests',
  新建班级: 'New Class',
  '一个班建议 10-20 人，系统会按人数给出均匀分组方案。': 'A class is recommended to have 10-20 students. The system suggests balanced group sizes by headcount.',
  创建为新班级: 'Create as New Class',
  成员: 'Members',
  '选择要拉入的学生': 'Select students to add',
  拉入同学: 'Add Students',
  当前班级暂无学生: 'No students in this class',
  画像: 'Profile',
  已录入: 'Ready',
  未录入: 'Missing',
  角色方向: 'Role Direction',
  剔除: 'Remove',
  班级活动: 'Class Activities',
  '这里展示当前班级关联的组队活动。教师在活动中心创建活动时选择班级后，会自动出现在这里；学生从学生端发起的班级活动也会同步显示。': 'Activities linked to the current class appear here. Teacher-created class activities and student-created class activities are both shown.',
  方式: 'Mode',
  状态: 'Status',
  '参与/小组': 'Participants / Groups',
  查看活动: 'View Activity',
  申请审批: 'Requests',
  暂无申请: 'No requests',
  学生: 'Student',
  类型: 'Type',
  加入: 'Join',
  退出: 'Leave',
  申请说明: 'Request Note',
  通过: 'Approve',
  拒绝: 'Reject',
  分组建议: 'Grouping Advice',
  请选择班级查看建议: 'Select a class to view advice',
  '建议基于当前 active 成员人数生成；真正自动分组时还会结合画像均衡。': 'Advice is based on active members; actual grouping also balances profiles.',
  重新计算: 'Recalculate',
  智能分组分析: 'AI Grouping Analysis',
  'DeepSeek 大模型分析': 'DeepSeek model analysis',
  '规则兜底分析（未配置大模型或调用失败）': 'Rule-based fallback analysis',
  分析依据: 'Rationale',
  教师建议: 'Teacher Actions',
  风险提醒: 'Risks',
  班级设置: 'Class Settings',
  班级名称: 'Class Name',
  班级代码: 'Class Code',
  专业: 'Major',
  年级: 'Grade',
  课程名称: 'Course Name',
  人数上限: 'Capacity',
  说明: 'Description',
  保存当前班级: 'Save Class',
  '解散/归档班级': 'Dissolve / Archive Class',
  TeamActivityCenter: 'Team Activity Center',
  '先创建一次组队活动，再选择“任务驱动自动组队”或“学生自由组队”。学生只有参与该活动后，才会进入对应队伍流程。': 'Create a team activity first, then choose task-driven auto grouping or student free teaming. Students enter the team workflow after joining the activity.',
  活动数: 'Activities',
  队伍: 'Teams',
  '队伍/小组': 'Teams / Groups',
  任务反馈: 'Task Feedback',
  '可选，如：人机交互课程': 'Optional, e.g. HCI course',
  班级范围: 'Class Scope',
  '请选择班级：活动必须归属于具体班级': 'Select a class: every activity must belong to a class',
  '老师填写任务需求，学生补充标签后系统自动匹配。': 'Teacher writes requirements; students add tags, then the system matches automatically.',
  '学生创建或加入队伍，老师最后锁定结果。': 'Students create or join teams; teacher locks final results.',
  '说明这次任务要做什么、希望队伍具备哪些能力': 'Describe the task and expected team capabilities',
  '输入或选择角色': 'Type or select roles',
  '如 Python、数据分析、文档汇报': 'e.g. Python, data analysis, presentation',
  未识别班级: 'Unknown Class',
  暂无任务说明: 'No task notes',
  任务驱动: 'Task-driven',
  自由组队: 'Free teaming',
  发布给学生填写: 'Publish to Students',
  自动生成候选分组: 'Generate Candidate Groups',
  发布候选分组: 'Publish Candidate Groups',
  锁定自由组队: 'Lock Free Teams',
  当前活动暂无参与学生: 'No participants in this activity',
  小组: 'Group',
  成员数: 'Members',
  角色: 'Role',
  技能标签: 'Skill Tags',
  暂无候选分组: 'No candidate groups',
  确认记录: 'Confirmation Records',
  处理: 'Resolve',
  社区管理: 'Community Management',
  数据导出: 'Data Export',
  系统设置: 'System Settings',
  默认每组人数: 'Default Group Size',
  调优周期: 'Adjustment Cycle',
  生成候选分组: 'Generate Candidate Groups',
  锁定正式团队: 'Lock Final Teams',
  锁定自由组队结果: 'Lock Free Teaming Result',
  活动分组智能分析: 'AI Activity Grouping Analysis',
  'DeepSeek 大模型返回': 'DeepSeek Model Response',
  专业判断: 'Professional Judgment',
  下一步动作: 'Next Actions',
  风险预警: 'Risk Alerts',
  等待学生参与: 'Waiting for students',
  标签数: 'Tag Count',
  尚未生成小组: 'No groups generated yet',
  均衡度: 'Balance',
  确认: 'Confirmation',
  '学生确认后再锁定正式团队；有微调申请时，老师可记录处理意见并同步调整角色。': 'Lock final teams after student confirmation. When adjustment requests appear, teachers can record handling notes and update roles.',
  期望推荐角色: 'Expected / Suggested Role',
  '期望/推荐角色': 'Expected / Suggested Role',
  任务偏好: 'Task Preferences',
  原因备注: 'Reason / Note',
  '原因/备注': 'Reason / Note',
  处理说明: 'Handling Note',
  驳回: 'Reject',
  学生自由队伍: 'Student Free Teams',
  暂无队伍说明: 'No team description',
  待处理申请: 'Pending Requests',
  学员画像全景: 'Student Profile Overview',
  '教师端展示完整评分、来源拆解、标签证据与分组参考；学生端不展示分数。': 'Teacher view shows full scores, source breakdown, tag evidence and grouping references; students do not see scores.',
  查看计算规则: 'View Scoring Rules',
  学员总数: 'Total Students',
  画像已录入: 'Profiles Ready',
  画像完成率: 'Profile Completion',
  活动筛选: 'Activity Filter',
  全部组队活动: 'All Team Activities',
  搜索学员: 'Search Students',
  输入姓名或账号: 'Enter name or account',
  当前显示: 'Showing',
  暂无符合条件的学员: 'No matching students',
  三维综合分: '3D Composite Score',
  专业角色: 'Major / Role',
  '专业/角色': 'Major / Role',
  未识别专业: 'Unknown Major',
  未识别角色: 'Unknown Role',
  画像详情: 'Profile Details',
  活动详情: 'Activity Detail',
  打开详情: 'Open Detail',
  关闭: 'Close',
  未设置: 'Not set',
  头像: 'Avatar',
  账号: 'Account',
  当前班级暂无活动: 'No activities in this class',
  第: 'Week ',
  '如：人工智能 2401 班': 'e.g. AI 2401 Class',
  '如：AI2401': 'e.g. AI2401',
  '如：第 4 周产品原型项目组队': 'e.g. Week 4 product prototype teaming',
  等待学生确认: 'Waiting for student confirmation',
  '待处理申请：': 'Pending requests:',
  标签: 'Tags',
  作者: 'Author',
  标题: 'Title',
  内容: 'Content',
  互动: 'Engagement',
  '管理员账号：': 'Admin account:',
  未填写: 'Not set',
  '头像支持图片链接；留空时显示姓名首字。': 'Avatar accepts an image URL; if empty, shows the first letter of your name.',
  '如：AI 产品课程负责人 / 助教': 'e.g. AI product course lead / TA',
  '如任课老师、助教、负责班级等': 'e.g. instructor, TA, class lead',
  '如：智慧教育、项目制学习、AI 产品设计': 'e.g. smart education, project-based learning, AI product design',
  '如：周二/周四答疑，24 小时内回复': 'e.g. office hours Tue/Thu, reply within 24h',
  'Ocean 海蓝': 'Ocean',
  'Aurora 极光': 'Aurora',
  'Sunrise 晨光': 'Sunrise',
  '修改密码不会强制退出当前会话，下次登录请使用新密码。': 'Changing password does not log you out; use the new password next login.',
  维度: 'Dimension',
  主动: 'Active',
  被动: 'Passive',
  任务: 'Task',
  规则: 'Rules',
  'LLM 分析原始摘要': 'LLM analysis raw summary',
  暂无画像详情: 'No profile details',
  '1. 信息整理': '1. Information',
  '主动标签、自由描述、社区互动、聊天和任务表现会作为分组参考。': 'Active tags, free text, community, chat and task performance inform grouping.',
  '2. 三维评分': '2. Three-dimensional scoring',
  '知识、技能、协作分别按不同权重融合，最终归一化 0-10 分。': 'Knowledge, skill and collaboration are weighted and normalized to 0-10.',
  '3. 分组/任务': '3. Grouping / tasks',
  '系统根据角色、标签、技能和工作量生成分组与任务建议。': 'The system suggests groups and tasks by role, tags, skills and workload.',
  画像评分公式: 'Profile scoring formula',
  知识: 'Knowledge',
  '= 30%主动标签 + 30%LLM + 15%被动标签 + 15%任务表现 + 10%规则解析': '= 30% active tags + 30% LLM + 15% passive tags + 15% task performance + 10% rule parsing',
  技能: 'Skills',
  '= 35%主动标签 + 30%LLM + 15%被动标签 + 20%任务表现': '= 35% active tags + 30% LLM + 15% passive tags + 20% task performance',
  协作: 'Collaboration',
  '= 25%主动标签 + 20%LLM + 30%被动标签 + 25%任务表现': '= 25% active tags + 20% LLM + 30% passive tags + 25% task performance',
  分组逻辑: 'Grouping logic',
  '系统先挑选每组核心成员，再逐步补充其他成员，参考技能差异、标签多样性、角色搭配和专业方向。若组间差距过大，会进行微调。': 'Core members are picked first, then others added for skill/tag/role/major balance; large gaps trigger adjustment.',
  任务分配逻辑: 'Task assignment logic',
  '候选人匹配分 = 角色匹配 + 标签匹配 + 技能适配 - 当前工时负载。没有明显合适人选时，优先分给累计工时较少的成员。': 'Candidate score = role match + tag match + skill fit - current workload; ties go to lower total hours.',
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
})

ADMIN_TEXT_I18N.ja = {
  ...(ADMIN_TEXT_I18N.ja || {}),
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
  ADMIN_TEXT_I18N[lang] = { ...ADMIN_TEXT_I18N.en, ...(ADMIN_TEXT_I18N[lang] || {}) }
})

function lookupTextTranslation(original, target) {
  if (!target) return original
  if (target[original]) return target[original]
  const compact = original.replace(/\s+/g, ' ').trim()
  if (target[compact]) return target[compact]
  const countSuffix = compact.match(/^(.+?)(\s*\(\d+\))$/)
  if (countSuffix && target[countSuffix[1]]) return `${target[countSuffix[1]]}${countSuffix[2]}`
  return original
}

let adminOpenCCConverter = null
function getAdminOpenCC() {
  if (adminOpenCCConverter === null && window.TeamMindI18n) {
    adminOpenCCConverter = window.TeamMindI18n.initOpenCC() || false
  }
  return adminOpenCCConverter || null
}

/** 项目流程阶段 */
const WORKFLOW_PHASES = [
  { key: 'team', label: '组队阶段', range: [1, 3], color: '#0ea5e9' },
  { key: 'task', label: '任务分配阶段', range: [4, 4], color: '#8b5cf6' },
  { key: 'monitor', label: '进度监督阶段', range: [5, 5], color: '#059669' },
]

const WORKBENCH_STEPS = [
  {
    n: 1,
    title: '学员信息',
    phase: 'team',
    hint: '查看哪些学员已经完成标签填写，必要时提醒未完成的学员。',
  },
  {
    n: 2,
    title: '智能分组',
    phase: 'team',
    hint: '根据学员标签、专业方向和角色偏好生成小组，教师可查看结果并继续调整。',
  },
  {
    n: 3,
    title: '组内分工',
    phase: 'team',
    hint: '为每个小组明确角色分工，可使用推荐结果，也可以手动修改。',
  },
  {
    n: 4,
    title: '任务拆解分配',
    phase: 'task',
    hint: '选择任务模板并分配负责人，兼顾能力匹配和工作量。',
  },
  {
    n: 5,
    title: '透明监督',
    phase: 'monitor',
    hint: '查看小组完成率、任务进度和风险提醒，方便及时跟进。',
  },
]

const ROLE_OPTIONS = [
  '技术开发', '设计执行', '协调对接', '数据支持', '质量审核',
  '创意策划', '文案撰写', '执行落地', '对外对接',
]

const ADMIN_DYNAMIC_I18N = {
  'zh-CN': {
    separator: '、',
    unset: '未设置',
    status: {
      active: '启用中', inactive: '已停用', archived: '已归档',
      draft: '草稿', collecting: '收集中', grouping: '分组中', confirmation: '确认中',
      confirming: '确认中', preview: '预览中', tasking: '任务中', adjusting: '调整中',
      published: '已发布', locked: '已锁定', completed: '已完成',
      joined: '已参与', pending: '待处理', approved: '已通过', rejected: '已拒绝',
      accepted: '已接受', adjust_requested: '申请微调', resolved: '已处理',
      hidden: '已隐藏',
    },
    mode: { task_auto: '任务驱动自动组队', free_team: '学生自由组队' },
    shortMode: { task_auto: '任务驱动', free_team: '自由组队' },
    requestType: { join: '加入', leave: '退出' },
    score: { knowledge: '知识方向', skill: '技能表现', collab: '协作情况' },
  },
  'zh-Hant': {
    separator: '、',
    unset: '未設定',
    status: {
      active: '啟用中', inactive: '已停用', archived: '已封存',
      draft: '草稿', collecting: '收集中', grouping: '分組中', confirmation: '確認中',
      confirming: '確認中', preview: '預覽中', tasking: '任務中', adjusting: '調整中',
      published: '已發布', locked: '已鎖定', completed: '已完成',
      joined: '已參與', pending: '待處理', approved: '已通過', rejected: '已拒絕',
      accepted: '已接受', adjust_requested: '申請微調', resolved: '已處理',
      hidden: '已隱藏',
    },
    mode: { task_auto: '任務驅動自動組隊', free_team: '學生自由組隊' },
    shortMode: { task_auto: '任務驅動', free_team: '自由組隊' },
    requestType: { join: '加入', leave: '退出' },
    score: { knowledge: '知識方向', skill: '技能表現', collab: '協作情況' },
  },
  en: {
    separator: ', ',
    unset: 'Not set',
    status: {
      active: 'Active', inactive: 'Inactive', archived: 'Archived',
      draft: 'Draft', collecting: 'Collecting', grouping: 'Grouping', confirmation: 'Confirming',
      confirming: 'Confirming', preview: 'Preview', tasking: 'Tasking', adjusting: 'Adjusting',
      published: 'Published', locked: 'Locked', completed: 'Completed',
      joined: 'Joined', pending: 'Pending', approved: 'Approved', rejected: 'Rejected',
      accepted: 'Accepted', adjust_requested: 'Adjustment requested', resolved: 'Resolved',
      hidden: 'Hidden',
    },
    mode: { task_auto: 'Task-driven Auto Grouping', free_team: 'Student Free Teaming' },
    shortMode: { task_auto: 'Task-driven', free_team: 'Free Teaming' },
    requestType: { join: 'Join', leave: 'Leave' },
    score: { knowledge: 'Knowledge', skill: 'Skills', collab: 'Collaboration' },
  },
  ja: {
    separator: '、',
    unset: '未設定',
    status: {
      active: '有効', inactive: '無効', archived: 'アーカイブ済み',
      draft: '下書き', collecting: '収集中', grouping: '編成中', confirmation: '確認中',
      confirming: '確認中', preview: 'プレビュー', tasking: 'タスク中', adjusting: '調整中',
      published: '公開済み', locked: 'ロック済み', completed: '完了',
      joined: '参加済み', pending: '保留中', approved: '承認済み', rejected: '却下済み',
      accepted: '承認済み', adjust_requested: '調整依頼', resolved: '対応済み',
      hidden: '非表示',
    },
    mode: { task_auto: 'タスク駆動の自動編成', free_team: '学生の自由編成' },
    shortMode: { task_auto: 'タスク駆動', free_team: '自由編成' },
    requestType: { join: '参加', leave: '退出' },
    score: { knowledge: '知識', skill: 'スキル', collab: '協働' },
  },
  ko: {
    separator: ', ',
    unset: '미설정',
    status: {
      active: '활성', inactive: '비활성', archived: '보관됨',
      draft: '초안', collecting: '수집 중', grouping: '편성 중', confirmation: '확인 중',
      confirming: '확인 중', preview: '미리보기', tasking: '작업 중', adjusting: '조정 중',
      published: '게시됨', locked: '잠김', completed: '완료',
      joined: '참여함', pending: '대기 중', approved: '승인됨', rejected: '거절됨',
      accepted: '수락됨', adjust_requested: '조정 요청', resolved: '처리됨',
      hidden: '숨김',
    },
    mode: { task_auto: '작업 기반 자동 팀 구성', free_team: '학생 자유 팀 구성' },
    shortMode: { task_auto: '작업 기반', free_team: '자유 팀 구성' },
    requestType: { join: '가입', leave: '나가기' },
    score: { knowledge: '지식', skill: '기술', collab: '협업' },
  },
  fr: {
    separator: ', ',
    unset: 'Non défini',
    status: {
      active: 'Actif', inactive: 'Inactif', archived: 'Archivé',
      draft: 'Brouillon', collecting: 'Collecte', grouping: 'Regroupement', confirmation: 'Confirmation',
      confirming: 'Confirmation', preview: 'Aperçu', tasking: 'Tâches', adjusting: 'Ajustement',
      published: 'Publié', locked: 'Verrouillé', completed: 'Terminé',
      joined: 'Inscrit', pending: 'En attente', approved: 'Approuvé', rejected: 'Refusé',
      accepted: 'Accepté', adjust_requested: 'Ajustement demandé', resolved: 'Résolu',
      hidden: 'Masqué',
    },
    mode: { task_auto: 'Regroupement automatique par tâche', free_team: 'Équipes libres étudiantes' },
    shortMode: { task_auto: 'Par tâche', free_team: 'Libre' },
    requestType: { join: 'Rejoindre', leave: 'Quitter' },
    score: { knowledge: 'Connaissances', skill: 'Compétences', collab: 'Collaboration' },
  },
  de: {
    separator: ', ',
    unset: 'Nicht gesetzt',
    status: {
      active: 'Aktiv', inactive: 'Inaktiv', archived: 'Archiviert',
      draft: 'Entwurf', collecting: 'Sammeln', grouping: 'Gruppierung', confirmation: 'Bestätigung',
      confirming: 'Bestätigung', preview: 'Vorschau', tasking: 'Aufgabenphase', adjusting: 'Anpassung',
      published: 'Veröffentlicht', locked: 'Gesperrt', completed: 'Abgeschlossen',
      joined: 'Teilgenommen', pending: 'Ausstehend', approved: 'Genehmigt', rejected: 'Abgelehnt',
      accepted: 'Akzeptiert', adjust_requested: 'Anpassung angefragt', resolved: 'Erledigt',
      hidden: 'Ausgeblendet',
    },
    mode: { task_auto: 'Aufgabenbasierte automatische Teambildung', free_team: 'Freie Teambildung' },
    shortMode: { task_auto: 'Aufgabenbasiert', free_team: 'Frei' },
    requestType: { join: 'Beitreten', leave: 'Verlassen' },
    score: { knowledge: 'Wissen', skill: 'Fähigkeiten', collab: 'Zusammenarbeit' },
  },
  es: {
    separator: ', ',
    unset: 'Sin definir',
    status: {
      active: 'Activo', inactive: 'Inactivo', archived: 'Archivado',
      draft: 'Borrador', collecting: 'Recopilando', grouping: 'Agrupando', confirmation: 'Confirmación',
      confirming: 'Confirmando', preview: 'Vista previa', tasking: 'Tareas', adjusting: 'Ajuste',
      published: 'Publicado', locked: 'Bloqueado', completed: 'Completado',
      joined: 'Participa', pending: 'Pendiente', approved: 'Aprobado', rejected: 'Rechazado',
      accepted: 'Aceptado', adjust_requested: 'Ajuste solicitado', resolved: 'Resuelto',
      hidden: 'Oculto',
    },
    mode: { task_auto: 'Agrupación automática por tareas', free_team: 'Equipos libres de estudiantes' },
    shortMode: { task_auto: 'Por tareas', free_team: 'Libre' },
    requestType: { join: 'Unirse', leave: 'Salir' },
    score: { knowledge: 'Conocimiento', skill: 'Habilidades', collab: 'Colaboración' },
  },
}

const http = axios.create({ baseURL: API_BASE, timeout: 30000 })

/** setup 外工具函数使用的翻译器（setup 内会赋值） */
let adminUiT = (key) => key
let adminGetLang = () => 'zh-CN'
let adminGetOpenCCFn = () => null

http.interceptors.request.use((cfg) => {
  const t = TeamMindAdminRuntime.storage.getItem('tf_admin_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})
function isAdminAuthFailure(err) {
  const status = err.response?.status
  if (status === 401) return true
  if (status !== 422) return false
  const url = String(err.config?.url || '')
  return url.includes('/admin/') || url.includes('/auth/me')
}

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (!isAdminAuthFailure(err)) {
      ElementPlus?.ElMessage?.error(err.response?.data?.error || err.message || '请求失败')
    }
    if (isAdminAuthFailure(err)) {
      TeamMindAdminRuntime.storage.removeItem('tf_admin_token')
      TeamMindAdminRuntime.storage.removeItem('tf_admin_user')
      window.dispatchEvent(new CustomEvent('teammind-admin-auth-expired'))
    }
    return Promise.reject(err)
  }
)

function safeJsonStorage(key, fallback = null) {
  try {
    return JSON.parse(TeamMindAdminRuntime.storage.getItem(key) || 'null') || fallback
  } catch {
    TeamMindAdminRuntime.storage.removeItem(key)
    return fallback
  }
}

function userInitial(name) {
  return (name || 'A').charAt(0).toUpperCase()
}

function userAvatar(u) {
  return u?.avatar_url || ''
}

function activityDisplayTitle(activity) {
  if (!activity) return ''
  const rawTitle = activity.title || ''
  if (window.TeamMindI18n?.translateDemoText) {
    if (rawTitle) {
      return window.TeamMindI18n.translateDemoText(rawTitle, adminUiT, adminGetLang(), adminGetOpenCCFn())
    }
    const className = activity.classroom?.name || adminUiT('未识别班级')
    const title = adminUiT('未命名活动')
    return window.TeamMindI18n.translateDemoText(`${className}｜${title}`, adminUiT, adminGetLang(), adminGetOpenCCFn())
  }
  const className = activity.classroom?.name || adminUiT('未识别班级')
  const title = activity.title || adminUiT('未命名活动')
  return title.startsWith(`${className}｜`) ? title : `${className}｜${title}`
}

/** Element Plus CDN 全量包使用 ElMessageBox，非 MessageBox */
function adminConfirm(message, title) {
  const box = ElementPlus.ElMessageBox || ElementPlus.MessageBox
  const confirmTitle = title || adminUiT('确认')
  if (box?.confirm) {
    return box.confirm(message, confirmTitle, {
      type: 'warning',
      confirmButtonText: adminUiT('确定'),
      cancelButtonText: adminUiT('取消'),
    })
  }
  return window.confirm(`${confirmTitle}\n\n${message}`) ? Promise.resolve() : Promise.reject('cancel')
}

function scoreVal(profile, key) {
  if (!profile) return 0
  return Number(profile[`${key}_final`] || profile[`${key}_score`] || 0)
}

function scorePct(profile, key) {
  return Math.min(100, Math.round(scoreVal(profile, key) * 10))
}

function scoreColor(key) {
  return { knowledge: '#0ea5e9', skill: '#8b5cf6', collab: '#ec4899' }[key] || '#0ea5e9'
}

function scoreLabel(key) {
  return { knowledge: '知识方向', skill: '技能表现', collab: '协作情况' }[key] || key
}

function breakdownRows(profile) {
  const b = profile?.score_breakdown || {}
  return ['knowledge', 'skill', 'collab'].map((key) => ({
    key,
    label: scoreLabel(key),
    active: b.active?.[key] ?? '—',
    llm: b.llm?.[key] ?? '—',
    passive: b.passive?.[key] ?? '—',
    task: b.task?.[key] ?? '—',
    rule: b.rule?.[key] ?? '—',
  }))
}

function safeList(v) {
  return Array.isArray(v) ? v : []
}

function formatJson(v) {
  try {
    if (!v) return '{}'
    if (typeof v === 'string') {
      try {
        return JSON.stringify(JSON.parse(v), null, 2)
      } catch {
        return v
      }
    }
    return JSON.stringify(v, null, 2)
  } catch {
    return '{}'
  }
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
    display_theme: u?.display_theme || 'ocean',
  }
}

function tagDimensionClass(tag, fallback = 'skill') {
  return `badge-${tag?.dimension || fallback}`
}

function tagIcon(tag, fallback = 'skill') {
  const dim = tag?.dimension || fallback
  return { knowledge: '知', skill: '技', collab: '协' }[dim] || '标'
}

const App = {
  setup() {
    const page = ref('workbench')
    const workbenchStep = ref(1)
    const user = ref(safeJsonStorage('tf_admin_user'))
    const token = ref(TeamMindAdminRuntime.storage.getItem('tf_admin_token') || '')
    const loading = ref(false)
    const userSearch = ref('')
    const rulesVisible = ref(false)
    const profileDrawerVisible = ref(false)
    const selectedUserRow = ref(null)
    const activityDetailDrawerVisible = ref(false)
    let refreshTimer = null

    const loginForm = ref({ account: 'admin', password: '' })
    const overview = ref({ user_count: 0, profile_count: 0, group_count: 0, groups: [] })
    const users = ref([])
    const commandDash = ref({ alerts: [] })
    const sysConfig = ref({ default_group_size: 4, default_adjust_days: 7, max_group_users: 50 })
    const templates = ref({})
    const activities = ref([])
    const selectedActivityId = ref(null)
    const activityDetail = ref(null)
    const classes = ref([])
    const selectedClassId = ref(null)
    const classDetail = ref(null)
    const classTab = ref('members')
    const classForm = ref({
      name: '',
      code: '',
      major: '',
      grade: '2024',
      course_name: '',
      max_students: 20,
      description: '',
    })
    const classMemberForm = ref({ user_ids: [] })
    const classAdviceGroupSize = ref(4)
    const activityForm = ref({
      title: '',
      course_name: '',
      mode: 'task_auto',
      group_size: 4,
      class_id: null,
      task_goal: '',
      description: '',
      required_tags: [],
      required_roles: [],
      deadline: '',
    })
    const communityPosts = ref([])
    const exportGroupId = ref(null)
    const accountForm = ref(buildAccountForm(user.value))
    const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })
    const language = ref(ADMIN_I18N[DEFAULT_APP_LANG] ? DEFAULT_APP_LANG : 'zh-CN')

    const opsGroupSize = ref(4)
    const opsTemplate = ref('product_dev')
    const opsGroupId = ref(null)
    const teamDash = ref(null)
    const roleEdits = ref([])

    const isLoggedIn = computed(() => !!token.value)
    const t = window.TeamMindI18n
      ? window.TeamMindI18n.createTranslator({
          structuredI18n: ADMIN_I18N,
          textI18n: ADMIN_TEXT_I18N,
          getLang: () => language.value,
          getOpenCC: getAdminOpenCC,
        })
      : (key) => ADMIN_I18N[language.value]?.[key] || ADMIN_I18N['zh-CN'][key] || key
    adminUiT = t
    adminGetLang = () => language.value
    adminGetOpenCCFn = getAdminOpenCC
    const displayDemoText = (text) => {
      void language.value
      if (text == null || text === '') return ''
      return window.TeamMindI18n?.translateDemoText(String(text), t, language.value, getAdminOpenCC()) || String(text)
    }
    const formatGroupingAdviceText = (advice) => {
      void language.value
      if (!advice) return ''
      return window.TeamMindI18n?.formatGroupingAdvice(advice, t) || ''
    }
    const formatInsightText = (text) => {
      void language.value
      if (text == null || text === '') return ''
      return window.TeamMindI18n?.translateBackendInsight(String(text), t, language.value, getAdminOpenCC()) || String(text)
    }
    const dynamicPack = computed(() => ADMIN_DYNAMIC_I18N[language.value] || ADMIN_DYNAMIC_I18N.en)
    const dynamicText = (group, key) => {
      if (key === null || key === undefined || key === '') return '—'
      const normalized = group === 'status' && window.TeamMindI18n?.normalizeActivityStatus
        ? window.TeamMindI18n.normalizeActivityStatus(key)
        : key
      return dynamicPack.value[group]?.[normalized] || dynamicPack.value[group]?.[key] || String(key)
    }
    const formatStatus = (status) => dynamicText('status', status)
    const formatMode = (mode, short = false) => dynamicText(short ? 'shortMode' : 'mode', mode)
    const exportGroups = computed(() => overview.value.groups || [])
    const formatRequestType = (type) => dynamicText('requestType', type)
    const scoreLabel = (key) => dynamicText('score', key)
    const tagName = (tag) => {
      if (tag === null || tag === undefined || tag === '') return ''
      if (typeof tag === 'string' || typeof tag === 'number') return String(tag)
      return tag.name || tag.label || tag.value || tag.title || tag.key || tag.category || ''
    }
    const formatList = (items, empty = dynamicPack.value.unset) => {
      const rows = safeList(items).map(tagName).filter(Boolean)
      return rows.length ? rows.join(dynamicPack.value.separator) : empty
    }
    const formatTagList = (items) => formatList(items, '—')
    const navItems = computed(() => NAV_ITEMS.map((item) => {
      const translated = ADMIN_I18N[language.value]?.nav?.[item.key]
        || ADMIN_I18N.en?.nav?.[item.key]
        || ADMIN_I18N['zh-CN'].nav[item.key]
      return { ...item, label: translated?.[0] || item.label, desc: translated?.[1] || item.desc }
    }))
    const currentNav = computed(() => {
      if (page.value === 'account') return { label: t('accountNavLabel'), desc: t('accountNavDesc') }
      return navItems.value.find((n) => n.key === page.value) || navItems.value[0]
    })
    const currentStepInfo = computed(() => WORKBENCH_STEPS.find((s) => s.n === workbenchStep.value) || WORKBENCH_STEPS[0])
    const currentPhase = computed(() => {
      const step = workbenchStep.value
      return WORKFLOW_PHASES.find((p) => step >= p.range[0] && step <= p.range[1]) || WORKFLOW_PHASES[0]
    })

    const studentUsers = computed(() => users.value.filter((r) => r.user?.role === 'user'))
    const profileReady = computed(() => studentUsers.value.filter((r) => r.has_profile))
    const profilePending = computed(() => studentUsers.value.filter((r) => !r.has_profile))
    const profileRate = computed(() => {
      const t = studentUsers.value.length
      if (!t) return 0
      return Math.round((profileReady.value.length / t) * 100)
    })

    const filteredUsers = computed(() => {
      const q = userSearch.value.trim().toLowerCase()
      const participantIds = new Set((activityDetail.value?.participants || []).map((p) => p.user_id))
      let rows = users.value
      if (selectedActivityId.value) {
        rows = rows.filter((row) => participantIds.has(row.user?.id))
      }
      if (!q) return rows
      return rows.filter((row) => {
        const u = row.user || {}
        return (u.name || '').toLowerCase().includes(q) || (u.account || '').toLowerCase().includes(q)
      })
    })

    const selectedActivity = computed(() => activityDetail.value || activities.value.find((a) => a.id === selectedActivityId.value) || null)
    const activityParticipants = computed(() => activityDetail.value?.participants || [])
    const activityGroups = computed(() => activityDetail.value?.groups || [])
    const activityRooms = computed(() => activityDetail.value?.rooms || [])
    const activityConfirmations = computed(() => activityDetail.value?.confirmations || [])
    const activityConfirmationSummary = computed(() => activityDetail.value?.confirmation_summary || { accepted: 0, adjust_requested: 0, pending: 0, total: 0, accept_rate: 0 })
    const selectedClass = computed(() => classDetail.value || classes.value.find((c) => c.id === selectedClassId.value) || null)
    const classMembers = computed(() => classDetail.value?.members || [])
    const classRequests = computed(() => classDetail.value?.requests || [])
    const classActivities = computed(() => classDetail.value?.activities || [])
    const classPendingRequests = computed(() => classRequests.value.filter((r) => r.status === 'pending'))
    const classAdvice = computed(() => selectedClass.value?.grouping_advice || {})
    const selectedClassAdviceSummary = computed(() => {
      void language.value
      const advice = selectedClass.value?.grouping_advice
      if (!advice?.sizes?.length) return t('一个班建议 10-20 人，系统会按人数给出均匀分组方案。')
      return formatGroupingAdviceText(advice)
    })
    const classAdvicePanelSummary = computed(() => {
      void language.value
      const advice = classAdvice.value
      if (!advice?.sizes?.length) return t('请选择班级查看建议')
      return formatGroupingAdviceText(advice)
    })
    const activityFormClassAdviceSummary = computed(() => {
      void language.value
      const cls = classes.value.find((c) => c.id === activityForm.value.class_id)
      if (!cls?.grouping_advice?.sizes?.length) return ''
      return formatGroupingAdviceText(cls.grouping_advice)
    })
    const classAvailableUsers = computed(() => {
      const memberIds = new Set(classMembers.value.map((m) => m.user?.id).filter(Boolean))
      return studentUsers.value.filter((row) => row.user?.id && !memberIds.has(row.user.id))
    })

    function openProfileDrawer(row) {
      selectedUserRow.value = row
      profileDrawerVisible.value = true
    }

    function setAuth(data) {
      if (data.user?.role !== 'admin') {
        ElementPlus.ElMessage.error('请使用管理员账号登录')
        return
      }
      token.value = data.token
      user.value = data.user
      accountForm.value = buildAccountForm(data.user)
      TeamMindAdminRuntime.storage.setItem('tf_admin_token', data.token)
      TeamMindAdminRuntime.storage.setItem('tf_admin_user', JSON.stringify(data.user))
      window.removeEventListener('hashchange', onHashChange)
      window.addEventListener('hashchange', onHashChange)
      if (window.location.hash !== '#workbench') window.location.hash = 'workbench'
      refreshAll()
      nextTick(updateDocumentTitle)
    }

    async function doLogin() {
      if (!loginForm.value.account.trim() || !loginForm.value.password) {
        return ElementPlus.ElMessage.warning('请填写管理员账号和密码')
      }
      loading.value = true
      try {
        const { data } = await http.post('/auth/login', loginForm.value)
        setAuth(data)
        ElementPlus.ElMessage.success('登录成功')
      } finally {
        loading.value = false
      }
    }

    function logout() {
      stopAutoRefresh()
      token.value = ''
      user.value = null
      TeamMindAdminRuntime.storage.removeItem('tf_admin_token')
      TeamMindAdminRuntime.storage.removeItem('tf_admin_user')
      if (window.location.hash) window.location.hash = ''
      updateDocumentTitle()
    }

    function handleAuthExpired() {
      if (!token.value && !user.value) return
      stopAutoRefresh()
      token.value = ''
      user.value = null
      page.value = 'workbench'
      ElementPlus.ElMessage.warning('登录状态已失效，请重新登录')
    }

    async function validateSession() {
      if (!token.value) return false
      try {
        const { data } = await http.get('/auth/me')
        if (data?.role !== 'admin') {
          ElementPlus.ElMessage.error('请使用管理员账号登录')
          logout()
          return false
        }
        user.value = data
        accountForm.value = buildAccountForm(data)
        TeamMindAdminRuntime.storage.setItem('tf_admin_user', JSON.stringify(data))
        return true
      } catch {
        logout()
        return false
      }
    }

    async function loadMe() {
      const { data } = await http.get('/auth/me')
      user.value = data
      accountForm.value = buildAccountForm(data)
      TeamMindAdminRuntime.storage.setItem('tf_admin_user', JSON.stringify(data))
    }

    async function saveAccount() {
      loading.value = true
      try {
        const { data } = await http.put('/auth/me', accountForm.value)
        user.value = data
        accountForm.value = buildAccountForm(data)
        TeamMindAdminRuntime.storage.setItem('tf_admin_user', JSON.stringify(data))
        ElementPlus.ElMessage.success('个人资料已保存')
      } finally { loading.value = false }
    }

    async function changePassword() {
      if (!passwordForm.value.old_password || !passwordForm.value.new_password) {
        return ElementPlus.ElMessage.warning('请填写旧密码和新密码')
      }
      if (passwordForm.value.new_password.length < 6) {
        return ElementPlus.ElMessage.warning('新密码至少 6 位')
      }
      if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
        return ElementPlus.ElMessage.warning('两次输入的新密码不一致')
      }
      loading.value = true
      try {
        await http.post('/auth/change-password', {
          old_password: passwordForm.value.old_password,
          new_password: passwordForm.value.new_password,
        })
        passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
        ElementPlus.ElMessage.success('密码已修改')
      } finally { loading.value = false }
    }

    async function loadOverview() {
      const { data } = await http.get('/admin/overview')
      overview.value = data
    }

    async function loadUsers() {
      const { data } = await http.get('/admin/users')
      users.value = data
    }

    async function loadCommandDashboard() {
      const { data } = await http.get('/admin/dashboard', { params: selectedActivityId.value ? { activity_id: selectedActivityId.value } : {} })
      commandDash.value = data
    }

    async function loadConfig() {
      const [cfg, tpl] = await Promise.all([
        http.get('/admin/config'),
        http.get('/admin/templates'),
      ])
      sysConfig.value = cfg.data
      templates.value = tpl.data
      opsGroupSize.value = cfg.data.default_group_size || 4
    }

    async function loadCommunityPosts() {
      const { data } = await http.get('/admin/community/posts')
      communityPosts.value = data
    }

    async function loadActivities() {
      const { data } = await http.get('/admin/team-activities')
      activities.value = data
      if (!selectedActivityId.value && data.length) selectedActivityId.value = data[0].id
    }

    async function loadClasses() {
      const { data } = await http.get('/admin/classes')
      classes.value = data
      if (!selectedClassId.value && data.length) selectedClassId.value = data[0].id
      if (!activityForm.value.class_id && data.length) activityForm.value.class_id = data[0].id
    }

    async function loadClassDetail(id = selectedClassId.value) {
      if (!id) {
        classDetail.value = null
        return
      }
      selectedClassId.value = id
      const { data } = await http.get(`/admin/classes/${id}`)
      classDetail.value = data
      classForm.value = {
        name: data.name || '',
        code: data.code || '',
        major: data.major || '',
        grade: data.grade || '',
        course_name: data.course_name || '',
        max_students: data.max_students || 20,
        description: data.description || '',
        status: data.status || 'active',
      }
    }

    async function createClass() {
      if (!classForm.value.name.trim()) return ElementPlus.ElMessage.warning('请填写班级名称')
      loading.value = true
      try {
        const { data } = await http.post('/admin/classes', classForm.value)
        ElementPlus.ElMessage.success('班级已创建')
        selectedClassId.value = data.id
        classForm.value = { name: '', code: '', major: '', grade: '2024', course_name: '', max_students: 20, description: '' }
        await loadClasses()
      } finally { loading.value = false }
    }

    async function saveClass() {
      if (!selectedClassId.value) return
      loading.value = true
      try {
        await http.put(`/admin/classes/${selectedClassId.value}`, classForm.value)
        ElementPlus.ElMessage.success('班级信息已保存')
        await loadClasses()
      } finally { loading.value = false }
    }

    async function archiveClass() {
      if (!selectedClassId.value) return
      try {
        await adminConfirm('解散后班级会归档或标记解散，历史活动、小组和任务不会被删除。确定继续？', '解散班级')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.delete(`/admin/classes/${selectedClassId.value}`)
        ElementPlus.ElMessage.success('班级已处理')
        await loadClasses()
      } finally { loading.value = false }
    }

    async function addClassMembers() {
      if (!selectedClassId.value || !classMemberForm.value.user_ids.length) return ElementPlus.ElMessage.warning('请选择要拉入的学生')
      loading.value = true
      try {
        await http.post(`/admin/classes/${selectedClassId.value}/members`, { user_ids: classMemberForm.value.user_ids })
        classMemberForm.value.user_ids = []
        ElementPlus.ElMessage.success('学生已加入班级')
        await loadClassDetail()
      } finally { loading.value = false }
    }

    async function removeClassMember(row) {
      if (!selectedClassId.value || !row?.user?.id) return
      try {
        await adminConfirm(`确定将 ${row.user.name} 移出当前班级吗？`, '剔除学生')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.delete(`/admin/classes/${selectedClassId.value}/members/${row.user.id}`)
        ElementPlus.ElMessage.success('已移出班级')
        await loadClassDetail()
      } finally { loading.value = false }
    }

    async function reviewClassRequest(req, action) {
      if (!selectedClassId.value || !req) return
      const note = window.prompt(action === 'approve' ? '审批备注（可选）' : '拒绝原因（可选）', '')
      if (note === null) return
      loading.value = true
      try {
        await http.post(`/admin/classes/${selectedClassId.value}/requests/${req.id}/${action}`, { note })
        ElementPlus.ElMessage.success(action === 'approve' ? '已通过申请' : '已拒绝申请')
        await loadClasses()
      } finally { loading.value = false }
    }

    async function refreshClassAdvice() {
      if (!selectedClassId.value) return
      const { data } = await http.get(`/admin/classes/${selectedClassId.value}/grouping-advice`, { params: { group_size: classAdviceGroupSize.value } })
      if (classDetail.value) classDetail.value.grouping_advice = data
    }

    async function loadActivityDetail(id = selectedActivityId.value) {
      if (!id) {
        activityDetail.value = null
        return
      }
      selectedActivityId.value = id
      const { data } = await http.get(`/admin/team-activities/${id}`)
      activityDetail.value = data
      opsGroupId.value = data.groups?.[0]?.id || opsGroupId.value
      await Promise.all([loadOverview(), loadCommandDashboard()])
    }

    async function openActivityDetail(id) {
      await loadActivityDetail(id)
      activityDetailDrawerVisible.value = true
    }

    async function createActivity() {
      if (!activityForm.value.title.trim()) return ElementPlus.ElMessage.warning('请填写活动标题')
      if (!activityForm.value.class_id) return ElementPlus.ElMessage.warning('请选择班级范围，活动必须归属于具体班级')
      loading.value = true
      try {
        const { data } = await http.post('/admin/team-activities', activityForm.value)
        ElementPlus.ElMessage.success('组队活动已创建')
        selectedActivityId.value = data.id
        activityForm.value.title = ''
        activityForm.value.task_goal = ''
        activityForm.value.description = ''
        activityForm.value.required_tags = []
        activityForm.value.required_roles = []
        await loadActivities()
      } finally { loading.value = false }
    }

    async function publishActivityCollect() {
      if (!selectedActivityId.value) return
      try {
        await adminConfirm('发布后学生将可以看到并填写该活动，确定发布吗？', '发布组队活动')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.post(`/admin/team-activities/${selectedActivityId.value}/publish-collect`)
        ElementPlus.ElMessage.success('已发布给学生填写')
        await loadActivityDetail()
      } finally { loading.value = false }
    }

    async function autoGroupActivity() {
      if (!selectedActivityId.value) return
      try {
        await adminConfirm('系统将根据当前画像生成候选分组，并进入预沟通确认阶段。确定继续吗？', '生成候选分组')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.post(`/admin/team-activities/${selectedActivityId.value}/auto-group`)
        ElementPlus.ElMessage.success('已生成活动小组')
        await loadActivityDetail()
      } finally { loading.value = false }
    }

    async function publishActivityGroups() {
      if (!selectedActivityId.value) return
      try {
        await adminConfirm('锁定后将作为正式团队进入任务分配阶段，确定继续吗？', '锁定正式团队')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.post(`/admin/team-activities/${selectedActivityId.value}/lock-groups`)
        ElementPlus.ElMessage.success('已锁定正式团队')
        await loadActivityDetail()
      } finally { loading.value = false }
    }

    async function resolveConfirmation(conf, action = 'resolved') {
      if (!selectedActivityId.value || !conf) return
      const note = window.prompt(action === 'rejected' ? '请填写驳回原因（可选）' : '处理说明（可选，例如已调整角色或建议组内协商）', conf.handled_note || '')
      if (note === null) return
      const role = action === 'resolved' ? window.prompt('如需调整角色，请填写新角色；不调整可留空。', conf.preferred_role || '') : ''
      loading.value = true
      try {
        await http.post(`/admin/team-activities/${selectedActivityId.value}/confirmations/${conf.id}/resolve`, {
          status: action,
          handled_note: note || '',
          role: role || '',
        })
        ElementPlus.ElMessage.success('确认记录已处理')
        await loadActivityDetail()
        if (opsGroupId.value) await loadTeamDash(opsGroupId.value)
      } finally { loading.value = false }
    }

    async function lockFreeTeams() {
      if (!selectedActivityId.value) return
      try {
        await adminConfirm('锁定后学生自由组队结果将转为正式团队，确定继续吗？', '锁定自由组队')
      } catch {
        return
      }
      loading.value = true
      try {
        await http.post(`/admin/team-activities/${selectedActivityId.value}/lock-free-teams`)
        ElementPlus.ElMessage.success('已锁定自由组队结果')
        await loadActivityDetail()
      } finally { loading.value = false }
    }

    async function loadTeamDash(gid) {
      if (!gid) {
        teamDash.value = null
        return
      }
      const { data } = await http.get(`/admin/team/${gid}/dashboard`)
      teamDash.value = data
      syncRoleEdits(data)
    }

    function syncRoleEdits(dash) {
      roleEdits.value = (dash?.members || []).map((m) => ({
        user_id: m.user?.id,
        name: m.user?.name,
        role: m.team_role || m.profile?.pref_role || '执行落地',
      }))
    }

    async function refreshAll() {
      loading.value = true
      try {
        await Promise.all([loadCommandDashboard(), loadOverview(), loadUsers(), loadConfig(), loadActivities(), loadClasses()])
      } finally {
        loading.value = false
      }
      window.setTimeout(() => {
        if (page.value === 'workbench' && selectedActivityId.value && !activityDetail.value) loadActivityDetail(selectedActivityId.value)
        if (page.value === 'classes' && selectedClassId.value && !classDetail.value) loadClassDetail(selectedClassId.value)
      }, 80)
    }

    async function opsCreateGroups() {
      const ids = profileReady.value.map((r) => r.user?.id).filter(Boolean)
      if (ids.length < opsGroupSize.value) {
        ElementPlus.ElMessage.warning(`已录入画像的学员仅 ${ids.length} 人，少于每组 ${opsGroupSize.value} 人，无法分组`)
        return
      }
      try {
        await adminConfirm(
          '将对已录入画像的学员执行 AI 分组。注意：不会自动删除已有小组，重复操作会产生多批小组。确定继续？',
          '智能分组'
        )
      } catch {
        return
      }
      loading.value = true
      try {
        const { data } = await http.post('/admin/ops/create-groups', {
          user_ids: ids,
          group_size: opsGroupSize.value,
          config: { mode: 'heterogeneous' },
        })
        ElementPlus.ElMessage.success(`已创建 ${data.groups?.length || 0} 个小组`)
        await refreshAll()
        workbenchStep.value = 3
        if (data.groups?.length) opsGroupId.value = data.groups[data.groups.length - 1].id
      } finally {
        loading.value = false
      }
    }

    async function opsAssignRolesAll() {
      loading.value = true
      try {
        const { data } = await http.post('/admin/ops/assign-roles-all')
        ElementPlus.ElMessage.success(`已为 ${data.groups?.length || 0} 个小组分配角色`)
        await refreshAll()
        if (opsGroupId.value) await loadTeamDash(opsGroupId.value)
      } finally {
        loading.value = false
      }
    }

    async function opsAssignRolesOne() {
      if (!opsGroupId.value) return ElementPlus.ElMessage.warning('请先选择小组')
      loading.value = true
      try {
        await http.post('/admin/ops/assign-roles', { group_id: opsGroupId.value })
        ElementPlus.ElMessage.success('角色已自动分配')
        await loadTeamDash(opsGroupId.value)
        await loadOverview()
      } finally {
        loading.value = false
      }
    }

    async function saveGroupRoles() {
      if (!opsGroupId.value) return
      loading.value = true
      try {
        await http.put(`/admin/group/${opsGroupId.value}/roles`, {
          member_roles: roleEdits.value.map((r) => ({ user_id: r.user_id, role: r.role })),
        })
        ElementPlus.ElMessage.success('角色已保存')
        await loadTeamDash(opsGroupId.value)
      } finally {
        loading.value = false
      }
    }

    async function opsAssignTasks() {
      if (!opsGroupId.value) return ElementPlus.ElMessage.warning('请先选择小组')
      loading.value = true
      try {
        const { data } = await http.post('/admin/ops/assign-tasks', {
          group_id: opsGroupId.value,
          template_key: opsTemplate.value,
        })
        ElementPlus.ElMessage.success(`已分配 ${data.tasks?.length || 0} 个任务`)
        workbenchStep.value = 5
        await loadTeamDash(opsGroupId.value)
      } finally {
        loading.value = false
      }
    }

    async function opsAdjustTasks() {
      if (!opsGroupId.value) return ElementPlus.ElMessage.warning('请先选择小组')
      loading.value = true
      try {
        const { data } = await http.post('/admin/ops/adjust-tasks', { group_id: opsGroupId.value })
        ElementPlus.ElMessage.success(`生成 ${data.suggestions?.length || 0} 条调优建议`)
        await loadTeamDash(opsGroupId.value)
      } finally {
        loading.value = false
      }
    }

    async function saveConfig() {
      loading.value = true
      try {
        await http.put('/admin/config', sysConfig.value)
        opsGroupSize.value = sysConfig.value.default_group_size
        ElementPlus.ElMessage.success('配置已保存')
      } finally {
        loading.value = false
      }
    }

    async function downloadExport(resource, params) {
      try {
        await adminConfirm('导出文件可能包含学生画像、分组或任务数据，请确认仅用于教学管理或课程评估。', '确认导出数据')
      } catch {
        return
      }
      loading.value = true
      try {
        const res = await http.get(`/export/${resource}`, { params: params || {}, responseType: 'blob' })
        const ext = params?.format === 'pdf' ? 'pdf' : 'xlsx'
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = `${resource}.${ext}`
        a.click()
        URL.revokeObjectURL(url)
        ElementPlus.ElMessage.success('下载已开始')
      } finally {
        loading.value = false
      }
    }

    async function downloadReportExport() {
      const groupId = exportGroupId.value || opsGroupId.value || exportGroups.value[0]?.id
      if (!groupId) return ElementPlus.ElMessage.warning(t('请先选择有报告的小组'))
      await downloadExport('report', { group_id: groupId, format: 'pdf' })
    }

    function startAutoRefresh() {
      stopAutoRefresh()
      if (workbenchStep.value === 5 && opsGroupId.value) {
        refreshTimer = setInterval(() => loadTeamDash(opsGroupId.value), 30000)
      }
    }

    function stopAutoRefresh() {
      if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
      }
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
      if (!PAGE_KEYS.includes(p)) p = 'workbench'
      if (!pushHash && page.value === p) return
      page.value = p
      if (pushHash && window.location.hash !== `#${p}`) {
        window.location.hash = p
      }
      updateDocumentTitle()
      stopAutoRefresh()
      if (p === 'workbench') {
        refreshAll()
      }
      if (p === 'classes') loadClasses().then(() => selectedClassId.value && loadClassDetail(selectedClassId.value))
      if (p === 'users') loadUsers()
      if (p === 'community') loadCommunityPosts()
      if (p === 'export') loadOverview()
      if (p === 'settings') loadConfig()
      if (p === 'account') loadMe()
    }

    function setLanguage(lang) {
      language.value = ADMIN_I18N[lang] ? lang : 'zh-CN'
      TeamMindAdminRuntime.storage.setItem(APP_LANG_KEY, language.value)
      TeamMindAdminRuntime.storage.setItem('teammind_portal_lang', language.value)
      document.documentElement.lang = language.value
      updateDocumentTitle()
    }

    async function updatePostStatus(post, status) {
      if (status !== 'published') {
        try {
          await adminConfirm('隐藏后学生端将不再展示该帖子，确定继续吗？', '隐藏社区帖子')
        } catch {
          return
        }
      }
      await http.put(`/admin/community/posts/${post.id}/status`, { status })
      ElementPlus.ElMessage.success('状态已更新')
      await loadCommunityPosts()
    }

    function setStep(n) {
      workbenchStep.value = n
      stopAutoRefresh()
      if (n === 5 && opsGroupId.value) {
        loadTeamDash(opsGroupId.value)
        startAutoRefresh()
      }
    }

    function onHashChange() {
      const key = window.location.hash.replace('#', '')
      if (PAGE_KEYS.includes(key)) go(key, false)
    }

    onMounted(() => {
      setLanguage(language.value)
      window.addEventListener('teammind-admin-auth-expired', handleAuthExpired)
      if (isLoggedIn.value) {
        validateSession().then((ok) => {
          if (!ok) return
          const key = window.location.hash.replace('#', '')
          page.value = PAGE_KEYS.includes(key) ? key : 'workbench'
          window.addEventListener('hashchange', onHashChange)
          refreshAll()
          if (page.value === 'classes') loadClasses()
          if (page.value === 'users') loadUsers()
          if (page.value === 'community') loadCommunityPosts()
          if (page.value === 'settings') loadConfig()
          if (page.value === 'account') loadMe()
        })
      }
    })

    onUnmounted(() => {
      stopAutoRefresh()
      window.removeEventListener('hashchange', onHashChange)
      window.removeEventListener('teammind-admin-auth-expired', handleAuthExpired)
    })

    return {
      NAV_ITEMS,
      navItems,
      WORKBENCH_STEPS,
      WORKFLOW_PHASES,
      ROLE_OPTIONS,
      page,
      workbenchStep,
      user,
      loading,
      loginForm,
      overview,
      users,
      commandDash,
      sysConfig,
      templates,
      activities,
      selectedActivityId,
      selectedActivity,
      activityDetail,
      classes,
      selectedClassId,
      selectedClass,
      classDetail,
      classTab,
      classForm,
      classMemberForm,
      classAdviceGroupSize,
      classMembers,
      classRequests,
      classActivities,
      classPendingRequests,
      classAdvice,
      classAvailableUsers,
      activityForm,
      activityParticipants,
      activityGroups,
      activityRooms,
      activityConfirmations,
      activityConfirmationSummary,
      communityPosts,
      exportGroupId,
      exportGroups,
      userSearch,
      rulesVisible,
      profileDrawerVisible,
      selectedUserRow,
      activityDetailDrawerVisible,
      opsGroupSize,
      opsTemplate,
      opsGroupId,
      teamDash,
      roleEdits,
      isLoggedIn,
      currentNav,
      currentStepInfo,
      currentPhase,
      studentUsers,
      profileReady,
      profilePending,
      profileRate,
      filteredUsers,
      userInitial,
      userAvatar,
      activityDisplayTitle,
      displayDemoText,
      formatGroupingAdviceText,
      formatInsightText,
      selectedClassAdviceSummary,
      classAdvicePanelSummary,
      activityFormClassAdviceSummary,
      openProfileDrawer,
      scoreVal,
      scorePct,
      scoreColor,
      tagDimensionClass,
      tagIcon,
      tagName,
      scoreLabel,
      formatStatus,
      formatMode,
      formatRequestType,
      formatList,
      formatTagList,
      breakdownRows,
      safeList,
      formatJson,
      doLogin,
      logout,
      accountForm,
      passwordForm,
      STUDENT_PORTAL_URL,
      language,
      LANGUAGE_OPTIONS,
      t,
      setLanguage,
      loadMe,
      saveAccount,
      changePassword,
      go,
      setStep,
      refreshAll,
      loadClasses,
      loadClassDetail,
      createClass,
      saveClass,
      archiveClass,
      addClassMembers,
      removeClassMember,
      reviewClassRequest,
      refreshClassAdvice,
      loadActivities,
      loadActivityDetail,
      openActivityDetail,
      createActivity,
      publishActivityCollect,
      autoGroupActivity,
      publishActivityGroups,
      lockFreeTeams,
      resolveConfirmation,
      opsCreateGroups,
      opsAssignRolesAll,
      opsAssignRolesOne,
      saveGroupRoles,
      opsAssignTasks,
      opsAdjustTasks,
      saveConfig,
      loadCommunityPosts,
      updatePostStatus,
      downloadExport,
      downloadReportExport,
      loadTeamDash,
      startAutoRefresh,
    }
  },
  template: `
    <div v-if="!isLoggedIn" class="login-page">
      <div class="login-brand">
        <h1>{{ t('brandTitle') }}</h1>
        <p class="brand-en">{{ t('brandEn') }}</p>
        <p class="tagline">{{ t('loginTagline') }}</p>
        <span class="badge-admin">{{ t('studentAccess') }}</span>
        <a class="role-switch-card" :href="STUDENT_PORTAL_URL">
          <span>🎓</span>
          <strong>{{ t('switchToStudent') }}</strong>
          <small>{{ t('switchToStudentHint') }}</small>
        </a>
      </div>
      <div class="login-panel">
        <div class="login-card">
          <el-select v-model="language" size="small" style="width:140px;margin-bottom:16px" @change="setLanguage">
            <el-option v-for="item in LANGUAGE_OPTIONS" :key="item.code" :label="item.label" :value="item.code" />
          </el-select>
          <div class="card-title">{{ t('loginTitle') }}</div>
          <p class="card-sub">{{ t('loginSub') }}</p>
          <el-form label-position="top" @submit.prevent="doLogin">
            <el-form-item :label="t('account')"><el-input v-model="loginForm.account" size="large" /></el-form-item>
            <el-form-item :label="t('password')"><el-input v-model="loginForm.password" type="password" show-password size="large" @keyup.enter="doLogin" /></el-form-item>
            <el-button type="primary" :loading="loading" @click="doLogin" size="large" style="width:100%">{{ t('loginButton') }}</el-button>
          </el-form>
          <div class="demo-hint">{{ t('demoHint') }}</div>
          <a class="login-switch-link" :href="STUDENT_PORTAL_URL">🎓 {{ t('switchToStudent') }}</a>
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
            <span class="nav-icon">{{ n.icon }}</span>
            <span>{{ n.label }}</span>
          </a>
        </nav>
        <div class="aside-switch">
          <a :href="STUDENT_PORTAL_URL">
            <span>🎓</span>
            <strong>{{ t('switchToStudent') }}</strong>
          </a>
        </div>
      </aside>

      <div class="main">
        <header class="header">
          <div>
            <div class="header-title">{{ currentNav.label }}</div>
            <div class="page-desc">{{ currentNav.desc }}</div>
          </div>
          <div class="header-actions">
            <el-select v-model="language" size="small" style="width:132px" @change="setLanguage">
              <el-option v-for="item in LANGUAGE_OPTIONS" :key="item.code" :label="item.label" :value="item.code" />
            </el-select>
            <a class="top-switch-button" :href="STUDENT_PORTAL_URL">🎓 {{ t('switchToStudent') }}</a>
            <el-button @click="refreshAll" :loading="loading" plain>{{ t('refresh') }}</el-button>
            <el-dropdown trigger="click">
              <div class="user-chip clickable">
                <div class="avatar">
                  <img v-if="userAvatar(user)" :src="userAvatar(user)" :alt="t('头像')" />
                  <span v-else>{{ userInitial(user?.name) }}</span>
                </div>
                <span>{{ user?.name }}</span>
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
            <div class="activity-hero">
              <div>
                <p class="eyebrow">Class Management</p>
                <h2>{{ t('班级管理') }}</h2>
                <p>{{ t('先维护班级和成员，再在组队活动中选择班级范围。学生加入或退出班级都需要老师审批，避免分组范围混乱。') }}</p>
              </div>
              <div class="hero-stats">
                <div><strong>{{ classes.length }}</strong><span>{{ t('班级数') }}</span></div>
                <div><strong>{{ classes.reduce((s,c)=>s+(c.member_count||0),0) }}</strong><span>{{ t('班级学生') }}</span></div>
                <div><strong>{{ classes.reduce((s,c)=>s+(c.pending_count||0),0) }}</strong><span>{{ t('待审批') }}</span></div>
                <div><strong>{{ classAdvice.group_count || 0 }}</strong><span>{{ t('建议组数') }}</span></div>
              </div>
            </div>

            <div class="class-layout">
              <div class="card class-list-card">
                <div class="card-header"><h3>{{ t('班级列表') }}</h3><el-button @click="loadClasses">{{ t('刷新') }}</el-button></div>
                <div v-if="!classes.length" class="empty-note">{{ t('暂无班级，请先创建。') }}</div>
                <div v-for="c in classes" :key="c.id" class="activity-row" :class="{active: selectedClassId===c.id}" @click="loadClassDetail(c.id)">
                  <div>
                    <strong>{{ displayDemoText(c.name) }}</strong>
                    <p>{{ displayDemoText(c.course_name || c.major) || (t('未设置课程') + ' ·') }} {{ formatStatus(c.status) }}</p>
                  </div>
                  <div style="display:flex;gap:6px;align-items:center">
                    <el-tag>{{ c.member_count || 0 }} {{ t('人') }}</el-tag>
                    <el-tag v-if="c.pending_count" type="warning">{{ c.pending_count }} {{ t('审批') }}</el-tag>
                  </div>
                </div>
              </div>

              <div class="card class-main-card">
                <div class="card-header">
                  <div>
                    <h3>{{ selectedClass?.name ? displayDemoText(selectedClass.name) : t('新建班级') }}</h3>
                    <p class="hint">{{ selectedClassAdviceSummary }}</p>
                  </div>
                  <el-button type="primary" plain @click="createClass">{{ t('创建为新班级') }}</el-button>
                </div>
                <el-tabs v-model="classTab">
                  <el-tab-pane :label="t('成员')" name="members">
                    <div class="class-tools">
                      <el-select v-model="classMemberForm.user_ids" multiple filterable :placeholder="t('选择要拉入的学生')" style="width:100%">
                        <el-option v-for="row in classAvailableUsers" :key="row.user.id" :label="row.user.name + ' / ' + row.user.account" :value="row.user.id" />
                      </el-select>
                      <el-button type="primary" @click="addClassMembers">{{ t('拉入同学') }}</el-button>
                    </div>
                    <el-table :data="classMembers" stripe :empty-text="t('当前班级暂无学生')">
                      <el-table-column :label="t('姓名')"><template #default="{row}">{{ row.user?.name }}</template></el-table-column>
                      <el-table-column :label="t('账号')"><template #default="{row}">{{ row.user?.account }}</template></el-table-column>
                      <el-table-column :label="t('画像')"><template #default="{row}"><el-tag :type="row.profile?'success':'info'" size="small">{{ row.profile ? t('已录入') : t('未录入') }}</el-tag></template></el-table-column>
                      <el-table-column :label="t('角色方向')"><template #default="{row}">{{ row.profile?.pref_role || '—' }}</template></el-table-column>
                      <el-table-column :label="t('操作')" width="110"><template #default="{row}"><el-button size="small" type="danger" plain @click="removeClassMember(row)">{{ t('剔除') }}</el-button></template></el-table-column>
                    </el-table>
                  </el-tab-pane>

                  <el-tab-pane :label="t('班级活动') + (classActivities.length ? ' (' + classActivities.length + ')' : '')" name="activities">
                    <p class="hint">{{ t('这里展示当前班级关联的组队活动。教师在活动中心创建活动时选择班级后，会自动出现在这里；学生从学生端发起的班级活动也会同步显示。') }}</p>
                    <el-table :data="classActivities" stripe :empty-text="t('当前班级暂无活动')">
                      <el-table-column :label="t('活动标题')" min-width="180"><template #default="{row}">{{ activityDisplayTitle(row) }}</template></el-table-column>
                      <el-table-column :label="t('方式')" width="130"><template #default="{row}">{{ formatMode(row.mode, true) }}</template></el-table-column>
                      <el-table-column :label="t('状态')" width="110"><template #default="{row}">{{ formatStatus(row.status) }}</template></el-table-column>
                      <el-table-column :label="t('参与/小组')" width="130"><template #default="{row}">{{ row.participant_count || 0 }} {{ t('人') }} / {{ row.group_count || row.team_count || 0 }} {{ t('组') }}</template></el-table-column>
                      <el-table-column :label="t('操作')" width="130">
                        <template #default="{row}">
                          <el-button size="small" type="primary" plain @click="go('workbench'); loadActivityDetail(row.id)">{{ t('查看活动') }}</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </el-tab-pane>

                  <el-tab-pane :label="t('申请审批') + (classPendingRequests.length ? ' (' + classPendingRequests.length + ')' : '')" name="requests">
                    <el-table :data="classRequests" stripe :empty-text="t('暂无申请')">
                      <el-table-column :label="t('学生')"><template #default="{row}">{{ row.user?.name || row.user_id }}</template></el-table-column>
                      <el-table-column :label="t('类型')" width="90"><template #default="{row}">{{ formatRequestType(row.request_type) }}</template></el-table-column>
                      <el-table-column :label="t('状态')" width="100"><template #default="{row}"><el-tag :type="row.status==='pending'?'warning':(row.status==='approved'?'success':'info')" size="small">{{ formatStatus(row.status) }}</el-tag></template></el-table-column>
                      <el-table-column prop="message" :label="t('申请说明')" />
                      <el-table-column :label="t('操作')" width="180">
                        <template #default="{row}">
                          <el-button size="small" type="success" :disabled="row.status!=='pending'" @click="reviewClassRequest(row,'approve')">{{ t('通过') }}</el-button>
                          <el-button size="small" plain :disabled="row.status!=='pending'" @click="reviewClassRequest(row,'reject')">{{ t('拒绝') }}</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </el-tab-pane>

                  <el-tab-pane :label="t('分组建议')" name="advice">
                    <div class="class-advice-box">
                      <div>
                        <h3>{{ classAdvicePanelSummary }}</h3>
                        <p class="hint">{{ t('建议基于当前 active 成员人数生成；真正自动分组时还会结合画像均衡。') }}</p>
                      </div>
                      <div class="class-tools compact">
                        <el-input-number v-model="classAdviceGroupSize" :min="3" :max="5" />
                        <el-button @click="refreshClassAdvice">{{ t('重新计算') }}</el-button>
                      </div>
                    </div>
                    <div v-if="classAdvice.ai_analysis" class="ai-insight-card">
                      <div class="ai-insight-head">
                        <span>AI</span>
                        <div>
                          <strong>{{ t('智能分组分析') }}</strong>
                          <p>{{ classAdvice.ai_analysis.source==='deepseek' ? t('DeepSeek 大模型分析') : t('规则兜底分析（未配置大模型或调用失败）') }}</p>
                        </div>
                      </div>
                      <p>{{ formatInsightText(classAdvice.ai_analysis.summary) }}</p>
                      <div class="ai-insight-grid">
                        <div><b>{{ t('分析依据') }}</b><span v-for="x in classAdvice.ai_analysis.rationale||[]" :key="x">{{ formatInsightText(x) }}</span></div>
                        <div><b>{{ t('教师建议') }}</b><span v-for="x in classAdvice.ai_analysis.teacher_actions||[]" :key="x">{{ formatInsightText(x) }}</span></div>
                        <div><b>{{ t('风险提醒') }}</b><span v-for="x in classAdvice.ai_analysis.risks||[]" :key="x">{{ formatInsightText(x) }}</span></div>
                      </div>
                    </div>
                    <div class="advice-size-row">
                      <div v-for="(s,idx) in (classAdvice.sizes||[])" :key="idx" class="advice-size-card">
                        <span>{{ t('第') }} {{ idx + 1 }} {{ t('组') }}</span>
                        <strong>{{ s }} {{ t('人') }}</strong>
                      </div>
                    </div>
                  </el-tab-pane>

                  <el-tab-pane :label="t('班级设置')" name="settings">
                    <el-form label-position="top" class="class-form-grid">
                      <el-form-item :label="t('班级名称')"><el-input v-model="classForm.name" :placeholder="t('如：人工智能 2401 班')" /></el-form-item>
                      <el-form-item :label="t('班级代码')"><el-input v-model="classForm.code" :placeholder="t('如：AI2401')" /></el-form-item>
                      <el-form-item :label="t('专业')"><el-input v-model="classForm.major" /></el-form-item>
                      <el-form-item :label="t('年级')"><el-input v-model="classForm.grade" /></el-form-item>
                      <el-form-item :label="t('课程名称')"><el-input v-model="classForm.course_name" /></el-form-item>
                      <el-form-item :label="t('人数上限')"><el-input-number v-model="classForm.max_students" :min="10" :max="60" /></el-form-item>
                      <el-form-item :label="t('说明')" class="wide"><el-input v-model="classForm.description" type="textarea" :rows="3" /></el-form-item>
                    </el-form>
                    <div class="toolbar-row">
                      <el-button type="primary" @click="saveClass">{{ t('保存当前班级') }}</el-button>
                      <el-button type="danger" plain @click="archiveClass">{{ t('解散/归档班级') }}</el-button>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </div>
          </template>

          <template v-if="page==='workbench'">
            <div class="activity-hero">
              <div>
                <p class="eyebrow">{{ t('TeamActivityCenter') }}</p>
                <h2>{{ t('组队活动中心') }}</h2>
                <p>{{ t('先创建一次组队活动，再选择“任务驱动自动组队”或“学生自由组队”。学生只有参与该活动后，才会进入对应队伍流程。') }}</p>
              </div>
              <div class="hero-stats">
                <div><strong>{{ activities.length }}</strong><span>{{ t('活动数') }}</span></div>
                <div><strong>{{ selectedActivity?.participant_count || 0 }}</strong><span>{{ t('参与学生') }}</span></div>
                <div><strong>{{ selectedActivity?.group_count || selectedActivity?.team_count || 0 }}</strong><span>{{ t('队伍/小组') }}</span></div>
                <div><strong>{{ commandDash.feedback_count || 0 }}</strong><span>{{ t('任务反馈') }}</span></div>
              </div>
            </div>

            <div class="activity-layout">
              <div class="card activity-form-card">
                <div class="card-header"><h3>{{ t('创建组队活动') }}</h3></div>
                <el-form label-position="top">
                  <el-form-item :label="t('活动标题')"><el-input v-model="activityForm.title" :placeholder="t('如：第 4 周产品原型项目组队')" /></el-form-item>
                  <el-form-item :label="t('课程/场景')"><el-input v-model="activityForm.course_name" :placeholder="t('可选，如：人机交互课程')" /></el-form-item>
                  <el-form-item :label="t('班级范围')">
                    <el-select v-model="activityForm.class_id" filterable :placeholder="t('请选择班级：活动必须归属于具体班级')" style="width:100%">
                      <el-option v-for="c in classes" :key="c.id" :label="displayDemoText(c.name) + ' · ' + (c.member_count || 0) + ' ' + t('人')" :value="c.id" />
                    </el-select>
                    <p class="hint" v-if="activityFormClassAdviceSummary">{{ activityFormClassAdviceSummary }}</p>
                  </el-form-item>
                  <el-form-item :label="t('组队方式')">
                    <div class="mode-card-grid">
                      <div class="mode-card" :class="{active: activityForm.mode==='task_auto'}" @click="activityForm.mode='task_auto'">
                        <strong>{{ t('任务驱动自动组队') }}</strong>
                        <span>{{ t('老师填写任务需求，学生补充标签后系统自动匹配。') }}</span>
                      </div>
                      <div class="mode-card" :class="{active: activityForm.mode==='free_team'}" @click="activityForm.mode='free_team'">
                        <strong>{{ t('学生自由组队') }}</strong>
                        <span>{{ t('学生创建或加入队伍，老师最后锁定结果。') }}</span>
                      </div>
                    </div>
                  </el-form-item>
                  <el-form-item :label="t('每组人数')"><el-input-number v-model="activityForm.group_size" :min="2" :max="8" /></el-form-item>
                  <el-form-item :label="t('任务需求/组队说明')"><el-input v-model="activityForm.task_goal" type="textarea" :rows="4" :placeholder="t('说明这次任务要做什么、希望队伍具备哪些能力')" /></el-form-item>
                  <el-form-item :label="t('建议角色')">
                    <el-select v-model="activityForm.required_roles" multiple filterable allow-create default-first-option :placeholder="t('输入或选择角色')" style="width:100%">
                      <el-option v-for="r in ROLE_OPTIONS" :key="r" :label="displayDemoText(r)" :value="r" />
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="t('关键标签')"><el-select v-model="activityForm.required_tags" multiple filterable allow-create default-first-option :placeholder="t('如 Python、数据分析、文档汇报')" style="width:100%" /></el-form-item>
                  <el-button type="primary" :loading="loading" @click="createActivity">{{ t('创建活动') }}</el-button>
                </el-form>
              </div>

              <div class="card activity-list-card">
                <div class="card-header"><h3>{{ t('活动列表') }}</h3><el-button @click="loadActivities">{{ t('刷新') }}</el-button></div>
                <div v-if="!activities.length" class="empty-note">{{ t('暂无活动，先创建一个组队活动。') }}</div>
                <div
                  v-for="a in activities"
                  :key="a.id"
                  class="activity-row"
                  :class="{active: selectedActivityId===a.id}"
                  role="button"
                  tabindex="0"
                  @click="openActivityDetail(a.id)"
                  @keyup.enter="openActivityDetail(a.id)"
                >
                  <div class="activity-row-main">
                    <strong>{{ activityDisplayTitle(a) }}</strong>
                    <p>{{ displayDemoText(a.classroom?.name) || (t('未识别班级') + ' ·') }} {{ formatMode(a.mode) }}· {{ formatStatus(a.status) }}</p>
                  </div>
                  <div class="activity-row-meta">
                    <el-tag>{{ a.participant_count || 0 }} {{ t('人参与') }}</el-tag>
                    <span class="open-detail-link">{{ t('打开详情') }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedActivity" class="card activity-detail-card">
              <div class="card-header">
                <div>
                  <h3>{{ activityDisplayTitle(selectedActivity) }}</h3>
                  <p class="hint">{{ selectedActivity.task_goal || selectedActivity.description || t('暂无任务说明') }}</p>
                </div>
                <el-tag size="large" type="success">{{ formatMode(selectedActivity.mode, true) }} · {{ formatStatus(selectedActivity.status) }}</el-tag>
              </div>
              <div class="activity-actions">
                <el-button type="primary" plain :disabled="selectedActivity.status!=='draft'" :loading="loading" @click="publishActivityCollect">{{ t('发布给学生填写') }}</el-button>
                <el-button v-if="selectedActivity.mode==='task_auto'" type="primary" :disabled="!activityParticipants.length" :loading="loading" @click="autoGroupActivity">{{ t('生成候选分组') }}</el-button>
                <el-button v-if="selectedActivity.mode==='task_auto'" type="success" :disabled="!activityGroups.length" :loading="loading" @click="publishActivityGroups">{{ t('锁定正式团队') }}</el-button>
                <el-button v-if="selectedActivity.mode==='free_team'" type="success" :disabled="!activityRooms.length" :loading="loading" @click="lockFreeTeams">{{ t('锁定自由组队结果') }}</el-button>
              </div>

              <div class="activity-summary-grid">
                <div><span>{{ t('参与人数') }}</span><strong>{{ activityParticipants.length }}</strong></div>
                <div><span>{{ t('已生成小组') }}</span><strong>{{ activityGroups.length }}</strong></div>
                <div><span>{{ t('自由队伍') }}</span><strong>{{ activityRooms.length }}</strong></div>
                <div><span>{{ t('确认率') }}</span><strong>{{ activityConfirmationSummary.accept_rate || 0 }}%</strong></div>
              </div>

              <div v-if="selectedActivity.ai_analysis" class="ai-insight-card">
                <div class="ai-insight-head">
                  <span>AI</span>
                  <div>
                    <strong>{{ t('活动分组智能分析') }}</strong>
                    <p>{{ selectedActivity.ai_analysis.source==='deepseek' ? t('DeepSeek 大模型返回') : t('规则兜底分析（未配置大模型或调用失败）') }}</p>
                  </div>
                </div>
                <p>{{ formatInsightText(selectedActivity.ai_analysis.summary) }}</p>
                <div class="ai-insight-grid">
                  <div><b>{{ t('专业判断') }}</b><span v-for="x in selectedActivity.ai_analysis.rationale||[]" :key="x">{{ formatInsightText(x) }}</span></div>
                  <div><b>{{ t('下一步动作') }}</b><span v-for="x in selectedActivity.ai_analysis.teacher_actions||[]" :key="x">{{ formatInsightText(x) }}</span></div>
                  <div><b>{{ t('风险预警') }}</b><span v-for="x in selectedActivity.ai_analysis.risks||[]" :key="x">{{ formatInsightText(x) }}</span></div>
                </div>
              </div>

              <div class="activity-section">
                <h4>{{ t('参与学生') }}</h4>
                <el-table :data="activityParticipants" size="small" :empty-text="t('等待学生参与')">
                  <el-table-column :label="t('姓名')"><template #default="{row}">{{ row.user?.name || row.user_id }}</template></el-table-column>
                  <el-table-column :label="t('标签数')"><template #default="{row}">{{ (row.active_tags||[]).length }}</template></el-table-column>
                  <el-table-column :label="t('状态')"><template #default="{row}"><el-tag size="small">{{ formatStatus(row.status) }}</el-tag></template></el-table-column>
                </el-table>
              </div>

              <div v-if="selectedActivity.mode==='task_auto'" class="activity-section">
                <h4>{{ t('候选分组结果') }}</h4>
                <el-table :data="activityGroups" size="small" :empty-text="t('尚未生成小组')">
                  <el-table-column prop="group_name" :label="t('小组')" width="120" />
                  <el-table-column :label="t('成员数')" width="90"><template #default="{row}">{{ row.member_ids?.length || 0 }}</template></el-table-column>
                  <el-table-column prop="balance_score" :label="t('均衡度')" width="90" />
                  <el-table-column :label="t('确认')" width="130"><template #default="{row}">{{ row.confirmation_summary?.accepted || 0 }}/{{ row.confirmation_summary?.total || 0 }} · {{ row.confirmation_summary?.accept_rate || 0 }}%</template></el-table-column>
                  <el-table-column :label="t('说明')"><template #default="{row}"><span class="explain-text">{{ formatInsightText(row.ai_analysis?.summary) || row.complement_note || '—' }}</span></template></el-table-column>
                </el-table>
              </div>

              <div v-if="selectedActivity.mode==='task_auto' && activityGroups.length" class="activity-section">
                <h4>{{ t('预沟通确认与微调申请') }}</h4>
                <p class="hint">{{ t('学生确认后再锁定正式团队；有微调申请时，老师可记录处理意见并同步调整角色。') }}</p>
                <el-table :data="activityConfirmations" size="small" :empty-text="t('等待学生确认')">
                  <el-table-column :label="t('学生')" width="110"><template #default="{row}">{{ row.user?.name || row.user_id }}</template></el-table-column>
                  <el-table-column :label="t('状态')" width="120">
                    <template #default="{row}">
                      <el-tag size="small" :type="row.status==='accepted'?'success':(row.status==='adjust_requested'?'warning':'info')">{{ formatStatus(row.status) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="preferred_role" :label="t('期望/推荐角色')" width="140" />
                  <el-table-column :label="t('任务偏好')" min-width="160"><template #default="{row}">{{ formatTagList(row.task_preferences) }}</template></el-table-column>
                  <el-table-column prop="reason" :label="t('原因/备注')" min-width="180" />
                  <el-table-column prop="handled_note" :label="t('处理说明')" min-width="160" />
                  <el-table-column :label="t('操作')" width="180">
                    <template #default="{row}">
                      <el-button size="small" type="primary" plain @click="resolveConfirmation(row,'resolved')">{{ t('处理') }}</el-button>
                      <el-button size="small" plain @click="resolveConfirmation(row,'rejected')">{{ t('驳回') }}</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div v-if="selectedActivity.mode==='free_team'" class="activity-section">
                <h4>{{ t('学生自由队伍') }}</h4>
                <div class="free-room-grid">
                  <div v-for="room in activityRooms" :key="room.id" class="free-room-card">
                    <strong>{{ room.name }}</strong>
                    <p>{{ room.description || t('暂无队伍说明') }}</p>
                    <div class="room-members">
                      <el-tag v-for="m in room.members||[]" :key="m.id" size="small">{{ m.name }}</el-tag>
                    </div>
                    <p class="hint">{{ t('待处理申请：') }} {{ (room.pending_requests||[]).length }}</p>
                  </div>
                </div>
              </div>
            </div>

            <el-drawer
              v-model="activityDetailDrawerVisible"
              size="760px"
              class="activity-detail-drawer"
              :with-header="false"
            >
              <div v-if="selectedActivity" class="activity-drawer-content">
                <div class="activity-drawer-head">
                  <div>
                    <p class="eyebrow">{{ t('活动详情') }}</p>
                    <h2>{{ activityDisplayTitle(selectedActivity) }}</h2>
                    <p>{{ selectedActivity.task_goal || selectedActivity.description || t('暂无任务说明') }}</p>
                  </div>
                  <el-button plain @click="activityDetailDrawerVisible=false">{{ t('关闭') }}</el-button>
                </div>

                <div class="activity-drawer-tags">
                  <el-tag type="success">{{ formatMode(selectedActivity.mode) }}</el-tag>
                  <el-tag>{{ formatStatus(selectedActivity.status) }}</el-tag>
                  <el-tag type="info">{{ displayDemoText(selectedActivity.classroom?.name) || t('未识别班级') }}</el-tag>
                </div>

                <div class="activity-summary-grid drawer-summary-grid">
                  <div><span>{{ t('参与人数') }}</span><strong>{{ activityParticipants.length }}</strong></div>
                  <div><span>{{ t('已生成小组') }}</span><strong>{{ activityGroups.length }}</strong></div>
                  <div><span>{{ t('自由队伍') }}</span><strong>{{ activityRooms.length }}</strong></div>
                  <div><span>{{ t('确认率') }}</span><strong>{{ activityConfirmationSummary.accept_rate || 0 }}%</strong></div>
                </div>

                <div class="activity-drawer-meta">
                  <div><span>{{ t('班级范围') }}</span><strong>{{ displayDemoText(selectedActivity.classroom?.name) || t('未识别班级') }}</strong></div>
                  <div><span>{{ t('每组人数') }}</span><strong>{{ selectedActivity.group_size || activityForm.group_size || 4 }} {{ t('人') }}</strong></div>
                  <div><span>{{ t('建议角色') }}</span><strong>{{ formatList(selectedActivity.required_roles) }}</strong></div>
                  <div><span>{{ t('关键标签') }}</span><strong>{{ formatList(selectedActivity.required_tags) }}</strong></div>
                </div>

                <div class="activity-actions drawer-actions">
                  <el-button type="primary" plain :disabled="selectedActivity.status!=='draft'" :loading="loading" @click="publishActivityCollect">{{ t('发布给学生填写') }}</el-button>
                  <el-button v-if="selectedActivity.mode==='task_auto'" type="primary" :disabled="!activityParticipants.length" :loading="loading" @click="autoGroupActivity">{{ t('生成候选分组') }}</el-button>
                  <el-button v-if="selectedActivity.mode==='task_auto'" type="success" :disabled="!activityGroups.length" :loading="loading" @click="publishActivityGroups">{{ t('锁定正式团队') }}</el-button>
                  <el-button v-if="selectedActivity.mode==='free_team'" type="success" :disabled="!activityRooms.length" :loading="loading" @click="lockFreeTeams">{{ t('锁定自由组队结果') }}</el-button>
                </div>

                <div class="activity-section">
                  <h4>{{ t('参与学生') }}</h4>
                  <el-table :data="activityParticipants" size="small" :empty-text="t('等待学生参与')">
                    <el-table-column :label="t('姓名')" width="120"><template #default="{row}">{{ row.user?.name || row.user_id }}</template></el-table-column>
                    <el-table-column :label="t('标签')"><template #default="{row}">{{ formatTagList(row.active_tags) }}</template></el-table-column>
                    <el-table-column :label="t('状态')" width="110"><template #default="{row}"><el-tag size="small">{{ formatStatus(row.status) }}</el-tag></template></el-table-column>
                  </el-table>
                </div>

                <div v-if="selectedActivity.mode==='task_auto'" class="activity-section">
                  <h4>{{ t('候选分组结果') }}</h4>
                  <el-table :data="activityGroups" size="small" :empty-text="t('尚未生成小组')">
                    <el-table-column prop="group_name" :label="t('小组')" width="120" />
                    <el-table-column :label="t('成员数')" width="90"><template #default="{row}">{{ row.member_ids?.length || 0 }}</template></el-table-column>
                    <el-table-column prop="balance_score" :label="t('均衡度')" width="90" />
                    <el-table-column :label="t('说明')"><template #default="{row}"><span class="explain-text">{{ formatInsightText(row.ai_analysis?.summary) || row.complement_note || '—' }}</span></template></el-table-column>
                  </el-table>
                </div>

                <div v-if="selectedActivity.mode==='free_team'" class="activity-section">
                  <h4>{{ t('学生自由队伍') }}</h4>
                  <div class="free-room-grid">
                    <div v-for="room in activityRooms" :key="room.id" class="free-room-card">
                      <strong>{{ room.name }}</strong>
                      <p>{{ room.description || t('暂无队伍说明') }}</p>
                      <div class="room-members">
                        <el-tag v-for="m in room.members||[]" :key="m.id" size="small">{{ m.name }}</el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-drawer>
          </template>

          <template v-if="page==='users'">
            <div class="card users-card">
              <div class="card-header">
                <div>
                  <h3>{{ t('学员画像全景') }}</h3>
                  <p class="hint">{{ t('教师端展示完整评分、来源拆解、标签证据与分组参考；学生端不展示分数。') }}</p>
                </div>
                <el-button type="primary" plain @click="rulesVisible=true">{{ t('查看计算规则') }}</el-button>
              </div>
              <div class="teacher-overview-grid">
                <div class="teacher-metric"><span>{{ t('学员总数') }}</span><strong>{{ studentUsers.length }}</strong></div>
                <div class="teacher-metric"><span>{{ t('画像已录入') }}</span><strong>{{ profileReady.length }}</strong></div>
                <div class="teacher-metric"><span>{{ t('画像完成率') }}</span><strong>{{ profileRate }}%</strong></div>
              </div>
              <div class="users-filter-panel">
                <div class="filter-field">
                  <span>{{ t('活动筛选') }}</span>
                  <el-select v-model="selectedActivityId" clearable :placeholder="t('全部组队活动')" @change="loadActivityDetail">
                    <el-option v-for="a in activities" :key="a.id" :label="a.title" :value="a.id" />
                  </el-select>
                </div>
                <div class="filter-field grow">
                  <span>{{ t('搜索学员') }}</span>
                  <el-input v-model="userSearch" :placeholder="t('输入姓名或账号')" clearable />
                </div>
                <div class="filter-summary">
                  {{ t('当前显示') }} <strong>{{ filteredUsers.length }}</strong> {{ t('人') }}
                </div>
              </div>
              <el-table :data="filteredUsers" stripe class="profile-table" :empty-text="t('暂无符合条件的学员')">
                <el-table-column :label="t('姓名')"><template #default="{row}">{{ row.user?.name }}</template></el-table-column>
                <el-table-column :label="t('账号')"><template #default="{row}">{{ row.user?.account }}</template></el-table-column>
                <el-table-column :label="t('画像')" width="100">
                  <template #default="{row}"><el-tag :type="row.has_profile?'success':'info'" size="small">{{ row.has_profile ? t('已录入') : t('未录入') }}</el-tag></template>
                </el-table-column>
                <el-table-column :label="t('三维综合分')" width="240">
                  <template #default="{row}">
                    <div v-if="row.profile" class="score-mini-stack">
                      <div v-for="k in ['knowledge','skill','collab']" :key="k" class="score-mini">
                        <span>{{ scoreLabel(k) }}</span>
                        <el-progress :percentage="scorePct(row.profile, k)" :color="scoreColor(k)" :show-text="false" />
                        <b>{{ scoreVal(row.profile, k) }}</b>
                      </div>
                    </div>
                    <span v-else>—</span>
                  </template>
                </el-table-column>
                <el-table-column :label="t('专业/角色')" min-width="160">
                  <template #default="{row}">
                    <div v-if="row.profile" class="profile-brief">
                      <strong>{{ row.profile.major || row.profile.field || t('未识别专业') }}</strong>
                      <span>{{ row.profile.pref_role || t('未识别角色') }}</span>
                    </div>
                    <span v-else>—</span>
                  </template>
                </el-table-column>
                <el-table-column :label="t('主动标签')" min-width="220">
                  <template #default="{row}">
                    <div class="tag-cell">
                      <span v-for="(t, idx) in (row.profile?.active_tags||[]).slice(0,3)" :key="tagName(t) || idx" class="ability-badge" :class="tagDimensionClass(t)">
                        <b>{{ tagIcon(t) }}</b>{{ tagName(t) }}
                      </span>
                      <span v-if="(row.profile?.active_tags||[]).length > 3" class="more-tags">+{{ (row.profile?.active_tags||[]).length - 3 }}</span>
                    </div>
                    <span v-if="!(row.profile?.active_tags||[]).length">—</span>
                  </template>
                </el-table-column>
                <el-table-column :label="t('被动标签')" min-width="220">
                  <template #default="{row}">
                    <div class="tag-cell">
                      <span v-for="(t, idx) in (row.profile?.passive_tags||[]).slice(0,3)" :key="tagName(t) || idx" class="ability-badge passive" :class="tagDimensionClass(t)">
                        <b>{{ tagIcon(t) }}</b>{{ tagName(t) }}
                      </span>
                      <span v-if="(row.profile?.passive_tags||[]).length > 3" class="more-tags">+{{ (row.profile?.passive_tags||[]).length - 3 }}</span>
                    </div>
                    <span v-if="!(row.profile?.passive_tags||[]).length">—</span>
                  </template>
                </el-table-column>
                <el-table-column :label="t('操作')" width="120">
                  <template #default="{row}">
                    <el-button size="small" type="primary" plain :disabled="!row.profile" @click="openProfileDrawer(row)">{{ t('画像详情') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>

          <template v-if="page==='community'">
            <div class="card">
              <div class="card-header"><h3>{{ t('学习社区帖子') }}</h3><el-button @click="loadCommunityPosts">{{ t('刷新') }}</el-button></div>
              <el-table :data="communityPosts" stripe>
                <el-table-column prop="id" label="ID" width="70" />
                <el-table-column prop="author" :label="t('作者')" width="120" />
                <el-table-column prop="title" :label="t('标题')" width="180" />
                <el-table-column :label="t('内容')" min-width="240"><template #default="{row}">{{ row.content?.slice(0,80) }}</template></el-table-column>
                <el-table-column :label="t('互动')" width="150"><template #default="{row}">{{ t('赞') }}{{ row.stats?.likes||0 }} / {{ t('藏') }}{{ row.stats?.favorites||0 }} / {{ t('评') }}{{ row.stats?.comments||0 }}</template></el-table-column>
                <el-table-column :label="t('状态')" width="100"><template #default="{row}">{{ formatStatus(row.status) }}</template></el-table-column>
                <el-table-column :label="t('操作')" width="180">
                  <template #default="{row}">
                    <el-button size="small" type="warning" @click="updatePostStatus(row, 'hidden')">{{ t('隐藏') }}</el-button>
                    <el-button size="small" type="success" @click="updatePostStatus(row, 'published')">{{ t('恢复') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>

          <template v-if="page==='export'">
            <div class="card">
              <div class="card-header">
                <div>
                  <h3>{{ t('数据导出') }}</h3>
                  <p class="hint">{{ t('支持导出画像、分组、任务数据；报告导出需先选择已生成报告的小组。') }}</p>
                </div>
                <el-select v-model="exportGroupId" :placeholder="t('选择报告小组')" style="width:240px">
                  <el-option v-for="g in exportGroups" :key="g.id" :label="g.group_name || (t('小组') + g.id)" :value="g.id" />
                </el-select>
              </div>
              <div class="export-grid">
                <div class="export-tile" @click="downloadExport('profile')"><div class="tile-icon">📊</div><div class="tile-label">{{ t('导出画像') }}</div></div>
                <div class="export-tile" @click="downloadExport('group')"><div class="tile-icon">👥</div><div class="tile-label">{{ t('导出分组') }}</div></div>
                <div class="export-tile" @click="downloadExport('task')"><div class="tile-icon">📋</div><div class="tile-label">{{ t('导出任务') }}</div></div>
                <div class="export-tile" @click="downloadReportExport"><div class="tile-icon">📄</div><div class="tile-label">{{ t('导出报告 PDF') }}</div></div>
              </div>
            </div>
          </template>

          <template v-if="page==='settings'">
            <div class="card">
              <div class="card-header">
                <div>
                  <h3>{{ t('settingsTitle') }}</h3>
                  <p class="hint">{{ t('languageShared') }}</p>
                </div>
              </div>
              <el-form label-width="160px" style="max-width:480px">
                <el-form-item :label="t('language')">
                  <el-select v-model="language" style="width:100%" @change="setLanguage">
                    <el-option v-for="item in LANGUAGE_OPTIONS" :key="item.code" :label="item.label" :value="item.code" />
                  </el-select>
                </el-form-item>
                <el-form-item :label="t('defaultGroupSize')"><el-input-number v-model="sysConfig.default_group_size" :min="3" :max="6" /></el-form-item>
                <el-form-item :label="t('adjustDays')"><el-input-number v-model="sysConfig.default_adjust_days" :min="1" :max="30" /></el-form-item>
                <el-button type="primary" @click="saveConfig">{{ t('save') }}</el-button>
              </el-form>
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
                <p class="profile-headline">{{ user?.headline || '课堂项目负责人 / 任课教师' }}</p>
                <p>{{ user?.bio || '完善管理员主页信息，便于区分不同任课老师或助教账号。' }}</p>
                <el-tag type="success">{{ t('管理员账号：') }} {{ user?.account }}</el-tag>
                <el-tag v-if="user?.availability">{{ user.availability }}</el-tag>
              </div>
            </div>
            <div class="profile-showcase">
              <div class="showcase-item"><b>{{ t('教学/研究方向') }}</b><span>{{ user?.research_interest || '填写课程主题、研究兴趣或负责班级' }}</span></div>
              <div class="showcase-item"><b>{{ t('课程主页') }}</b><a v-if="user?.portfolio_url" :href="user.portfolio_url" target="_blank">Course / Portfolio</a><span v-else>{{ t('未填写') }}</span></div>
              <div class="showcase-item"><b>{{ t('公开主页') }}</b><a v-if="user?.github_url" :href="user.github_url" target="_blank">GitHub / Lab</a><span v-else>{{ t('未填写') }}</span></div>
            </div>
            <div class="account-grid">
              <div class="card">
                <h3>{{ t('个人资料') }}</h3>
                <p class="hint">{{ t('头像支持图片链接；留空时显示姓名首字。') }}</p>
                <el-form label-position="top">
                  <el-form-item :label="t('姓名')"><el-input v-model="accountForm.name" maxlength="64" /></el-form-item>
                  <el-form-item :label="t('个人标题')"><el-input v-model="accountForm.headline" maxlength="120" :placeholder="t('如：AI 产品课程负责人 / 助教')" /></el-form-item>
                  <el-form-item :label="t('头像链接')"><el-input v-model="accountForm.avatar_url" placeholder="https://..." maxlength="512" /></el-form-item>
                  <el-form-item :label="t('个人介绍')"><el-input v-model="accountForm.bio" type="textarea" :rows="4" maxlength="240" show-word-limit :placeholder="t('如任课老师、助教、负责班级等')" /></el-form-item>
                  <el-form-item :label="t('教学/研究方向')"><el-input v-model="accountForm.research_interest" maxlength="240" :placeholder="t('如：智慧教育、项目制学习、AI 产品设计')" /></el-form-item>
                  <el-form-item :label="t('可联系时间')"><el-input v-model="accountForm.availability" maxlength="120" :placeholder="t('如：周二/周四答疑，24 小时内回复')" /></el-form-item>
                  <el-form-item :label="t('课程主页')"><el-input v-model="accountForm.portfolio_url" placeholder="https://..." maxlength="512" /></el-form-item>
                  <el-form-item :label="t('公开主页')"><el-input v-model="accountForm.github_url" placeholder="https://..." maxlength="512" /></el-form-item>
                  <el-form-item :label="t('主页主题')"><el-select v-model="accountForm.display_theme" style="width:100%"><el-option :label="t('Ocean 海蓝')" value="ocean" /><el-option :label="t('Aurora 极光')" value="aurora" /><el-option :label="t('Sunrise 晨光')" value="sunrise" /></el-select></el-form-item>
                  <el-button type="primary" :loading="loading" @click="saveAccount">{{ t('保存资料') }}</el-button>
                </el-form>
              </div>
              <div class="card">
                <h3>{{ t('账号安全') }}</h3>
                <p class="hint">{{ t('修改密码不会强制退出当前会话，下次登录请使用新密码。') }}</p>
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

      <el-drawer v-model="profileDrawerVisible" size="720px" :title="t('学员画像详情')">
        <template v-if="selectedUserRow?.profile">
          <div class="drawer-student-head">
            <div class="avatar">{{ userInitial(selectedUserRow.user?.name) }}</div>
            <div>
              <h3>{{ selectedUserRow.user?.name }}</h3>
              <p>{{ selectedUserRow.user?.account }} · {{ selectedUserRow.profile.major || selectedUserRow.profile.field || '专业待识别' }}</p>
            </div>
          </div>
          <div class="drawer-score-grid">
            <div v-for="k in ['knowledge','skill','collab']" :key="k" class="drawer-score-card">
              <span>{{ scoreLabel(k) }}</span>
              <strong :style="{color: scoreColor(k)}">{{ scoreVal(selectedUserRow.profile, k) }}</strong>
              <el-progress :percentage="scorePct(selectedUserRow.profile, k)" :color="scoreColor(k)" />
            </div>
          </div>
          <div class="detail-section">
            <h4>{{ t('评分来源拆解') }}</h4>
            <div class="breakdown-table">
              <div class="breakdown-head"><span>{{ t('维度') }}</span><span>{{ t('主动') }}</span><span>LLM</span><span>{{ t('被动') }}</span><span>{{ t('任务') }}</span><span>{{ t('规则') }}</span></div>
              <div class="breakdown-line" v-for="r in breakdownRows(selectedUserRow.profile)" :key="r.key">
                <span>{{ r.label }}</span><b>{{ r.active }}</b><b>{{ r.llm }}</b><b>{{ r.passive }}</b><b>{{ r.task }}</b><b>{{ r.rule }}</b>
              </div>
            </div>
          </div>
          <div class="detail-section">
            <h4>{{ t('标签证据') }}</h4>
            <p class="detail-label">{{ t('主动标签') }}</p>
            <span v-for="(t, idx) in safeList(selectedUserRow.profile.active_tags)" :key="tagName(t) || idx" class="ability-badge" :class="tagDimensionClass(t)"><b>{{ tagIcon(t) }}</b>{{ tagName(t) }}<small v-if="t.category"> · {{ t.category }}</small></span>
            <p class="detail-label">{{ t('被动标签') }}</p>
            <span v-for="(t, idx) in safeList(selectedUserRow.profile.passive_tags)" :key="tagName(t) || idx" class="ability-badge passive" :class="tagDimensionClass(t)"><b>{{ tagIcon(t) }}</b>{{ tagName(t) }}<small v-if="t.weight"> · {{ Math.round(t.weight*100) }}%</small></span>
          </div>
          <div class="detail-section">
            <h4>{{ t('结构化解析') }}</h4>
            <div class="parse-grid">
              <div><span>{{ t('学历') }}</span><b>{{ selectedUserRow.profile.degree || '—' }}</b></div>
              <div><span>{{ t('专业/方向') }}</span><b>{{ selectedUserRow.profile.major || selectedUserRow.profile.field || '—' }}</b></div>
              <div><span>{{ t('偏好角色') }}</span><b>{{ selectedUserRow.profile.pref_role || '—' }}</b></div>
              <div><span>{{ t('画像时间') }}</span><b>{{ selectedUserRow.profile.create_time || '—' }}</b></div>
            </div>
          </div>
          <div class="detail-section" v-if="selectedUserRow.profile.llm_analysis">
            <h4>{{ t('LLM 分析原始摘要') }}</h4>
            <pre class="json-preview">{{ formatJson(selectedUserRow.profile.llm_analysis) }}</pre>
          </div>
        </template>
        <el-empty v-else :description="t('暂无画像详情')" />
      </el-drawer>

      <el-dialog v-model="rulesVisible" :title="t('计算规则说明')" width="760px">
        <div class="rule-flow">
          <div class="rule-card"><strong>{{ t('1. 信息整理') }}</strong><p>{{ t('主动标签、自由描述、社区互动、聊天和任务表现会作为分组参考。') }}</p></div>
          <div class="rule-arrow">→</div>
          <div class="rule-card"><strong>{{ t('2. 三维评分') }}</strong><p>{{ t('知识、技能、协作分别按不同权重融合，最终归一化 0-10 分。') }}</p></div>
          <div class="rule-arrow">→</div>
          <div class="rule-card"><strong>{{ t('3. 分组/任务') }}</strong><p>{{ t('系统根据角色、标签、技能和工作量生成分组与任务建议。') }}</p></div>
        </div>
        <div class="formula-panel">
          <h4>{{ t('画像评分公式') }}</h4>
          <p><b>{{ t('知识') }}</b> {{ t('= 30%主动标签 + 30%LLM + 15%被动标签 + 15%任务表现 + 10%规则解析') }}</p>
          <p><b>{{ t('技能') }}</b> {{ t('= 35%主动标签 + 30%LLM + 15%被动标签 + 20%任务表现') }}</p>
          <p><b>{{ t('协作') }}</b> {{ t('= 25%主动标签 + 20%LLM + 30%被动标签 + 25%任务表现') }}</p>
        </div>
        <div class="formula-panel">
          <h4>{{ t('分组逻辑') }}</h4>
          <p>{{ t('系统先挑选每组核心成员，再逐步补充其他成员，参考技能差异、标签多样性、角色搭配和专业方向。若组间差距过大，会进行微调。') }}</p>
        </div>
        <div class="formula-panel">
          <h4>{{ t('任务分配逻辑') }}</h4>
          <p>{{ t('候选人匹配分 = 角色匹配 + 标签匹配 + 技能适配 - 当前工时负载。没有明显合适人选时，优先分给累计工时较少的成员。') }}</p>
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
    root.innerHTML = '<p>初始化失败: ' + e.message + '</p>'
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootApp)
else bootApp()
