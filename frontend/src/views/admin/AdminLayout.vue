<template>
  <div class="admin-shell">
    <header class="admin-nav">
      <div class="nav-inner">
        <div class="brand-block">
          <div>
            <div class="brand-title">管理后台</div>
            <div class="brand-subtitle">平台审核中心</div>
          </div>
        </div>

        <nav class="nav-tabs">
          <router-link to="/admin/welcome" class="nav-tab" active-class="active">总览</router-link>
          <router-link to="/admin/dashboard" class="nav-tab" active-class="active">统计</router-link>
          <router-link to="/admin/videos" class="nav-tab" active-class="active">视频管理</router-link>
          <router-link to="/admin/users" class="nav-tab" active-class="active">用户管理</router-link>
        </nav>

        <button class="back-button" @click="$router.push('/')">返回前台</button>
      </div>
    </header>

    <main class="admin-main">
      <section class="hero-panel">
        <div>
          <p class="hero-eyebrow">管理员中心</p>
          <h1 class="hero-title">内容审核、用户治理与运营概览</h1>
          <p class="hero-desc">统一查看平台关键数据，快速处理视频审核、用户封禁与密码重置申请。</p>
        </div>
      </section>

      <section class="page-wrapper">
        <router-view />
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.96), rgba(243, 245, 248, 0.96) 38%, rgba(232, 236, 241, 0.98)),
    linear-gradient(180deg, #f6f7fb 0%, #eef2f7 100%);
  color: #1d1d1f;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.admin-nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  backdrop-filter: blur(24px);
  background: rgba(248, 248, 250, 0.72);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.nav-inner {
  max-width: 1240px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.brand-block {
  display: flex;
  align-items: center;
  min-width: 220px;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.brand-subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.nav-tab {
  padding: 10px 18px;
  border-radius: 999px;
  text-decoration: none;
  color: #667085;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.nav-tab:hover {
  color: #111827;
  background: rgba(255, 255, 255, 0.76);
}

.nav-tab.active {
  color: #111827;
  background: #ffffff;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.back-button {
  border: none;
  height: 42px;
  padding: 0 18px;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 12px 20px rgba(17, 24, 39, 0.18);
}

.back-button:hover {
  transform: translateY(-1px);
}

.admin-main {
  max-width: 1240px;
  margin: 0 auto;
  padding: 28px 24px 40px;
}

.hero-panel {
  padding: 28px 30px;
  border-radius: 28px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(243, 246, 250, 0.94)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(243, 246, 249, 0.98));
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow:
    0 18px 38px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.78);
}

.hero-eyebrow {
  margin: 0 0 8px;
  color: #667085;
  font-size: 13px;
  font-weight: 600;
}

.hero-title {
  margin: 0;
  font-size: 34px;
  line-height: 1.15;
  letter-spacing: -0.04em;
}

.hero-desc {
  margin: 12px 0 0;
  max-width: 720px;
  color: #667085;
  font-size: 15px;
  line-height: 1.7;
}

.page-wrapper {
  margin-top: 24px;
}

@media (max-width: 960px) {
  .nav-inner {
    flex-direction: column;
    align-items: stretch;
  }

  .brand-block {
    min-width: 0;
  }

  .nav-tabs {
    overflow-x: auto;
  }

  .hero-title {
    font-size: 28px;
  }
}
</style>

<style>
.admin-shell .el-card {
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 24px;
  box-shadow:
    0 12px 28px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.82) !important;
  background: rgba(255, 255, 255, 0.9);
}

.admin-shell .el-card__header {
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  padding: 20px 24px;
}

.admin-shell .el-card__body {
  padding: 22px 24px;
}

.admin-shell .el-table {
  --el-table-header-bg-color: rgba(248, 250, 252, 0.84);
  --el-table-row-hover-bg-color: rgba(244, 247, 250, 0.92);
  --el-table-border-color: rgba(15, 23, 42, 0.08);
  font-size: 13px;
}

.admin-shell .el-table th.el-table__cell {
  color: #6b7280;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.02em;
}

.admin-shell .el-button--primary {
  border-radius: 999px;
  background: #111827;
  border-color: #111827;
}

.admin-shell .el-button--primary:hover {
  background: #1f2937;
  border-color: #1f2937;
}

.admin-shell .el-button--default,
.admin-shell .el-button--danger,
.admin-shell .el-button--warning,
.admin-shell .el-button--success {
  border-radius: 999px;
}

.admin-shell .el-input__wrapper,
.admin-shell .el-select__wrapper {
  border-radius: 999px;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.08) inset !important;
}
</style>
