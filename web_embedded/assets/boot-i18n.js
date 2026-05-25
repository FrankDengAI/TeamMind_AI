/**
 * 启动加载屏 i18n（在 Vue 挂载前根据 localStorage / URL 语言偏好切换文案）
 */
;(function () {
  function applyBootI18n() {
    if (typeof globalThis.teammindApplyBootInline === 'function') {
      globalThis.teammindApplyBootInline()
      return
    }
    if (!globalThis.TeamMindI18n?.applyBootScreenI18n) return
    const card = document.querySelector('.boot-card')
    const variant = card?.getAttribute('data-boot-variant') || 'student'
    globalThis.TeamMindI18n.applyBootScreenI18n(variant)
  }

  applyBootI18n()
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyBootI18n)
  }
})()
