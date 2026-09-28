<template>
  <div class="page diet">
    <NavBar title="饮食记录" />

    <div class="toolbar">
      <button class="date-pick" @click="showCalendar = true">
        <AppIcon name="calendar" :size="16" />
        <span class="num">{{ recordDate }}</span>
        <AppIcon name="chevdown" :size="14" />
      </button>
      <button class="add-btn" @click="showAction = true">
        <AppIcon name="plus" :size="16" /> 记录饮食
      </button>
    </div>

    <van-pull-refresh v-model="refreshing" @refresh="loadData">
      <div class="meals stagger">
        <div class="card card--edge meal-group" v-for="g in groups" :key="g.type">
          <div class="group-head">
            <span class="group-name"><i class="tick" :class="g.type" />{{ g.label }}</span>
            <span class="group-cal num">{{ g.total }} kcal</span>
          </div>
          <van-swipe-cell v-for="item in g.items" :key="item.id">
            <DietItem :item="item" @edit="onEdit" @delete="onDelete" />
            <template #right>
              <van-button square type="danger" text="删除" class="del-btn" @click="onDelete(item)" />
            </template>
          </van-swipe-cell>
          <div v-if="!g.items.length" class="empty">暂无记录</div>
        </div>
      </div>

      <div class="card card--edge summary">
        <div class="eyebrow">今日汇总 / TODAY</div>
        <div class="sum-grid">
          <div class="sum"><span>总热量</span><b class="num">{{ totalCalorie }}</b><i>kcal</i></div>
          <div class="sum"><span>蛋白质</span><b class="num">{{ totalProtein }}</b><i>g</i></div>
          <div class="sum"><span>脂肪</span><b class="num">{{ totalFat }}</b><i>g</i></div>
          <div class="sum"><span>碳水</span><b class="num">{{ totalCarb }}</b><i>g</i></div>
        </div>
      </div>
    </van-pull-refresh>

    <!-- 移动端悬浮加号 -->
    <button class="fab" @click="showAction = true" aria-label="记录饮食">
      <AppIcon name="plus" :size="24" />
    </button>

    <!-- 方式选择 -->
    <van-action-sheet
      v-model:show="showAction"
      :actions="actionList"
      cancel-text="取消"
      description="选择记录方式"
      @select="onSelectAction"
    />

    <!-- 文字输入 -->
    <van-popup v-model:show="showText" position="bottom" round>
      <div class="popup-wrap">
        <div class="popup-title">文字记录</div>
        <van-form @submit="submitText">
          <van-cell-group inset>
            <van-field name="meal_type" label="餐次">
              <template #input>
                <van-radio-group v-model="textForm.meal_type" direction="horizontal">
                  <van-radio name="breakfast">早</van-radio>
                  <van-radio name="lunch">午</van-radio>
                  <van-radio name="dinner">晚</van-radio>
                  <van-radio name="snack">加餐</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field
              v-model="textForm.food_desc"
              label="描述"
              type="textarea"
              rows="2"
              placeholder="如：两碗米饭 + 一份炒青菜"
              :rules="[{ required: true, message: '请填写食物描述' }]"
            />
            <van-field v-model="textForm.calorie" type="digit" label="热量(kcal)" placeholder="0" />
            <van-field v-model="textForm.protein" type="digit" label="蛋白质(g)" placeholder="选填" />
            <van-field v-model="textForm.fat" type="digit" label="脂肪(g)" placeholder="选填" />
            <van-field v-model="textForm.carbohydrate" type="digit" label="碳水(g)" placeholder="选填" />
          </van-cell-group>
          <div class="popup-actions">
            <van-button block round type="primary" native-type="submit">保存</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <!-- 拍照识别结果 -->
    <van-popup v-model:show="showRecognize" position="bottom" round>
      <div class="popup-wrap">
        <div class="popup-title">识别结果（可修改）</div>
        <div v-if="recognizing" class="recognizing">
          <van-loading size="18px" /> 正在识别食物...
        </div>
        <template v-else>
          <div class="rec-list">
            <div class="rec-item" v-for="(f, i) in recognizedList" :key="i">
              <van-field v-model="f.name" label="名称" />
              <div class="rec-grid">
                <van-field v-model="f.weight" type="digit" label="重量(g)" />
                <van-field v-model="f.calorie" type="digit" label="热量" />
                <van-field v-model="f.protein" type="digit" label="蛋白(g)" />
                <van-field v-model="f.fat" type="digit" label="脂肪(g)" />
                <van-field v-model="f.carbohydrate" type="digit" label="碳水(g)" />
              </div>
            </div>
          </div>
          <div class="popup-actions">
            <van-button block round type="primary" @click="saveRecognized">保存到今日饮食</van-button>
          </div>
        </template>
      </div>
    </van-popup>

    <!-- 编辑弹窗 -->
    <van-popup v-model:show="showEdit" position="bottom" round>
      <div class="popup-wrap" v-if="editItem">
        <div class="popup-title">编辑记录</div>
        <van-form @submit="submitEdit">
          <van-cell-group inset>
            <van-field v-model="editItem.food_desc" label="描述" :rules="[{ required: true }]" />
            <van-field v-model="editItem.calorie" type="digit" label="热量(kcal)" />
            <van-field v-model="editItem.protein" type="digit" label="蛋白质(g)" />
            <van-field v-model="editItem.fat" type="digit" label="脂肪(g)" />
            <van-field v-model="editItem.carbohydrate" type="digit" label="碳水(g)" />
          </van-cell-group>
          <div class="popup-actions">
            <van-button block round type="primary" native-type="submit">更新</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <!-- 日历 -->
    <van-calendar v-model:show="showCalendar" :min-date="minDate" :max-date="maxDate" @confirm="onPickDate" />

    <!-- 隐藏文件输入 -->
    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      capture="environment"
      style="display: none"
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import DietItem from '@/components/DietItem.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { listDiet, addDiet, updateDiet, deleteDiet } from '@/api/diet'
import { recognizeFood } from '@/api/ai'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import { formatDate, today } from '@/utils/format'
import { MEAL_TYPE_MAP } from '@/utils/common'

