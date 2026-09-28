<template>
  <div class="page exercise">
    <NavBar title="运动与饮水" />

    <div class="grid-2 ex-grid">
      <!-- 饮水 -->
      <section class="card card--edge water-card">
        <div class="card-head">
          <span class="eyebrow">饮水 / WATER</span>
          <AppIcon name="drop" :size="16" class="hd-ico cyan" />
        </div>
        <div class="water-amount">
          <b class="num">{{ water.total_amount }}</b>
          <span class="num">/ {{ water.target_amount }} ml</span>
        </div>
        <van-progress :percentage="waterPercent" color="var(--cyan)" :show-pivot="false" class="water-bar" />
        <div class="water-quick">
          <button class="wq" @click="submitWater(100)">+100</button>
          <button class="wq" @click="submitWater(300)">+300</button>
          <button class="wq" @click="submitWater(500)">+500</button>
        </div>
      </section>

      <!-- 运动列表 -->
      <section class="card card--edge ex-card">
        <div class="card-head">
          <span class="eyebrow">今日运动 / WORKOUT</span>
          <button class="ghost" @click="showAdd = true"><AppIcon name="plus" :size="14" /> 添加</button>
        </div>

        <div v-if="!list.length" class="ex-empty">还没有运动记录</div>

        <div v-for="item in list" :key="item.id" class="ex-item">
          <div class="ex-icon">
            <AppIcon :name="iconName(item.exercise_type)" :size="20" />
          </div>
          <div class="ex-info">
            <div class="ex-name">{{ exerciseLabel(item.exercise_type) }}</div>
            <div class="ex-meta num">{{ item.duration }} min · {{ Math.round(item.calorie_burn) }} kcal</div>
          </div>
          <button class="ex-del" @click="onDelete(item)" aria-label="删除">
            <AppIcon name="trash" :size="17" />
          </button>
        </div>

        <div class="ex-total" v-if="list.length">
          今日累计消耗 <b class="num">{{ totalBurn }}</b> kcal
        </div>
      </section>
    </div>

    <!-- 添加运动 -->
    <van-popup v-model:show="showAdd" position="bottom" round>
      <div class="popup-wrap">
        <div class="popup-title">添加运动</div>
        <van-form @submit="onAdd">
          <van-cell-group inset>
            <van-field name="type" label="运动类型">
              <template #input>
                <van-radio-group v-model="form.exercise_type" direction="horizontal">
                  <van-radio v-for="(m, key) in metOptions" :key="key" :name="key">
                    {{ m.label }}
                  </van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field
              v-model="form.duration"
              type="digit"
              label="时长(分钟)"
              placeholder="如 30"
              :rules="[{ required: true, message: '请填写时长' }]"
            />
            <van-cell title="预计消耗">
              <template #value>
                <span class="est num">{{ estBurn }} kcal</span>
              </template>
            </van-cell>
            <p v-if="!weight" class="est-warn">
              尚未填写真实体重，无法估算消耗。请先在「我的 - 个人资料」补充。
            </p>
          </van-cell-group>
          <div class="popup-actions">
            <van-button block round type="primary" native-type="submit">保存</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { addExercise, listExercise, deleteExercise } from '@/api/exercise'
import { addWater, todayWater } from '@/api/water'
import { showToast, showConfirmDialog } from 'vant'
import { today } from '@/utils/format'
import { MET_TABLE, exerciseLabel, calcExerciseBurn } from '@/utils/common'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
// 体重必须取真实值：没有就按 0 处理，绝不用 60kg 之类的假设值参与热量计算
const weight = computed(() => Number(userStore.userInfo?.current_weight) || 0)

const water = reactive({ total_amount: 0, target_amount: 2000, date: '' })
const waterPercent = computed(() =>
  water.target_amount ? Math.min(Math.round((water.total_amount / water.target_amount) * 100), 100) : 0
)

const list = ref([])
const showAdd = ref(false)
const form = reactive({ exercise_type: 'running', duration: '' })
const metOptions = MET_TABLE

// 体重缺失时无法给出可信估算，直接返回 0 并在界面提示，不编造结果
const estBurn = computed(() => {
  if (!form.duration || !weight.value) return 0
  return calcExerciseBurn(form.exercise_type, Number(form.duration), weight.value)
})

