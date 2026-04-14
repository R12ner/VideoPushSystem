<template>
  <div class="detail-container">
    <div v-if="video" class="main-layout">
      
      <el-row :gutter="24">
        <!-- 左侧：播放器 + 信息 + 评论 -->
        <el-col :span="17" :xs="24">
          <div class="content-wrapper">
            
            <!-- 1. 播放器容器 -->
            <div class="video-container">
              <CustomVideoPlayer 
                ref="videoRef"
                :src="video.url" 
                :autoplay="true"
                :end-screen-data="endScreenVideos"
                :post-roll-data="relatedVideos"
                :subtitle-url="video.subtitle_url"
                @timeupdate="handleTimeUpdate"
                @play="onVideoPlay"
                @pause="onVideoPause"
                @navigate="goToVideo"
              />
              
            </div>
            
            <!-- 2. 视频信息区 -->
            <div class="info-section">
              <h1 class="title">{{ video.title }}</h1>
              
              <div class="action-bar">
                <!-- 左侧：作者信息 + 关注按钮 -->
                <div class="left-meta">
                  <div class="uploader-mini" @click="$router.push(`/@${video.uploader_name}`)">
                    <el-avatar :size="40" :src="video.uploader_avatar" />
                    <div class="uploader-text">
                      <div class="name">{{ video.uploader_name }}
                      <VerificationBadge :type="video.uploader_verification_type" />
                      </div>
                      <div class="subs">{{ channelStats.fans }} 位订阅者</div>
                    </div>
                  </div>
                  
                  <button 
                    class="yt-sub-btn" 
                    :class="{ subscribed: channelStats.is_following }"
                    @click="handleSubscribe"
                  >
                    {{ channelStats.is_following ? '已订阅' : '订阅' }}
                  </button>
                </div>
                
                <!-- 右侧：点赞 & 收藏 -->
                <div class="right-actions">
                  <div class="yt-like-btn" @click="toggleLike" :class="{ active: interaction.is_like }">
                    <el-icon size="20">
                      <svg v-if="interaction.is_like" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-1.91l-.01-.01L23 10z"/></svg>
                      <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M9 21h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.58 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2zM9 9l4.34-4.34L12 10h9v2l-3 7H9V9zM1 9h4v12H1z"/></svg>
                    </el-icon>
                    <span class="like-count">{{ formatCount(currentLikes) }}</span>
                  </div>
                  <div class="yt-action-btn" @click="toggleFav" :class="{ active: interaction.is_fav }">
                    <el-icon size="20" v-if="interaction.is_fav"><StarFilled style="fill: #e6a23c" /></el-icon>
                    <el-icon size="20" v-else><Star /></el-icon>
                    <span>{{ interaction.is_fav ? '已收藏' : '收藏' }}</span>
                  </div>

                  <!-- 编辑按钮 -->
                  <div v-if="isOwner || userStore.userInfo.is_admin" class="yt-action-btn" @click="goToEdit">
                    <el-icon size="20"><Edit /></el-icon> <span>编辑</span>
                  </div>
                </div>
              </div>
              
              <div class="description-box">
                <div class="desc-meta">
                  <span>{{ video.views }}次观看</span> • 
                  <!-- 修复：使用 formatDate -->
                  <span>{{ formatDate(video.upload_time) }}</span>
                </div>
                <div class="desc-text">{{ video.description || '暂无简介' }}</div>
              </div>
              
              <div v-if="!video.is_short" class="ai-summary-card">
                <div class="ai-summary-head">
                  <div class="ai-summary-title-wrap">
                    <div class="ai-summary-icon">
                      <el-icon><MagicStick /></el-icon>
                    </div>
                    <div>
                      <div class="ai-summary-title">AI 总结</div>
                      <div class="ai-summary-note">
                        <span class="info-circle">i</span>
                        <span>质量和准确性可能会有差异</span>
                      </div>
                    </div>
                  </div>
                  <div class="ai-summary-actions">
                    <button
                      v-if="hasAiSummary"
                      class="apple-ai-btn secondary"
                      :disabled="aiSummaryLoading"
                      @click="loadAiSummary(true)"
                    >
                      <el-icon><RefreshRight /></el-icon>
                      <span>重新生成</span>
                    </button>
                    <button
                      class="apple-ai-btn primary"
                      :disabled="aiSummaryLoading"
                      @click="loadAiSummary(false)"
                    >
                      <el-icon v-if="!aiSummaryLoading"><MagicStick /></el-icon>
                      <el-icon v-else class="is-loading"><Loading /></el-icon>
                      <span>{{ aiSummaryLoading ? '生成中...' : (hasAiSummary ? '查看总结' : '生成总结') }}</span>
                    </button>
                  </div>
                </div>

                <div v-if="aiSummaryError" class="ai-summary-error">{{ aiSummaryError }}</div>
                <div v-else-if="aiSummaryLoading" class="ai-summary-loading">
                  <el-skeleton :rows="4" animated />
                </div>
                <div v-else-if="hasAiSummary" class="ai-summary-content">
                  <div class="ai-summary-meta-row">
                    <span class="ai-badge">{{ aiSummaryMeta.source === 'subtitle' ? '字幕摘要' : '元数据摘要' }}</span>
                    <span class="ai-badge subtle" v-if="aiSummaryMeta.cached">已缓存</span>
                    <span class="ai-summary-time" v-if="aiSummaryMeta.generated_at">{{ aiSummaryMeta.generated_at }}</span>
                  </div>
                  <div class="ai-summary-text">{{ aiSummary }}</div>
                </div>
              </div>
            </div>

            <!-- 3. 评论区 -->
            <div class="comment-section">
              <div class="comment-header">
                <h3>{{ comments.length }} 条评论</h3>
                <div class="sort-btn" @click="toggleSort">
                  <el-icon><Sort /></el-icon> 
                  <span>排序方式：{{ sortType === 'hot' ? '最热优先' : '最新优先' }}</span>
                </div>
              </div>
              
              <div class="comment-input">
                <el-avatar :size="40" :src="userStore.userInfo.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'" />
                <div class="input-wrapper">
                  <el-input v-model="commentText" type="textarea" :rows="1" placeholder="添加评论..." class="yt-input" />
                  <div class="input-actions" v-if="commentText">
                    <el-button round size="small" @click="commentText = ''">取消</el-button>
                    <el-button type="primary" round size="small" @click="postComment(null)">评论</el-button>
                  </div>
                </div>
              </div>

              <!-- 评论列表 -->
              <div class="comment-list">
                <div v-for="c in comments" :key="c.id" class="comment-item">
                  <el-avatar :size="40" :src="c.user.avatar" class="c-avatar" />
                  <div class="c-body">
                    <div v-if="c.is_pinned" class="pinned-badge">
                      <el-icon><Top /></el-icon> 由 {{ video.uploader_name }} 置顶
                    </div>

                    <div class="c-header">
                      <span class="c-user">@{{ c.user.username }}
                      <VerificationBadge :type="c.user.verification_type" />
                      </span>
                      <span class="c-time">{{ c.time }}</span>
                    </div>
                    <div class="c-text">{{ c.content }}</div>
                    
                    <div class="c-actions">
                      <div class="c-action-btn" @click="handleLikeComment(c)" :class="{ 'is-liked': c.is_liked }">
                        <svg v-if="c.is_liked" style="width:16px;height:16px;margin-right:4px;" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-1.91l-.01-.01L23 10z"/></svg>
                        <svg v-else style="width:16px;height:16px;margin-right:4px;" viewBox="0 0 24 24" fill="currentColor"><path d="M9 21h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.58 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2zM9 9l4.34-4.34L12 10h9v2l-3 7H9V9zM1 9h4v12H1z"/></svg>
                        {{ c.likes || '' }}
                      </div>
                      <div class="c-action-btn" @click="openReply(c.id, c.user.username)">回复</div>

                      <el-dropdown v-if="isOwner || canDeleteComment(c)" trigger="click" @command="(command) => handleCommentMenu(command, c)">
                        <span class="c-more-btn"><el-icon><MoreFilled /></el-icon></span>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item v-if="isOwner" command="pin">{{ c.is_pinned ? '取消置顶' : '置顶评论' }}</el-dropdown-item>
                            <el-dropdown-item v-if="canDeleteComment(c)" command="delete">删除评论</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>

                    <div v-if="replyTargetId === c.id" class="reply-input-box">
                      <el-input 
                        v-model="replyText" 
                        size="small" 
                        placeholder="写下你的回复..." 
                        ref="replyInputRef"
                      />
                      <div class="reply-btns">
                        <el-button size="small" @click="replyTargetId = null">取消</el-button>
                        <el-button type="primary" size="small" @click="postComment(c.id)">回复</el-button>
                      </div>
                    </div>

                    <div v-if="c.replies && c.replies.length > 0">
                      <div class="replies-toggle" v-if="!c.expanded" @click="c.expanded = true">
                        <el-icon><CaretBottom /></el-icon> 展开 {{ c.replies.length }} 条回复
                      </div>
                      <div v-else>
                        <div v-for="r in c.replies" :key="r.id" class="reply-item">
                          <el-avatar :size="24" :src="r.user.avatar" class="r-avatar" />
                          <div class="r-body">
                            <div class="c-header">
                              <span class="c-user">@{{ r.user.username }}
                              <VerificationBadge :type="r.user.verification_type" />
                              </span>
                              <span class="c-time">{{ r.time }}</span>
                            </div>
                            <div class="c-text">{{ r.content }}</div>
                            <div class="c-actions">
                              <div class="c-action-btn" @click="handleLikeComment(r)" :class="{ 'is-liked': r.is_liked }">
                                <svg v-if="r.is_liked" style="width:14px;height:14px;margin-right:4px;" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-1.91l-.01-.01L23 10z"/></svg>
                                <svg v-else style="width:14px;height:14px;margin-right:4px;" viewBox="0 0 24 24" fill="currentColor"><path d="M9 21h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.58 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2zM9 9l4.34-4.34L12 10h9v2l-3 7H9V9zM1 9h4v12H1z"/></svg>
                                {{ r.likes || '' }}
                              </div>
                              <div class="c-action-btn" @click="openReply(c.id, r.user.username)">回复</div>
                              <el-dropdown v-if="canDeleteComment(r)" trigger="click" @command="(command) => handleCommentMenu(command, r)">
                                <span class="c-more-btn"><el-icon><MoreFilled /></el-icon></span>
                                <template #dropdown>
                                  <el-dropdown-menu>
                                    <el-dropdown-item command="delete">删除评论</el-dropdown-item>
                                  </el-dropdown-menu>
                                </template>
                              </el-dropdown>
                            </div>
                          </div>
                        </div>
                        <div class="replies-toggle" @click="c.expanded = false">
                          <el-icon><CaretTop /></el-icon> 收起
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </div>

          </div>
        </el-col>

        <!-- 右侧：推荐列表 -->
        <el-col :span="7" :xs="24">
          <div class="sidebar-content">
            
            <!-- 播放列表卡片 -->
            <div v-if="playlistVideos.length > 0" class="playlist-panel">
              <div class="panel-header">
                <div class="panel-title">正在播放</div>
                <div class="panel-subtitle">当前播放列表</div>
              </div>
              <div class="panel-list">
                <div 
                  v-for="(v, index) in playlistVideos" 
                  :key="v.id" 
                  class="panel-item" 
                  :class="{ active: String(v.id) === String(video.id) }"
                  @click="goToVideo(v.id, route.query.list)"
                >
                  <div class="panel-index" v-if="String(v.id) !== String(video.id)">{{ index + 1 }}</div>
                  <div class="panel-index" v-else><el-icon><VideoPlay /></el-icon></div>
                  
                  <div class="panel-thumb">
                    <img :src="v.cover_url">
                  </div>
                  <div class="panel-info">
                    <div class="panel-v-title">{{ v.title }}</div>
                    <div class="panel-v-author">{{ v.uploader_name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 相关视频推荐 -->
            <div class="recommend-list">
              <div v-for="item in relatedVideos" :key="item.id" class="related-item" @click="goToVideo(item.id)">
                <div class="related-cover-box">
                  <img :src="item.cover_url" class="related-cover"/>
                  <span class="duration">{{ formatDuration(item.duration) }}</span>
                </div>
                <div class="related-info">
                  <div class="related-title">{{ item.title }}</div>
                  <div class="related-meta">{{ item.uploader_name }}</div>
                  <div class="related-meta">{{ item.views }}次观看</div>
                </div>
              </div>
            </div>
            
          </div>
        </el-col>
      </el-row>
    </div>
    <VideoEditModal ref="editModalRef" @saved="loadPageData(video.id)" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '../store/user';
import { getVideoDetail, postAction, checkFavStatus, generateAiSummary } from '../api/video';
import { getRelatedVideos } from '../api/recommend';
import { getComments, sendComment, deleteComment, likeComment, pinComment, checkInteractionStatus } from '../api/interaction';
import { toggleFollow, getChannelInfo } from '../api/user';
import { getPlaylistVideos } from '../api/playlist'; 
import { getVideosByIds } from '../api/video';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Star, StarFilled, Sort, CaretBottom, CaretTop, MoreFilled, Top, VideoPlay, Edit, MagicStick, RefreshRight, Loading } from '@element-plus/icons-vue';
import CustomVideoPlayer from '../components/CustomVideoPlayer.vue';
import VideoEditModal from '../components/VideoEditModal.vue';
import VerificationBadge from '../components/VerificationBadge.vue';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const videoRef = ref(null);

const video = ref(null);
const relatedVideos = ref([]);
const endScreenVideos = ref([]);
const currentLikes = ref(0);
const interaction = ref({ is_fav: false, is_like: false });
const channelStats = ref({ fans: 0, is_following: false });
const aiSummary = ref('');
const aiSummaryMeta = ref({});
const aiSummaryLoading = ref(false);
const aiSummaryError = ref('');

const comments = ref([]);
const commentText = ref('');
const replyText = ref('');
const replyTargetId = ref(null);
const sortType = ref('hot');

const isVideoPaused = ref(false);

const playlistVideos = ref([]);
const currentVideoTime = ref(0); // 跟踪当前播放时间

let lastSaveTime = Date.now();

const editModalRef = ref(null);
const hasAiSummary = computed(() => aiSummary.value.trim().length > 0);

const isOwner = computed(() => {
  if (!video.value || !userStore.userInfo) return false;
  return String(video.value.uploader_id) === String(userStore.userInfo.id);
});

const loadPageData = async (videoId) => {
  // 重置状态
  interaction.value = { is_fav: false, is_like: false, last_progress: 0 };
  channelStats.value.is_following = false;
  aiSummary.value = '';
  aiSummaryMeta.value = {};
  aiSummaryLoading.value = false;
  aiSummaryError.value = '';
  try {
    const res = await getVideoDetail(videoId);
    video.value = res.data.data;
    currentLikes.value = res.data.data.likes || 0;
    
    if (video.value.end_screen_video_ids) {
        try {
            const esRes = await getVideosByIds(video.value.end_screen_video_ids);
            if(esRes.data.code === 200) {
                endScreenVideos.value = esRes.data.data;
            }
        } catch(e) { console.error('End screen fetch failed', e); }
    } else {
        endScreenVideos.value = [];
    }
    
    // 获取频道信息
    const channelRes = await getChannelInfo({
      author_id: video.value.uploader_id,
      visitor_id: userStore.token ? userStore.userInfo.id : null
    });
    channelStats.value = channelRes.data.data.stats;

    const recRes = await getRelatedVideos(videoId);
    relatedVideos.value = recRes.data.data;

    if (route.query.list) {
      const plRes = await getPlaylistVideos(route.query.list);
      if (plRes.data.code === 200) {
        playlistVideos.value = plRes.data.data;
      }
    } else {
      playlistVideos.value = []; 
    }

    loadComments();

    if (userStore.token) {
      // 1. 获取交互状态（定义 statusRes）
      const statusRes = await checkInteractionStatus(userStore.userInfo.id, videoId);
      interaction.value = statusRes.data.data;

      // 2. 【核心修复】必须在这个 if 内部使用 statusRes
      const lastProg = statusRes.data.data.last_progress;
      if (lastProg > 0) {
        // 确保 DOM 更新后再调用播放器方法
        setTimeout(() => {
          if (videoRef.value) {
            videoRef.value.setCurrentTime(lastProg);
            ElMessage.success(`已为您跳转到上次观看位置`);
            
            // 调用播放器的播放方法（需要确保 CustomVideoPlayer 已更新并暴露了 playVideo）
            if (videoRef.value.playVideo) {
              videoRef.value.playVideo();
            } else {
              // 兼容性处理：如果没更新组件，尝试直接调用原生 play
              console.warn('playVideo method not found, falling back');
              videoRef.value.videoRef?.play(); 
            }
          }
        }, 100);
      }

      // 3. 记录本次观看
      postAction({ user_id: userStore.userInfo.id, video_id: videoId, type: 'view' });
    }
  } catch (e) {
    console.error(e);
    if (e.response && (e.response.status === 404 || e.response.status === 403)) {
      router.replace('/404');
    }
  }
};

const loadAiSummary = async (forceRefresh = false) => {
  if (!video.value || video.value.is_short || aiSummaryLoading.value) return;

  aiSummaryLoading.value = true;
  aiSummaryError.value = '';

  try {
    const res = await generateAiSummary(video.value.id, forceRefresh);
    if (res.data.code === 200) {
      aiSummary.value = res.data.data.summary || '';
      aiSummaryMeta.value = res.data.data || {};
    } else {
      aiSummaryError.value = res.data.msg || 'AI 总结生成失败';
    }
  } catch (e) {
    aiSummaryError.value = e.response?.data?.msg || 'AI 总结生成失败，请稍后重试';
  } finally {
    aiSummaryLoading.value = false;
  }
};

const goToVideo = (vid, playlistId = null) => {
  // 切换视频前保存当前视频进度
  if (video.value && currentVideoTime.value > 0) {
    saveProgress(currentVideoTime.value);
  }
  
  if (playlistId) {
    router.push({ path: `/video/${vid}`, query: { list: playlistId } });
  } else {
    router.push({ path: `/video/${vid}` });
  }
};

const goToEdit = () => {
  editModalRef.value.open(video.value.id);
};

const handleSubscribe = async () => {
  if (!userStore.token) return ElMessage.warning('请先登录');
  if (String(userStore.userInfo.id) === String(video.value.uploader_id)) return ElMessage.warning('不能订阅自己');
  try {
    const res = await toggleFollow({ follower_id: userStore.userInfo.id, followed_id: video.value.uploader_id });
    if (res.data.code === 200) {
      channelStats.value.is_following = res.data.is_following;
      channelStats.value.fans = res.data.fans_count;
      ElMessage.success(res.data.is_following ? '订阅成功' : '已取消订阅');
    }
  } catch (e) { ElMessage.error('操作失败'); }
};

const onVideoPause = () => { 
  isVideoPaused.value = true;
  // 暂停时也保存一次进度
  saveProgress(currentVideoTime.value);
};
const onVideoPlay = () => { isVideoPaused.value = false; };

const loadComments = async () => { const uid = userStore.token ? userStore.userInfo.id : null; const res = await getComments(video.value.id, sortType.value, uid); comments.value = res.data.data.map(c => ({ ...c, expanded: false })); };
const toggleSort = () => { sortType.value = sortType.value === 'hot' ? 'new' : 'hot'; loadComments(); };
const postComment = async (parentId = null) => { if (!userStore.token) return ElMessage.warning('请先登录'); const content = parentId ? replyText.value : commentText.value; if (!content.trim()) return; await sendComment({ user_id: userStore.userInfo.id, video_id: video.value.id, content: content, parent_id: parentId }); commentText.value = ''; replyText.value = ''; replyTargetId.value = null; ElMessage.success('评论成功'); loadComments(); };
const openReply = (rootId, targetUsername = null) => { if (!userStore.token) return ElMessage.warning('请先登录'); replyTargetId.value = rootId; if (targetUsername) { replyText.value = `回复 @${targetUsername} : `; } else { replyText.value = ''; } };
const canDeleteComment = (comment) => userStore.token && String(userStore.userInfo.id) === String(comment.user.id);
const handleLikeComment = async (comment) => { if (!userStore.token) return ElMessage.warning('请先登录'); try { const res = await likeComment(comment.id, userStore.userInfo.id); if (res.data.code === 200) { comment.likes = res.data.likes; comment.is_liked = (res.data.action === 'like'); } } catch (e) { console.error(e); } };
const handleDeleteComment = async (comment) => {
  if (!canDeleteComment(comment)) return;

  try {
    await ElMessageBox.confirm('删除后将无法恢复，是否继续？', '确认删除', {
      confirmButtonText: '继续删除',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await ElMessageBox.confirm('请再次确认，你要删除这条评论吗？', '二次确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await deleteComment(comment.id, userStore.userInfo.id);
    ElMessage.success('评论已删除');
    loadComments();
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('删除失败');
    }
  }
};
const handleCommentMenu = async (command, comment) => {
  if (command === 'pin') {
    await handlePin(comment.id);
    return;
  }

  if (command === 'delete') {
    await handleDeleteComment(comment);
  }
};
const handlePin = async (commentId) => { try { await pinComment({ user_id: userStore.userInfo.id, comment_id: commentId }); ElMessage.success('操作成功'); loadComments(); } catch (e) { ElMessage.error('操作失败'); } };
const toggleLike = async () => { if (!userStore.token) return ElMessage.warning('请先登录'); const isLiking = !interaction.value.is_like; const type = isLiking ? 'like' : 'unlike'; try { interaction.value.is_like = isLiking; if (isLiking) { currentLikes.value += 1; } else { currentLikes.value -= 1; } await postAction({ user_id: userStore.userInfo.id, video_id: video.value.id, type }); } catch (e) { interaction.value.is_like = !isLiking; currentLikes.value = isLiking ? currentLikes.value - 1 : currentLikes.value + 1; ElMessage.error('操作失败'); } };
const toggleFav = async () => { if (!userStore.token) return ElMessage.warning('请先登录'); const type = interaction.value.is_fav ? 'unfavorite' : 'favorite'; try { await postAction({ user_id: userStore.userInfo.id, video_id: video.value.id, type }); interaction.value.is_fav = !interaction.value.is_fav; } catch (e) { ElMessage.error('操作失败'); } };
const handleShare = () => {
   const url = window.location.href;
   navigator.clipboard.writeText(url).then(() => { ElMessage.success('链接已复制'); });
};

// 监听播放时间，触发弹幕 (Removed)
const saveProgress = async (time) => {
  if (!userStore.token || !video.value) return;
  if (isNaN(time) || time < 0) return;
  
  try {
    // 这里的 type: 'progress' 对应后端 video.py 中的 action 逻辑
    await postAction({
      user_id: userStore.userInfo.id,
      video_id: video.value.id,
      type: 'progress',
      progress: Math.floor(time)
    });
  } catch (e) {
    // 静默失败，不打扰用户，但在控制台记录
    console.warn('保存观看进度失败', e);
  }
};

// 修改：handleTimeUpdate 函数
const handleTimeUpdate = (time) => {
  currentVideoTime.value = time;
  
  // 进度保存逻辑 (每 5 秒保存一次)
  const now = Date.now();
  if (now - lastSaveTime > 5000) {
    saveProgress(time);
    lastSaveTime = now;
  }
};

const formatCount = (num) => num >= 10000 ? (num / 10000).toFixed(1) + '万' : num;
const formatDate = (timeStr) => timeStr ? timeStr.split(' ')[0] : '';
const formatDuration = (seconds) => {
  if (!seconds) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

// 快捷键处理 (为了代码完整性保留)
const handleKeydown = (e) => {
  if (e.code === 'Space') {
    e.preventDefault(); 
    // 这里需要操作播放器实例，可以通过 ref 传递方法，或者在 custom-player 内部处理
  }
};

watch(() => route.params.id, (newId) => { if(newId) loadPageData(newId); });

onMounted(() => { 
  if(route.params.id) loadPageData(route.params.id); 
  document.addEventListener('keydown', handleKeydown);
});

// 修改：组件销毁时立即保存一次
onBeforeUnmount(() => {
  if (video.value && currentVideoTime.value > 0) {
    saveProgress(currentVideoTime.value);
  }
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.content-wrapper { background: transparent; margin-bottom: 20px; }
.video-container { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 12px; }
.real-video { width: 100%; height: 100%; }

/* Mobile Adaptation for Detail Page */
@media screen and (max-width: 992px) {
  .detail-container { padding: 0 10px; }
  .el-col { width: 100% !important; flex: 0 0 100%; max-width: 100%; }
  .sidebar-content { margin-top: 20px; }
  .ai-summary-head { flex-direction: column; }
  .ai-summary-actions { justify-content: flex-start; }
}

.info-section { padding: 20px 0; }
.title { font-size: 20px; font-weight: 700; margin: 0 0 10px 0; line-height: 28px; color: #0f0f0f; }
.action-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }
.left-meta { display: flex; align-items: center; gap: 20px; }
.uploader-mini { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.uploader-text .name { font-weight: 600; font-size: 16px; color: #0f0f0f; }
.uploader-text .subs { font-size: 12px; color: #606060; }
.yt-sub-btn { background: #0f0f0f; color: #fff; border: none; padding: 0 16px; height: 36px; border-radius: 18px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
.yt-sub-btn:hover { background: #272727; }
.yt-sub-btn.subscribed { background: #f2f2f2; color: #0f0f0f; }
.yt-sub-btn.subscribed:hover { background: #e5e5e5; }

.right-actions { display: flex; gap: 10px; }
.yt-like-btn, .yt-action-btn { display: flex; align-items: center; height: 36px; border-radius: 18px; background-color: #f2f2f2; padding: 0 16px; cursor: pointer; font-size: 14px; font-weight: 500; color: #0f0f0f; gap: 8px; user-select: none; }
.yt-like-btn:hover, .yt-action-btn:hover { background-color: #e5e5e5; }
.yt-like-btn.active, .yt-action-btn.active { background-color: #0f0f0f; color: #fff; }
.description-box { background-color: #f2f2f2; border-radius: 12px; padding: 12px; margin-top: 10px; font-size: 14px; cursor: pointer; }
.desc-meta { font-weight: 600; color: #0f0f0f; margin-bottom: 8px; }
.desc-text { color: #0f0f0f; line-height: 20px; white-space: pre-wrap; }

.ai-summary-card {
  margin-top: 16px;
  padding: 20px 22px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.95), rgba(247, 249, 252, 0.92) 45%, rgba(240, 244, 248, 0.96)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 246, 249, 0.98));
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(18px);
  position: relative;
  overflow: hidden;
}

.ai-summary-card::before {
  content: "";
  position: absolute;
  top: -30px;
  right: -30px;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(148, 163, 184, 0.14), rgba(148, 163, 184, 0));
  pointer-events: none;
}

.ai-summary-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.ai-summary-title-wrap {
  display: flex;
  gap: 14px;
  align-items: center;
}

.ai-summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(226, 232, 240, 0.9));
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 8px 18px rgba(15, 23, 42, 0.08);
}

.ai-summary-title {
  font-size: 19px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.ai-summary-note {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: #64748b;
}

.info-circle {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(100, 116, 139, 0.14);
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.ai-summary-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.apple-ai-btn {
  height: 38px;
  border: none;
  border-radius: 999px;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.apple-ai-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.apple-ai-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.apple-ai-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #111827, #1f2937 55%, #374151);
  box-shadow: 0 12px 22px rgba(17, 24, 39, 0.18);
}

.apple-ai-btn.secondary {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.ai-summary-loading,
.ai-summary-content,
.ai-summary-error {
  margin-top: 16px;
}

.ai-summary-error {
  color: #c2410c;
  background: rgba(255, 247, 237, 0.98);
  border: 1px solid rgba(251, 146, 60, 0.25);
  border-radius: 18px;
  padding: 13px 15px;
  font-size: 13px;
}

.ai-summary-meta-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  color: #0f172a;
  font-size: 12px;
  font-weight: 600;
}

.ai-badge.subtle {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.ai-summary-time {
  font-size: 12px;
  color: #64748b;
}

.ai-summary-text {
  white-space: pre-wrap;
  color: #0f172a;
  line-height: 1.82;
  font-size: 14px;
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(15, 23, 42, 0.05);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.comment-section { margin-top: 24px; }
.comment-header { display: flex; align-items: center; gap: 30px; margin-bottom: 24px; }
.sort-btn { display: flex; align-items: center; gap: 8px; font-weight: 500; cursor: pointer; font-size: 14px; color: #0f0f0f; }
.comment-input { display: flex; gap: 16px; margin-bottom: 32px; }
.input-wrapper { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.input-actions { display: flex; justify-content: flex-end; gap: 8px; }
.comment-item { display: flex; gap: 16px; margin-bottom: 24px; }
.c-body { flex: 1; }
.pinned-badge { font-size: 12px; color: #fff; background: #606060; display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 2px; margin-bottom: 8px; font-weight: 500; }
.c-header { margin-bottom: 4px; font-size: 13px; }
.c-user { font-weight: 600; color: #0f0f0f; margin-right: 5px; }
.c-time { color: #606060; }
.c-text { font-size: 14px; line-height: 20px; color: #0f0f0f; margin-bottom: 8px; }
.c-actions { display: flex; gap: 16px; align-items: center; color: #606060; font-size: 12px; user-select: none; }
.c-action-btn { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.c-action-btn:hover { color: #0f0f0f; }
.c-action-btn.is-liked { color: #065fd4; }
.c-action-btn.danger { color: #b42318; }
.c-action-btn.danger:hover { color: #7a271a; }
.c-more-btn { transform: rotate(90deg); cursor: pointer; display: none; }
.comment-item:hover .c-more-btn { display: inline-block; }
.reply-input-box { margin-top: 10px; margin-bottom: 10px; }
.reply-btns { margin-top: 8px; display: flex; justify-content: flex-end; gap: 10px; }
.replies-toggle { margin-top: 8px; color: #065fd4; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 5px; width: fit-content; border-radius: 18px; padding: 5px 10px; }
.replies-toggle:hover { background-color: #def1ff; }
.reply-item { display: flex; gap: 10px; margin-top: 10px; margin-bottom: 10px; }

.recommend-list { display: flex; flex-direction: column; gap: 8px; }
.related-item { display: flex; gap: 8px; cursor: pointer; }
.related-cover-box { position: relative; width: 168px; height: 94px; border-radius: 8px; overflow: hidden; flex-shrink: 0; background: #ddd; }
.related-cover { width: 100%; height: 100%; object-fit: cover; }
.duration { position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,0.8); color: white; font-size: 12px; padding: 1px 4px; border-radius: 4px; font-weight: 500; }
.related-info { display: flex; flex-direction: column; gap: 4px; }
.related-title { font-size: 14px; font-weight: 600; color: #0f0f0f; line-height: 20px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.related-meta { font-size: 12px; color: #606060; }

/* 播放列表面板样式 */
.playlist-panel {
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
  margin-bottom: 20px;
}
.panel-header {
  background: #f2f2f2;
  padding: 15px;
  border-bottom: 1px solid #e5e5e5;
}
.panel-title { font-weight: bold; font-size: 16px; margin-bottom: 4px; }
.panel-subtitle { font-size: 12px; color: #606060; }

.panel-list {
  max-height: 400px;
  overflow-y: auto;
}
.panel-item {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.panel-item:hover { background: #f2f2f2; }
.panel-item.active { background: #e5e5e5; }

.panel-index { width: 24px; font-size: 12px; color: #606060; text-align: center; }
.panel-thumb { width: 100px; height: 56px; border-radius: 4px; overflow: hidden; margin: 0 10px; flex-shrink: 0; }
.panel-thumb img { width: 100%; height: 100%; object-fit: cover; }
.panel-info { flex: 1; min-width: 0; }
.panel-v-title { font-size: 14px; font-weight: 600; color: #0f0f0f; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.panel-v-author { font-size: 12px; color: #606060; }
</style>
