<template>
  <div class="home-container">
    
    <FilterBar 
      v-if="!isSearch" 
      :categories="categories" 
      v-model="currentCategory" 
      @change="changeCategory" 
    />

    <div class="home-content-inner">
      
      <div v-if="isSearch">
        <div class="search-filter-bar">
           <el-icon><Filter /></el-icon> 搜索结果：{{ videoList.length }} 条相关视频
        </div>
        <div class="video-list-wrapper search-mode">
          <div v-for="video in videoList" :key="video.id" 
               class="video-card list-card hover-effect" 
               @click="goToVideo(video)"
               @mouseenter="handleMouseEnter(video, 'start')"
               @mouseleave="handleMouseLeave"
          >
            <div class="thumbnail-wrapper">
              <video 
                v-if="hoverVideoId === video.id"
                :id="'preview-' + video.id"
                class="preview-video"
                :src="video.url"
                muted autoplay loop
              ></video>
              <img v-else :src="video.cover_url" class="thumbnail" />
              <span class="duration" v-if="hoverVideoId !== video.id">{{ formatTime(video.duration) }}</span>
            </div>
            <div class="video-info">
              <img :src="video.uploader_avatar" class="uploader-avatar" />
              <div class="text-info">
                <h3 class="video-title" :title="video.title">{{ video.title }}</h3>
                <div class="video-meta">
                  {{ formatCount(video.views) }}次观看 • {{ formatDate(video.upload_time) }}
                </div>
                <div class="search-channel-row">
                  <img :src="video.uploader_avatar" class="search-avatar" />
                  <span class="search-author">
                    {{ video.uploader_name }}
                    <VerificationBadge :type="video.uploader_verification_type" />
                  </span>
                </div>
                <div class="search-desc">{{ video.description || '暂无简介' }}</div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-if="videoList.length === 0" description="没有找到相关视频" />
      </div>

      <div v-else-if="currentCategory !== '全部'">
         <div class="video-grid grid-3-cols" style="margin-top: 20px;">
            <div v-for="video in categoryList" :key="video.id" 
                 class="video-card horizontal-card hover-effect" 
                 @click="goToVideo(video)"
                 @mouseenter="handleMouseEnter(video, 'start')"
                 @mouseleave="handleMouseLeave"
            >
               <div class="thumbnail-wrapper">
                  <video 
                    v-if="hoverVideoId === video.id"
                    :id="'preview-' + video.id"
                    class="preview-video"
                    :src="video.url"
                    muted autoplay loop
                  ></video>
                  <img v-else :src="video.cover_url" class="thumbnail" />
                  
                  <div class="progress-bar-bg" v-if="hoverVideoId !== video.id && video.progress_percent > 0">
                     <div class="progress-bar-fill" :style="{ width: video.progress_percent + '%' }"></div>
                  </div>

                  <span class="duration" v-if="hoverVideoId !== video.id">{{ formatTime(video.duration) }}</span>
                </div>
                <div class="video-info">
                  <img :src="video.uploader_avatar" class="uploader-avatar" />
                  <div class="text-info">
                    <h3 class="video-title" :title="video.title">{{ video.title }}</h3>
                    <div class="channel-name">
                       {{ video.uploader_name }}
                       <VerificationBadge :type="video.uploader_verification_type" />
                    </div>
                    
                    <div class="video-meta" v-if="video.progress > 0">
                        观看至 {{ formatTime(video.progress) }}
                    </div>
                    <div class="video-meta" v-else>
                        {{ formatCount(video.views) }}次观看 • {{ formatDate(video.upload_time) }}
                    </div>

                  </div>
                </div>
            </div>
         </div>
         <el-empty v-if="!loading && categoryList.length === 0" description="该分类下暂无视频" />
      </div>

      <div v-else class="home-sections">
        
        <div class="section-container" v-if="discoverList && discoverList.length > 0">
          <div class="video-grid grid-3-cols">
            <div v-for="video in discoverList" :key="video.id" 
                 class="video-card horizontal-card hover-effect" 
                 @click="goToVideo(video)"
                 @mouseenter="handleMouseEnter(video, 'start')"
                 @mouseleave="handleMouseLeave"
            >
               <div class="thumbnail-wrapper">
                  <video 
                    v-if="hoverVideoId === video.id"
                    :id="'preview-' + video.id"
                    class="preview-video"
                    :src="video.url"
                    muted autoplay loop
                  ></video>
                  <img v-else :src="video.cover_url" class="thumbnail" />
                  <span class="duration" v-if="hoverVideoId !== video.id">{{ formatTime(video.duration) }}</span>
                </div>
                <div class="video-info">
                  <img :src="video.uploader_avatar" class="uploader-avatar" />
                  <div class="text-info">
                    <h3 class="video-title" :title="video.title">{{ video.title }}</h3>
                    <div class="channel-name">
                        {{ video.uploader_name }}
                        <VerificationBadge :type="video.uploader_verification_type" />
                    </div>
                    <div class="video-meta">{{ formatCount(video.views) }}次观看 • {{ formatDate(video.upload_time) }}</div>
                  </div>
                </div>
            </div>
          </div>
        </div>

        <div class="section-container" v-if="shortsList && shortsList.length > 0">
          <div class="section-header shorts-header">
             <el-icon color="#FF0000" size="24" style="margin-right:5px"><VideoPlay /></el-icon>
             <h3>Shorts</h3>
          </div>
          <div class="video-grid grid-5-cols">
             <div v-for="video in shortsList" :key="'shorts-'+video.id" 
                  class="video-card vertical-card hover-effect" 
                  @click="goToVideo(video)"
                  @mouseenter="handleMouseEnter(video, 'start')"
                  @mouseleave="handleMouseLeave"
             >
                  <div class="thumbnail-wrapper vertical">
                    <video 
                      v-if="hoverVideoId === video.id"
                      :id="'preview-' + video.id"
                      class="preview-video"
                      :src="video.url"
                      muted autoplay loop
                      style="object-fit: cover;"
                    ></video>
                    <img v-else :src="video.cover_url" class="thumbnail" />
                    <div class="shorts-overlay" v-if="hoverVideoId !== video.id">
                      <span class="shorts-views">{{ formatCount(video.views) }} 观看</span>
                    </div>
                  </div>
                  <div class="video-info">
                    <div class="text-info">
                      <h3 class="video-title">{{ video.title }}</h3>
                    </div>
                  </div>
             </div>
          </div>
        </div>
        
        <div class="section-container" v-if="mixList && mixList.length > 0">
          <div class="section-header"><h3>为您推荐</h3></div>
          <div class="video-grid grid-3-cols">
             <div v-for="video in mixList" :key="'mix-'+video.id" 
                  class="video-card horizontal-card hover-effect" 
                  @click="goToVideo(video)"
                  @mouseenter="handleMouseEnter(video, 'start')"
                  @mouseleave="handleMouseLeave"
             >
                <div class="thumbnail-wrapper">
                   <video 
                     v-if="hoverVideoId === video.id" 
                     :id="'preview-' + video.id"
                     class="preview-video" 
                     :src="video.url" 
                     muted autoplay loop
                   ></video>
                   <img v-else :src="video.cover_url" class="thumbnail" />
                   <span class="duration" v-if="hoverVideoId !== video.id">{{ formatTime(video.duration) }}</span>
                </div>
                <div class="video-info">
                   <img :src="video.uploader_avatar" class="uploader-avatar" />
                   <div class="text-info">
                     <h3 class="video-title">{{ video.title }}</h3>
                     <div class="channel-name">
                        {{ video.uploader_name }}
                        <VerificationBadge :type="video.uploader_verification_type" />
                     </div>
                     <div class="video-meta">{{ formatCount(video.views) }}次观看</div>
                   </div>
                </div>
             </div>
          </div>
        </div>

        <div class="section-container" v-if="historyList && historyList.length > 0">
          <div class="section-header"><h3>已观看</h3></div>
          <div class="video-grid grid-3-cols">
             <div v-for="video in historyList" :key="'hist-'+video.id" 
                  class="video-card horizontal-card hover-effect" 
                  @click="goToVideo(video)"
                  @mouseenter="handleMouseEnter(video, 'continue')"
                  @mouseleave="handleMouseLeave"
             >
                  <div class="thumbnail-wrapper">
                    <video 
                      v-if="hoverVideoId === video.id"
                      :id="'preview-' + video.id"
                      class="preview-video"
                      :src="video.url"
                      muted autoplay
                    ></video>
                    <img v-else :src="video.cover_url" class="thumbnail" />
                    
                    <div class="progress-bar-bg" v-if="hoverVideoId !== video.id && video.progress_percent > 0">
                      <div class="progress-bar-fill" :style="{ width: video.progress_percent + '%' }"></div>
                    </div>

                    <span class="duration" v-if="hoverVideoId !== video.id">{{ formatTime(video.duration) }}</span>
                  </div>
                  <div class="video-info">
                    <div class="text-info" style="margin-left:0">
                      <h3 class="video-title">{{ video.title }}</h3>
                      <div class="channel-name">
                         {{ video.uploader_name }}
                         <VerificationBadge :type="video.uploader_verification_type" />
                      </div>
                      
                      <div class="video-meta" v-if="video.progress > 0">观看至 {{ formatTime(video.progress) }}</div>
                      <div class="video-meta" v-else>{{ formatCount(video.views) }}次观看</div>
                    </div>
                  </div>
             </div>
          </div>
        </div>

      </div>

      <el-empty v-if="!loading && (!discoverList || discoverList.length === 0) && (!shortsList || shortsList.length === 0) && currentCategory === '全部' && !isSearch" description="这里空空如也" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../store/user';