const totalBurn = computed(() =>
  list.value.reduce((s, x) => s + Number(x.calorie_burn || 0), 0)
)

function iconName(type) {
  const map = {
    running: 'bolt',
    walking: 'bolt',
    swimming: 'drop',
    rope: 'bolt',
    cycling: 'bolt',
    strength: 'exercise',
    yoga: 'star',
    hiit: 'fire',
    basketball: 'target'
  }
  return map[type] || 'fire'
}

async function loadWater() {
  try {
    const res = await todayWater({ date: today() })
    Object.assign(water, res)
  } catch (e) {}
}
async function submitWater(amount) {
  try {
    const res = await addWater({ record_date: today(), amount })
    water.total_amount = res.total_amount
    water.target_amount = res.target_amount
    showToast({ type: 'success', message: '已添加 ' + amount + 'ml' })
  } catch (e) {}
}

// 只取当天记录：接口不传 date 会返回全部历史，
// 会让「今日运动 / 今日累计消耗」把历史数据也算进去
async function loadList() {
  try {
    const res = await listExercise({ date: today() })
    list.value = res.records || []
  } catch (e) {
    list.value = []
  }
}

async function onAdd() {
  if (!weight.value) {
    showToast({ type: 'fail', message: '请先在「我的 - 个人资料」填写真实体重' })
    return
  }
  try {
    await addExercise({
      record_date: today(),
      exercise_type: form.exercise_type,
      duration: Number(form.duration),
      calorie_burn: estBurn.value
    })
    showToast({ type: 'success', message: '已记录' })
    showAdd.value = false
    form.duration = ''
    loadList()
  } catch (e) {}
}

async function onDelete(item) {
  try {
    await showConfirmDialog({ title: '提示', message: '确定删除这条运动记录？' })
    await deleteExercise(item.id)
    showToast({ type: 'success', message: '已删除' })
    loadList()
  } catch (e) {}
}

onMounted(() => {
  loadWater()
  loadList()
})
</script>

<style lang="less" scoped>
@import '../styles/variable.less';

.page.exercise {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.hd-ico.cyan {
  color: var(--cyan);
}

// 饮水
.water-amount {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 14px;

  b {
    font-size: 40px;
    font-weight: 800;
    line-height: 1;
    color: var(--cyan);
  }
  span {
    font-size: 14px;
    color: var(--text-3);
  }
}
.water-bar {
  margin-bottom: 16px;
}
.water-quick {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;

  .wq {
    padding: 12px 0;
    border-radius: @r-md;
    border: 1px solid var(--border);
    background: var(--cyan-soft);
    color: var(--cyan);
    font-family: @font-mono;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    transition: transform @dur-fast @ease-out, border-color @dur-fast @ease-out;

    &:hover {
      transform: translateY(-1px);
      border-color: var(--cyan);
    }
  }
}

// 运动
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
.ex-empty {
  text-align: center;
  color: var(--text-3);
  font-size: 13px;
  padding: 30px 0;
}
.ex-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 0;
  border-bottom: 1px solid var(--border);

  .ex-icon {
    width: 40px;
    height: 40px;
    border-radius: @r-md;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--lime-soft);
    color: var(--lime-ink);
    flex-shrink: 0;
  }
  .ex-info {
    flex: 1;
    min-width: 0;
    .ex-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-1);
    }
    .ex-meta {
      font-size: 12px;
      color: var(--text-3);
      margin-top: 2px;
    }
  }
  .ex-del {
    width: 34px;
    height: 34px;
    border: none;
    border-radius: @r-sm;
    background: transparent;
    color: var(--text-3);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: var(--red);
      background: var(--red-soft);
    }
  }
}
.ex-total {
  margin-top: 14px;
  text-align: right;
  font-size: 13px;
  color: var(--text-2);

  b {
    color: var(--lime-ink);
    font-size: 18px;
    margin: 0 3px;
  }
}

.popup-wrap {
  padding: 24px 20px calc(24px + env(safe-area-inset-bottom));

  .popup-title {
    font-family: @font-display;
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 18px;
    text-align: center;
  }
  .popup-actions {
    margin-top: 18px;
  }
  .est {
    color: var(--lime-ink);
    font-weight: 600;
  }
  .est-warn {
    margin: 10px 16px 0;
    font-size: 12px;
    line-height: 1.6;
    color: var(--orange);
  }
}
</style>
