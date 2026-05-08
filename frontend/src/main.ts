import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import "markstream-vue/index.css";
import {
  Edit,
  Delete,
  Files,
  Search,
  Upload,
  Refresh,
  Close,
  Plus,
  Check,
  Warning,
  CircleCheck,
  CircleClose,
  Loading,
  ArrowLeft,
  ArrowRight,
  Bottom,
  Top,
  Back,
  Right,
  Paperclip,
} from "@element-plus/icons-vue";
import Antd from "ant-design-vue";
import "ant-design-vue/dist/reset.css";
import AntDesignXVue from "ant-design-x-vue";

import App from "./App.vue";
import router from "./router/simple";

const app = createApp(App);

// 按需注册 Element Plus 图标
const elementIcons = [
  Edit,
  Delete,
  Files,
  Search,
  Upload,
  Refresh,
  Close,
  Plus,
  Check,
  Warning,
  CircleCheck,
  CircleClose,
  Loading,
  ArrowLeft,
  ArrowRight,
  Bottom,
  Top,
  Back,
  Right,
  Paperclip,
];
elementIcons.forEach((comp) => {
  if (comp.name) app.component(comp.name, comp);
});

app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.use(Antd);
app.use(AntDesignXVue);

app.mount("#app");
