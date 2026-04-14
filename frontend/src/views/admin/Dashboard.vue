<template>
  <div class="dashboard-page">
    <section class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-label">用户总数</div>
        <div class="stat-value">{{ stats.total_users || 0 }}</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-label">视频总数</div>
        <div class="stat-value">{{ stats.total_videos || 0 }}</div>
      </el-card>
      <el-card class="stat-card accent">
        <div class="stat-label">待审核视频</div>
        <div class="stat-value">{{ stats.pending_videos || 0 }}</div>
      </el-card>
    </section>

    <section class="charts-grid">
      <el-card>
        <template #header>
          <div class="section-head">
            <div>
              <div class="section-title">近 7 日新增用户</div>
              <div class="section-subtitle">观察平台用户增长趋势</div>
            </div>
          </div>
        </template>
        <div ref="userChartRef" class="chart-box"></div>
      </el-card>

      <el-card>
        <template #header>
          <div class="section-head">
            <div>
              <div class="section-title">视频分类分布</div>
              <div class="section-subtitle">查看当前内容结构占比</div>
            </div>
          </div>
        </template>
        <div ref="pieChartRef" class="chart-box"></div>
      </el-card>
    </section>

    <section class="full-chart">
      <el-card>
        <template #header>
          <div class="section-head">
            <div>
              <div class="section-title">热门视频前十</div>
              <div class="section-subtitle">按播放量展示最受欢迎的视频</div>
            </div>
          </div>
        </template>
        <div ref="barChartRef" class="chart-box chart-box-large"></div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import { getStats } from '../../api/admin';

const stats = ref({});
const userChartRef = ref(null);
const pieChartRef = ref(null);
const barChartRef = ref(null);

let userChart = null;
let pieChart = null;
let barChart = null;

const baseTextColor = '#475467';
const titleColor = '#111827';
const gridLineColor = 'rgba(15, 23, 42, 0.08)';

const initCharts = (data) => {
  if (userChartRef.value) {
    userChart?.dispose();
    userChart = echarts.init(userChartRef.value);
    userChart.setOption({
      grid: { left: 36, right: 20, top: 30, bottom: 26 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: data.chart_users?.dates || [],
        axisLine: { lineStyle: { color: gridLineColor } },
        axisLabel: { color: baseTextColor }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: gridLineColor } },
        axisLabel: { color: baseTextColor }
      },
      series: [{
        data: data.chart_users?.counts || [],
        type: 'line',
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 4, color: '#111827' },
        itemStyle: { color: '#111827' },
        areaStyle: { color: 'rgba(17, 24, 39, 0.08)' }
      }]
    });
  }

  if (pieChartRef.value) {
    pieChart?.dispose();
    pieChart = echarts.init(pieChartRef.value);
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: {
        bottom: 0,
        textStyle: { color: baseTextColor }
      },
      series: [{
        name: '分类占比',
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '44%'],
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 3 },
        label: { color: titleColor },
        data: data.chart_category || []
      }]
    });
  }

  if (barChartRef.value) {
    barChart?.dispose();
    barChart = echarts.init(barChartRef.value);
    barChart.setOption({
      grid: { left: 40, right: 20, top: 20, bottom: 70 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: data.chart_top10?.titles || [],
        axisLabel: { interval: 0, rotate: 24, color: baseTextColor },
        axisLine: { lineStyle: { color: gridLineColor } }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: gridLineColor } },
        axisLabel: { color: baseTextColor }
      },
      series: [{
        data: data.chart_top10?.views || [],
        type: 'bar',
        barWidth: 24,
        itemStyle: {
          borderRadius: [12, 12, 4, 4],
          color: '#64748b'
        }
      }]
    });
  }
};

const handleResize = () => {
  userChart?.resize();
  pieChart?.resize();
  barChart?.resize();
};

onMounted(async () => {
  const res = await getStats();
  if (res.data.code === 200) {
    stats.value = res.data.data;
    initCharts(res.data.data);
    window.addEventListener('resize', handleResize);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  userChart?.dispose();
  pieChart?.dispose();
  barChart?.dispose();
});
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.stat-card {
  min-height: 150px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-card.accent {
  background: linear-gradient(135deg, rgba(255, 248, 235, 0.98), rgba(255, 243, 219, 0.96));
}

.stat-label {
  font-size: 14px;
  color: #667085;
}

.stat-value {
  margin-top: 12px;
  font-size: 42px;
  line-height: 1;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.04em;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #667085;
}

.chart-box {
  height: 320px;
}

.chart-box-large {
  height: 360px;
}

@media (max-width: 960px) {
  .stats-grid,
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
