import request from './request';

// 获取列表
export function getVideoList(params) {
  return request({
    url: '/video/list',
    method: 'get',
    params // 包含 category, q
  });
}

// 获取详情
export function getVideoDetail(id, userId) {
  return request({
    url: `/video/${id}`,
    method: 'get',
    params: userId ? { user_id: userId } : undefined
  });
}

export function generateAiSummary(videoId, refresh = false) {
  return request({
    url: `/video/${videoId}/ai_summary`,
    method: 'post',
    data: { refresh }
  });
}

// 上传视频 (注意要设置 Content-Type)
export function uploadVideo(formData) {
  return request({
    url: '/video/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

// 删除视频
export function deleteVideo(videoId) {
  return request({ url: `/video/delete/${videoId}`, method: 'delete' });
}

// 提交交互 (收藏/观看)
export function postAction(data) {
  // data: { user_id, video_id, type: 'view'/'favorite'/'unfavorite' }
  return request({ url: '/video/action', method: 'post', data });
}

// 检查收藏状态
export function checkFavStatus(userId, videoId) {
  return request({ 
    url: `/video/check_fav`, 
    method: 'get', 
    params: { user_id: userId, video_id: videoId } 
  });
}

// 1. 上传视频文件 (第一阶段)
export function uploadVideoFile(formData) {
  return request({
    url: '/video/upload_file',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

// 分片上传
export function uploadVideoChunk(formData) {
  return request({
    url: '/video/upload_chunk',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

// 合并分片
export function mergeVideoChunks(data) {
  return request({
    url: '/video/merge_chunks',
    method: 'post',
    data
  });
}

// 2. 发布视频信息 (第二阶段)
export function publishVideo(data) {
  // data: { id, title, description, category, tags, cover_url }
  return request({
    url: '/video/publish',
    method: 'post',
    data
  });
}

export function updateVideo(data) {
  // data: { id, user_id, title, description, visibility }
  return request({ url: '/video/update', method: 'post', data });
}

export function uploadSubtitle(formData) {
  return request({
    url: '/video/upload_subtitle',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

export function getVideosByIds(idsStr) {
  return request({
    url: '/video/batch_info',
    method: 'post',
    data: { ids: idsStr }
  });
}

export function getCreatorStats(userId) {
  return request({
    url: '/video/creator/stats',
    method: 'get',
    params: { user_id: userId }
  });
}