const recordDate = ref(today())
const refreshing = ref(false)
const records = ref([])

const minDate = new Date(new Date().setMonth(new Date().getMonth() - 3))
const maxDate = new Date()
const showCalendar = ref(false)

const showAction = ref(false)
const showText = ref(false)
const showRecognize = ref(false)
const showEdit = ref(false)
const recognizing = ref(false)
const fileInput = ref(null)
const recMealType = ref('lunch')

const recognizedList = ref([])
const editItem = ref(null)

const actionList = [
  { name: '拍照识别', value: 'camera' },
  { name: '文字输入', value: 'text' }
]

const textForm = reactive({
  meal_type: 'lunch',
  food_desc: '',
  calorie: '',
  protein: '',
  fat: '',
  carbohydrate: ''
})

const groups = computed(() => {
  const map = {
    breakfast: { type: 'breakfast', label: MEAL_TYPE_MAP.breakfast, items: [], total: 0 },
    lunch: { type: 'lunch', label: MEAL_TYPE_MAP.lunch, items: [], total: 0 },
    dinner: { type: 'dinner', label: MEAL_TYPE_MAP.dinner, items: [], total: 0 },
    snack: { type: 'snack', label: MEAL_TYPE_MAP.snack, items: [], total: 0 }
  }
  records.value.forEach((r) => {
    const g = map[r.meal_type] || map.snack
    g.items.push(r)
    g.total += Number(r.calorie || 0)
  })
  return Object.values(map)
})

const totalCalorie = computed(() =>
  records.value.reduce((s, r) => s + Number(r.calorie || 0), 0)
)
const totalProtein = computed(() =>
  records.value.reduce((s, r) => s + Number(r.protein || 0), 0)
)
const totalFat = computed(() =>
  records.value.reduce((s, r) => s + Number(r.fat || 0), 0)
)
const totalCarb = computed(() =>
  records.value.reduce((s, r) => s + Number(r.carbohydrate || 0), 0)
)

async function loadData() {
  try {
    const res = await listDiet({ record_date: recordDate.value })
    records.value = res.records || []
  } catch (e) {
    records.value = []
  } finally {
    refreshing.value = false
  }
}

function onPickDate(date) {
  recordDate.value = formatDate(date)
  showCalendar.value = false
  loadData()
}

function onSelectAction(action) {
  showAction.value = false
  if (action.value === 'text') {
    showText.value = true
  } else {
    fileInput.value.click()
  }
}

async function submitText() {
  try {
    await addDiet({
      record_date: recordDate.value,
      meal_type: textForm.meal_type,
      food_desc: textForm.food_desc,
      input_type: 'text',
      calorie: Number(textForm.calorie) || 0,
      protein: Number(textForm.protein) || 0,
      fat: Number(textForm.fat) || 0,
      carbohydrate: Number(textForm.carbohydrate) || 0
    })
    showToast({ type: 'success', message: '已保存' })
    showText.value = false
    Object.assign(textForm, {
      meal_type: 'lunch',
      food_desc: '',
      calorie: '',
      protein: '',
      fat: '',
      carbohydrate: ''
    })
    loadData()
  } catch (e) {}
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  recognize(file)
  e.target.value = ''
}

