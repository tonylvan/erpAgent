<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  // Set page title
  document.title = 'ERP 知识图谱平台'
})
</script>

<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<style>
html,
body,
#app,
.app-container {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  font-family:
    system-ui,
    -apple-system,
    "Segoe UI",
    Roboto,
    "Helvetica Neue",
    Arial,
    sans-serif;
  color: #0f172a;
  background: #e2e8f0;
}
</style>
