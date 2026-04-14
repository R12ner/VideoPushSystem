<template>
  <el-card class="page-card">
    <template #header>
      <div class="card-header">
        <div>
          <div class="page-title">用户管理</div>
          <div class="page-subtitle">查看用户状态与密码重置申请</div>
        </div>

        <div class="toolbar">
          <div class="segmented-control">
            <button
              class="segment-item"
              :class="{ active: viewMode === 'users' }"
              @click="switchMode('users')"
            >
              用户列表
            </button>
            <button
              class="segment-item"
              :class="{ active: viewMode === 'requests' }"
              @click="switchMode('requests')"
            >
              重置申请
            </button>
          </div>

          <el-input
            v-if="viewMode === 'users'"
            v-model="searchQuery"
            placeholder="搜索用户名或邮箱"
            :prefix-icon="Search"
            class="apple-search"
            clearable
          />
        </div>
      </div>
    </template>

    <el-table v-if="viewMode === 'users'" :data="filteredData">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="头像" width="88">
        <template #default="scope">
          <el-avatar :src="scope.row.avatar" :size="38" />
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="email" label="邮箱" min-width="220" />
      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.is_banned" type="danger" effect="plain" round>已封禁</el-tag>
          <el-tag v-else type="success" effect="plain" round>正常</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="right">
        <template #default="scope">
          <el-button
            v-if="!scope.row.is_admin"
            type="primary"
            link
            @click="handleBan(scope.row)"
          >
            {{ scope.row.is_banned ? '解除封禁' : '封禁用户' }}
          </el-button>
          <span v-else class="muted-text">管理员账号</span>
        </template>
      </el-table-column>
    </el-table>

    <el-table v-else :data="requestsData">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" width="160" />
      <el-table-column prop="email" label="邮箱" min-width="220" />
      <el-table-column prop="created_at" label="申请时间" width="190" />
      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 'pending'" type="warning" effect="plain" round>待处理</el-tag>
          <el-tag v-else-if="scope.row.status === 'sent'" type="success" effect="plain" round>已发送</el-tag>
          <el-tag v-else type="info" effect="plain" round>已完成</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="right">
        <template #default="scope">
          <el-button
            v-if="scope.row.status === 'pending'"
            type="primary"
            link
            @click="handleSendEmail(scope.row)"
            :loading="emailLoading === scope.row.id"
          >
            发送重置邮件
          </el-button>
          <span v-else class="muted-text">无需处理</span>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { getAdminUsers, banUser, getResetRequests, sendResetEmail } from '../../api/admin';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';

const viewMode = ref('users');
const tableData = ref([]);
const requestsData = ref([]);
const searchQuery = ref('');
const emailLoading = ref(null);

const loadUsers = async () => {
  const res = await getAdminUsers();
  tableData.value = res.data.data || [];
};

const loadRequests = async () => {
  const res = await getResetRequests();
  requestsData.value = res.data.data || [];
};

const switchMode = (mode) => {
  viewMode.value = mode;
  if (mode === 'users') {
    loadUsers();
  } else {
    loadRequests();
  }
};

const filteredData = computed(() => {
  if (!searchQuery.value) return tableData.value;
  const query = searchQuery.value.toLowerCase();
  return tableData.value.filter((user) =>
    user.username?.toLowerCase().includes(query) ||
    user.email?.toLowerCase().includes(query)
  );
});

const handleBan = async (row) => {
  await banUser(row.id);
  ElMessage.success(row.is_banned ? '已解除封禁' : '已封禁用户');
  loadUsers();
};

const handleSendEmail = async (row) => {
  emailLoading.value = row.id;
  try {
    const res = await sendResetEmail(row.id);
    if (res.data.code === 200) {
      ElMessage.success('重置邮件已发送');
      loadRequests();
    } else {
      ElMessage.error(res.data.msg || '发送失败');
    }
  } catch (error) {
    ElMessage.error('发送失败');
  } finally {
    emailLoading.value = null;
  }
};

onMounted(() => loadUsers());
</script>

<style scoped>
.page-card {
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.segmented-control {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
}

.segment-item {
  border: none;
  background: transparent;
  color: #667085;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.segment-item.active {
  background: #fff;
  color: #111827;
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.08);
}

.apple-search {
  width: 240px;
}

.muted-text {
  font-size: 12px;
  color: #98a2b3;
}

@media (max-width: 900px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .apple-search {
    width: 100%;
  }
}
</style>
