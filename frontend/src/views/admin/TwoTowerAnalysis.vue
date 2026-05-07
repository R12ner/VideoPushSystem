<template>
  <div class="analysis-page">
    <section class="top-bar">
      <div>
        <div class="page-title">双塔模型分析</div>
        <div class="page-subtitle">展示最近一次训练的损失曲线与召回指标变化</div>
      </div>
      <el-button type="primary" :loading="loading" @click="loadMetrics">刷新最新结果</el-button>
    </section>

    <div v-if="errorMessage" class="error-card">
      <div class="error-title">暂无训练指标</div>
      <div class="error-text">{{ errorMessage }}</div>
    </div>

    <template v-else>
      <section class="summary-grid">
        <el-card class="info-card">
          <template #header>
            <div class="card-title">训练信息</div>
          </template>
          <div class="info-list">
            <div class="info-row">
              <span class="label">最近训练时间</span>
              <span class="value">{{ metrics.trained_at || '--' }}</span>
            </div>
            <div class="info-row">
              <span class="label">数据集</span>
              <span class="value">{{ metrics.dataset || '--' }}</span>
            </div>
            <div class="info-row">
              <span class="label">Epoch 数</span>
              <span class="value">{{ metrics.config?.epochs ?? '--' }}</span>
            </div>
            <div class="info-row">
              <span class="label">Embedding 维度</span>
              <span class="value">{{ metrics.config?.embedding_dim ?? '--' }}</span>
            </div>
            <div class="info-row">
              <span class="label">Batch Size</span>
              <span class="value">{{ metrics.config?.batch_size ?? '--' }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="info-card compact">
          <template #header>
            <div class="card-title">最新指标</div>
          </template>
          <div class="metric-stack">
            <div class="metric-item">
              <span class="metric-name">Loss</span>
              <span class="metric-value">{{ latestPoint.loss ?? '--' }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-name">Recall@10</span>
              <span class="metric-value">{{ latestPoint.recall_at_10 ?? '--' }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-name">NDCG@10</span>
              <span class="metric-value">{{ latestPoint.ndcg_at_10 ?? '--' }}</span>
            </div>
          </div>
        </el-card>
      </section>

      <section class="chart-grid">
        <el-card>
          <template #header>
            <div class="card-title">损失曲线</div>
          </template>
          <div ref="lossChartRef" class="chart-box"></div>
        </el-card>

        <el-card>
          <template #header>
            <div class="card-title">Recall / NDCG 曲线</div>
          </template>
          <div ref="metricChartRef" class="chart-box"></div>
        </el-card>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { getTwoTowerMetrics } from '../../api/admin';

const loading = ref(false);
const errorMessage = ref('');
const metrics = ref({ config: {}, history: [] });
const lossChartRef = ref(null);
const metricChartRef = ref(null);

let lossChart = null;
let metricChart = null;

const historyPoints = computed(() => metrics.value.history || []);
const latestPoint = computed(() => historyPoints.value[historyPoints.value.length - 1] || {});

const buildXAxis = () => historyPoints.value.map((item) => `Epoch ${item.epoch}`);

const initCharts = async () => {
  await nextTick();
  if (!lossChartRef.value || !metricChartRef.value || !historyPoints.value.length) return;

  lossChart?.dispose();
  metricChart?.dispose();

  lossChart = echarts.init(lossChartRef.value);
  metricChart = echarts.init(metricChartRef.value);

  const xAxisData = buildXAxis();
  const axisColor = '#98a2b3';
  const splitLine = 'rgba(15, 23, 42, 0.08)';

  lossChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 18, top: 26, bottom: 28 },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: splitLine } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: axisColor },
      splitLine: { lineStyle: { color: splitLine } }
    },
    series: [{
      name: 'Loss',
      type: 'line',
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 4, color: '#111827' },
      itemStyle: { color: '#111827' },
      areaStyle: { color: 'rgba(17, 24, 39, 0.08)' },
      data: historyPoints.value.map((item) => item.loss)
    }]
  });

  metricChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: '#667085' }
    },
    grid: { left: 42, right: 18, top: 42, bottom: 28 },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: splitLine } }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: { color: axisColor },
      splitLine: { lineStyle: { color: splitLine } }
    },
    series: [
      {
        name: 'Recall@10',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3, color: '#2563eb' },
        itemStyle: { color: '#2563eb' },
        data: historyPoints.value.map((item) => item.recall_at_10)
      },
      {
        name: 'NDCG@10',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3, color: '#f59e0b' },
        itemStyle: { color: '#f59e0b' },
        data: historyPoints.value.map((item) => item.ndcg_at_10)
      }
    ]
  });
};

const handleResize = () => {
  lossChart?.resize();
  metricChart?.resize();
};

const loadMetrics = async () => {
  loading.value = true;
  errorMessage.value = '';

  try {
    const res = await getTwoTowerMetrics();
    if (res.data.code === 200) {
      metrics.value = {
        config: {},
        history: [],
        ...res.data.data
      };
      await initCharts();
    } else {
      errorMessage.value = res.data.msg || '读取双塔模型训练指标失败';
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.msg || '读取双塔模型训练指标失败';
    metrics.value = { config: {}, history: [] };
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadMetrics();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  lossChart?.dispose();
  metricChart?.dispose();
});
</script>

<style scoped>
.analysis-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.page-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #667085;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
}

.info-card {
  min-height: 220px;
}

.info-card.compact {
  min-height: auto;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-row,
.metric-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.label,
.metric-name {
  color: #667085;
  font-size: 14px;
}

.value,
.metric-value {
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  text-align: right;
}

.metric-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.chart-box {
  height: 340px;
}

.error-card {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 247, 237, 0.95);
  border: 1px solid rgba(251, 146, 60, 0.2);
}

.error-title {
  font-size: 18px;
  font-weight: 700;
  color: #9a3412;
}

.error-text {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: #c2410c;
}

@media (max-width: 960px) {
  .top-bar,
  .summary-grid {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
