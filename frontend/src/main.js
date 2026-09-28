import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import Vant from 'vant'
import 'vant/lib/index.css'
import './styles/global.less'
import { initTheme } from './store/modules/app'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Vant)

// 初始化深色模式（读取 localStorage 并写入 data-theme）
initTheme()

// 根字号由 global.less 的纯 CSS 控制：移动端 10vw 缩放，桌面锁定 37.5px，无需 JS 干预

app.mount('#app')
