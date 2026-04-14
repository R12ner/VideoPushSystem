<template>
  <div class="audit-page">
    <div class="page-top">
      <button class="ghost-back" @click="$router.go(-1)">返回上一页</button>
      <div>
        <div class="page-title">视频审核详情</div>
        <div class="page-subtitle">查看视频信息并执行通过、下架等审核操作</div>
      </div>
    </div>

    <div v-if="video" class="audit-layout">
      <section class="video-panel">
        <div class="player-shell">
          <video :src="video.url" controls autoplay class="audit-player"></video>
        </div>
      </section>

      <section class="side-panel">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <el-tag :type="statusType(video.status)" round>{{ statusText(video.status) }}</el-tag>
            </div>
          </template>

          <div class="info-item cover-row">
            <span class="label">封面</span>
            <img :src="video.cover_url" class="cover-preview" />
          </div>
          <div class="info-item">
            <span class="label">标题</span>
            <span class="value strong">{{ video.title }}</span>
          </div>
          <div class="info-item">
            <span class="label">作者</span>
            <span class="value">{{ video.uploader_name }}（ID: {{ video.uploader_id }}）</span>
          </div>
          <div class="info-item">
            <span class="label">分类</span>
            <el-tag size="small" round>{{ video.category || '未分类' }}</el-tag>
          </div>
          <div class="info-item">
            <span class="label">简介</span>
            <p class="value desc">{{ video.description || '暂无简介' }}</p>
          </div>
          <div class="info-item">
            <span class="label">标签</span>
            <span class="value">{{ video.tags || '暂无标签' }}</span>
          </div>
          <div class="info-item">
            <span class="label">上传时间</span>
            <span class="value">{{ video.upload_time }}</span>
          </div>
        </el-card>

        <el-card class="action-card">
          <template #header>
            <div class="card-header">
              <span>审核操作</span>
            </div>
          </template>

          <div class="action-buttons">
            <el-button type="success" size="large" @click="handleAudit(1)">通过并发布</el-button>
            <el-button type="danger" size="large" @click="handleAudit(2)">拒绝或下架</el-button>
            <el-button size="large" @click="$router.go(-1)">暂不处理，返回列表</el-button>
          </div>
        </el-card>
      </section>
    </div>

    <el-skeleton v-else :rows="10" animated />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getVideoDetail } from '../../api/video';
import { auditVideo } from '../../api/admin';
import { ElMessage, ElMessageBox } from 'element-plus';

const route = useRoute();
const router = useRouter();
const video = ref(null);
const videoId = route.params.id;

const loadData = async () => {
  try {
    const res = await getVideoDetail(videoId);
    if (res.data.code === 200) {
      video.value = res.data.data;
    }
  } catch (error) {
    ElMessage.error('无法加载视频信息，可能已被删除');
  }
};

const handleAudit = (status) => {
  const actionText = status === 1 ? '通过并发布' : '拒绝或下架';

  ElMessageBox.confirm(`确定要${actionText}这条视频吗？`, '审核确认', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: status === 1 ? 'success' : 'warning'
  }).then(async () => {
    try {
      await auditVideo({ id: videoId, status });
      ElMessage.success('审核操作成功');
      router.push('/admin/videos');
    } catch (error) {
      ElMessage.error('审核操作失败');
    }
  }).catch(() => {});
};

const statusType = (status) => {
  if (status === 0) return 'warning';
  if (status === 1) return 'success';
  return 'danger';
};

const statusText = (status) => {
  if (status === 0) return '待审核';
  if (status === 1) return '已发布';
  return '已下架';
};

onMounted(() => loadData());
</script>

<style scoped>
.audit-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ghost-back {
  height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.84);
  color: #111827;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.page-subtitle {
  margin-top: 4px;
  color: #667085;
  font-size: 13px;
}

.audit-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 20px;
  align-items: start;
}

.video-panel {
  min-height: 640px;
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, #09090b, #1f2937);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
}

.player-shell {
  width: 100%;
  height: 100%;
}

.audit-player {
  width: 100%;
  height: 100%;
  min-height: 640px;
  object-fit: contain;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
  color: #111827;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
  font-size: 14px;
}

.cover-row {
  align-items: center;
}

.label {
  width: 72px;
  flex-shrink: 0;
  color: #667085;
  font-weight: 600;
}

.value {
  flex: 1;
  color: #344054;
  word-break: break-word;
}

.value.strong {
  font-weight: 700;
  color: #111827;
}

.desc {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
}

.cover-preview {
  width: 150px;
  height: 84px;
  object-fit: cover;
  border-radius: 16px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-buttons .el-button {
  margin-left: 0;
  height: 46px;
}

@media (max-width: 1100px) {
  .audit-layout {
    grid-template-columns: 1fr;
  }

  .video-panel,
  .audit-player {
    min-height: 420px;
  }
}
</style>
