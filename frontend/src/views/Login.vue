<template>
  <div class="login-page">
    <el-card class="card">
      <h1>组队超脑</h1>
      <p class="brand-en">TeamMind AI</p>
      <p class="sub">组队超脑：AI 智能组队与任务匹配协作平台</p>
      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form @submit.prevent="onLogin">
            <el-form-item label="账号"><el-input v-model="form.account" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
            <el-button type="primary" :loading="loading" @click="onLogin" style="width:100%">登录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form>
            <el-form-item label="姓名"><el-input v-model="reg.name" /></el-form-item>
            <el-form-item label="账号"><el-input v-model="reg.account" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="reg.password" type="password" show-password /></el-form-item>
            <el-button type="primary" :loading="loading" @click="onRegister" style="width:100%">注册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <p class="hint">测试账号 admin / admin123</p>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const user = useUserStore()
const tab = ref('login')
const loading = ref(false)
const form = ref({ account: '', password: '' })
const reg = ref({ name: '', account: '', password: '' })

async function onLogin() {
  loading.value = true
  try {
    await user.login(form.value.account, form.value.password)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function onRegister() {
  loading.value = true
  try {
    await user.register(reg.value)
    ElMessage.success('注册成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1a1a2e, #16213e); }
.card { width: 420px; padding: 8px; }
h1 { color: #e94560; margin-bottom: 4px; }
.brand-en { color: #9aa0b5; margin-bottom: 8px; font-size: 13px; letter-spacing: .04em; }
.sub { color: #666; margin-bottom: 20px; font-size: 14px; }
.hint { margin-top: 16px; font-size: 12px; color: #999; text-align: center; }
</style>
