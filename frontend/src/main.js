import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import ElementPlus from 'element-plus';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import 'element-plus/dist/index.css';
import VueECharts from 'vue-echarts';
import 'echarts';

const app = createApp(App);

// Register Element Plus
app.use(ElementPlus);

// Register all icons globally
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// Register vue-echarts globally
app.component('v-chart', VueECharts);

app.use(router);

// Update document title on route change
router.afterEach((to) => {
  document.title = to.meta.title || 'GSD Platform'
})

app.mount("#app");
