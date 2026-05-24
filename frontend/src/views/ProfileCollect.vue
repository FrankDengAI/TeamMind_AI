<template>
  <div class="page">
    <h2>能力画像采集</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="文本录入" name="text">
        <el-select v-model="activeTags" multiple filterable placeholder="先选择主动标签" style="width:100%;margin-bottom:12px">
          <el-option-group v-for="(items, dim) in tagCatalog" :key="dim" :label="dim">
            <el-option v-for="t in items" :key="t.id" :label="t.name" :value="t.name" />
          </el-option-group>
        </el-select>
        <el-input v-model="rawText" type="textarea" :rows="8" placeholder="请用50-800字描述知识背景、技能与协作偏好..." maxlength="800" show-word-limit />
        <el-button type="primary" :loading="loading" @click="parseText" style="margin-top:12px">解析画像</el-button>
      </el-tab-pane>
      <el-tab-pane label="简历上传" name="resume">
        <el-upload drag :auto-upload="false" :limit="1" accept=".pdf,.docx,.doc" :on-change="onFileChange">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div>拖拽或点击上传 PDF / DOCX（≤10MB）</div>
        </el-upload>
        <el-button type="primary" :loading="loading" :disabled="!resumeFile" @click="parseResume" style="margin-top:12px">解析简历</el-button>
      </el-tab-pane>
    </el-tabs>

    <el-card v-if="profile" class="preview" shadow="hover">
      <template #header>
        <span>画像预览</span>
        <el-button type="success" size="small" @click="saveEdit">保存修正</el-button>
      </template>
      <el-form label-width="100px">
        <el-form-item label="身份"><el-input v-model="editForm.identity" /></el-form-item>
        <el-form-item label="学历"><el-input v-model="editForm.degree" /></el-form-item>
        <el-form-item label="专业"><el-input v-model="editForm.major" /></el-form-item>
        <el-form-item label="知识分"><el-slider v-model="editForm.knowledge_score" :min="1" :max="10" :step="0.1" /></el-form-item>
        <el-form-item label="技能分"><el-slider v-model="editForm.skill_score" :min="1" :max="10" :step="0.1" /></el-form-item>
        <el-form-item label="协作分"><el-slider v-model="editForm.collab_score" :min="1" :max="10" :step="0.1" /></el-form-item>
        <el-form-item label="偏好角色"><el-input v-model="editForm.pref_role" /></el-form-item>
        <el-form-item label="技术技能">
          <el-tag v-for="s in editForm.tech_skills" :key="s" style="margin:2px">{{ s }}</el-tag>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="history.length" class="history" header="历史画像">
      <el-table :data="history" size="small">
        <el-table-column prop="major" label="专业" />
        <el-table-column prop="skill_score" label="技能分" width="80" />
        <el-table-column prop="raw_source" label="来源" width="80" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="loadProfile(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const activeTab = ref('text')
const rawText = ref('')
const tagCatalog = ref({ knowledge: [], skill: [], collab: [] })
const activeTags = ref([])
const resumeFile = ref(null)
const loading = ref(false)
const profile = ref(null)
const history = ref([])
const editForm = ref({})

watch(profile, (p) => {
  if (p) editForm.value = { ...p, tech_skills: p.tech_skills || [] }
})

async function loadHistory() {
  const { data } = await http.get('/profile/history')
  history.value = data
}

async function loadTagCatalog() {
  const { data } = await http.get('/profile/tags/catalog')
  tagCatalog.value = data
}

async function parseText() {
  if (rawText.value.length < 50) return ElMessage.warning('至少输入50字')
  loading.value = true
  try {
    const { data } = await http.post('/profile/submit', {
      raw_text: rawText.value,
      active_tags: activeTags.value.map((name) => ({ name })),
    })
    profile.value = data.profile
    ElMessage.success('解析成功')
    loadHistory()
  } finally {
    loading.value = false
  }
}

function onFileChange(file) {
  resumeFile.value = file.raw
}

async function parseResume() {
  const fd = new FormData()
  fd.append('resume_file', resumeFile.value)
  loading.value = true
  try {
    const { data } = await http.post('/profile/resume', fd)
    profile.value = data.profile
    ElMessage.success('简历解析成功')
    loadHistory()
  } finally {
    loading.value = false
  }
}

function loadProfile(row) {
  profile.value = row
}

async function saveEdit() {
  await http.put(`/profile/${profile.value.id}`, editForm.value)
  ElMessage.success('已保存修正')
  loadHistory()
}

onMounted(() => {
  loadHistory()
  loadTagCatalog()
})
</script>

<style scoped>
.page { max-width: 900px; }
.preview { margin-top: 24px; }
.history { margin-top: 24px; }
</style>
