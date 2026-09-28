<template>
  <div class="stats-panel">
    <van-tabs v-model:active="active" class="stats-tabs">
      <van-tab title="体重趋势">
        <div class="tab-body">
          <div class="seg">
            <van-radio-group v-model="range" direction="horizontal">
              <van-radio name="day">日</van-radio>
              <van-radio name="week">周</van-radio>
              <van-radio name="month">月</van-radio>
            </van-radio-group>
          </div>

          <div class="tiles">
            <div class="tile"><span>初始</span><b class="num">{{ weightStat.initial }}</b><i>kg</i></div>
            <div class="tile"><span>当前</span><b class="num">{{ weightStat.current }}</b><i>kg</i></div>
            <div class="tile good"><span>累计减重</span><b class="num">{{ weightStat.lost }}</b><i>kg</i></div>
            <div class="tile"><span>目标</span><b class="num">{{ weightStat.target }}</b><i>kg</i></div>
          </div>

          <div class="card card--edge chart-card">
            <div class="eyebrow">体重变化曲线 / TREND</div>
            <div v-if="weightEmpty" class="chart-empty">
              <AppIcon name="chart" :size="26" />
              <p>暂无体重记录</p>
              <span>记录体重后即可查看变化趋势</span>
            </div>
            <ChartLine v-else :option="weightOption" height="320px" />
          </div>
        </div>
      </van-tab>

      <van-tab title="营养分析">
        <div class="tab-body">
          <div class="grid-2">
            <div class="card card--edge chart-card">
              <div class="eyebrow">近 7 日热量摄入</div>
              <div v-if="calorieEmpty" class="chart-empty">
                <AppIcon name="chart" :size="26" />
                <p>暂无摄入数据</p>
                <span>记录饮食后即可查看</span>
              </div>
              <ChartLine v-else :option="calorieOption" height="280px" />
            </div>
            <div class="card card--edge chart-card">
              <div class="eyebrow">三大营养素供能比</div>
              <div v-if="calorieEmpty" class="chart-empty">
                <AppIcon name="chart" :size="26" />
                <p>暂无营养数据</p>
                <span>记录饮食后即可查看</span>
              </div>
              <ChartPie v-else :option="nutriPieOption" height="280px" />
            </div>
          </div>
        </div>
      </van-tab>

      <van-tab title="周度报告">
        <div class="tab-body">
          <div class="tiles">
            <div class="tile"><span>平均体重</span><b class="num">{{ weekly.avg_weight }}</b><i>kg</i></div>
            <div class="tile good"><span>平均缺口</span><b class="num">{{ weekly.avg_deficit }}</b><i>kcal</i></div>
            <div class="tile good"><span>达标率</span><b class="num">{{ weekly.goal_rate }}</b><i>%</i></div>
          </div>

          <div class="card card--edge chart-card">
            <div class="eyebrow">本周摄入 vs 消耗</div>
            <div v-if="weeklyEmpty" class="chart-empty">
              <AppIcon name="chart" :size="26" />
              <p>本周暂无数据</p>
              <span>记录饮食与运动后即可查看</span>
            </div>
            <ChartLine v-else :option="weeklyOption" height="280px" />
          </div>

          <div class="card card--edge report-summary">
            <AppIcon name="bolt" :size="18" />
            <p>{{ weekly.summary || '保持节奏，本周表现不错，继续坚持即可达成目标。' }}</p>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import ChartLine from '@/components/ChartLine.vue'
import ChartPie from '@/components/ChartPie.vue'
import { weightTrend, nutrientTrend, weeklyStats } from '@/api/stats'

// 统计面板：独立「数据统计」页与首页移动端区块共用，
// 数据全部来自后端统计接口，不做本地伪造。
const active = ref(0)
const range = ref('week')

const AXIS = '#8a96a3'
const SPLIT = 'rgba(138,150,163,0.20)'
const LIME = '#c6f24e'
const ORANGE = '#ff7a2f'
const CYAN = '#35e0ff'

