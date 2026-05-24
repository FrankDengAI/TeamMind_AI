<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">组队超脑 <span class="logo-en">TeamMind AI</span></div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/profile"><el-icon><User /></el-icon>能力画像</el-menu-item>
        <el-menu-item index="/group"><el-icon><Connection /></el-icon>智能分组</el-menu-item>
        <el-menu-item index="/dashboard/personal"><el-icon><Tickets /></el-icon>个人看板</el-menu-item>
        <el-menu-item index="/dashboard/team"><el-icon><DataBoard /></el-icon>团队看板</el-menu-item>
        <el-menu-item v-if="user.isAdmin" index="/admin"><el-icon><Setting /></el-icon>管理后台</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ user.user?.name }}</span>
        <el-button type="danger" link @click="onLogout">退出</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

function onLogout() {
  user.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { min-height: 100vh; }
.aside { background: #1a1a2e; color: #fff; }
.logo { padding: 20px; font-weight: 700; font-size: 18px; color: #e94560; }
.logo-en { font-size: 12px; color: #9aa0b5; font-weight: 600; }
.aside :deep(.el-menu) { border: none; background: transparent; }
.header { display: flex; justify-content: flex-end; align-items: center; gap: 16px; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
</style>
