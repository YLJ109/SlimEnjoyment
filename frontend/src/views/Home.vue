<template>
  <div class="page home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-main">
        <span class="eyebrow">今日概览 / OVERVIEW</span>
        <h2 class="hero-greet">{{ greeting }}，{{ nickname }}</h2>
        <div class="hero-sub num">{{ todayStr }}</div>
      </div>
      <div class="hero-stats">
        <div class="hs">
          <span class="hs-k">连续打卡</span>
          <div class="hs-v"><b class="num">{{ checkinDays }}</b><span class="hs-u">天</span></div>
        </div>
        <div class="hs">
          <span class="hs-k">推荐摄入</span>
          <div class="hs-v"><b class="num">{{ recommend }}</b><span class="hs-u">kcal</span></div>
        </div>
        <div class="hs">
          <span class="hs-k">已摄入</span>
          <div class="hs-v"><b class="num">{{ todayData.total_calorie }}</b><span class="hs-u">kcal</span></div>
        </div>
      </div>
    </section>

    <div class="dash">
      <!-- 左列 -->
      <div class="col stagger">
        <!-- 能量 -->
        <section class="card card--edge energy">
          <div class="card-head">
            <span class="eyebrow">能量 / ENERGY</span>
            <span class="head-note num">{{ todayData.total_calorie }} / {{ recommend }}</span>
          </div>
          <CalorieCard :intake="todayData.total_calorie" :recommend="recommend" />
          <div class="macros">
            <div class="macro" v-for="n in nutri" :key="n.key">
              <div class="m-top">
                <span class="m-label">{{ n.label }}</span>
                <span class="m-val num">{{ n.cur }}<i>/{{ n.target }}g</i></span>
              </div>
              <div class="m-track">
                <span class="m-fill" :style="{ width: n.percent + '%', background: n.color }" />
              </div>
            </div>
          </div>
        </section>

        <!-- 快捷入口 -->
        <section class="card card--edge quick">
          <div class="card-head"><span class="eyebrow">快捷 / QUICK</span></div>
          <div class="quick-grid">
            <button class="qtile" v-for="q in quickList" :key="q.key" @click="q.action">
              <span class="qtile-ico" :style="{ color: q.color, background: q.bg }">
                <AppIcon :name="q.icon" :size="20" />
              </span>
              <span class="qtile-label">{{ q.label }}</span>
            </button>
          </div>
        </section>
      </div>

      <!-- 右列 -->
      <div class="col stagger">
        <!-- AI 食谱 -->
        <section class="card card--edge plan">
          <div class="card-head">
            <span class="eyebrow">今日 AI 食谱 / MEAL PLAN</span>
            <button class="ghost" @click="regeneratePlan">
              <AppIcon name="refresh" :size="14" /> 重新生成
            </button>
          </div>

          <div v-if="planLoading" class="plan-loading">
            <van-loading size="18px" color="var(--lime)" />
            <span>AI 正在为你定制专属食谱…</span>
          </div>
          <div v-else-if="!hasPlan" class="plan-empty">
            <span class="pe-ico"><AppIcon name="bolt" :size="20" /></span>
            <p class="pe-title">还没有今日食谱</p>
            <p class="pe-sub">让 AI 根据你的目标热量生成一日三餐</p>
            <button class="pe-btn" @click="regeneratePlan">立即生成</button>
          </div>
          <template v-else>
            <div class="meal" v-for="m in mealList" :key="m.type">
              <div class="meal-head">
                <span class="meal-name"><i class="m-dot" :class="m.type" />{{ m.label }}</span>
                <span class="meal-cal num">{{ m.total }} kcal</span>
              </div>
              <div class="meal-items">
                <button
                  class="meal-item"
                  v-for="(it, i) in m.items"
                  :key="i"
                  @click="showMealDetail(m.type, it)"
                >
                  <span class="it-name ellipsis">{{ it.name }}</span>
                  <span class="it-cal num">{{ it.calorie }} kcal</span>
                </button>
                <div v-if="!m.items.length" class="meal-empty">暂无菜品</div>
              </div>
            </div>
            <div class="adapt" v-if="plan.adapt_desc">
              <AppIcon name="bolt" :size="15" />
              <span>{{ plan.adapt_desc }}</span>
            </div>
          </template>
        </section>
      </div>
    </div>

    <!-- 数据统计（并入首页，替代原底部「统计」Tab；桌面端仍可从侧栏进入独立页） -->
    <section class="card card--edge home-stats">
      <div class="hs-head">
        <span class="eyebrow">数据统计 / STATS</span>
        <button class="hs-link" @click="router.push('/stats')">完整报告 →</button>
      </div>
      <StatsPanel />
    </section>

    <!-- 记录体重弹窗 -->
    <van-popup v-model:show="showWeight" position="bottom" round>
      <div class="popup-wrap">
        <div class="popup-title">记录今日体重</div>
        <van-field v-model="weightInput" type="digit" label="体重" placeholder="kg" :border="false" />
        <van-button type="primary" block round @click="saveWeight">保存</van-button>
      </div>
    </van-popup>

    <!-- 喝水弹窗 -->
    <van-popup v-model:show="showWater" position="bottom" round>
      <div class="popup-wrap">
        <div class="popup-title">今日饮水</div>
        <div class="water-info">
          <span class="cur num">{{ waterToday.total_amount }}</span>
          <span class="target num">/ {{ waterToday.target_amount }} ml</span>
        </div>
        <van-progress :percentage="waterPercent" color="var(--cyan)" :show-pivot="false" class="water-bar" />
        <div class="water-btns">
          <van-button round type="primary" @click="submitWater(200)">+200ml</van-button>
          <van-button round plain type="primary" @click="submitWater(500)">+500ml</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 食谱详情 -->
    <van-popup v-model:show="showMeal" position="bottom" round>
      <div class="popup-wrap" v-if="currentMeal">
        <div class="popup-title">{{ mealLabelOf(currentMeal.type) }} · {{ currentMeal.item.name }}</div>
        <div class="meal-detail">
          <div class="detail-row"><span>重量</span><b class="num">{{ currentMeal.item.weight }} g</b></div>
          <div class="detail-row"><span>热量</span><b class="num">{{ currentMeal.item.calorie }} kcal</b></div>
          <div class="detail-row"><span>做法</span><b>{{ currentMeal.item.practice || '—' }}</b></div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import CalorieCard from '@/components/CalorieCard.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useUserStore } from '@/store/modules/user'
