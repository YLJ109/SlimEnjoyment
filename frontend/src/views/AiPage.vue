<template>
  <div class="ai-page">
    <div class="ai-layout">
      <!-- ===== 会话栏 ===== -->
      <aside class="conv-panel" :class="{ open: convOpen }">
        <div class="conv-head">
          <button class="new-btn" @click="newSession">
            <AppIcon name="plus" :size="16" />
            <span>新建对话</span>
          </button>
        </div>

        <div class="conv-list">
          <div
            v-for="s in sessions"
            :key="s.id"
            class="conv-item"
            :class="{ active: s.id === activeId }"
            @click="selectSession(s.id)"
          >
            <span class="ci-ico"><AppIcon name="chat" :size="15" /></span>
            <div class="ci-main">
              <div class="ci-title ellipsis">{{ s.title }}</div>
              <div class="ci-meta">{{ relTime(s.updatedAt) }} · {{ s.messages.length }} 条</div>
            </div>
            <button class="ci-del" :aria-label="'删除 ' + s.title" @click.stop="removeSession(s.id)">
              <AppIcon name="trash" :size="14" />
            </button>
          </div>
          <div v-if="!sessions.length" class="conv-empty">暂无历史对话</div>
        </div>

        <div class="conv-foot">
          <button class="mem-btn" @click="memOpen = true">
            <AppIcon name="star" :size="15" />
            <span>长期记忆</span>
            <i class="mem-count num">{{ memories.length }}</i>
          </button>
        </div>
      </aside>
      <div class="conv-mask" v-if="convOpen" @click="convOpen = false" />

      <!-- ===== 对话区 ===== -->
      <section class="chat-area">
        <div class="chat" ref="chatBox">
          <div v-if="!messages.length" class="welcome">
            <div class="welcome-logo"><AppIcon name="ai" :size="30" /></div>
            <h3 class="welcome-title">你好，我是你的专属减脂助手</h3>
            <p class="sub">可以问我饮食、运动、平台期等问题</p>
            <div class="quick-q">
              <button v-for="q in quickQuestions" :key="q" class="q-btn" @click="send(q)">
                {{ q }}
              </button>
            </div>
          </div>

          <div
            v-for="(m, i) in messages"
            :key="activeId + '-' + i"
            class="msg"
            :class="m.role === 'user' ? 'right' : 'left'"
          >
            <div class="avatar" :class="m.role">
              <AppIcon :name="m.role === 'user' ? 'user' : 'ai'" :size="16" />
            </div>
            <div class="bubble" :class="{ 'bubble-md': m.role === 'assistant' }">
              <img v-if="m.image" :src="m.image" class="bubble-img" />
              <!-- 助手回复走 markdown 渲染；流式期间追加光标 -->
              <div
                v-if="m.role === 'assistant'"
                class="md-body"
                v-html="renderMarkdown(m.content)"
              />
              <span v-else class="text">{{ m.content }}</span>
              <span
                v-if="m.role === 'assistant' && streamingId === activeId && i === messages.length - 1 && thinking"
                class="caret"
              />
            </div>
          </div>

          <div v-if="thinking && !streaming" class="msg left">
            <div class="avatar ai"><AppIcon name="ai" :size="16" /></div>
            <div class="bubble typing">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-bar">
          <button
            class="img-btn hist-btn"
            :aria-label="convOpen ? '关闭历史' : '历史对话'"
            @click="convOpen = !convOpen"
          >
            <AppIcon name="clock" :size="19" />
          </button>
          <van-uploader :after-read="onImageRead" :max-count="1" :show-upload="false" accept="image/*">
            <button class="img-btn" aria-label="上传图片"><AppIcon name="camera" :size="20" /></button>
          </van-uploader>
          <button
            v-if="voiceSupported"
            class="img-btn voice-btn"
            :class="{ active: voiceActive }"
            :aria-label="voiceActive ? '松开停止' : '按住说话'"
            @mousedown.prevent="onMicDown"
            @mouseup="onMicUp"
            @mouseleave="onMicUp"
            @touchstart.prevent="onMicDown"
            @touchend.prevent="onMicUp"
          >
            <AppIcon name="mic" :size="20" />
          </button>
          <input
            class="chat-input"
            v-model="inputText"
            placeholder="输入你的问题...（按住麦克风说话）"
            @keyup.enter="send()"
          />
          <button class="send-btn" @click="send()" aria-label="发送">
            <AppIcon name="send" :size="18" />
          </button>
        </div>

        <!-- 语音聆听指示 -->
        <div class="voice-tip" v-if="voiceActive">
          <span class="vt-dot" />
          <span class="vt-label">正在聆听</span>
          <span class="vt-text">{{ liveTranscript || '请开始说话…' }}</span>
        </div>
      </section>
    </div>

    <!-- 记忆库 -->
    <van-popup v-model:show="memOpen" position="bottom" round>
      <div class="popup-wrap">
        <div class="popup-title">长期记忆</div>
        <p class="mem-tip">这些内容会跨会话保存，并在每次提问时自动提供给 AI 参考。</p>

        <div class="mem-list">
          <div v-for="(m, i) in memories" :key="i" class="mem-item">
            <span class="mem-text">{{ m }}</span>
            <button class="mem-del" aria-label="删除记忆" @click="delMemory(i)">
              <AppIcon name="trash" :size="14" />
            </button>
          </div>
          <div v-if="!memories.length" class="mem-empty">
            还没有记忆。例如添加：「我不吃香菜」「目标 75kg」「晚上 8 点后不进食」
          </div>
        </div>

        <div class="mem-add">
          <input
            v-model="memInput"
            class="mem-input"
            placeholder="添加一条记忆，回车保存"
            maxlength="120"
            @keyup.enter="addMemory"
          />
          <button class="mem-add-btn" @click="addMemory">添加</button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { aiChat, aiChatStream, recognizeFood } from '@/api/ai'
