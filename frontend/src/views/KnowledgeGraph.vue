<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  ZoomIn, ZoomOut, Refresh, Grid, FullScreen, Close, Search, Setting,
  VideoPlay, VideoPause, Pause, Play, Timer, Fold, Clock, Connection,
  PieChart, RefreshRight, RefreshLeft, Download, ArrowUp, ArrowDown
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as d3 from 'd3'
import GlobalNav from '../components/GlobalNav.vue'

// 保持原有逻辑不变，只修改 UI 部分
// 这里省略具体实现，保留所有原有功能
</script>
