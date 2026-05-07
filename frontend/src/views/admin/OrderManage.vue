<template>
  <el-card class="page-card">
    <template #header>
      <div class="card-header">
        <div>
          <div class="page-title">订单管理</div>
          <div class="page-subtitle">查看所有用户的历史订单与支付状态</div>
        </div>

        <div class="toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索订单号、用户名、邮箱或订单名称"
            :prefix-icon="Search"
            class="search-input"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />

          <el-select
            v-model="statusFilter"
            placeholder="支付状态"
            class="status-filter"
            clearable
            @change="handleSearch"
          >
            <el-option label="全部状态" value="" />
            <el-option label="待支付" value="WAIT_BUYER_PAY" />
            <el-option label="支付成功" value="TRADE_SUCCESS" />
            <el-option label="交易完成" value="TRADE_FINISHED" />
          </el-select>

          <el-button type="primary" @click="handleSearch">刷新</el-button>
        </div>
      </div>
    </template>

    <el-table :data="tableData" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="order_no" label="订单号" min-width="210" show-overflow-tooltip />
      <el-table-column label="用户信息" min-width="220">
        <template #default="scope">
          <div class="user-cell">
            <div class="user-name">{{ scope.row.username || '未知用户' }}</div>
            <div class="user-email">{{ scope.row.email || '暂无邮箱' }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="subject" label="订单名称" min-width="180" show-overflow-tooltip />
      <el-table-column label="认证类型" width="120">
        <template #default="scope">
          {{ formatVerType(scope.row.target_ver_type) }}
        </template>
      </el-table-column>
      <el-table-column label="金额" width="100" align="center">
        <template #default="scope">
          ¥{{ formatAmount(scope.row.total_amount) }}
        </template>
      </el-table-column>
      <el-table-column label="支付状态" width="120" align="center">
        <template #default="scope">
          <el-tag :type="statusTagType(scope.row.trade_status)" effect="plain" round>
            {{ formatStatus(scope.row.trade_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50]"
        :total="total"
        @current-change="loadData"
        @size-change="handleSizeChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { getAdminOrders } from '../../api/admin';

const loading = ref(false);
const tableData = ref([]);
const searchQuery = ref('');
const statusFilter = ref('');
const page = ref(1);
const pageSize = ref(10);
const total = ref(0);

const formatStatus = (status) => {
  const map = {
    WAIT_BUYER_PAY: '待支付',
    TRADE_SUCCESS: '支付成功',
    TRADE_FINISHED: '交易完成'
  };
  return map[status] || status || '未知状态';
};

const statusTagType = (status) => {
  const map = {
    WAIT_BUYER_PAY: 'warning',
    TRADE_SUCCESS: 'success',
    TRADE_FINISHED: 'info'
  };
  return map[status] || 'info';
};

const formatVerType = (type) => {
  const map = {
    1: '个人认证',
    2: '音乐人认证'
  };
  return map[type] || '未设置';
};

const formatAmount = (amount) => {
  const value = Number(amount || 0);
  return value.toFixed(2);
};

const loadData = async () => {
  loading.value = true;
  try {
    const res = await getAdminOrders({
      q: searchQuery.value,
      status: statusFilter.value,
      page: page.value,
      page_size: pageSize.value
    });
    const payload = res.data.data || {};
    tableData.value = payload.list || [];
    total.value = payload.total || 0;
  } catch (error) {
    ElMessage.error('订单数据加载失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  page.value = 1;
  loadData();
};

const handleSizeChange = () => {
  page.value = 1;
  loadData();
};

onMounted(() => loadData());
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

.search-input {
  width: 300px;
}

.status-filter {
  width: 148px;
}

.user-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.user-name {
  font-weight: 600;
  color: #111827;
}

.user-email {
  font-size: 12px;
  color: #667085;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 980px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .status-filter {
    width: 100%;
  }

  .pagination-wrap {
    justify-content: center;
    overflow-x: auto;
  }
}
</style>