import { todayDiet } from '@/api/diet'
import { getMetrics, getCheckin } from '@/api/auth'
import { generatePlan, getPlan } from '@/api/ai'
import { addWeight } from '@/api/weight'
import { addWater, todayWater } from '@/api/water'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { formatDate, today, weekdayCN } from '@/utils/format'
import { MEAL_TYPE_MAP } from '@/utils/common'

const router = useRouter()
const userStore = useUserStore()

const nickname = computed(() => userStore.userInfo?.username || '瘦友')
// 连续打卡天数：一律来自后端 user_checkin 表，未取到就是 0，不做任何本地伪造
const checkinDays = ref(0)
const checkinTotal = ref(0)

const nowHour = new Date().getHours()
const greeting = computed(() => {
  if (nowHour < 6) return '夜深了'
  if (nowHour < 11) return '早上好'
  if (nowHour < 14) return '中午好'
  if (nowHour < 18) return '下午好'
  return '晚上好'
})
const todayStr = computed(() => formatDate(new Date()) + ' ' + weekdayCN(new Date()))

const todayData = reactive({
  total_calorie: 0,
  total_protein: 0,
  total_fat: 0,
  total_carbohydrate: 0
})
const recommend = ref(0)

// 营养素进度
const nutri = computed(() => {
  const rec = recommend.value || 1500
  const targets = {
    protein: Math.round((rec * 0.25) / 4),
    fat: Math.round((rec * 0.25) / 9),
    carbohydrate: Math.round((rec * 0.5) / 4)
  }
  const make = (key, label, color, cur) => {
    const target = targets[key] || 1
    const percent = Math.min(Math.round((cur / target) * 100), 100)
    return { key, label, color, cur: Math.round(cur || 0), target, percent }
  }
  return [
    make('protein', '蛋白质', 'var(--lime)', todayData.total_protein),
    make('fat', '脂肪', 'var(--orange)', todayData.total_fat),
    make('carbohydrate', '碳水', 'var(--cyan)', todayData.total_carbohydrate)
  ]
})