import { renderMarkdown } from '@/utils/markdown'
import { compressImage } from '@/utils/image'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ---------------- 未配置大模型 Key 的引导（B9） ----------------
 * 后端在未配置 Key 时返回 HTTP 400 + 业务 message。前端 axios 包装在非 200 时
 * reject 的是 axios error（业务文案在 e.response.data.message）；流式接口（fetch）
 * 则抛 new Error(message)。两种形态都要兼容。
 */
function aiErrMsg(e) {
  const r = e && e.response
  if (r && r.data && r.data.message) return r.data.message
  if (e && e.message) return e.message
  return ''
}
function isKeyMissing(e) {
  const m = String(aiErrMsg(e))
  return m.includes('未配置') && m.includes('Key')
}
function guideKeySetup() {
  showConfirmDialog({
    title: '尚未配置大模型 Key',
    message:
      'AI 功能需要先配置大模型 Key（国内大模型均可，如智谱 GLM）。是否前往「我的 → 大模型配置」填写？',
    confirmButtonText: '去配置',
    cancelButtonText: '稍后'
  })
    .then(() => router.push('/mine'))
    .catch(() => {})
}

/* ---------------- 会话存储（localStorage 持久化） ---------------- */
const STORE_KEY = 'jf_ai_sessions'
const ACTIVE_KEY = 'jf_ai_active'
const MEM_KEY = 'jf_ai_memories'

function loadSessions() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORE_KEY) || '[]')
    return Array.isArray(raw) ? raw.filter((s) => s && s.id) : []
  } catch (e) {
    return []
  }
}
function persist() {
  // blob: URL 无法跨会话持久化且会泄漏，落盘前剔除（仅保留 data URL 缩略图）
  const clean = sessions.value.slice(0, 50).map((s) => ({
    ...s,
    messages: s.messages.map((m) =>
      m.image && String(m.image).startsWith('blob:') ? { ...m, image: '' } : m
    )
  }))
  localStorage.setItem(STORE_KEY, JSON.stringify(clean))
}
function loadMemories() {
  try {
    const raw = JSON.parse(localStorage.getItem(MEM_KEY) || '[]')
    return Array.isArray(raw) ? raw.filter((x) => typeof x === 'string' && x.trim()) : []
  } catch (e) {
    return []
  }
}

