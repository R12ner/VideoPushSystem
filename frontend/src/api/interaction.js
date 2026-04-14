import request from './request';

// 获取评论 (支持排序)
export function getComments(videoId, sortBy = 'hot', userId = null) {
  return request({ 
    url: `/interaction/comments`, 
    method: 'get',
    params: { video_id: videoId, sort_by: sortBy, user_id: userId }
  });
}
// 发送评论 (支持回复)
export function sendComment(data) {
  // data: { user_id, video_id, content, parent_id(可选) }
  return request({ url: '/interaction/comment/add', method: 'post', data });
}
// 评论点赞 (新增 userId)
export function deleteComment(commentId, userId) {
  return request({
    url: '/interaction/comment/delete',
    method: 'post',
    data: { comment_id: commentId, user_id: userId }
  });
}
export function likeComment(commentId, userId) {
  return request({ 
    url: '/interaction/comment/like', 
    method: 'post', 
    data: { comment_id: commentId, user_id: userId } 
  });
}
// 置顶评论
export function pinComment(data) {
  // data: { user_id, comment_id }
  return request({ url: '/interaction/comment/pin', method: 'post', data });
}
// 检查点赞/收藏状态
export function checkInteractionStatus(userId, videoId) {
  return request({ 
    url: `/interaction/check_status`, 
    method: 'get', 
    params: { user_id: userId, video_id: videoId }
  });
}
