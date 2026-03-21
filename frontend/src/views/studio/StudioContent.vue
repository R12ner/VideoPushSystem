<template>
  <div class="content-page">
    <div class="page-header">
      <h3>频道内容</h3>
      <!-- 新增刷新按钮 -->
      <el-button :icon="Refresh" circle size="small" @click="loadData" title="刷新列表" />
    </div>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="视频" name="videos">
        <el-table 
          v-loading="loading"
          :data="videoList" 
          style="width: 100%" 
          :header-cell-style="{background:'#f9f9f9'}"
        >
          <!-- 视频信息列 -->
          <el-table-column label="视频" min-width="300">
            <template #default="scope">
              <div class="video-cell">
                <div class="thumb-wrap">
                  <img :src="scope.row.cover_url" class="cell-thumb" />
                  <span class="duration">{{ formatTime(scope.row.duration) }}</span>
                </div>
                <div class="cell-info">
                  <div class="cell-title">{{ scope.row.title }}</div>
                  <div class="cell-desc">{{ scope.row.description?.substring(0, 30) }}...</div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <!-- 状态列 -->
          <el-table-column label="状态" width="100">
            <template #default="scope">
               <el-tag v-if="scope.row.status == -1" type="info" size="small">草稿</el-tag>
               <el-tag v-else-if="scope.row.status == 0" type="warning" size="small">审核中</el-tag>
               <el-tag v-else-if="scope.row.status == 2" type="danger" size="small">已下架</el-tag>
               <el-tag v-else type="success" size="small">正常</el-tag>
            </template>
          </el-table-column>

          <!-- 可见性列 -->
          <el-table-column label="可见性" width="100">
            <template #default="scope">
               <div style="display:flex;align-items:center;gap:5px;font-size:13px">
                 <el-icon v-if="scope.row.visibility === 'public'" color="#67C23A"><View /></el-icon> 
                 <el-icon v-else color="#909399"><Lock /></el-icon>
                 {{ scope.row.visibility === 'public' ? '公开' : '私享' }}
               </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="upload_time" label="日期" width="160" sortable />
          <el-table-column prop="views" label="观看次数" width="110" sortable />
          
          <!-- 操作列 -->
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="scope">
              <el-button-group>
                
                <!-- 1. 发布按钮 (仅草稿状态显示) -->
                <el-tooltip v-if="scope.row.status == -1" content="提交发布">
                  <el-button type="success" size="small" :icon="Upload" @click="handlePublish(scope.row)" />
                </el-tooltip>

                <!-- 2. 撤回按钮 (仅审核中显示) -->
                <el-tooltip v-if="scope.row.status == 0" content="撤回为草稿">
                  <el-button type="warning" size="small" :icon="Hide" @click="handleRetract(scope.row.id)" />
                </el-tooltip>

                <el-tooltip content="编辑详情">
                  <el-button type="primary" size="small" :icon="Edit" @click="openEditModal(scope.row.id)" />
                </el-tooltip>
                <el-tooltip content="在 YouTube 上查看">
                  <el-button type="info" size="small" :icon="View" @click="windowOpen(scope.row.id)" />
                </el-tooltip>
                <el-tooltip content="永久删除">
                  <el-button type="danger" size="small" :icon="Delete" @click="handleDelete(scope.row.id)" />
                </el-tooltip>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 引入编辑组件 -->
    <VideoEditModal ref="editModalRef" @saved="loadData" @deleted="loadData" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../store/user';
import request from '../../api/request';
import { deleteVideo, updateVideo, publishVideo } from '../../api/video'; // 【新增】引入 publishVideo
import { View, Edit, Delete, Lock, Refresh, Hide, Upload } from '@element-plus/icons-vue'; // 【新增】引入 Upload 图标
import { ElMessage, ElMessageBox } from 'element-plus';
import VideoEditModal from '../../components/VideoEditModal.vue';

const userStore = useUserStore();
const router = useRouter();
const activeTab = ref('videos');
const videoList = ref([]);
const loading = ref(false);
const editModalRef = ref(null);

const loadData = async () => {
  loading.value = true;
  try {
    const res = await request.get(`/video/creator/stats?user_id=${userStore.userInfo.id}`);
    if (res.data.code === 200) {
      videoList.value = res.data.data.all_videos;
    }
  } catch (e) {
    console.error(e);
    ElMessage.error('加载视频列表失败');
  } finally {
    loading.value = false;
  }
};

const formatTime = (seconds) => {
  if (!seconds) return '00:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

// 【新增】发布逻辑 (草稿 -> 审核中)
const handlePublish = (row) => {
  const confirmMsg = row.visibility === 'public'
    ? '确定要提交该视频进行审核吗？'
    : '当前视频为私密，发布后将自动改为公开并进入审核，是否继续？';
  ElMessageBox.confirm(confirmMsg, '发布视频', { type: 'success' })
    .then(async () => {
      try {
        // 发布默认设为公开
        await publishVideo({ id: row.id, visibility: 'public' }); 
        ElMessage.success('已提交审核');
        loadData();
      } catch (e) {
        ElMessage.error('操作失败');
      }
    });
};

// 撤回逻辑 (审核中 -> 草稿)
const handleRetract = (id) => {
  ElMessageBox.confirm('确定要撤回该视频并保存为草稿吗？', '撤回审核', { type: 'info' })
    .then(async () => {
      try {
        await updateVideo({ id, user_id: userStore.userInfo.id, action: 'draft' });
        ElMessage.success('已撤回为草稿');
        loadData();
      } catch (e) {
        ElMessage.error('操作失败');
      }
    });
};

const handleDelete = (id) => {
  ElMessageBox.confirm('永久删除此视频？此操作无法撤销。', '删除视频', { type: 'warning' })
    .then(async () => {
      try {
        await deleteVideo(id);
        ElMessage.success('已删除');
        loadData();
      } catch (e) {
        ElMessage.error('删除失败');
      }
    });
};

const windowOpen = (id) => {
    const url = window.location.origin + `/#/video/${id}`;
    window.open(url, '_blank');
}

const openEditModal = (id) => {
  editModalRef.value.open(id);
};

onMounted(() => loadData());
</script>

<style scoped>
.content-page { background: #fff; padding: 0; min-height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.page-header h3 { margin: 0; }
.video-cell { display: flex; gap: 15px; align-items: flex-start; }
.thumb-wrap { position: relative; width: 120px; height: 68px; flex-shrink: 0; }
.cell-thumb { width: 100%; height: 100%; object-fit: cover; border-radius: 4px; }
.duration { position: absolute; bottom: 2px; right: 2px; background: rgba(0,0,0,0.8); color: white; font-size: 10px; padding: 1px 3px; border-radius: 2px; }
.cell-info { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
.cell-title { font-size: 14px; font-weight: 500; color: #0f0f0f; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;}
.cell-desc { font-size: 12px; color: #606060; }
</style>
