
<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const currentPage = ref('home')
const inputText = ref('')
const showResult = ref(false)
const isChecking = ref(false)
const historyList = ref([])
const reportTime = ref('')
const historyKeyword = ref('')
const reportCard = ref(null)
const activeHelp = ref('')

const conclusions = [
  {
    label: '确认属实',
    type: 'true',
    description: '现有可靠证据支持该信息，暂未发现足以推翻该信息的证据。'
  },
  {
    label: '确认不实',
    type: 'false',
    description: '现有可靠证据表明该信息存在错误，与事实或可靠资料不符。'
  },
  {
    label: '部分属实',
    type: 'partial',
    description: '信息中有真实内容，但部分描述不准确，或者缺少重要背景。'
  },
  {
    label: '暂无法核实',
    type: 'unknown',
    description: '目前缺乏足够可靠的证据，暂时无法判断信息的真实性。证据不足不代表信息一定是假的。'
  }
]

const currentConclusion = ref('unknown')

const filteredHistory = computed(() => {
  const keyword = historyKeyword.value.trim().toLowerCase()
  if (!keyword) return historyList.value

  return historyList.value.filter(item =>
    item.content.toLowerCase().includes(keyword)
  )
})

const formatConclusion = (type) => {
  return conclusions.find(item => item.type === type)?.label || '暂无法核实'
}

// 从浏览器本地读取历史记录
onMounted(() => {
  try {
    const savedHistory = localStorage.getItem('factlens-history')
    if (savedHistory) {
      const parsed = JSON.parse(savedHistory)
      if (Array.isArray(parsed)) {
        historyList.value = parsed
      }
    }
  } catch {
    ElMessage.error('历史记录读取失败')
  }
})

// 历史记录发生变化时自动保存
watch(
  historyList,
  (newList) => {
    try {
      localStorage.setItem('factlens-history', JSON.stringify(newList))
    } catch {
      ElMessage.error('历史记录保存失败，请检查浏览器存储空间')
    }
  },
  { deep: true }
)

// 开始核查
const checkInfo = async () => {
  if (isChecking.value) return

  if (!inputText.value.trim()) {
    ElMessage.warning('请先输入需要核查的信息')
    return
  }

  isChecking.value = true

  try {
    // 模拟核查过程，等待 1.5 秒
    await new Promise(resolve => setTimeout(resolve, 1500))

    currentConclusion.value = 'unknown'
    activeHelp.value = ''

    reportTime.value = new Date().toLocaleString('zh-CN')

    historyList.value.unshift({
      id: Date.now(),
      content: inputText.value.trim(),
      conclusion: '暂无法核实',
      time: reportTime.value
    })

    showResult.value = true
    currentPage.value = 'home'

    await nextTick()

    reportCard.value?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })

    ElMessage.success('演示核查完成')
  } catch (error) {
    console.error('核查过程发生错误：', error)
    ElMessage.error('核查过程中出现错误，请重试')
  } finally {
    isChecking.value = false
  }
}

const openHistory = async (item) => {
  inputText.value = item.content
  currentConclusion.value = 'unknown'
  reportTime.value = item.time
  activeHelp.value = ''
  showResult.value = true
  currentPage.value = 'home'

  await nextTick()
  reportCard.value?.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  })
}

const deleteHistory = (id) => {
  historyList.value = historyList.value.filter(item => item.id !== id)
  ElMessage.success('已删除这条记录')
}

const clearHistory = () => {
  if (historyList.value.length === 0) return

  if (confirm('确定要清空全部历史记录吗？此操作无法恢复。')) {
    historyList.value = []
    ElMessage.success('历史记录已清空')
  }
}

const clearInput = () => {
  inputText.value = ''
  ElMessage.success('输入内容已清空')
}

const toggleHelp = (type) => {
  activeHelp.value = activeHelp.value === type ? '' : type
}

// 生成可复制的报告文字
const reportText = computed(() => {
  const conclusion = formatConclusion(currentConclusion.value)

  return `FactLens 信息核查报告
核查时间：${reportTime.value}
核查结论：${conclusion}

一、核查内容
${inputText.value}

二、分析摘要
系统已接收该信息。目前展示的是前端演示结果，尚未连接真实 AI 分析和外部证据检索服务。

三、分析理由
正式版本将提取信息中的核心主张，并结合外部资料判断其真实性。在缺少充分证据的情况下，不会直接认定信息为真或假。

四、支持证据
当前暂无经过核实的支持证据。

五、反驳证据
当前暂无经过核实的反驳证据。

六、核查说明
本报告目前为模拟展示，不代表已经完成真实的信息核查。`
})

