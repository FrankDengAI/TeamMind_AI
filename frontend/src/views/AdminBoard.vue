<template>
  <div class="page">
    <h2>管理后台</h2>
    <el-row :gutter="16">
      <el-col :span="6"><el-statistic title="用户数" :value="overview.user_count" /></el-col>
      <el-col :span="6"><el-statistic title="画像数" :value="overview.profile_count" /></el-col>
      <el-col :span="6"><el-statistic title="小组数" :value="overview.group_count" /></el-col>
    </el-row>

    <el-card header="系统配置" style="margin-top:20px">
      <el-form inline>
        <el-form-item label="调优周期(天)"><el-input-number v-model="config.default_adjust_days" :min="3" :max="14" /></el-form-item>
        <el-form-item label="默认组人数"><el-input-number v-model="config.default_group_size" :min="3" :max="6" /></el-form-item>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </el-form>
    </el-card>

    <el-card header="数据导出" style="margin-top:20px">
      <el-button @click="exportData('profile')">导出画像</el-button>
      <el-button @click="exportData('group')">导出分组</el-button>
      <el-button @click="exportData('task')">导出任务</el-button>
      <el-button @click="exportReport">导出报告PDF</el-button>
    </el-card>

    <el-card header="用户列表" style="margin-top:20px">
      <el-table :data="users">
        <el-table-column label="姓名" prop="user.name" />
        <el-table-column label="账号" prop="user.account" />
        <el-table-column label="角色" prop="user.role" />
        <el-table-column label="画像" prop="has_profile">
          <template #default="{ row }">{{ row.has_profile ? '有' : '无' }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const overview = ref({ user_count: 0, profile_count: 0, group_count: 0 })
const users = ref([])
const config = ref({ default_adjust_days: 7, default_group_size: 4 })

async function load() {
  const [ov, us, cfg] = await Promise.all([
    http.get('/admin/overview'),
    http.get('/admin/users'),
    http.get('/admin/config'),
  ])
  overview.value = ov.data
  users.value = us.data
  config.value = { ...config.value, ...cfg.data }
}

async function saveConfig() {
  await http.put('/admin/config', config.value)
  ElMessage.success('配置已保存')
}

async function download(url, filename) {
  const { data, headers } = await http.get(url, { responseType: 'blob' })
  const blobUrl = URL.createObjectURL(new Blob([data], { type: headers['content-type'] || 'application/octet-stream' }))
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(blobUrl)
}

async function exportData(type) {
  await download(`/export/${type}?format=xlsx`, `${type}.xlsx`)
}

async function exportReport() {
  const gid = overview.value.groups?.[0]?.id
  if (gid) await download(`/export/report?format=pdf&group_id=${gid}`, `group-${gid}-report.pdf`)
  else ElMessage.warning('请先生成分组与报告')
}

onMounted(load)
</script>
