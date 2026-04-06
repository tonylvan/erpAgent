<template>
  <header class="global-nav">
    <div class="nav-container">
      <!-- 左侧：品牌 Logo -->
      <div class="nav-brand">
        <div class="brand-icon">
          <el-icon :size="28"><Connection /></el-icon>
        </div>
        <div class="brand-text">
          <h1>GSD 平台</h1>
          <span>ERP Knowledge Graph Platform</span>
        </div>
      </div>

      <!-- 中间：导航链接 -->
      <nav class="nav-links">
        <router-link 
          to="/" 
          class="nav-link"
          active-class="active"
        >
          <el-icon><Bell /></el-icon>
          <span>预警中心</span>
        </router-link>
        <router-link 
          to="/smart-query" 
          class="nav-link"
          active-class="active"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问数</span>
        </router-link>
        <router-link 
          to="/knowledge-graph" 
          class="nav-link"
          active-class="active"
        >
          <el-icon><Connection /></el-icon>
          <span>知识图谱</span>
        </router-link>
        <router-link 
          to="/tickets" 
          class="nav-link"
          active-class="active"
        >
          <el-icon><Document /></el-icon>
          <span>工单中心</span>
        </router-link>
      </nav>

      <!-- 右侧：操作按钮 -->
      <div class="nav-actions">
        <el-button :icon="Refresh" circle @click="handleRefresh" title="刷新" />
        <el-dropdown trigger="click">
          <el-avatar :size="36" src="https://picsum.photos/80/80" class="user-avatar" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>个人中心</el-dropdown-item>
              <el-dropdown-item>系统设置</el-dropdown-item>
              <el-dropdown-item divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup>
import { 
  Bell, 
  ChatDotRound, 
  Connection, 
  Document, 
  Refresh 
} from '@element-plus/icons-vue'

const handleRefresh = () => {
  location.reload()
}
</script>

<style scoped>
.global-nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

/* Brand Section */
.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.brand-text h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1a202c;
  line-height: 1.2;
}

.brand-text span {
  font-size: 11px;
  color: #718096;
  display: block;
  margin-top: 2px;
}

/* Navigation Links */
.nav-links {
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.04);
  padding: 6px;
  border-radius: 12px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 10px;
  text-decoration: none;
  color: #4a5568;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.8);
  color: #667eea;
}

.nav-link.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.nav-link .el-icon {
  font-size: 18px;
}

/* Actions Section */
.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.user-avatar:hover {
  transform: scale(1.1);
}

/* Responsive */
@media (max-width: 1024px) {
  .nav-links {
    gap: 4px;
  }
  
  .nav-link {
    padding: 10px 14px;
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    height: auto;
    padding: 16px;
    gap: 16px;
  }
  
  .nav-links {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .nav-link {
    padding: 8px 16px;
    font-size: 13px;
  }
  
  .brand-text h1 {
    font-size: 18px;
  }
}
</style>