const copyReport = async () => {
  try {
    await navigator.clipboard.writeText(reportText.value)
    ElMessage.success('报告已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请检查浏览器剪贴板权限')
  }
}

const recheckInfo = () => {
  checkInfo()
}
</script>

<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">F</div>
        <span>FactLens</span>
      </div>

      <div class="nav-title">工作空间</div>

      <button class="nav-item" :class="{ active: currentPage === 'home' }" @click="currentPage = 'home'">
        <span class="nav-icon">⌂</span> 首页
      </button>

      <button class="nav-item" :class="{ active: currentPage === 'history' }" @click="currentPage = 'history'">
        <span class="nav-icon">◷</span> 历史记录
      </button>

      <button class="nav-item" :class="{ active: currentPage === 'about' }" @click="currentPage = 'about'">
        <span class="nav-icon">ⓘ</span> 项目介绍
      </button>

      <div class="sidebar-bottom">
        <div class="sidebar-note">
          <div class="note-title">FactLens</div>
          <div class="note-text">让真相，清晰一点。</div>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="breadcrumb">
          FactLens / {{ currentPage === 'home' ? '首页' : currentPage === 'history' ? '历史记录' : '项目介绍' }}
        </div>
        <div class="topbar-tag">信息核查系统</div>
      </header>

      <!-- 首页 -->
      <section v-if="currentPage === 'home'" class="page-content">
        <div class="welcome-section">
          <div class="eyebrow">AI INFORMATION CHECKING</div>
          <h1>让真相，清晰一点。</h1>
          <p>输入你想核查的信息，帮助你更理性地辨别网络信息。</p>
        </div>

        <div class="input-card">
          <div class="card-heading">
            <div>
              <h2>开始信息核查</h2>
              <p>输入一段你想核实的文字内容</p>
            </div>
            <span class="step-label">01 / INPUT</span>
          </div>

          <el-input
            v-model="inputText"
            type="textarea"
            :rows="6"
            maxlength="2000"
            show-word-limit
            resize="vertical"
            placeholder="例如：每天喝八杯水一定适合所有人……"
            class="fact-input"
            :disabled="isChecking"
          />

          <div class="input-footer">
            <span class="word-count">请尽量提供完整的信息</span>
            <div class="input-actions">
              <el-button
                class="clear-input-button"
                @click="clearInput"
                :disabled="isChecking"
              >
                清空内容
              </el-button>

              <el-button
                type="primary"
                class="primary-button"
                @click="checkInfo"
                :loading="isChecking"
                :disabled="isChecking"
              >
                {{ isChecking ? '正在核查…' : '开始核查 →' }}
              </el-button>
            </div>
          </div>

          <div class="input-tip">
            <span>ⓘ</span>
            请尽量提供完整的信息，以便后续进行分析。
          </div>
        </div>

        <!-- 核查结果 -->
        <div v-if="showResult" ref="reportCard" class="report-card">
          <div class="report-header">
            <div>
              <div class="eyebrow">CHECKING REPORT</div>
              <h2>核查报告</h2>
              <div class="report-time">核查时间：{{ reportTime }}</div>
            </div>

            <span class="result-status" :class="currentConclusion">
              {{ formatConclusion(currentConclusion) }}
            </span>
          </div>

          <!-- 四种结论说明 -->
          <div class="conclusion-guide">
            <button
              v-for="item in conclusions"
              :key="item.type"
              class="conclusion-option"
              :class="[item.type, { selected: currentConclusion === item.type, expanded: activeHelp === item.type }]"
              @click="toggleHelp(item.type)"
              :aria-expanded="activeHelp === item.type"
            >
              <span class="conclusion-dot"></span>
              {{ item.label }}
              <span class="help-mark">ⓘ</span>
            </button>
          </div>

          <div v-if="activeHelp" class="conclusion-explanation">
            <strong>{{ formatConclusion(activeHelp) }}</strong>
            <p>{{ conclusions.find(item => item.type === activeHelp).description }}</p>
          </div>

          <div class="report-section">
            <h3><span>01</span> 核查内容</h3>
            <div class="report-text">{{ inputText }}</div>
          </div>

          <div class="report-section">
            <h3><span>02</span> 分析摘要</h3>
            <p>
              系统已接收该信息。目前展示的是前端演示结果，
              尚未连接真实 AI 分析和外部证据检索服务。
            </p>
          </div>

          <div class="report-section">
            <h3><span>03</span> 分析理由</h3>
            <p>
              正式版本将提取信息中的核心主张，并结合外部资料判断其真实性。
              在缺少充分证据的情况下，不会直接认定信息为真或假。
            </p>
          </div>

          <div class="report-section">
            <h3><span>04</span> 支持证据</h3>
            <div class="evidence-box">
              <span class="evidence-label support">支持信息</span>
              <p>当前暂无经过核实的支持证据，正式版本将展示检索到的相关来源。</p>
            </div>
          </div>

          <div class="report-section">
            <h3><span>05</span> 反驳证据</h3>
            <div class="evidence-box">
              <span class="evidence-label oppose">反驳信息</span>
              <p>当前暂无经过核实的反驳证据，正式版本将展示相关反面资料。</p>
            </div>
          </div>

          <div class="report-section">
            <h3><span>06</span> 核查说明</h3>
            <p>
              本报告目前为模拟展示，不代表已经完成真实的信息核查。
              正式版本将结合权威机构、政府网站及其他可靠来源进行分析。
            </p>
          </div>

          <div class="report-notice">
            当前为前端演示版本，核查结论仅用于展示页面效果。
          </div>

          <div class="report-actions">
            <el-button class="copy-button" @click="copyReport">
              复制核查报告
            </el-button>
            <el-button
              type="primary"
              class="primary-button"
              @click="recheckInfo"
              :loading="isChecking"
              :disabled="isChecking"
            >
              {{ isChecking ? '正在核查…' : '重新核查 →' }}
            </el-button>
          </div>
        </div>

        <div v-else class="empty-hint">
          <div class="empty-icon">✳</div>
          <p>提交信息后，核查报告将在这里展示。</p>
        </div>
      </section>

      <!-- 历史记录 -->
      <section v-if="currentPage === 'history'" class="page-content">
        <div class="page-heading">
          <div>
            <div class="eyebrow">CHECKING HISTORY</div>
            <h1>历史记录</h1>
            <p>查看你之前提交过的信息。</p>
          </div>
          <el-button v-if="historyList.length > 0" class="clear-button" @click="clearHistory">
            清空记录
          </el-button>
        </div>

        <div class="history-summary">
          <span>共保存 <strong>{{ historyList.length }}</strong> 条核查记录</span>
        </div>

        <div v-if="historyList.length > 0" class="history-search">
          <el-input
            v-model="historyKeyword"
            clearable
            placeholder="搜索历史核查内容……"
          />
        </div>

        <div v-if="filteredHistory.length > 0" class="history-list">
          <div v-for="item in filteredHistory" :key="item.id" class="history-item">
            <div class="history-main" @click="openHistory(item)">
              <div class="history-title">{{ item.content }}</div>
              <div class="history-meta">
                <span>{{ item.time }}</span>
                <span class="history-status">{{ item.conclusion }}</span>
              </div>
            </div>
            <el-button class="delete-button" @click="deleteHistory(item.id)">删除</el-button>
          </div>
        </div>

        <div v-else-if="historyList.length > 0" class="empty-card">
          <div class="empty-icon">⌕</div>
          <h3>没有找到相关记录</h3>
          <p>试试更换关键词。</p>
          <el-button plain @click="historyKeyword = ''">清除搜索</el-button>
        </div>

        <div v-else class="empty-card">
          <div class="empty-icon">◷</div>
          <h3>暂时没有历史记录</h3>
          <p>完成一次信息核查后，记录会显示在这里。</p>
          <el-button type="primary" plain @click="currentPage = 'home'">去核查信息</el-button>
        </div>
      </section>

      <!-- 项目介绍 -->
      <section v-if="currentPage === 'about'" class="page-content">
        <div class="welcome-section">
          <div class="eyebrow">ABOUT FACTLENS</div>
          <h1>关于 FactLens</h1>
          <p>让信息核查更简单，让网络信息更加透明。</p>
        </div>

        <div class="about-card">
          <h2>项目简介</h2>
          <p>
            FactLens 是一个 AI 多领域谣言鉴别与信息核查系统。
            用户可以输入需要核查的网络信息，系统通过人工智能分析、
            外部证据检索等方式，对信息进行分析，并生成相应的核查报告，
            帮助用户提高信息辨别能力。
          </p>
        </div>

        <div class="about-card">
          <h2>核心功能</h2>
          <div class="feature-grid">
            <div class="feature-item">
              <div class="feature-icon">01</div>
              <h3>信息输入</h3>
              <p>支持用户输入需要核查的文字信息。</p>
            </div>
            <div class="feature-item">
              <div class="feature-icon">02</div>
              <h3>智能分析</h3>
              <p>提取信息中的核心主张，分析主要内容。</p>
            </div>
            <div class="feature-item">
              <div class="feature-icon">03</div>
              <h3>证据检索</h3>
              <p>从外部资料中寻找相关证据和信息来源。</p>
            </div>
            <div class="feature-item">
              <div class="feature-icon">04</div>
              <h3>报告生成</h3>
              <p>整理分析结果，生成清晰的核查报告。</p>
            </div>
          </div>
        </div>

        <div class="about-card">
          <h2>核查原则</h2>
          <div class="principle-list">
            <div class="principle-item">
              <span>01</span>
              <div>
                <h3>重视证据</h3>
                <p>判断信息时，应当结合可靠来源和实际证据。</p>
              </div>
            </div>
            <div class="principle-item">
              <span>02</span>
              <div>
                <h3>保持客观</h3>
                <p>不根据个人观点或片面信息直接下结论。</p>
              </div>
            </div>
            <div class="principle-item">
              <span>03</span>
              <div>
                <h3>谨慎判断</h3>
                <p>证据不足时，应当标记为暂无法核实。</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer class="footer">FactLens · 让真相，清晰一点。</footer>
    </main>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #f7f6f2;
  color: #34463d;
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
}

