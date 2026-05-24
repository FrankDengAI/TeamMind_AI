<template>
  <div class="page">
    <h2>个人看板</h2>
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card header="协作画像">
          <template v-if="stats.profile">
            <p>知识 {{ stats.profile.knowledge_score }} · 技能 {{ stats.profile.skill_score }} · 协作 {{ stats.profile.collab_score }}</p>
            <el-tag>{{ stats.profile.pref_role }}</el-tag>
          </template>
          <p v-else>暂无画像，请先完成采集</p>
        </el-card>
        <el-card header="数据统计" style="margin-top:16px">
          <p>完成率 {{ stats.stats?.completion_rate }}%</p>
          <p>准时率 {{ stats.stats?.on_time_rate }}%</p>
          <p>活跃天数 {{ stats.stats?.active_days }}</p>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card header="我的任务">
          <el-table :data="stats.tasks || []">
            <el-table-column prop="task_name" label="任务" />
            <el-table-column prop="difficulty" label="难度" width="60" />
            <el-table-column label="进度" width="200">
              <template #default="{ row }">
                <el-slider v-model="row.progress" :max="100" @change="(v) => updateProgress(row.id, v)" />
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" />
          </el-table>
        </el-card>
        <div ref="chartRef" style="height:260px;margin-top:16px"></div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import http from '@/api/http'

const stats = ref({})
const chartRef = ref(null)
let chart = null
let timer = null

async function load() {
  const { data } = await http.get('/board/personal')
  stats.value = data
  renderChart()
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const tasks = stats.value.tasks || []
  chart.setOption({
    title: { text: '任务进度' },
    xAxis: { type: 'category', data: tasks.map((t) => t.task_name) },
    yAxis: { type: 'value', max: 100 },
    series: [{ type: 'bar', data: tasks.map((t) => t.progress), itemStyle: { color: '#e94560' } }],
  })
}

async function updateProgress(taskId, progress) {
  await http.post(`/task/${taskId}/progress`, { progress, submit_status: 'on_time' })
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
