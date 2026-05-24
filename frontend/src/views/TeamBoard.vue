<template>
  <div class="page">
    <h2>团队看板</h2>
    <el-select v-model="groupId" placeholder="选择团队" style="width:240px;margin-bottom:16px" @change="load">
      <el-option v-for="b in boards" :key="b.group.id" :label="b.group.group_name" :value="b.group.id" />
    </el-select>
    <el-button @click="generateReport" type="primary">生成团队报告</el-button>

    <el-card v-if="current" header="全员进度">
      <el-row :gutter="12">
        <el-col v-for="m in current.members" :key="m.user?.id" :span="6">
          <el-card shadow="never" class="member-card">
            <p class="name">{{ m.user?.name }}</p>
            <el-progress :percentage="avgProgress(m.tasks)" />
            <el-tag size="small">{{ m.profile?.pref_role }}</el-tag>
          </el-card>
        </el-col>
      </el-row>
      <p style="margin-top:12px">团队完成率 {{ current.completion_rate }}%</p>
    </el-card>

    <el-card v-if="pendingAdjusts.length" header="待确认调优" style="margin-top:16px">
      <el-table :data="pendingAdjusts">
        <el-table-column prop="task_name" label="任务" />
        <el-table-column prop="reason" label="说明" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="confirmAdjust(row.id, true)">确认</el-button>
            <el-button size="small" @click="confirmAdjust(row.id, false)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div ref="teamChart" style="height:280px;margin-top:16px"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const boards = ref([])
const groupId = ref(null)
const teamChart = ref(null)
let chart = null
let timer = null

const current = computed(() => boards.value.find((b) => b.group.id === groupId.value))
const pendingAdjusts = computed(() => {
  if (!current.value) return []
  return (current.value.tasks || [])
    .filter((t) => t.pending_adjust)
    .map((t) => ({ id: t.id, task_name: t.task_name, reason: readPendingAdjust(t.pending_adjust).reason || '等待教师确认调优建议' }))
})

function readPendingAdjust(value) {
  if (!value) return {}
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch {
    return {}
  }
}

function avgProgress(tasks) {
  if (!tasks?.length) return 0
  return Math.round(tasks.reduce((s, t) => s + t.progress, 0) / tasks.length)
}

async function load() {
  const { data } = await http.get('/board/sync', { params: groupId.value ? { group_id: groupId.value } : {} })
  boards.value = data.boards
  if (!groupId.value && boards.value.length) groupId.value = boards.value[0].group.id
  renderChart()
}

function renderChart() {
  if (!teamChart.value || !current.value) return
  if (!chart) chart = echarts.init(teamChart.value)
  chart.setOption({
    title: { text: '成员贡献进度' },
    tooltip: {},
    xAxis: { type: 'category', data: current.value.members.map((m) => m.user?.name) },
    yAxis: { type: 'value', max: 100 },
    series: [{ type: 'bar', data: current.value.members.map((m) => avgProgress(m.tasks)) }],
  })
}

async function generateReport() {
  if (!groupId.value) return
  await http.post('/report/generate', { group_id: groupId.value })
  ElMessage.success('报告已生成')
}

async function confirmAdjust(taskId, accept) {
  await http.post(`/task/${taskId}/adjust/confirm`, { accept })
  ElMessage.success(accept ? '已应用调优' : '已拒绝')
  load()
}

onMounted(() => {
  load()
  timer = setInterval(load, 30000)
})
onUnmounted(() => {
  clearInterval(timer)
  chart?.dispose()
})
</script>

<style scoped>
.member-card { text-align: center; }
.name { font-weight: 600; margin-bottom: 8px; }
</style>