button,
textarea {
  font: inherit;
}

.app-container {
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  background: #344b40;
  color: white;
  padding: 30px 20px;
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 21px;
  font-weight: 700;
  margin-bottom: 55px;
  padding-left: 8px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 11px;
  background: #91aa99;
  color: #263c31;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 21px;
  font-weight: 800;
}

.nav-title {
  color: #a9b9ae;
  font-size: 12px;
  margin: 0 0 14px 10px;
  letter-spacing: 1px;
}

.nav-item {
  border: none;
  background: transparent;
  color: #d5ded8;
  width: 100%;
  padding: 14px 15px;
  border-radius: 10px;
  text-align: left;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 13px;
  font-size: 14px;
  cursor: pointer;
}

.nav-item:hover {
  background: #40594c;
}

.nav-item.active {
  background: #506b5c;
  color: white;
}

.nav-icon {
  font-size: 19px;
  width: 20px;
  text-align: center;
}

.sidebar-bottom {
  margin-top: auto;
}

.sidebar-note {
  border-top: 1px solid #53685c;
  padding: 22px 8px 5px;
}

.note-title {
  font-size: 13px;
  margin-bottom: 8px;
  color: #e5ece7;
}

.note-text {
  font-size: 12px;
  color: #aebdb3;
}

.main-content {
  margin-left: 240px;
  min-height: 100vh;
}

