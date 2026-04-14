<template>
  <div class="welcome-page">
    <section class="headline-card">
      <div class="headline-top">
        <div>
          <div class="eyebrow">总览</div>
          <h1>管理员总览</h1>
        </div>
        <div class="status-chip">系统运行正常</div>
      </div>

      <p class="headline-desc">
        你可以在这里处理平台审核、查看运营概览，以及管理用户相关事务。
      </p>

      <div class="action-row">
        <button class="primary-btn" @click="$router.push('/admin/videos')">进入视频管理</button>
        <button class="secondary-btn" @click="$router.push('/admin/dashboard')">查看数据概览</button>
      </div>
    </section>

    <section class="content-grid">
      <el-card class="panel-card">
        <template #header>
          <div class="panel-header">
            <span>快捷入口</span>
          </div>
        </template>

        <div class="shortcut-list">
          <button class="shortcut-item" @click="$router.push('/admin/videos')">
            <span class="shortcut-title">视频管理</span>
            <span class="shortcut-desc">审核、下架、预览和删除视频内容</span>
          </button>
          <button class="shortcut-item" @click="$router.push('/admin/users')">
            <span class="shortcut-title">用户管理</span>
            <span class="shortcut-desc">查看用户状态并处理密码重置申请</span>
          </button>
          <button class="shortcut-item" @click="$router.push('/admin/dashboard')">
            <span class="shortcut-title">数据概览</span>
            <span class="shortcut-desc">查看新增用户、分类分布和热门视频</span>
          </button>
        </div>
      </el-card>

      <el-card class="panel-card">
        <template #header>
          <div class="panel-header">
            <span>今日建议</span>
          </div>
        </template>

        <div class="check-list">
          <div class="check-item">
            <span class="check-dot"></span>
            <span>优先处理待审核视频，保持内容流转及时。</span>
          </div>
          <div class="check-item">
            <span class="check-dot"></span>
            <span>检查异常账号与违规内容，降低平台风险。</span>
          </div>
          <div class="check-item">
            <span class="check-dot"></span>
            <span>结合概览页数据，观察近期内容与用户变化。</span>
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<style scoped>
.welcome-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.headline-card {
  padding: 28px 30px;
  border-radius: 24px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(255, 255, 255, 0.88);
  box-shadow:
    0 14px 30px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.headline-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  font-size: 12px;
  font-weight: 700;
  color: #667085;
  letter-spacing: 0.04em;
}

.headline-card h1 {
  margin: 10px 0 0;
  font-size: 32px;
  line-height: 1.15;
  letter-spacing: -0.04em;
  color: #111827;
}

.headline-desc {
  margin: 14px 0 0;
  max-width: 680px;
  color: #667085;
  font-size: 15px;
  line-height: 1.75;
}

.status-chip {
  flex-shrink: 0;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.06);
  color: #344054;
  font-size: 12px;
  font-weight: 700;
}

.action-row {
  margin-top: 22px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn {
  height: 42px;
  padding: 0 18px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.primary-btn {
  border: none;
  background: #111827;
  color: #fff;
}

.secondary-btn {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: #fff;
  color: #111827;
}

.primary-btn:hover,
.secondary-btn:hover {
  transform: translateY(-1px);
}

.content-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 20px;
}

.panel-card {
  overflow: hidden;
}

.panel-header {
  font-size: 17px;
  font-weight: 700;
  color: #111827;
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shortcut-item {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(248, 250, 252, 0.82);
  border-radius: 18px;
  padding: 18px 18px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.shortcut-item:hover {
  background: rgba(243, 244, 246, 0.95);
  transform: translateY(-1px);
}

.shortcut-title {
  display: block;
  color: #111827;
  font-size: 16px;
  font-weight: 700;
}

.shortcut-desc {
  display: block;
  margin-top: 6px;
  color: #667085;
  font-size: 14px;
  line-height: 1.65;
}

.check-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.check-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  color: #475467;
  font-size: 14px;
  line-height: 1.7;
}

.check-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.check-dot {
  width: 8px;
  height: 8px;
  margin-top: 8px;
  border-radius: 50%;
  background: #111827;
  flex-shrink: 0;
}

@media (max-width: 960px) {
  .headline-top,
  .content-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .headline-card h1 {
    font-size: 28px;
  }
}
</style>