const weightStat = reactive({ initial: '—', current: '—', lost: '—', target: '—' })
const weightOption = ref({})
const calorieOption = ref({})
const nutriPieOption = ref({})
const weeklyOption = ref({})
const weekly = reactive({ avg_weight: '—', avg_deficit: '—', goal_rate: '—', summary: '' })

const weightEmpty = ref(true)
const calorieEmpty = ref(true)
const weeklyEmpty = ref(true)

function lineOption({ dates, series, markLineVal, area }) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: '12%', right: '4%', top: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: AXIS } },
      axisLabel: { color: AXIS, fontSize: 10 },
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: AXIS, fontSize: 10 },
      splitLine: { lineStyle: { color: SPLIT } }
    },
    series: series.map((s) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: s.data,
      itemStyle: { color: s.color },
      lineStyle: { color: s.color, width: 2 },
      areaStyle: area
        ? { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: s.color + '55' }, { offset: 1, color: s.color + '05' }] } }
        : undefined,
      markLine: s.markLine
        ? {
            silent: true,
            symbol: 'none',
            lineStyle: { color: ORANGE, type: 'dashed' },
            data: [{ yAxis: markLineVal }],
            label: { formatter: '目标 ' + markLineVal, color: ORANGE, fontSize: 10 }
          }
        : undefined
    }))
  }
}

async function loadWeight() {
  try {
    const res = await weightTrend({ range: range.value })
    const dates = res.dates || []
    const weights = res.weights || []
    weightOption.value = lineOption({
      dates,
      series: [{ name: '体重', data: weights, color: LIME }],
      markLineVal: res.target_weight,
      area: true
    })
    const nums = weights.filter((w) => w != null).map(Number)
    weightEmpty.value = nums.length === 0
    weightStat.initial = nums.length ? nums[0] : '—'
    weightStat.current = nums.length ? nums[nums.length - 1] : '—'
    weightStat.lost =
      nums.length >= 2 ? (Number(nums[0]) - Number(nums[nums.length - 1])).toFixed(1) : '—'
    weightStat.target = res.target_weight != null ? res.target_weight : '—'
  } catch (e) {
    weightOption.value = lineOption({ dates: [], series: [{ name: '体重', data: [], color: LIME }] })
  }
}

async function loadNutrient() {
  try {
    const res = await nutrientTrend({ days: 7 })
    const dates = res.dates || []
    calorieOption.value = lineOption({
      dates,
      series: [{ name: '热量', data: res.calorie || [], color: ORANGE }],
      area: true
    })
    // 供能比：蛋白*4 / 脂肪*9 / 碳水*4
    const ps = (res.protein || []).reduce((a, b) => a + Number(b || 0), 0)
    const fs = (res.fat || []).reduce((a, b) => a + Number(b || 0), 0)
    const cs = (res.carbohydrate || []).reduce((a, b) => a + Number(b || 0), 0)
    const pe = ps * 4
    const fe = fs * 9
    const ce = cs * 4
    calorieEmpty.value = pe + fe + ce === 0
    nutriPieOption.value = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} kcal ({d}%)' },
      legend: { bottom: 0, textStyle: { color: AXIS } },
      series: [
        {
          type: 'pie',
          radius: ['42%', '66%'],
          center: ['50%', '45%'],
          label: { color: AXIS, formatter: '{b}\n{d}%' },
          data: [
            { name: '蛋白质', value: Math.round(pe), itemStyle: { color: LIME } },
            { name: '脂肪', value: Math.round(fe), itemStyle: { color: ORANGE } },
            { name: '碳水', value: Math.round(ce), itemStyle: { color: CYAN } }
          ]
        }
      ]
    }
  } catch (e) {
    calorieOption.value = lineOption({ dates: [], series: [{ name: '热量', data: [], color: ORANGE }] })
  }
}

