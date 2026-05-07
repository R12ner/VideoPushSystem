import request from './request';

export function getStats() { return request.get('/admin/stats'); }
export function getTwoTowerMetrics() { return request.get('/admin/two_tower_metrics'); }
export function getAdminOrders(params) { return request.get('/admin/orders', { params }); }

export function getAdminVideos(params) { return request.get('/admin/videos', { params }); }
export function auditVideo(data) { return request.post('/admin/video/audit', data); }
export function deleteVideoAdmin(id) { return request.post('/admin/video/delete', { id }); }

export function getAdminUsers(q) { return request.get('/admin/users', { params: { q } }); }
export function banUser(id) { return request.post('/admin/user/ban', { id }); }

export function getResetRequests() { return request.get('/admin/reset_requests'); }
export function sendResetEmail(id) { return request.post('/admin/send_reset_email', { id }); }