import { getVideoList } from '../api/video';
import { getRecommendVideos } from '../api/recommend';
import { getMyHistory } from '../api/user'; 
import { Filter, VideoPlay } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import FilterBar from '../components/FilterBar.vue';
import VerificationBadge from '../components/VerificationBadge.vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const categories = ref(['全部']);
const currentCategory = ref('全部');
const loading = ref(false);

const isSearch = computed(() => !!route.query.q);

const videoList = ref([]); 
const categoryList = ref([]); 
const discoverList = ref([]);
const shortsList = ref([]);
const historyList = ref([]);
const mixList = ref([]);

const hoverVideoId = ref(null);

const formatTime = (seconds) => {
  if (!seconds) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const formatDate = (timeStr) => timeStr ? timeStr.split(' ')[0] : '';
const formatCount = (num) => num >= 10000 ? (num/10000).toFixed(1) + '万' : num;

const fetchData = async () => {
  loading.value = true;
  const queryQ = route.query.q || '';
  
  try {
    if (queryQ) {
      const res = await getVideoList({ q: queryQ });
      // 兼容两种响应结构
      const list = res.data.data ? res.data.data : (res.data.list ? res.data.list : res.data);
      videoList.value = Array.isArray(list) ? list : [];
    } else {
      const uid = userStore.token ? userStore.userInfo.id : null;
      const res = await getRecommendVideos(uid); 
      
      // 【修复】适配新版后端接口格式 { list: [], source: '' }
      // 注意：axios 返回的 res.data 才是后端响应体
      const responseData = res.data; 
      
      // 尝试获取列表数据 (兼容旧版 {code:200, data: ...} 和新版 {list: ...})
      let rawList = [];
      if (responseData.list) {
          rawList = responseData.list;
      } else if (responseData.data && Array.isArray(responseData.data)) {
          rawList = responseData.data;
      } else if (responseData.code === 200 && responseData.data && responseData.data.discover) {
          // 旧版复杂结构兼容
          rawList = responseData.data.discover;
      }

      console.log('Backend Response:', responseData); // 调试用
      console.log('Parsed List:', rawList);

      if (rawList && rawList.length > 0) {
        // 前端手动分桶
        discoverList.value = rawList.filter(v => !v.is_short);
        shortsList.value = rawList.filter(v => v.is_short);
        
        // 暂时留空，后续可加独立接口
        historyList.value = []; 
        mixList.value = []; 
        
        // 【修复】恢复完整的分类列表
        // 如果后端返回了 categories 则使用，否则使用默认全集
        if (responseData.categories && responseData.categories.length > 0) {
             categories.value = responseData.categories;
        } else {
             // 调整顺序：常规分类在前，功能性分类在后
             categories.value = ['全部', '科技', '生活', '娱乐', '教育', '电影', '音乐', '游戏', '体育', '最近上传', '已观看'];
        }
      } else {
        discoverList.value = [];
        shortsList.value = [];
      }
    }
  } catch (e) { console.error(e); } finally { loading.value = false; }
};

const changeCategory = async (cat) => {
  currentCategory.value = cat;
  loading.value = true;
  categoryList.value = [];

  try {
    if(route.query.q) { router.push('/'); }
    
    if (cat === '全部') {
      await fetchData();
    } 
    else if (cat === '最近上传') {
      const res = await getVideoList({}); 
      categoryList.value = res.data.data;
    } 
    else if (cat === '已观看') {
      if (!userStore.token) {
        ElMessage.warning('请登录查看已观看视频');
        currentCategory.value = '全部'; 
        await fetchData();
      } else {
        const res = await getMyHistory(userStore.userInfo.id);
        categoryList.value = res.data.data;
      }
    } 
    else {
      const res = await getVideoList({ category: cat });
      categoryList.value = res.data.data;
    }
  } catch(e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const goToVideo = (videoOrId) => {
  const video = typeof videoOrId === 'object' ? videoOrId : { id: videoOrId, is_short: false };
  if (video.is_short) {
    router.push(`/shorts/${video.id}`);
    return;
  }
  router.push(`/video/${video.id}`);
};

const handleMouseEnter = async (video, mode) => {
  hoverVideoId.value = video.id;
  await nextTick();
  const videoEl = document.getElementById(`preview-${video.id}`);
  if (videoEl) {
    if (mode === 'continue' && video.progress) {
      videoEl.currentTime = video.progress;
    } else {
      videoEl.currentTime = 0;
    }
    try { 
      await videoEl.play().catch(e => {
        if (e.name !== 'AbortError') console.warn(e);
      });
    } catch (e) { 
      // ignore
    }
  }
};

const handleMouseLeave = () => { hoverVideoId.value = null; };

watch(() => route.query, fetchData);
onMounted(fetchData);
</script>

<style scoped>
.home-container { width: 100%; }
.home-content-inner { padding: 0 24px 40px 24px; max-width: 2200px; margin: 0 auto; }
.search-filter-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; font-size: 16px; font-weight: 500; color: #0f0f0f; border-bottom: 1px solid #e5e5e5; padding-bottom: 10px; }
.video-grid { display: grid; gap: 20px; row-gap: 40px; }
.grid-3-cols { grid-template-columns: repeat(3, 1fr); }
.grid-5-cols { grid-template-columns: repeat(5, 1fr); }

@media screen and (max-width: 1400px) { .grid-3-cols { grid-template-columns: repeat(3, 1fr); } .grid-5-cols { grid-template-columns: repeat(4, 1fr); } }
@media screen and (max-width: 1100px) { .grid-3-cols { grid-template-columns: repeat(2, 1fr); } .grid-5-cols { grid-template-columns: repeat(3, 1fr); } }
@media screen and (max-width: 768px) { .grid-3-cols { grid-template-columns: 1fr; } .grid-5-cols { grid-template-columns: repeat(2, 1fr); } }

.video-card { cursor: pointer; transition: transform 0.2s; display: flex; flex-direction: column; position: relative; border-radius: 12px; background: #fff; }
.hover-effect { transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s; }
.hover-effect:hover { transform: scale(1.05); z-index: 10; box-shadow: 0 8px 24px rgba(0,0,0,0.15); }

/* 封面容器：注意移除了 background: #000 以消除圆角黑边 */
.horizontal-card .thumbnail-wrapper { 
  position: relative; 
  width: 100%; 
  aspect-ratio: 16 / 9; 
  border-radius: 12px; 
  overflow: hidden;  
  margin-bottom: 12px; 
}
.horizontal-card:hover .thumbnail-wrapper { border-radius: 12px 12px 0 0; }

.vertical-card .thumbnail-wrapper { 
  position: relative; 
  width: 100%; 
  aspect-ratio: 9 / 16; 
  border-radius: 12px; 
  overflow: hidden;  
  margin-bottom: 8px; 
}

.preview-video { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumbnail { width: 100%; height: 100%; object-fit: cover; }
.duration { position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: white; padding: 3px 4px; border-radius: 4px; font-size: 12px; font-weight: 500; }
.shorts-overlay { position: absolute; bottom: 0; left: 0; right: 0; top: 0; background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 30%); display: flex; flex-direction: column; justify-content: flex-end; padding: 10px; pointer-events: none;}
.shorts-views { color: white; font-size: 12px; font-weight: bold; }

/* 【核心新增】进度条样式 */
.progress-bar-bg { 
  position: absolute; 
  bottom: 0; 
  left: 0; 
  width: 100%; 
  height: 4px; 
  background: rgba(255,255,255,0.4); 
  z-index: 2; /* 确保在图片上层 */
}
.progress-bar-fill { 
  height: 100%; 
  background: #FF0000; 
  border-radius: 0 2px 2px 0;
}

.video-info { display: flex; gap: 12px; align-items: flex-start; padding: 0 4px; }
.uploader-avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; background: #ddd; }
.text-info { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.video-title { margin: 0 0 4px 0; font-size: 16px; font-weight: 600; color: #0f0f0f; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.channel-name, .video-meta { font-size: 14px; color: #606060; }
.home-sections { display: flex; flex-direction: column; gap: 40px; margin-top: 20px; }
.section-header { display: flex; align-items: center; margin-bottom: 16px; }
.section-header h3 { margin: 0; font-size: 20px; font-weight: 700; color: #0f0f0f; }
.shorts-header { gap: 8px; color: #0f0f0f; }

.search-mode { display: flex; flex-direction: column; max-width: 1000px; margin: 0 auto; gap: 16px; }
.search-mode .video-card { flex-direction: row; gap: 16px; align-items: flex-start; }
.search-mode .thumbnail-wrapper { width: 360px; max-width: 40%; height: auto; aspect-ratio: 16 / 9; margin-bottom: 0; }
.search-mode .video-info { flex: 1; gap: 0; }
.search-mode .video-title { font-size: 18px; margin-bottom: 6px; }
.search-channel-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #606060; font-size: 12px; }
.search-avatar { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; }
.search-desc { font-size: 12px; color: #606060; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
@media screen and (max-width: 768px) { .search-mode .thumbnail-wrapper { width: 160px; max-width: none; } .search-mode .video-title { font-size: 14px; } .search-desc { display: none; } }
</style>