// AI 食谱
const plan = reactive({ breakfast: [], lunch: [], dinner: [], total_calorie: 0, adapt_desc: '' })
const planLoading = ref(false)
const mealList = computed(() => [
  { type: 'breakfast', label: MEAL_TYPE_MAP.breakfast, items: plan.breakfast, total: sumCal(plan.breakfast) },
  { type: 'lunch', label: MEAL_TYPE_MAP.lunch, items: plan.lunch, total: sumCal(plan.lunch) },
  { type: 'dinner', label: MEAL_TYPE_MAP.dinner, items: plan.dinner, total: sumCal(plan.dinner) }
])
function sumCal(arr) {
  return (arr || []).reduce((s, x) => s + Number(x.calorie || 0), 0)
}
const hasPlan = computed(
  () => plan.breakfast.length > 0 || plan.lunch.length > 0 || plan.dinner.length > 0
)

const quickList = [
  { key: 'diet', label: '记录饮食', icon: 'diet', color: 'var(--lime-ink)', bg: 'var(--lime-soft)', action: () => router.push('/diet') },
  { key: 'weight', label: '记录体重', icon: 'target', color: 'var(--lime-ink)', bg: 'var(--lime-soft)', action: () => (showWeight.value = true) },
  { key: 'exercise', label: '运动', icon: 'fire', color: 'var(--orange)', bg: 'var(--orange-soft)', action: () => router.push('/exercise') },
  { key: 'water', label: '喝水', icon: 'drop', color: 'var(--cyan)', bg: 'var(--cyan-soft)', action: () => openWater() }
]

const showWeight = ref(false)
const weightInput = ref('')
const showWater = ref(false)
const waterToday = reactive({ total_amount: 0, target_amount: 2000, date: '' })
const waterPercent = computed(() =>
  waterToday.target_amount ? Math.min(Math.round((waterToday.total_amount / waterToday.target_amount) * 100), 100) : 0
)

const showMeal = ref(false)
const currentMeal = ref(null)
function showMealDetail(type, item) {
  currentMeal.value = { type, item }
  showMeal.value = true
}
function mealLabelOf(type) {
  return MEAL_TYPE_MAP[type] || type
}

async function fetchToday() {
  try {
    const res = await todayDiet({ date: today() })
    Object.assign(todayData, res)
  } catch (e) {}
}
async function fetchMetrics() {
  try {
    const res = await getMetrics()
    recommend.value = res.recommend_calorie
  } catch (e) {}
}
async function fetchPlan() {
  planLoading.value = true
  try {
    // 1) 先读已保存的当日食谱（快，不触发 AI）
    const saved = await getPlan({ date: today() })
    if (saved && saved.plan) {
      applyPlan(saved.plan)
      return
    }
    // 2) 当天还没有食谱 -> 生成一份（首次约 30~40s，后端失败会自动降级）
    const res = await generatePlan({ date: today() })
    applyPlan(res.plan)
  } catch (e) {
    // 容错：保持空态，页面提供「立即生成」入口
  } finally {
    planLoading.value = false
  }
}
function applyPlan(p) {
  plan.breakfast = p.breakfast || []
  plan.lunch = p.lunch || []
  plan.dinner = p.dinner || []
  plan.total_calorie = p.total_calorie || 0
  plan.adapt_desc = p.adapt_desc || ''
}
async function regeneratePlan() {
  showLoadingToast({ message: 'AI 正在定制食谱…', forbidClick: true, duration: 0 })
  let ok = false
  try {
    const res = await generatePlan({ date: today() })
    applyPlan(res.plan)
    ok = true
  } catch (e) {
    ok = false
  } finally {
    closeToast()
  }
  showToast({ type: ok ? 'success' : 'fail', message: ok ? '已更新食谱' : '生成失败，请稍后重试' })
}

async function saveWeight() {
  if (!weightInput.value) {
    showToast('请输入体重')
    return
  }
  try {
    await addWeight({ record_date: today(), weight: Number(weightInput.value) })
    showToast({ type: 'success', message: '已记录' })
    showWeight.value = false
  } catch (e) {}
}