async function loadWeekly() {
  try {
    const res = await weeklyStats()
    weekly.avg_weight = res.avg_weight != null ? res.avg_weight : '—'
    weekly.avg_deficit = res.avg_deficit != null ? res.avg_deficit : '—'
    weekly.goal_rate = res.goal_rate != null ? res.goal_rate : '—'
    weekly.summary = res.summary || ''
    weeklyEmpty.value = ![...(res.intake || []), ...(res.burned || [])].some(
      (v) => Number(v) > 0
    )
    weeklyOption.value = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: ['摄入', '消耗'], top: 0, textStyle: { color: AXIS } },
      grid: { left: '12%', right: '4%', top: 40, bottom: 30 },
      xAxis: {
        type: 'category',
        data: res.days || [],
        axisLine: { lineStyle: { color: AXIS } },
        axisLabel: { color: AXIS, fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: AXIS, fontSize: 10 },
        splitLine: { lineStyle: { color: SPLIT } }
      },
      series: [
        {
          name: '摄入',
          type: 'bar',
          data: res.intake || [],
          itemStyle: { color: ORANGE, borderRadius: [4, 4, 0, 0] }
        },
        {
          name: '消耗',
          type: 'bar',
          data: res.burned || [],
          itemStyle: { color: LIME, borderRadius: [4, 4, 0, 0] }
        }
      ]
    }
  } catch (e) {
    weekly.summary = '暂无周报数据，坚持记录后我会为你生成专属总结。'
  }
}

watch(range, loadWeight)

onMounted(() => {
  loadWeight()
  loadNutrient()
  loadWeekly()
})
</script>

<style lang="less" scoped>
@import '../styles/variable.less';

.stats-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tab-body {
  padding: 18px 0 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.seg {
  display: inline-flex;
  align-self: center;
}

.tiles {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.tile {
  padding: 16px 12px;
  border-radius: @r-md;
  background: var(--surface);
  border: 1px solid var(--border);
  text-align: center;

  span {
    display: block;
    font-size: 11.5px;
    color: var(--text-3);
    margin-bottom: 8px;
    letter-spacing: 0.03em;
  }
  b {
    font-size: 26px;
    font-weight: 800;
    color: var(--text-1);
    line-height: 1;
  }
  i {
    font-size: 11px;
    color: var(--text-3);
    font-style: normal;
    margin-left: 3px;
  }
  &.good b {
    color: var(--lime-ink);
  }
}

.chart-card {
  .eyebrow {
    margin-bottom: 14px;
  }
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 190px;
  gap: 4px;
  color: var(--text-3);

  svg {
    color: var(--border-2);
    margin-bottom: 8px;
  }
  p {
    font-size: 13.5px;
    color: var(--text-2);
    font-weight: 500;
  }
  span {
    font-size: 12px;
    color: var(--text-3);
  }
}

.report-summary {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: var(--lime-soft);
  border-color: transparent;

  :deep(svg) {
    color: var(--lime-ink);
    flex-shrink: 0;
    margin-top: 2px;
  }
  p {
    margin: 0;
    font-size: 13.5px;
    line-height: 1.6;
    color: var(--lime-ink);
  }
}

// Vant tabs 分段感
:deep(.van-tabs__wrap) {
  margin-bottom: 4px;
}
:deep(.van-tab) {
  font-family: @font-body;
  font-size: 14.5px;
}

// 分段选择（日/周/月）
:deep(.van-radio-group) {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px;
  gap: 4px;
  display: inline-flex;
}
:deep(.van-radio) {
  padding: 6px 18px;
  border-radius: 999px;
  margin-right: 0;
}
:deep(.van-radio__icon) {
  display: none;
}
:deep(.van-radio__label) {
  color: var(--text-2);
  font-size: 13px;
}
:deep(.van-radio--checked) {
  background: var(--lime);
}
:deep(.van-radio--checked .van-radio__label) {
  color: var(--on-lime);
  font-weight: 600;
}

@media (max-width: 1023px) {
  .tiles {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