const sessions = ref(loadSessions())
const activeId = ref(localStorage.getItem(ACTIVE_KEY) || '')
const memories = ref(loadMemories())
const memOpen = ref(false)
const memInput = ref('')
const convOpen = ref(false)

const current = computed(() => sessions.value.find((s) => s.id === activeId.value) || null)
const messages = computed(() => (current.value ? current.value.messages : []))

function ensureSession() {
  // activeId 有效 -> 直接用
  const cur = sessions.value.find((s) => s.id === activeId.value)
  if (cur) return cur
  // activeId 失效 -> 回退到最近一个会话
  if (sessions.value.length) {
    activeId.value = sessions.value[0].id
    localStorage.setItem(ACTIVE_KEY, activeId.value)
    return sessions.value[0]
  }
  // 完全没有 -> 新建并选中
  return createSession(true)
}
function createSession(select = true) {
  const s = {
    id: 's_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    title: '新对话',
    messages: [],
    updatedAt: Date.now()
  }
  sessions.value.unshift(s)
  if (select) activeId.value = s.id
  persist()
  localStorage.setItem(ACTIVE_KEY, activeId.value)
  return s
}
function newSession() {
  // 已有空白会话则直接复用，避免堆一排「新对话」
  const blank = sessions.value.find((s) => !s.messages.length)
  if (blank) {
    activeId.value = blank.id
  } else {
    createSession(true)
  }
  persist()
  localStorage.setItem(ACTIVE_KEY, activeId.value)
  convOpen.value = false
}
function selectSession(id) {
  activeId.value = id
  localStorage.setItem(ACTIVE_KEY, id)
  convOpen.value = false
  scrollToBottom()
}
function removeSession(id) {
  const idx = sessions.value.findIndex((s) => s.id === id)
  if (idx === -1) return
  sessions.value.splice(idx, 1)
  if (activeId.value === id) {
    activeId.value = sessions.value[0]?.id || ''
    if (!activeId.value) createSession(true)
  }
  persist()
  localStorage.setItem(ACTIVE_KEY, activeId.value)
  showToast({ message: '已删除对话' })
}
function touch(session) {
  session.updatedAt = Date.now()
  if (session.title === '新对话' && session.messages.length) {
    const first = session.messages.find((m) => m.role === 'user')
    if (first) session.title = first.content.slice(0, 14) || '新对话'
  }
  // 置顶最近使用的会话
  const idx = sessions.value.findIndex((s) => s.id === session.id)
  if (idx > 0) {
    const [it] = sessions.value.splice(idx, 1)
    sessions.value.unshift(it)
  }
  persist()
}

/* ---------------- 长期记忆 ---------------- */
function addMemory() {
  const v = memInput.value.trim()
  if (!v) return
  if (memories.value.length >= 20) {
    showToast({ message: '最多保存 20 条记忆' })
    return
  }
  memories.value.push(v.slice(0, 120))
  memInput.value = ''
  localStorage.setItem(MEM_KEY, JSON.stringify(memories.value))
  showToast({ type: 'success', message: '已保存' })
}
function delMemory(i) {
  memories.value.splice(i, 1)
  localStorage.setItem(MEM_KEY, JSON.stringify(memories.value))
}

/* ---------------- 相对时间 ---------------- */
function relTime(ts) {
  if (!ts) return ''
  const diff = Date.now() - ts
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return m + ' 分钟前'
  const h = Math.floor(m / 60)
  if (h < 24) return h + ' 小时前'
  const d = Math.floor(h / 24)
  if (d < 30) return d + ' 天前'
  return new Date(ts).toLocaleDateString('zh-CN')
}