.topbar {
  height: 66px;
  padding: 0 48px;
  background: rgba(255, 255, 255, 0.75);
  border-bottom: 1px solid #eeede7;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.breadcrumb {
  color: #7c8981;
  font-size: 13px;
}

.topbar-tag {
  font-size: 12px;
  color: #688071;
  background: #edf2ed;
  padding: 7px 13px;
  border-radius: 20px;
}

.page-content {
  max-width: 1050px;
  padding: 48px;
  margin: 0 auto;
}

.welcome-section {
  margin-bottom: 35px;
}

.eyebrow {
  color: #829b89;
  font-size: 11px;
  letter-spacing: 2px;
  font-weight: 700;
  margin-bottom: 13px;
}

h1 {
  font-size: 30px;
  color: #344b40;
  margin: 0 0 13px;
  font-weight: 650;
}

.welcome-section p,
.page-heading p {
  color: #89938c;
  font-size: 14px;
  margin: 0;
  line-height: 1.8;
}

.input-card,
.report-card,
.about-card,
.empty-card {
  background: white;
  border: 1px solid #eeede8;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 5px 24px rgba(53, 70, 59, 0.035);
}

.card-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 22px;
}

.card-heading h2,
.report-header h2,
.about-card h2 {
  font-size: 18px;
  color: #344b40;
  margin: 0 0 8px;
}