async function openWater() {
  showWater.value = true
  try {
    const res = await todayWater({ date: today() })
    Object.assign(waterToday, res)
  } catch (e) {}
}
async function submitWater(amount) {
  try {
    const res = await addWater({ record_date: today(), amount })
    waterToday.total_amount = res.total_amount
    waterToday.target_amount = res.target_amount
    showToast({ type: 'success', message: '已添加 ' + amount + 'ml' })
  } catch (e) {}
}

function goMine() {
  router.push('/mine')
}

// 拉取真实打卡数据（服务端在记录饮食/饮水/体重/运动时自动打卡）
async function fetchCheckin() {
  try {
    const res = await getCheckin()
    if (res) {
      checkinDays.value = Number(res.continuous_days) || 0
      checkinTotal.value = Number(res.total_days) || 0
    }
  } catch (e) {
    checkinDays.value = 0
    checkinTotal.value = 0
  }
}

onMounted(() => {
  fetchToday()
  fetchMetrics()
  fetchPlan()
  fetchCheckin()
})
// 记录饮食/饮水/体重后服务端会自动打卡 -> 这几个动作完成后刷新连续天数
watch(
  () => [todayData.total_calorie, waterToday.total_amount],
  () => fetchCheckin()
)
</script>

<style lang="less" scoped>
@import '../styles/variable.less';

.page.home {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

// ---------- Hero ----------
.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  padding: 4px 2px 2px;
}
.hero-main {
  .hero-greet {
    font-family: @font-display;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.1;
    margin: 10px 0 4px;
    letter-spacing: -0.01em;
  }
  .hero-sub {
    font-size: 13px;
    color: var(--text-3);
    letter-spacing: 0.04em;
  }
}
.hero-stats {
  display: flex;
  gap: 10px;
}
.hs {
  min-width: 104px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: @r-md;

  .hs-k {
    font-size: 11px;
    color: var(--text-3);
    letter-spacing: 0.04em;
  }
  .hs-v {
    margin-top: 4px;
    display: flex;
    align-items: baseline;
    gap: 4px;
    b {
      font-size: 22px;
      font-weight: 800;
      color: var(--text-1);
      line-height: 1;
    }
    .hs-u {
      font-size: 11px;
      color: var(--text-3);
    }
  }
}

// ---------- 仪表盘网格 ----------
.dash {
  display: grid;
  grid-template-columns: 1.08fr 1fr;
  gap: 18px;
  align-items: start;
}
.col {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;

  .head-note {
    font-size: 12px;
    color: var(--text-3);
  }
}

// 能量
.energy {
  .macros {
    margin-top: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .macro {
    .m-top {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 6px;
      .m-label {
        font-size: 12.5px;
        color: var(--text-2);
      }
      .m-val {
        font-size: 12.5px;
        color: var(--text-1);
        font-weight: 600;
        i {
          color: var(--text-3);
          font-style: normal;
          font-weight: 400;
        }
      }
    }
    .m-track {
      height: 7px;
      border-radius: 999px;
      background: var(--surface-2);
      overflow: hidden;
    }
    .m-fill {
      display: block;
      height: 100%;
      border-radius: 999px;
      transition: width @dur-slow @ease-out;
    }
  }
}

// 快捷
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.qtile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 6px;
  border: 1px solid var(--border);
  border-radius: @r-md;
  background: var(--surface-2);
  cursor: pointer;
  color: var(--text-2);
  transition: transform @dur-fast @ease-out, border-color @dur-fast @ease-out,
    background @dur-fast @ease-out;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--border-2);
    background: var(--hover);
  }
  .qtile-ico {
    width: 40px;
    height: 40px;
    border-radius: @r-md;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .qtile-label {
    font-size: 12.5px;
    color: var(--text-1);
  }
}

// 食谱
.ghost {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-family: @font-mono;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 5px 11px;
  cursor: pointer;
  transition: color @dur-fast @ease-out, border-color @dur-fast @ease-out;

  &:hover {
    color: var(--lime-ink);
    border-color: var(--lime);
  }
}

.plan-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 0;
  color: var(--text-3);
  font-size: 13px;
}