/* ---------------- 发送 ---------------- */
const inputText = ref('')
const thinking = ref(false)
const streaming = ref(false)
const streamingId = ref('')
const chatBox = ref(null)

const quickQuestions = ['今天吃多了怎么办', '平台期怎么突破', '外卖怎么点', '零食推荐']

function scrollToBottom(force = true) {
  nextTick(() => {
    const el = chatBox.value
    if (!el) return
    // 用户手动往上翻时不强行拽回底部（流式输出尤其重要）
    if (!force && el.scrollHeight - el.scrollTop - el.clientHeight > 160) return
    el.scrollTop = el.scrollHeight
  })
}

async function send(text) {
  const content = (text != null ? text : inputText.value).trim()
  if (!content || thinking.value) return
  const session = ensureSession()
  session.messages.push({ role: 'user', content, ts: Date.now() })
  inputText.value = ''
  touch(session)
  scrollToBottom()

  thinking.value = true
  streaming.value = true
  streamingId.value = session.id
  try {
    const history = session.messages
      .filter((m) => !m.image)
      .map((m) => ({ role: m.role, content: m.content }))
    history.pop() // 去掉刚加入的 user 消息（后端会从 history 读取）

    // 先占位一条空回复，流式内容直接写进去，实现打字机效果
    const reply = { role: 'assistant', content: '', ts: Date.now() }
    session.messages.push(reply)

    let got = ''
    try {
      got = await aiChatStream(
        { message: content, history, memories: memories.value },
        (piece) => {
          reply.content += piece
          scrollToBottom(false)
        }
      )
    } catch (e) {
      // 无 Key 时非流式同样会失败，直接交给外层引导，避免多余请求
      if (isKeyMissing(e)) throw e
      // 流式失败 -> 回退到非流式一次性请求
      const res = await aiChat({ message: content, history, memories: memories.value })
      got = res.reply || ''
      reply.content = got
    }

    if (!reply.content) {
      reply.content = '抱歉，我暂时无法回答，请稍后再试。'
    }
  } catch (e) {
    if (isKeyMissing(e)) {
      guideKeySetup()
      session.messages.push({
        role: 'assistant',
        content:
          '尚未配置大模型 Key。请前往「我的 → 大模型配置」填写任一国内大模型 Key（如智谱 GLM）后再试。',
        ts: Date.now()
      })
    } else {
      session.messages.push({
        role: 'assistant',
        content: '抱歉，我暂时无法回答，请稍后再试。',
        ts: Date.now()
      })
    }
  } finally {
    thinking.value = false
    streaming.value = false
    streamingId.value = ''
    touch(session)
    scrollToBottom()
  }
}

async function onImageRead(file) {
  const item = file instanceof Array ? file[0] : file
  // 仅使用 Vant 提供的 base64 预览（data URL），避免 URL.createObjectURL
  // 存入 localStorage 后刷新裂图且无法释放的内存泄漏问题
  const imgUrl = item.content || ''
  const session = ensureSession()
  session.messages.push({
    role: 'user',
    content: '这张图片里的食物大概多少热量？',
    image: imgUrl,
    ts: Date.now()
  })
  touch(session)
  scrollToBottom()
  showLoadingToast({ message: '识别中...', forbidClick: true })
  thinking.value = true
  try {
    // 手机原图往往 >5MB 且可能是 HEIC/WebP，直接上传必被后端拒绝（400）。
    // 先在前端降采样+转 JPEG，再上传。
    const upload = await compressImage(item.file)
    const fd = new FormData()
    fd.append('file', upload)
    const res = await recognizeFood(fd)
    const list = res.food_list || []
    const names = list.map((f) => `${f.name} ${Math.round(f.calorie || 0)}kcal`).join('、')
    const reply = list.length
      ? `识别到：${names}。总计约 ${Math.round(res.total_calorie || 0)} kcal。建议搭配蔬菜与蛋白质，控制总热量在推荐范围内。`
      : '未能识别到食物，请换一张更清晰的照片或手动描述。'
    session.messages.push({ role: 'assistant', content: reply, ts: Date.now() })
  } catch (e) {
    if (isKeyMissing(e)) {
      guideKeySetup()
      session.messages.push({
        role: 'assistant',
        content:
          '尚未配置视觉理解模型的 Key。请前往「我的 → 大模型配置」填写（视觉能力可选智谱 GLM-4V）后再试。',
        ts: Date.now()
      })
    } else {
      // 透出后端的具体原因（如「图片大小不能超过 5MB」），避免只给一句无信息的兜底文案
      session.messages.push({
        role: 'assistant',
        content: aiErrMsg(e) || '图片识别失败，请重试或文字描述。',
        ts: Date.now()
      })
    }
  } finally {
    thinking.value = false
    closeToast()
    touch(session)
    scrollToBottom()
  }
}

