<template>
  <el-card class="page-card">
    <template #header>
      <div class="card-header">
        <div>
          <div class="page-title">视频管理</div>
          <div class="page-subtitle">统一处理审核、下架、预览与删除操作</div>
        </div>

        <div class="header-actions">
          <el-select
            v-model="filterStatus"
            placeholder="按状态筛选"
            @change="handleStatusChange"
            size="small"
            class="status-filter"
          >
            <el-option label="全部状态" value="" />
            <el-option label="待审核" value="0" />
            <el-option label="已发布" value="1" />
            <el-option label="已下架" value="2" />
          </el-select>
        </div>
      </div>
    </template>

    <el-table :data="tableData" style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="封面" width="120">
        <template #default="scope">
          <div class="video-cover-wrapper">
            <img :src="scope.row.cover_url" class="video-cover" />
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 0" type="warning" effect="plain" round>待审核</el-tag>
          <el-tag v-else-if="scope.row.status === 1" type="success" effect="plain" round>已发布</el-tag>
          <el-tag v-else type="danger" effect="plain" round>已下架</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="240" align="right">
        <template #default="scope">
          <div class="action-links">
            <el-button
              v-if="scope.row.status === 0 || scope.row.status === 2"
              link
              type="primary"
              @click="goToAudit(scope.row.id)"
            >
              去审核
            </el-button>

            <el-button
              v-if="scope.row.status === 1"
              link
              type="warning"
              @click="handleAudit(scope.row, 2)"
            >
              下架视频
            </el-button>

            <el-button
              v-if="scope.row.status === 1"
              link
              type="primary"
              @click="openPreview(scope.row)"
            >
              预览
            </el-button>

            <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getAdminVideos, auditVideo, deleteVideoAdmin } from '../../api/admin';
import { ElMessage, ElMessageBox } from 'element-plus';

const STATUS_CACHE_KEY = 'adminVideoManageStatus';
const router = useRouter();
const route = useRoute();
const tableData = ref([]);
const filterStatus = ref(route.query.status ?? sessionStorage.getItem(STATUS_CACHE_KEY) ?? '');

const loadData = async () => {
  const res = await getAdminVideos({ status: filterStatus.value });
  tableData.value = res.data.data || [];
};

const rememberStatus = () => {
  if (filterStatus.value) {
    sessionStorage.setItem(STATUS_CACHE_KEY, filterStatus.value);
  } else {
    sessionStorage.removeItem(STATUS_CACHE_KEY);
  }
};

const handleStatusChange = () => {
  rememberStatus();
  router.replace({
    path: '/admin/videos',
    query: filterStatus.value ? { status: filterStatus.value } : {}
  });
  loadData();
};

const handleAudit = async (row, status) => {
  await auditVideo({ id: row.id, status });
  ElMessage.success(status === 2 ? '视频已下架' : '审核操作成功');
  loadData();
};

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要永久删除这条视频吗？删除后无法恢复。', '删除确认', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  }).then(async () => {
    await deleteVideoAdmin(row.id);
    ElMessage.success('视频已删除');
    loadData();
  }).catch(() => {});
};

const goToAudit = (id) => {
  rememberStatus();
  router.push({
    path: `/admin/audit/${id}`,
    query: filterStatus.value ? { status: filterStatus.value } : {}
  });
};

const openPreview = (row) => {
  const url = router.resolve({ path: `/video/${row.id}` }).href;
  window.open(url, '_blank');
};

onMounted(() => {
  rememberStatus();
  loadData();
});
</script>

<style scoped>
.page-card {
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.page-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #667085;
}

.status-filter {
  width: 150px;
}

.video-cover-wrapper {
  width: 88px;
  height: 50px;
  border-radius: 12px;
  overflow: hidden;
  background: #f3f4f6;
}

.video-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.action-links {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 2px 14px;
}

@media (max-width: 900px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .status-filter {
    width: 100%;
  }
}
</style>
