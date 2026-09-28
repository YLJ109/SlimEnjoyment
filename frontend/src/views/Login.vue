<template>
  <div class="auth-split">
    <!-- 品牌面板 -->
    <aside class="brand-panel">
      <div class="bp-top">
        <span class="bp-logo"><AppIcon name="logo" :size="20" /></span>
        <span class="bp-name">轻享瘦</span>
        <span class="bp-badge num">V1.0</span>
      </div>

      <div class="bp-main">
        <span class="eyebrow">FAT-LOSS OS</span>
        <h1 class="bp-headline">科学减脂<br /><span>数据驱动</span></h1>
        <p class="bp-sub">AI 识别 · 营养算法 · 能量管理</p>

        <div class="bp-metrics">
          <div class="bpm"><b class="num">AI</b><span>智能识别</span></div>
          <div class="bpm"><b class="num">4</b><span>维数据</span></div>
          <div class="bpm"><b class="num">24h</b><span>能量追踪</span></div>
        </div>
      </div>

      <div class="bp-foot num">© 2026 轻享瘦 · JIANFEI OS</div>
    </aside>

    <!-- 表单面板 -->
    <main class="form-panel">
      <div class="form-box">
        <div class="fb-head">
          <span class="eyebrow">登录 / SIGN IN</span>
          <h2 class="fb-title">欢迎回来</h2>
          <p class="fb-sub">登录以继续你的减脂计划</p>
        </div>

        <van-form class="form" @submit="onSubmit">
          <van-cell-group inset>
            <van-field
              v-model="form.username"
              name="username"
              label="用户名"
              placeholder="请输入用户名(4-20位)"
              :rules="[{ required: true, message: '请填写用户名' }, { validator: validateUsername, message: '用户名需 4-20 位' }]"
            />
            <van-field
              v-model="form.password"
              type="password"
              name="password"
              label="密码"
              placeholder="请输入密码(6-20位)"
              :rules="[{ required: true, message: '请填写密码' }, { validator: validatePassword, message: '密码需 6-20 位' }]"
            />
          </van-cell-group>

          <div class="submit">
            <van-button round block type="primary" native-type="submit" :loading="loading" loading-text="登录中...">
              登 录
            </van-button>
          </div>
        </van-form>

        <div class="footer">
          <span>还没有账号？</span>
          <span class="link" @click="goRegister">立即注册</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useUserStore } from '@/store/modules/user'
import { showToast } from 'vant'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

function validateUsername(val) {
  return val.length >= 4 && val.length <= 20
}
function validatePassword(val) {
  return val.length >= 6 && val.length <= 20
}

async function onSubmit() {
  loading.value = true
  try {
    const data = await userStore.login({
      username: form.username,
      password: form.password
    })
    showToast({ type: 'success', message: '登录成功' })
    if (userStore.isProfileComplete) {
      router.replace('/home')
    } else {
      router.replace('/profile-init')
    }
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

function goRegister() {
  router.push('/register')
}
</script>

<style lang="less" scoped>
@import '../styles/variable.less';

.auth-split {
  min-height: 100vh;
  display: flex;
}

// ---------- 品牌面板 ----------
.brand-panel {
  position: relative;
  width: 46%;
  max-width: 560px;
  padding: 40px 48px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  background: var(--bg-2);
  border-right: 1px solid var(--border);

  // 氛围：网格 + 青柠光斑
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: linear-gradient(var(--grid-line) 1px, transparent 1px),
      linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
    background-size: 42px 42px;
    -webkit-mask-image: radial-gradient(90% 80% at 20% 10%, #000 40%, transparent 100%);
    mask-image: radial-gradient(90% 80% at 20% 10%, #000 40%, transparent 100%);
  }
  &::after {
    content: '';
    position: absolute;
    width: 520px;
    height: 520px;
    right: -180px;
    bottom: -200px;
    border-radius: 50%;
    background: radial-gradient(circle, var(--lime-soft), transparent 62%);
    filter: blur(20px);
  }

  .bp-top {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 10px;

    .bp-logo {
      width: 32px;
      height: 32px;
      border-radius: @r-md;
      background: var(--lime);
      color: var(--on-lime);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--glow-lime);
    }
    .bp-name {
      font-family: @font-display;
      font-size: 17px;
      font-weight: 700;
      color: var(--text-1);
    }
    .bp-badge {
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--border-2);
      color: var(--text-3);
    }
  }

  .bp-main {
    position: relative;
    z-index: 1;

    .bp-headline {
      font-family: @font-display;
      font-size: 52px;
      line-height: 1.02;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin: 18px 0 14px;
      color: var(--text-1);

      span {
        color: var(--lime-ink);
      }
    }
    .bp-sub {
      font-size: 14px;
      color: var(--text-3);
      letter-spacing: 0.04em;
      margin: 0;
    }
    .bp-metrics {
      margin-top: 34px;
      display: flex;
      gap: 26px;

      .bpm {
        display: flex;
        flex-direction: column;
        gap: 2px;
        b {
          font-size: 24px;
          font-weight: 800;
          color: var(--text-1);
          line-height: 1;
        }
        span {
          font-size: 11.5px;
          color: var(--text-3);
        }
      }
    }
  }

  .bp-foot {
    position: relative;
    z-index: 1;
    font-size: 11px;
    letter-spacing: 0.14em;
    color: var(--text-3);
  }
}

// ---------- 表单面板 ----------
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}

.form-box {
  width: 100%;
  max-width: 384px;
}

.fb-head {
  margin-bottom: 26px;

  .fb-title {
    font-family: @font-display;
    font-size: 30px;
    font-weight: 700;
    color: var(--text-1);
    margin: 12px 0 6px;
    letter-spacing: -0.01em;
  }
  .fb-sub {
    font-size: 13.5px;
    color: var(--text-3);
    margin: 0;
  }
}

.form {
  :deep(.van-field) {
    padding: 13px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: @r-md;
    margin-bottom: 12px;
  }
  :deep(.van-cell-group--inset) {
    margin: 0;
    background: transparent;
    border-radius: 0;
  }
  :deep(.van-field__label) {
    width: 62px;
    color: var(--text-2);
  }
}

.submit {
  margin-top: 6px;
}

.footer {
  text-align: center;
  margin-top: 20px;
  color: var(--text-3);
  font-size: 13px;

  .link {
    color: var(--lime-ink);
    font-weight: 600;
    cursor: pointer;
    margin-left: 4px;
  }
}

// ---------- 移动端：品牌面板折叠为顶部横幅 ----------
@media (max-width: 900px) {
  .auth-split {
    flex-direction: column;
  }
  .brand-panel {
    width: 100%;
    max-width: none;
    padding: 22px 22px 26px;
    border-right: none;
    border-bottom: 1px solid var(--border);

    .bp-main .bp-headline {
      font-size: 34px;
      margin: 12px 0 8px;
    }
    .bp-metrics,
    .bp-foot {
      display: none;
    }
  }
  .form-panel {
    padding: 26px 20px 40px;
    align-items: flex-start;
  }
}
</style>