watch(activeId, scrollToBottom)
onMounted(() => {
  ensureSession()
  scrollToBottom()
  initVoice()
})

onUnmounted(() => {
  // 离开页面时立即中止语音识别，避免麦克风常驻占用与定时器/监听器泄漏
  try {
    if (recognition) recognition.abort()
  } catch (e) {
    /* 已停止则忽略 */
  }
  recognition = null
})

/* ---------------- 语音输入（Web Speech API，浏览器内置，无需 Key） ----------------
 * 长按空格（输入聚焦时）或按住麦克风按钮说话，松开停止并填入输入框。
 */
const voiceSupported = ref(false)
const voiceActive = ref(false)
const liveTranscript = ref('')
let recognition = null
let recognizing = false

function initVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) {
    voiceSupported.value = false
    return
  }
  try {
    recognition = new SR()
    recognition.lang = 'zh-CN'
    recognition.continuous = true
    recognition.interimResults = true

    recognition.onresult = (e) => {
      let final = ''
      let interim = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript
        if (e.results[i].isFinal) final += t
        else interim += t
      }
      liveTranscript.value = (final + interim).trim()
    }
    recognition.onerror = (ev) => {
      const err = (ev && ev.error) || 'unknown'
      // no-speech / aborted 属正常交互，不提示
      if (err !== 'no-speech' && err !== 'aborted') {
        showToast({ type: 'fail', message: '语音识别失败：' + err })
      }
      cleanupVoice()
    }
    recognition.onend = () => {
      commitVoice()
      cleanupVoice()
    }
    voiceSupported.value = true
  } catch (e) {
    voiceSupported.value = false
  }
}

function commitVoice() {
  const t = (liveTranscript.value || '').trim()
  if (!t) return
  const prefix = inputText.value && inputText.value.trim() ? inputText.value.trim() + ' ' : ''
  inputText.value = prefix + t
  liveTranscript.value = ''
}

function cleanupVoice() {
  recognizing = false
  voiceActive.value = false
}

function startVoice() {
  if (!voiceSupported.value) {
    showToast({ message: '当前浏览器不支持语音输入，请使用 Chrome / Edge' })
    return
  }
  if (recognizing) return
  try {
    recognition.start()
    recognizing = true
    voiceActive.value = true
    liveTranscript.value = ''
  } catch (e) {
    // 已处于 started 状态时 start() 会抛错，忽略
    recognizing = false
    voiceActive.value = false
  }
}

function stopVoice() {
  if (!recognizing || !recognition) {
    cleanupVoice()
    return
  }
  try {
    recognition.stop() // 触发 onend -> commitVoice + cleanupVoice
  } catch (e) {
    commitVoice()
    cleanupVoice()
  }
}

function onMicDown() {
  startVoice()
}
function onMicUp() {
  stopVoice()
}
</script>

<style lang="less" scoped>
@import '../styles/variable.less';

.ai-page {
  // 壳层已改为「固定视口 + 内容区内部滚动」，这里直接撑满父容器即可，
  // 不再用 calc 硬算高度（硬算不准会在页面底部留出一条空隙）
  height: 100%;
  min-height: 420px;
}