.card-heading p {
  font-size: 13px;
  color: #929b94;
  margin: 0;
}

.step-label {
  font-size: 10px;
  letter-spacing: 1px;
  color: #9aaa9e;
}

.fact-input .el-textarea__inner {
  background: #fbfbf9;
  border: 1px solid #e7e9e3;
  border-radius: 11px;
  padding: 17px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.8;
  color: #3e5045;
  box-shadow: none;
}

.fact-input .el-textarea__inner:focus {
  border-color: #8ca694;
  box-shadow: 0 0 0 1px #8ca694;
}

.fact-input .el-input__count {
  background: transparent;
  color: #a1aaa3;
  font-size: 12px;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18px;
  gap: 12px;
}

.word-count {
  color: #a1aaa3;
  font-size: 12px;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-input-button.el-button {
  border-color: #e8e9e2;
  color: #77847a;
  background: white;
  border-radius: 9px;
  height: auto;
  padding: 12px 18px;
  font-size: 13px;
}

.primary-button.el-button {
  background: #557665;
  border-color: #557665;
  color: white;
  border-radius: 9px;
  padding: 12px 22px;
  height: auto;
  font-size: 13px;
}

.primary-button.el-button:hover {
  background: #405f4e;
  border-color: #405f4e;
}

.primary-button.el-button.is-loading {
  background: #718b7b;
  border-color: #718b7b;
  opacity: 0.85;
}

.input-tip {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0eb;
  color: #9aa39c;
  font-size: 12px;
}

.input-tip span {
  margin-right: 7px;
}

.report-card {
  margin-top: 25px;
  scroll-margin-top: 25px;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 23px;
  border-bottom: 1px solid #eeefe9;
  margin-bottom: 20px;
  gap: 12px;
}

.report-header h2 {
  font-size: 21px;
  margin: 0;
}

.report-time {
  color: #9aa39c;
  font-size: 12px;
  margin-top: 10px;
}

.result-status {
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.result-status.true,
.conclusion-option.true {
  color: #527d60;
  background: #eaf3eb;
}

.result-status.false,
.conclusion-option.false {
  color: #a45f59;
  background: #f8ecea;
}

.result-status.partial,
.conclusion-option.partial {
  color: #987b43;
  background: #f8f2e5;
}

.result-status.unknown,
.conclusion-option.unknown {
  color: #88784e;
  background: #f6f2e7;
}

.conclusion-guide {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}

.conclusion-option {
  border: 1px solid transparent;
  border-radius: 9px;
  padding: 11px 9px;
  font-size: 12px;
  text-align: center;
  opacity: 0.65;
  cursor: pointer;
  transition: all 0.2s;
}

.conclusion-option:hover,
.conclusion-option.expanded {
  opacity: 1;
  border-color: currentColor;
}

.conclusion-option.selected {
  opacity: 1;
  font-weight: 600;
}

.help-mark {
  margin-left: 3px;
  font-size: 11px;
}

.conclusion-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  margin-right: 5px;
  vertical-align: middle;
}

.conclusion-explanation {
  background: #f8faf7;
  border: 1px solid #e9eee8;
  border-radius: 9px;
  padding: 14px 16px;
  margin-bottom: 25px;
}

.conclusion-explanation strong {
  color: #506a59;
  font-size: 13px;
}

.conclusion-explanation p {
  color: #78857b;
  font-size: 12px;
  line-height: 1.8;
  margin: 7px 0 0;
}

.report-section {
  margin-bottom: 27px;
}

.report-section h3 {
  color: #3c5145;
  font-size: 15px;
  margin: 0 0 13px;
}

.report-section h3 span {
  color: #91a495;
  font-size: 12px;
  margin-right: 10px;
}

.report-section p,
.report-text {
  color: #77847a;
  font-size: 13px;
  line-height: 1.9;
  margin: 0;
}

.report-text {
  background: #f8f8f5;
  border-radius: 9px;
  padding: 14px 16px;
  color: #47594d;
  overflow-wrap: anywhere;
}

.evidence-box {
  background: #fafbf8;
  border: 1px solid #eef0e9;
  border-radius: 10px;
  padding: 15px;
}

.evidence-label {
  display: inline-block;
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 5px;
  margin-bottom: 10px;
}

.evidence-label.support {
  background: #eaf2eb;
  color: #66856e;
}

.evidence-label.oppose {
  background: #f6ece8;
  color: #a17b6c;
}

.report-notice {
  background: #f8f6ee;
  color: #9b8b66;
  border-radius: 8px;
  padding: 13px 15px;
  font-size: 12px;
  line-height: 1.7;
}

.report-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid #eeefe9;
}

