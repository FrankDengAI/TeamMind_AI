<template>
  <div class="page">
    <h2>智能分组</h2>
    <el-card>
      <el-form inline>
        <el-form-item label="每组人数"><el-input-number v-model="groupSize" :min="3" :max="6" /></el-form-item>
        <el-form-item label="模式">
          <el-select v-model="mode"><el-option label="异构互补" value="heterogeneous" /><el-option label="技能聚焦" value="skill_focus" /></el-select>
        </el-form-item>
        <el-form-item label="任务模板">
          <el-select v-model="templateKey">
            <el-option v-for="(t,k) in templates" :key="k" :label="t.name" :value="k" />
          </el-select>
        </el-form-item>
        <el-button type="primary" :loading="loading" :disabled="!user.isAdmin" @click="createGroups">开始分组</el-button>
      </el-form>
      <p v-if="user.isAdmin" class="tip">管理员可对全部有画像用户分组，也可以在下方筛选指定成员。</p>
      <el-alert v-else title="普通用户不能创建分组，请等待教师发布组队活动。" type="info" :closable="false" style="margin-top:8px" />
      <el-select v-if="user.isAdmin" v-model="selectedIds" multiple filterable placeholder="不选择时默认使用全部有画像用户" style="width:100%;margin-top:8px">
        <el-option v-for="u in allUsers" :key="u.id" :label="`${u.name} (${u.id})`" :value="u.id" />
      </el-select>
    </el-card>

    <el-row :gutter="16" class="groups">
      <el-col v-for="g in groups" :key="g.id" :span="12">
        <el-card shadow="hover">
          <template #header>{{ g.group_name }} · 均衡 {{ g.balance_score }}</template>
          <p>成员 ID: {{ g.member_ids.join(', ') }}</p>
          <p>均分 知{{ g.avg_knowledge }} 技{{ g.avg_skill }} 协{{ g.avg_collab }}</p>
          <el-button size="small" :disabled="!user.isAdmin" @click="assignTasks(g.id)">分配任务</el-button>
          <el-button size="small" type="warning" :disabled="!user.isAdmin" @click="adjustTasks(g.id)">触发动态调优</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-alert v-if="validation" :title="validation.message" :type="validation.valid ? 'success' : 'warning'" style="margin-top:16px" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const groupSize = ref(4)
const mode = ref('heterogeneous')
const templateKey = ref('product_dev')
const loading = ref(false)
const groups = ref([])
const templates = ref({})
const selectedIds = ref([])
const allUsers = ref([])
const validation = ref(null)

async function loadGroups() {
  const { data } = await http.get('/group/list')
  groups.value = data
}

async function loadTemplates() {
  const { data } = await http.get('/task/templates')
  templates.value = data
}

async function createGroups() {
  if (!user.isAdmin) {
    ElMessage.warning('普通用户不能创建分组')
    return
  }
  loading.value = true
  try {
    let userIds = selectedIds.value
    if (!userIds.length) {
      const { data } = await http.get('/admin/users')
      userIds = data.filter((x) => x.has_profile).map((x) => x.user.id)
    }
    if (!userIds.length) return ElMessage.warning('无可用用户画像')
    const { data } = await http.post('/group/create', {
      user_ids: userIds,
      group_size: groupSize.value,
      config: { mode: mode.value },
    })
    groups.value = data.groups
    ElMessage.success(`已创建 ${data.groups.length} 个小组，均衡度 ${data.balance_score}`)
    loadGroups()
  } finally {
    loading.value = false
  }
}

async function assignTasks(groupId) {
  if (!user.isAdmin) return ElMessage.warning('普通用户不能分配任务')
  await http.post('/task/assign', { group_id: groupId, template_key: templateKey.value })
  ElMessage.success('任务已分配')
}

async function adjustTasks(groupId) {
  if (!user.isAdmin) return ElMessage.warning('普通用户不能触发调优')
  const { data } = await http.post('/task/adjust', { group_id: groupId })
  ElMessage.info(`生成 ${data.suggestions?.length || 0} 条调优建议`)
}

onMounted(() => {
  loadGroups()
  loadTemplates()
  if (user.isAdmin) {
    http.get('/admin/users').then(({ data }) => {
      allUsers.value = data.filter((x) => x.has_profile).map((x) => x.user)
    })
  }
})
</script>

<style scoped>
.groups { margin-top: 20px; }
.tip { font-size: 12px; color: #888; margin-top: 8px; }
</style>