.ai-layout {
  display: flex;
  height: 100%;
  min-height: 0;
  position: relative;
}

/* ---------------- 会话栏 ---------------- */
.conv-panel {
  width: 268px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  min-height: 0;
}

.conv-head {
  padding: 14px 12px 10px;
}

.new-btn {
  width: 100%;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: @font-display;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--on-lime);
  background: var(--lime);
  border: none;
  border-radius: @r-md;
  cursor: pointer;
  box-shadow: var(--glow-lime);
  transition: filter @dur-fast @ease-out, transform @dur-fast @ease-out;

  &:hover {
    filter: brightness(1.06);
    transform: translateY(-1px);
  }
}

.conv-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 4px 8px 10px;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--border-2);
    border-radius: 6px;
  }
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: @r-md;
  cursor: pointer;
  color: var(--text-2);
  transition: background @dur-fast @ease-out, color @dur-fast @ease-out;

  &:hover {
    background: var(--hover);
    .ci-del {
      opacity: 1;
    }
  }
  &.active {
    background: var(--lime-soft);
    color: var(--text-1);

    .ci-ico {
      color: var(--lime-ink);
    }
  }

  .ci-ico {
    flex-shrink: 0;
    display: flex;
    opacity: 0.75;
  }
  .ci-main {
    flex: 1;
    min-width: 0;
  }
  .ci-title {
    font-size: 13.5px;
    font-weight: 500;
    line-height: 1.3;
  }
  .ci-meta {
    font-family: @font-mono;
    font-size: 10.5px;
    color: var(--text-3);
    margin-top: 3px;
  }
  .ci-del {
    flex-shrink: 0;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    color: var(--text-3);
    border-radius: @r-sm;
    cursor: pointer;
    opacity: 0;
    transition: opacity @dur-fast @ease-out, color @dur-fast @ease-out;

    &:hover {
      color: var(--red);
      background: var(--red-soft);
    }
  }
}

.conv-empty {
  padding: 24px 12px;
  text-align: center;
  font-size: 12.5px;
  color: var(--text-3);
}

.conv-foot {
  padding: 10px 12px 12px;
  border-top: 1px solid var(--border);
}

.mem-btn {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  font-size: 13px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: @r-md;
  cursor: pointer;
  transition: color @dur-fast @ease-out, border-color @dur-fast @ease-out;

  &:hover {
    color: var(--lime-ink);
    border-color: var(--lime);
  }
  span {
    flex: 1;
    text-align: left;
  }
  .mem-count {
    font-style: normal;
    font-size: 11px;
    padding: 1px 7px;
    border-radius: 999px;
    background: var(--lime-soft);
    color: var(--lime-ink);
  }
}

.conv-mask {
  display: none;
}

/* ---------------- 对话区 ---------------- */
.chat-area {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

.chat {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 24px 26px;
  display: flex;
  flex-direction: column;

  > * {
    flex-shrink: 0;
  }
  &::-webkit-scrollbar {
    width: 8px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--border-2);
    border-radius: 8px;
  }
}

.welcome {
  text-align: center;
  margin: auto;
  max-width: 460px;
  padding: 8px 0;
  color: var(--text-3);

  .welcome-logo {
    width: 60px;
    height: 60px;
    margin: 0 auto 16px;
    border-radius: @r-lg;
    background: var(--lime);
    color: var(--on-lime);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--glow-lime);
  }
  .welcome-title {
    font-family: @font-display;
    font-size: 17px;
    font-weight: 700;
    color: var(--text-1);
    margin: 0 0 6px;
  }
  .sub {
    font-size: 13px;
    margin: 0;
  }
}

.quick-q {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 22px;

  .q-btn {
    font-size: 12.5px;
    padding: 7px 13px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    cursor: pointer;
    transition: color @dur-fast @ease-out, border-color @dur-fast @ease-out;

    &:hover {
      color: var(--lime-ink);
      border-color: var(--lime);
    }
  }
}

.msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 18px;
  width: 100%;

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: @r-sm;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.user {
      background: var(--surface-2);
      color: var(--text-2);
      border: 1px solid var(--border);
    }
    &.ai {
      background: var(--lime);
      color: var(--on-lime);
    }
  }

  .bubble {
    max-width: 76%;
    padding: 10px 14px;
    border-radius: @r-md;
    font-size: 14px;
    line-height: 1.65;
    word-break: break-word;
    white-space: pre-wrap;

    // markdown 渲染的回复：交回浏览器排版，不要再保留 pre-wrap
    &.bubble-md {
      white-space: normal;
    }

    .bubble-img {
      max-width: 100%;
      border-radius: @r-sm;
      display: block;
      margin-bottom: 8px;
    }
  }

  /* ---- markdown 内容排版 ---- */
  .md-body {
    > :first-child { margin-top: 0; }
    > :last-child { margin-bottom: 0; }

    p { margin: 0 0 8px; }
    h1, h2, h3, h4 {
      margin: 12px 0 6px;
      font-weight: 700;
      line-height: 1.35;
    }
    h1 { font-size: 17px; }
    h2 { font-size: 16px; }
    h3 { font-size: 15px; }
    h4 { font-size: 14px; }

    ul, ol { margin: 6px 0 8px; padding-left: 20px; }
    li { margin: 3px 0; }
    ul { list-style: disc; }
    ol { list-style: decimal; }

    strong { font-weight: 700; color: var(--lime-ink); }

    code {
      font-family: @font-mono;
      font-size: 12.5px;
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: 1px 5px;
    }
    pre {
      margin: 8px 0;
      padding: 10px 12px;
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: @r-sm;
      overflow-x: auto;
      code { background: none; border: none; padding: 0; }
    }

    blockquote {
      margin: 8px 0;
      padding: 2px 0 2px 10px;
      border-left: 3px solid var(--lime);
      color: var(--text-2);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0;
      font-size: 13px;
      th, td {
        border: 1px solid var(--border);
        padding: 5px 8px;
        text-align: left;
      }
      th { background: var(--surface-2); font-weight: 600; }
    }

    hr { border: none; border-top: 1px solid var(--border); margin: 12px 0; }
    a { color: var(--lime-ink); text-decoration: underline; }
  }

  /* 流式光标 */
  .caret {
    display: inline-block;
    width: 7px;
    height: 14px;
    margin-left: 2px;
    vertical-align: text-bottom;
    background: var(--lime);
    border-radius: 1px;
    animation: caret-blink 1s steps(2, start) infinite;
  }

  &.left .bubble {
    background: var(--surface);
    color: var(--text-1);
    border: 1px solid var(--border);
    border-top-left-radius: 3px;
  }
  &.right {
    flex-direction: row-reverse;
    .bubble {
      background: var(--lime);
      color: var(--on-lime);
      border-top-right-radius: 3px;
    }
  }
}

.typing {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-3);
    animation: blink 1.2s infinite;
    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}
@keyframes blink {
  0%,
  100% {
    opacity: 0.25;
  }
  50% {
    opacity: 1;
  }
}
@keyframes caret-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.1;
  }
}

/* ---------------- 输入区 ---------------- */
.input-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-top: 1px solid var(--border);
  background: var(--surface);

  .img-btn {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
    border: 1px solid var(--border);
    border-radius: @r-sm;
    background: var(--surface-2);
    color: var(--text-2);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: color @dur-fast @ease-out, border-color @dur-fast @ease-out;

    &:hover {
      color: var(--lime-ink);
      border-color: var(--lime);
    }
  }
  .voice-btn {
    &.active {
      color: var(--on-lime);
      background: var(--lime);
      border-color: var(--lime);
      animation: vt-pulse 1.2s ease-in-out infinite;
    }
  }
  .chat-input {
    flex: 1;
    height: 42px;
    padding: 0 14px;
    border-radius: @r-md;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    font-size: 14px;
    font-family: @font-body;
    outline: none;

    &::placeholder {
      color: var(--text-3);
    }
    &:focus {
      border-color: var(--lime);
    }
  }
  .send-btn {
    width: 44px;
    height: 42px;
    flex-shrink: 0;
    border: none;
    border-radius: @r-md;
    background: var(--lime);
    color: var(--on-lime);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: filter @dur-fast @ease-out, box-shadow @dur-fast @ease-out;

    &:hover {
      filter: brightness(1.06);
      box-shadow: var(--glow-lime);
    }
  }
}