async function recognize(file) {
  recognizing.value = true
  showRecognize.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await recognizeFood(fd)
    recognizedList.value = (res.food_list || []).map((f) => ({
      name: f.name || '',
      weight: String(f.weight || ''),
      calorie: String(f.calorie || ''),
      protein: String(f.protein || ''),
      fat: String(f.fat || ''),
      carbohydrate: String(f.carbohydrate || ''),
      sugar: String(f.sugar || ''),
      fiber: String(f.fiber || ''),
      sodium: String(f.sodium || '')
    }))
    if (!recognizedList.value.length) {
      showToast('未能识别食物，请手动输入')
    }
  } catch (e) {
    showToast('识别失败，请重试')
  } finally {
    recognizing.value = false
  }
}

async function saveRecognized() {
  try {
    for (const f of recognizedList.value) {
      await addDiet({
        record_date: recordDate.value,
        meal_type: recMealType.value,
        food_desc: f.name,
        input_type: 'image',
        calorie: Number(f.calorie) || 0,
        protein: Number(f.protein) || 0,
        fat: Number(f.fat) || 0,
        carbohydrate: Number(f.carbohydrate) || 0,
        sugar: Number(f.sugar) || 0,
        fiber: Number(f.fiber) || 0,
        sodium: Number(f.sodium) || 0
      })
    }
    showToast({ type: 'success', message: '已保存 ' + recognizedList.value.length + ' 项' })
    showRecognize.value = false
    recognizedList.value = []
    loadData()
  } catch (e) {}
}

function onEdit(item) {
  editItem.value = { ...item }
  showEdit.value = true
}

async function submitEdit() {
  const item = editItem.value
  try {
    await updateDiet(item.id, {
      food_desc: item.food_desc,
      calorie: Number(item.calorie) || 0,
      protein: Number(item.protein) || 0,
      fat: Number(item.fat) || 0,
      carbohydrate: Number(item.carbohydrate) || 0
    })
    showToast({ type: 'success', message: '已更新' })
    showEdit.value = false
    loadData()
  } catch (e) {}
}

async function onDelete(item) {
  try {
    await showConfirmDialog({ title: '提示', message: '确定删除这条记录？' })
    await deleteDiet(item.id)
    showToast({ type: 'success', message: '已删除' })
    loadData()
  } catch (e) {
    // 取消
  }
}

onMounted(loadData)
</script>

<style lang="less" scoped>
@import '../styles/variable.less';

.page.diet {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.date-pick {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border-radius: @r-md;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 13.5px;
  cursor: pointer;
  transition: border-color @dur-fast @ease-out;

  &:hover {
    border-color: var(--border-2);
  }
}
.add-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: @r-md;
  background: var(--lime);
  color: var(--on-lime);
  font-family: @font-display;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: filter @dur-fast @ease-out, box-shadow @dur-fast @ease-out;

  &:hover {
    filter: brightness(1.06);
    box-shadow: var(--glow-lime);
  }
}

.meals {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.meal-group {
  .group-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  .group-name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: @font-display;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-1);

    .tick {
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
      &.snack {
        background: var(--violet);
      }
    }
  }
  .group-cal {
    font-size: 12.5px;
    color: var(--orange);
    font-weight: 600;
  }
  .empty {
    text-align: center;
    color: var(--text-3);
    font-size: 12.5px;
    padding: 14px 0;
  }
}

.summary {
  margin-top: 16px;
  .sum-grid {
    margin-top: 14px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  .sum {
    text-align: center;
    padding: 12px 6px;
    background: var(--surface-2);
    border-radius: @r-md;
    span {
      display: block;
      font-size: 11.5px;
      color: var(--text-3);
      margin-bottom: 6px;
    }
    b {
      font-size: 22px;
      font-weight: 800;
      color: var(--text-1);
    }
    i {
      font-size: 11px;
      color: var(--text-3);
      font-style: normal;
      margin-left: 3px;
    }
  }
}

.del-btn {
  height: 100%;
}

.fab {
  position: fixed;
  right: 18px;
  bottom: calc(74px + env(safe-area-inset-bottom));
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: none;
  background: var(--lime);
  color: var(--on-lime);
  display: none;
  align-items: center;
  justify-content: center;
  box-shadow: var(--glow-lime), var(--shadow-2);
  z-index: 10;
  cursor: pointer;
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
}
.recognizing {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--text-3);
}
.rec-item {
  border-bottom: 1px solid var(--border);
  padding-bottom: 14px;
  margin-bottom: 14px;

  .rec-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0 12px;
  }
}

@media (max-width: 1023px) {
  .meals {
    grid-template-columns: 1fr;
  }
  .add-btn {
    display: none;
  }
  .fab {
    display: flex;
  }
  .summary .sum-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