.plan-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 30px 16px 26px;

  .pe-ico {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--lime-soft);
    color: var(--lime-ink);
    margin-bottom: 14px;
  }
  .pe-title {
    font-size: 14.5px;
    font-weight: 600;
    color: var(--text-1);
  }
  .pe-sub {
    font-size: 12.5px;
    color: var(--text-3);
    margin: 6px 0 18px;
    max-width: 260px;
    line-height: 1.5;
  }
  .pe-btn {
    font-family: @font-display;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: var(--on-lime);
    background: var(--lime);
    border: none;
    border-radius: @r-md;
    padding: 10px 30px;
    cursor: pointer;
    box-shadow: var(--glow-lime);
    transition: transform @dur-fast @ease-out, filter @dur-fast @ease-out;
    &:hover {
      transform: translateY(-2px);
      filter: brightness(1.06);
    }
  }
}

.meal {
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  &:last-of-type {
    border-bottom: none;
  }
  .meal-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    .meal-name {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-1);
      .m-dot {
        width: 8px;
        height: 8px;
        border-radius: 2px;
        &.breakfast {
          background: var(--orange);
        }
        &.lunch {
          background: var(--lime);
        }
        &.dinner {
          background: var(--cyan);
        }
      }
    }
    .meal-cal {
      font-size: 12.5px;
      color: var(--orange);
      font-weight: 600;
    }
  }
  .meal-items {
    display: flex;
    flex-direction: column;
  }
  .meal-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 7px 8px;
    border: none;
    background: transparent;
    border-radius: @r-sm;
    cursor: pointer;
    text-align: left;
    transition: background @dur-fast @ease-out;

    &:hover {
      background: var(--hover);
    }
    .it-name {
      font-size: 13.5px;
      color: var(--text-2);
      flex: 1;
      min-width: 0;
    }
    .it-cal {
      font-size: 12.5px;
      color: var(--text-3);
    }
  }
  .meal-empty {
    font-size: 12.5px;
    color: var(--text-3);
    padding: 4px 8px;
  }
}

.adapt {
  margin-top: 14px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  border-radius: @r-md;
  background: var(--lime-soft);
  border: 1px solid transparent;
  color: var(--lime-ink);
  font-size: 13px;
  line-height: 1.55;
}

// ---------- 弹窗 ----------
.popup-wrap {
  padding: 24px 20px calc(24px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 14px;

  .popup-title {
    font-family: @font-display;
    font-size: 17px;
    font-weight: 700;
    text-align: center;
  }
}
.water-info {
  text-align: center;
  .cur {
    font-size: 30px;
    font-weight: 800;
    color: var(--cyan);
  }
  .target {
    font-size: 14px;
    color: var(--text-3);
  }
}
.water-btns {
  display: flex;
  gap: 12px;
}
.meal-detail {
  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
    span {
      color: var(--text-3);
    }
    b {
      color: var(--text-1);
    }
  }
}

// ---------- 响应式 ----------
@media (max-width: 1023px) {
  .dash {
    grid-template-columns: 1fr;
  }
  .hero-greet {
    font-size: 24px !important;
  }
}

// ---------- 首页统计区块 ----------
// 移动端「统计」并入首页；桌面端保持原有三栏布局，不重复堆叠
.home-stats {
  .hs-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
  }
  .hs-link {
    border: none;
    background: transparent;
    padding: 0;
    font-family: @font-body;
    font-size: 12.5px;
    color: var(--lime-ink);
    cursor: pointer;

    &:hover {
      text-decoration: underline;
    }
  }

  // 嵌入首页时收窄图表高度，避免页面被拉得过长
  :deep(.chart-card) {
    .chart-empty {
      min-height: 150px;
    }
  }

  @media (max-width: 1023px) {
    // 图表组件是行内 style 高度，需 !important 才能覆盖
    :deep(.chart-card .chart-line),
    :deep(.chart-card .chart-pie) {
      height: 240px !important;
    }
  }
}

@media (min-width: 1024px) {
  .home-stats {
    display: none;
  }
}

@media (max-width: 560px) {
  .hero {
    align-items: stretch;
    gap: 14px;
  }
  .hero-main {
    .hero-greet {
      font-size: 22px !important;
    }
  }
  .hero-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    width: 100%;
  }
  .hs {
    min-width: 0;
    padding: 9px 10px;
    .hs-k {
      font-size: 10.5px;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .hs-v {
      gap: 2px;
      b {
        font-size: 18px;
      }
      .hs-u {
        font-size: 10px;
      }
    }
  }
  .quick-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }
}
</style>