/* 语音聆听指示条 */
.voice-tip {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 18px;
  border-top: 1px solid var(--border);
  background: var(--lime-soft);
  font-size: 12.5px;
  color: var(--lime-ink);

  .vt-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--lime);
    flex-shrink: 0;
    animation: vt-blink 1s steps(2, start) infinite;
  }
  .vt-label {
    font-weight: 600;
    flex-shrink: 0;
  }
  .vt-text {
    font-family: @font-body;
    color: var(--text-2);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
@keyframes vt-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(198, 242, 78, 0.45);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(198, 242, 78, 0);
  }
}
@keyframes vt-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.2;
  }
}

/* ---------------- 记忆库弹窗 ---------------- */
.popup-wrap {
  padding: 20px 20px 26px;

  .popup-title {
    font-family: @font-display;
    font-size: 16px;
    font-weight: 700;
    color: var(--text-1);
  }
}
.mem-tip {
  font-size: 12.5px;
  color: var(--text-3);
  margin: 6px 0 14px;
  line-height: 1.5;
}
.mem-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 40vh;
  overflow-y: auto;
}
.mem-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: @r-md;
  background: var(--surface-2);
  border: 1px solid var(--border);

  .mem-text {
    flex: 1;
    font-size: 13.5px;
    color: var(--text-1);
    line-height: 1.5;
  }
  .mem-del {
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    color: var(--text-3);
    border-radius: @r-sm;
    cursor: pointer;

    &:hover {
      color: var(--red);
      background: var(--red-soft);
    }
  }
}
.mem-empty {
  font-size: 12.5px;
  color: var(--text-3);
  padding: 14px 4px;
  line-height: 1.6;
}
.mem-add {
  display: flex;
  gap: 10px;
  margin-top: 14px;

  .mem-input {
    flex: 1;
    height: 42px;
    padding: 0 14px;
    border-radius: @r-md;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    font-size: 13.5px;
    outline: none;

    &::placeholder {
      color: var(--text-3);
    }
    &:focus {
      border-color: var(--lime);
    }
  }
  .mem-add-btn {
    height: 42px;
    padding: 0 20px;
    border: none;
    border-radius: @r-md;
    background: var(--lime);
    color: var(--on-lime);
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;

    &:hover {
      filter: brightness(1.06);
    }
  }
}

/* ---------------- 响应式 ---------------- */
@media (min-width: 1024px) {
  .ai-page {
    height: 100%;
  }
  .hist-btn {
    display: none; // 桌面会话栏常驻
  }
}

@media (max-width: 1023px) {
  .ai-page {
    height: 100%;
  }
  .conv-panel {
    position: fixed;
    top: 54px;
    bottom: calc(60px + env(safe-area-inset-bottom, 0px));
    left: 0;
    width: min(82vw, 300px);
    z-index: 40;
    transform: translateX(-100%);
    transition: transform @dur @ease-out;
    box-shadow: var(--shadow-3);
    border-right: 1px solid var(--border);

    &.open {
      transform: translateX(0);
    }
  }
  .conv-mask {
    display: block;
    position: fixed;
    inset: 54px 0 0 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
    z-index: 35;
  }
  .chat {
    padding: 18px 14px;
  }
  .msg {
    max-width: 100%;
  }
  .bubble {
    max-width: 82%;
  }
}
</style>