.copy-button.el-button {
  border-color: #e4e9e2;
  color: #617768;
  background: white;
  border-radius: 9px;
  height: auto;
  padding: 12px 20px;
  font-size: 13px;
}

.empty-hint {
  text-align: center;
  padding: 45px 20px;
  color: #a0aaa2;
  font-size: 13px;
}

.empty-icon {
  color: #9bad9f;
  font-size: 29px;
  margin-bottom: 12px;
}

.empty-hint p {
  margin: 0;
}

.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.clear-button.el-button {
  background: white;
  border-color: #e8e9e2;
  color: #8c7770;
}

.clear-button.el-button:hover,
.delete-button.el-button:hover {
  background: #f8efeb;
  border-color: #e8d8d0;
  color: #a27d70;
}

.history-summary {
  color: #89938c;
  font-size: 13px;
  margin-bottom: 15px;
}

.history-summary strong {
  color: #557665;
  font-size: 16px;
  margin: 0 3px;
}

.history-search {
  margin-bottom: 18px;
  max-width: 450px;
}

.history-search .el-input__wrapper {
  border-radius: 9px;
  box-shadow: 0 0 0 1px #e8e9e2 inset;
  padding: 4px 12px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 15px;
  background: white;
  border: 1px solid #eeede8;
  border-radius: 12px;
  padding: 20px;
}

.history-main {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.history-main:hover .history-title {
  color: #668673;
}

.history-title {
  color: #43564a;
  font-size: 14px;
  margin-bottom: 12px;
  overflow-wrap: anywhere;
}

.history-meta {
  display: flex;
  gap: 15px;
  align-items: center;
  color: #a1aaa3;
  font-size: 11px;
  flex-wrap: wrap;
}

.history-status {
  color: #927d51;
  background: #f7f2e7;
  padding: 4px 8px;
  border-radius: 5px;
}

.delete-button.el-button {
  border-color: #eee7e2;
  color: #a27d70;
  background: white;
}

.empty-card {
  text-align: center;
  padding: 65px 20px;
}

.empty-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: #536458;
  margin: 0 0 10px;
}

.empty-card p {
  color: #9ba49d;
  font-size: 13px;
  margin-bottom: 22px;
}

.about-card {
  margin-bottom: 20px;
}

.about-card h2 {
  margin-bottom: 20px;
}

.about-card > p {
  color: #78857b;
  font-size: 13px;
  line-height: 2;
  margin: 0;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.feature-item {
  background: #f9faf7;
  border: 1px solid #eff0e9;
  padding: 20px;
  border-radius: 11px;
}

.feature-icon {
  color: #8da493;
  font-size: 12px;
  letter-spacing: 1px;
  margin-bottom: 13px;
}

.feature-item h3,
.principle-item h3 {
  color: #43574a;
  font-size: 14px;
  margin: 0 0 9px;
}

.feature-item p,
.principle-item p {
  color: #929c94;
  font-size: 12px;
  line-height: 1.8;
  margin: 0;
}

.principle-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.principle-item {
  display: flex;
  gap: 17px;
  align-items: flex-start;
}

.principle-item > span {
  color: #91a494;
  font-size: 12px;
  padding-top: 2px;
}

.footer {
  text-align: center;
  color: #aab1aa;
  font-size: 11px;
  padding: 25px 20px 35px;
}

@media (max-width: 800px) {
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
    padding: 15px;
  }

  .logo {
    margin-bottom: 15px;
  }

  .nav-title,
  .sidebar-bottom {
    display: none;
  }

  .nav-item {
    display: inline-flex;
    width: auto;
    margin: 0 5px 0 0;
    padding: 9px 12px;
  }

  .main-content {
    margin-left: 0;
  }

  .topbar {
    padding: 0 20px;
  }

  .page-content {
    padding: 28px 18px;
  }

  h1 {
    font-size: 24px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .conclusion-guide {
    grid-template-columns: repeat(2, 1fr);
  }

  .input-card,
  .report-card,
  .about-card {
    padding: 20px;
  }

  .input-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .input-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .report-header {
    align-items: flex-start;
  }

  .report-actions {
    flex-wrap: wrap;
  }
}
</style>
