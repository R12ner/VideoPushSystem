<template>
  <div class="upload-page">
    
    <!-- 1. 初始状态：文件拖拽上传区 -->
    <div v-if="!isDialogVisible && !isEditMode" class="upload-trigger-area">
      <div class="upload-card">
        <div class="upload-icon-circle">
          <el-icon size="60" color="#909090"><UploadFilled /></el-icon>
        </div>
        <h2 style="margin-top:20px;color:#0f0f0f">上传视频</h2>
        <p style="color:#606060;font-size:14px;margin-bottom:30px">将视频文件拖放到此处进行上传</p>
        <el-button type="primary" size="large" @click="triggerFile" round>选择文件</el-button>
        <input type="file" ref="fileInput" accept="video/*" style="display: none" @change="handleFileSelected" />
      </div>
    </div>

    <!-- 2. 分步编辑弹窗 -->
    <el-dialog 
      v-model="isDialogVisible" 
      :show-close="false" 
      class="yt-upload-dialog"
      :fullscreen="true"
      destroy-on-close
    >
      <!-- 弹窗头部 -->
      <template #header>
        <div class="dialog-header">
          <div class="header-left-title">{{ isEditMode ? '视频详情' : (form.title || '上传视频') }}</div>
          
          <div class="step-indicator">
            <div class="step-item" :class="{ active: currentStep >= 0, finished: currentStep > 0 }">详细信息</div>
            <div class="step-line"></div>
            <div class="step-item" :class="{ active: currentStep >= 1, finished: currentStep > 1 }">视频元素</div>
            <div class="step-line"></div>
            <div class="step-item" :class="{ active: currentStep >= 2, finished: currentStep > 2 }">检查</div>
            <div class="step-line"></div>
            <div class="step-item" :class="{ active: currentStep >= 3, finished: currentStep > 3 }">公开范围</div>
          </div>

          <div class="header-actions">
            <span v-if="!isEditMode && uploadPercentage < 100" class="upload-status">正在上传 {{ Math.round(uploadPercentage) }}% ...</span>
            <span v-else class="upload-status success">{{ isEditMode ? '更改已保存' : '上传完成' }}</span>
            <el-icon class="close-btn" @click="handleClose"><Close /></el-icon>
          </div>
        </div>
        <el-progress v-if="!isEditMode && uploadPercentage < 100" :percentage="uploadPercentage" :show-text="false" :stroke-width="2" class="top-progress" />
      </template>

      <div class="dialog-body">
        <div class="body-content">
          <!-- 左侧内容区 (保持不变) -->
          <div class="left-form-section">
            
            <!-- STEP 0: 详细信息 -->
            <div v-show="currentStep === 0" class="step-content">
              <h3 class="section-title">详细信息</h3>
              <div class="yt-input-box">
                <label>标题 (必填)</label>
                <el-input v-model="form.title" type="textarea" autosize placeholder="添加标题" maxlength="100" show-word-limit />
              </div>
              <div class="yt-input-box mt-4">
                <label>说明</label>
                <el-input v-model="form.description" type="textarea" :rows="5" placeholder="向观众介绍你的视频" maxlength="5000" show-word-limit />
              </div>
              <div class="form-group mt-4">
                <label class="field-label">缩略图</label>
                <div class="helper-text">选择或上传一张图片，让你的视频脱颖而出。</div>
                <div class="thumbnail-selector">
                  <div class="thumb-box upload-box" @click="triggerCoverSelect" :class="{ selected: isCustomCoverSelected }">
                     <img v-if="customCoverUrl" :src="customCoverUrl" class="thumb-img" />
                     <div v-else class="upload-placeholder"><el-icon><Picture /></el-icon><span>上传缩略图</span></div>
                  </div>
                  <div v-for="(img, idx) in autoCovers" :key="idx" class="thumb-box auto-box" :class="{ selected: form.cover_url === img && !isCustomCoverSelected }" @click="selectAutoCover(img)">
                    <img :src="img" class="thumb-img" />
                  </div>
                  <div v-if="autoCovers.length === 0" class="thumb-box skeleton" v-for="i in 1"><span style="font-size:12px;color:#999">自动缩略图</span></div>
                </div>
                <input type="file" ref="coverInput" accept="image/*" style="display: none" @change="handleCoverSelected" />
              </div>
              <div class="form-row mt-4">
                <div class="form-col">
                  <label class="field-label">分类</label>
                  <el-select v-model="form.category" placeholder="选择" style="width: 100%">
                    <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
                  </el-select>
                </div>
              </div>
               <div class="form-group mt-4">
                  <label class="field-label">标签</label>
                  <el-input v-model="tagInput" placeholder="输入标签按回车生成" @keyup.enter="addTag" />
                  <div class="tags-container">
                    <el-tag v-for="tag in form.tags" :key="tag" closable @close="removeTag(tag)" class="tag-item">{{ tag }}</el-tag>
                  </div>
               </div>
            </div>

            <!-- STEP 1: 视频元素 -->
            <div v-show="currentStep === 1" class="step-content">
              <h3 class="section-title">视频元素</h3>
              
              <!-- 字幕 -->
              <div class="element-row">
                <div class="ele-icon"><el-icon><List /></el-icon></div>
                <div class="ele-info"><h4>添加字幕</h4><p>添加字幕可让更广泛的受众群体欣赏你的视频</p></div>
                <el-button plain @click="triggerSubtitle" v-if="!form.subtitle_url">添加</el-button>
                <div v-else style="display:flex;align-items:center;gap:10px">
                   <el-tag type="success">已添加字幕</el-tag>
                   <el-button link type="danger" @click="form.subtitle_url = ''">删除</el-button>
                </div>
                <input type="file" ref="subtitleInput" accept=".vtt,.srt,.json" style="display:none" @change="handleSubtitleSelected" />
              </div>
              
              <!-- 片尾画面 -->
              <div class="element-row">
                <div class="ele-icon"><el-icon><VideoPlay /></el-icon></div>
                <div class="ele-info"><h4>添加片尾画面</h4><p>宣传相关内容</p></div>
                <el-button plain @click="openEndScreenModal" v-if="!form.end_screen_video_ids">添加</el-button>
                 <div v-else style="display:flex;align-items:center;gap:10px">
                   <el-tag type="success">已选择 {{ form.end_screen_video_ids.split(',').length }} 个视频</el-tag>
                   <el-button link type="primary" @click="openEndScreenModal">修改</el-button>
                   <el-button link type="danger" @click="form.end_screen_video_ids = ''">删除</el-button>
                </div>
              </div>
            </div>

            <!-- STEP 2: 检查 -->
            <div v-show="currentStep === 2" class="step-content">
              <h3 class="section-title">检查</h3>
              <p style="color:#606060; font-size:14px; margin-bottom: 20px;">我们会检查你的视频是否存在版权问题。</p>
              <div class="check-result">
                <div class="check-row"><span class="check-label">版权</span><span class="check-val success"><el-icon><Check /></el-icon> 未发现问题</span></div>
              </div>
            </div>

            <!-- STEP 3: 公开范围 -->
            <div v-show="currentStep === 3" class="step-content">
              <h3 class="section-title">公开范围</h3>
              <div class="visibility-options">
                <el-radio-group v-model="form.visibility" class="vis-group">
                  <div class="vis-item">
                    <el-radio label="private" size="large">私享</el-radio>
                    <p class="vis-desc">只有你和你看选定的人可以看到视频</p>
                  </div>
                  <div class="vis-item">
                    <el-radio label="public" size="large">公开</el-radio>
                    <p class="vis-desc">所有人都可以搜索和观看</p>
                  </div>
                </el-radio-group>
              </div>
            </div>
          </div>

          <!-- 右侧：固定预览区 -->
          <div class="right-preview-section">
            <div class="preview-card">
              <div class="video-placeholder">
                <video v-if="serverVideoUrl" :src="serverVideoUrl" controls class="preview-video"></video>
                <div v-else class="preview-loading">
                  <el-icon class="is-loading" size="30"><Loading /></el-icon>
                  <p>视频加载中...</p>
                </div>
              </div>
              <div class="preview-meta">
                <div class="meta-row">
                  <span class="label">视频链接</span>
                  <span class="link-val" v-if="videoId">/video/{{ videoId }}</span>
                  <span class="link-val" v-else>...</span>
                  <el-icon class="copy-icon"><CopyDocument /></el-icon>
                </div>
                <div class="filename-row">
                  <div class="label">文件名</div>
                  <div class="val">{{ fileName || form.title }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <div class="footer-left"></div>
          <div class="footer-right">
            <el-button @click="prevStep" v-if="currentStep > 0">上一步</el-button>
            <el-button type="primary" @click="nextStep" v-if="currentStep < 3">下一步</el-button>
            
            <!-- 【核心修改】最后一步显示：保存为草稿 / 发布 -->
            <template v-if="currentStep === 3">
              <el-button @click="submitPublish('draft')" :loading="isPublishing">保存为草稿</el-button>
              <el-button type="primary" @click="submitPublish('publish')" :loading="isPublishing">
                {{ isEditMode ? '保存更改' : '发布' }}
              </el-button>
            </template>
          </div>
        </div>
      </template>

    </el-dialog>
    
    <ImageCropper ref="cropperRef" title="裁剪封面" :aspect-ratio="16/9" @upload="doUploadCustomCover" />

    <!-- 片尾视频选择弹窗 -->
    <el-dialog v-model="endScreenVisible" title="选择片尾推荐视频" width="600px" append-to-body>
       <div class="end-screen-selector">
          <p style="margin-bottom:10px;color:#666">请选择 1-2 个视频用于片尾推荐</p>
          <div v-loading="loadingMyVideos" class="video-select-list">
             <div 
               v-for="v in myVideos" 
               :key="v.id" 
               class="video-select-item"
               :class="{ selected: tempSelectedIds.includes(v.id) }"
               @click="toggleVideoSelection(v.id)"
             >
                <img :src="v.cover_url" class="select-thumb">
                <div class="select-info">
                   <div class="select-title">{{ v.title }}</div>
                   <div class="select-meta">{{ v.upload_time }}</div>
                </div>
                <el-icon v-if="tempSelectedIds.includes(v.id)" class="check-icon" color="#409EFF"><Check /></el-icon>
             </div>
             <el-empty v-if="myVideos.length === 0" description="暂无可用视频" />
          </div>
       </div>
       <template #footer>
          <el-button @click="endScreenVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmEndScreen">确定</el-button>
       </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../store/user';
import { uploadVideoFile, uploadVideoChunk, mergeVideoChunks, publishVideo, updateVideo, getVideoDetail, uploadSubtitle, getCreatorStats } from '../api/video';
import { uploadBanner, getChannelInfo } from '../api/user';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled, Close, Picture, Check, Loading, CopyDocument, List, VideoPlay } from '@element-plus/icons-vue';
import ImageCropper from '../components/ImageCropper.vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const isEditMode = computed(() => !!route.query.id);

const isDialogVisible = ref(false);
const currentStep = ref(0);
const uploadPercentage = ref(0);
const isSubmitting = ref(false);
const isPublishing = ref(false); // 独立发布状态

const fileInput = ref(null);
const coverInput = ref(null);
const subtitleInput = ref(null);
const cropperRef = ref(null);

const videoId = ref(null);
const fileName = ref('');
const serverVideoUrl = ref('');
const autoCovers = ref([]);
const customCoverUrl = ref('');
const isCustomCoverSelected = ref(false);
const tagInput = ref('');

// End Screen logic
const endScreenVisible = ref(false);
const myVideos = ref([]);
const loadingMyVideos = ref(false);
const tempSelectedIds = ref([]);

const form = reactive({
  title: '',
  description: '',
  category: '人物和博客',
  tags: [],
  playlist: '',
  cover_url: '', 
  visibility: 'public',
  subtitle_url: '',
  end_screen_video_ids: '' // "1,2"
});

const categories = ["宠物和动物", "电影和动画", "公益和社会活动", "教育", "科学和技术", "旅游和活动", "汽车和其他交通工具", "人物和博客", "体育", "喜剧", "新闻和政治", "音乐", "游戏", "娱乐", "DIY和生活百科"];

onMounted(async () => {
  if (!userStore.token) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  if (route.query.id) {
    const editId = route.query.id;
    try {
      const res = await getVideoDetail(editId, userStore.userInfo.id);
      if (res.data.code === 200) {
        const v = res.data.data;
        videoId.value = v.id;
        form.title = v.title;
        form.description = v.description;
        form.category = v.category || '人物和博客';
        form.visibility = v.visibility;
        form.cover_url = v.cover_url;
        form.subtitle_url = v.subtitle_url || '';
        form.end_screen_video_ids = v.end_screen_video_ids || '';
        customCoverUrl.value = v.cover_url;
        isCustomCoverSelected.value = true;
        serverVideoUrl.value = v.url;
        fileName.value = v.title + '.mp4';
        form.tags = v.tags ? v.tags.split(',') : [];
        isDialogVisible.value = true;
        uploadPercentage.value = 100; 
      }
    } catch (e) {
      ElMessage.error('获取视频详情失败');
      router.push('/');
    }
  }
});

const openEndScreenModal = async () => {
  endScreenVisible.value = true;
  loadingMyVideos.value = true;
  tempSelectedIds.value = form.end_screen_video_ids ? form.end_screen_video_ids.split(',').map(Number) : [];
  
  try {
     const res = await getCreatorStats(userStore.userInfo.id);
     if (res.data.code === 200) {
        // Filter out current video
        myVideos.value = res.data.data.all_videos.filter(v => String(v.id) !== String(videoId.value));
     }
  } catch(e) {
     console.error(e);
     ElMessage.error("获取视频列表失败");
  } finally {
     loadingMyVideos.value = false;
  }
};

const toggleVideoSelection = (vid) => {
   const idx = tempSelectedIds.value.indexOf(vid);
   if (idx > -1) {
      tempSelectedIds.value.splice(idx, 1);
   } else {
      if (tempSelectedIds.value.length >= 2) {
         ElMessage.warning("最多选择2个视频");
         return;
      }
      tempSelectedIds.value.push(vid);
   }
};

const confirmEndScreen = () => {
   form.end_screen_video_ids = tempSelectedIds.value.join(',');
   endScreenVisible.value = false;
};

const triggerFile = () => fileInput.value.click();
const triggerSubtitle = () => subtitleInput.value.click();

const handleSubtitleSelected = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await uploadSubtitle(formData);
    if (res.data.code === 200) {
      form.subtitle_url = res.data.url;
      ElMessage.success('字幕上传成功');
    } else {
      ElMessage.error(res.data.msg);
    }
  } catch (error) {
    ElMessage.error('上传失败');
  }
  e.target.value = '';
};

// 【核心修改】分片上传逻辑
const handleFileSelected = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  fileName.value = file.name;
  form.title = file.name.replace(/\.[^/.]+$/, "");
  isDialogVisible.value = true;
  currentStep.value = 0;
  uploadPercentage.value = 0;

  // 生成唯一 upload_id (时间戳 + 随机数)
  const uploadId = `${Date.now()}_${Math.floor(Math.random() * 1000)}`;
  
  const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB per chunk
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
  
  try {
    // 【核心优化】并发上传逻辑
    const CONCURRENCY = 3; // 同时上传3个分片
    let completedChunks = 0;

    const uploadChunkTask = async (index) => {
      const start = index * CHUNK_SIZE;
      const end = Math.min(file.size, start + CHUNK_SIZE);
      const chunk = file.slice(start, end);

      const formData = new FormData();
      formData.append('file', chunk);
      formData.append('chunk_index', index);
      formData.append('upload_id', uploadId);

      await uploadVideoChunk(formData);
      completedChunks++;
      uploadPercentage.value = Math.floor((completedChunks / totalChunks) * 90);
    };

    // 创建任务队列
    const tasks = [];
    for (let i = 0; i < totalChunks; i++) {
        tasks.push(() => uploadChunkTask(i));
    }

    // 执行并发控制
    const runPool = async () => {
        const pool = [];
        for (const task of tasks) {
            const p = task().then(() => {
                 pool.splice(pool.indexOf(p), 1);
            });
            pool.push(p);
            if (pool.length >= CONCURRENCY) {
                await Promise.race(pool);
            }
        }
        await Promise.all(pool);
    };

    await runPool();

    // 所有分片上传完成，请求合并
    const mergeData = {
      upload_id: uploadId,
      filename: file.name,
      total_chunks: totalChunks,
      uploader_id: userStore.userInfo.id
    };

    const res = await mergeVideoChunks(mergeData);
    if (res.data.code === 200) {
      uploadPercentage.value = 100;
      const d = res.data.data;
      videoId.value = d.id;
      serverVideoUrl.value = d.url;
      autoCovers.value = d.auto_covers || [];
      if (autoCovers.value.length > 0) form.cover_url = autoCovers.value[0];
      ElMessage.success('视频上传处理完成');
    } else {
      throw new Error(res.data.msg);
    }

  } catch (error) {
    console.error(error);
    ElMessage.error(error.message || '上传失败，请重试');
    isDialogVisible.value = false;
  } finally {
    e.target.value = ''; // Reset input
  }
};

const selectAutoCover = (url) => { form.cover_url = url; isCustomCoverSelected.value = false; };
const triggerCoverSelect = () => coverInput.value.click();
const handleCoverSelected = (e) => { const file = e.target.files[0]; if (file) cropperRef.value.open(file); e.target.value = ''; };
const doUploadCustomCover = async (blob, done) => {
  const formData = new FormData(); formData.append('file', blob, 'cover.jpg');
  try { const res = await uploadBanner(formData); if (res.data.code === 200) { customCoverUrl.value = res.data.url; form.cover_url = res.data.url; isCustomCoverSelected.value = true; done(); } } catch(e) { ElMessage.error('图片处理失败'); }
};

const addTag = () => { const val = tagInput.value.trim(); if (val && !form.tags.includes(val)) { form.tags.push(val); } tagInput.value = ''; };
const removeTag = (tag) => { form.tags = form.tags.filter(t => t !== tag); };
const nextStep = () => { if (currentStep.value < 3) currentStep.value++; };
const prevStep = () => { if (currentStep.value > 0) currentStep.value--; };

// 【核心修改】提交发布 (支持 draft 和 publish)
const submitPublish = async (actionType) => {
  if (!videoId.value) return ElMessage.warning('视频数据未就绪');
  
  isPublishing.value = true;
  try {
    const payload = {
      id: videoId.value,
      title: form.title,
      description: form.description,
      category: form.category,
      tags: form.tags.join(','),
      cover_url: form.cover_url,
      visibility: form.visibility,
      subtitle_url: form.subtitle_url, // Add this
      user_id: userStore.userInfo.id,
      action: actionType // 传入 'draft' 或 'publish'
    };

    let res;
    if (isEditMode.value) {
      res = await updateVideo(payload);
    } else {
      res = await publishVideo(payload);
    }

    if (res.data.code === 200) {
      ElMessage.success(actionType === 'draft' ? '已保存草稿' : (isEditMode.value ? '修改已保存' : '发布成功！'));
      isDialogVisible.value = false;
      router.push('/studio/content');
    } else {
       ElMessage.error(res.data.msg);
    }
  } catch (e) {
    ElMessage.error('操作失败');
  } finally {
    isPublishing.value = false;
  }
};

const handleClose = () => {
  if (!isEditMode.value && currentStep.value < 3) {
      ElMessageBox.confirm('上传尚未完成，确定要取消吗？视频将保存为草稿。', '提示')
        .then(() => { isDialogVisible.value = false; router.push('/studio/content'); })
        .catch(() => {});
  } else {
      isDialogVisible.value = false;
      router.go(-1);
  }
};
</script>

<style scoped>
/* 样式与之前一致 */
.upload-page { display: flex; justify-content: center; align-items: center; height: calc(100vh - 60px); background: #f9f9f9; padding: 10px; }
.upload-trigger-area { width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; }
.upload-card { width: 800px; height: 500px; background: #fff; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: flex; flex-direction: column; justify-content: center; align-items: center; max-width: 100%; }
.upload-icon-circle { width: 120px; height: 120px; background: #f9f9f9; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }

:deep(.yt-upload-dialog) { 
  display: flex; flex-direction: column; margin: 0 !important; 
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
  width: 960px !important; height: 90vh !important; max-height: 800px; 
  border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
  max-width: 98vw; /* Mobile adaption */
}
:deep(.el-dialog__header) { padding: 0; margin: 0; border-bottom: 1px solid #e5e5e5; }
:deep(.el-dialog__body) { padding: 0; flex: 1; overflow: hidden; display: flex; flex-direction: column; }

.dialog-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 24px; height: 60px; box-sizing: border-box; }
.header-left-title { font-weight: 600; font-size: 20px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.close-btn { cursor: pointer; font-size: 24px; color: #606060; }
.top-progress { position: absolute; bottom: 0; left: 0; width: 100%; }

/* Hide steps on small screens */
@media screen and (max-width: 768px) {
  .step-indicator { display: none !important; }
  .body-content { flex-direction: column; padding: 10px !important; }
  .right-preview-section { display: none !important; }
  .upload-card { padding: 20px; height: auto; }
}

.step-indicator { display: flex; align-items: center; flex: 1; justify-content: center; margin: 0 40px; }
.step-item { font-size: 14px; color: #606060; font-weight: 500; cursor: default; }
.step-item.active { color: #065fd4; font-weight: 700; }
.step-item.finished { color: #0f0f0f; }
.step-line { width: 40px; height: 1px; background: #e5e5e5; margin: 0 10px; }
.upload-status { font-size: 12px; color: #065fd4; margin-right: 15px; }
.upload-status.success { color: #000; }

.dialog-body { flex: 1; overflow-y: auto; background: #fff; }
.body-content { display: flex; padding: 24px 40px; gap: 24px; height: 100%; box-sizing: border-box; }

.left-form-section { flex: 1; min-width: 0; overflow-y: auto; padding-right: 10px; }
.section-title { font-size: 24px; font-weight: 600; margin-bottom: 20px; }

.yt-input-box { border: 1px solid #ccc; border-radius: 4px; padding: 10px; transition: border-color 0.2s; }
.yt-input-box:focus-within { border-color: #065fd4; }
.yt-input-box label { font-size: 12px; color: #606060; display: block; margin-bottom: 4px; }
:deep(.el-input__wrapper), :deep(.el-textarea__inner) { box-shadow: none !important; padding: 0; font-size: 15px; color: #0f0f0f; }

.field-label { display: block; font-weight: 500; color: #0f0f0f; margin-bottom: 8px; font-size: 14px; }
.helper-text { font-size: 12px; color: #606060; margin-top: 4px; margin-bottom: 8px; }

.thumbnail-selector { display: flex; gap: 10px; }
.thumb-box { width: 127px; aspect-ratio: 16/9; border: 2px solid transparent; border-radius: 2px; cursor: pointer; overflow: hidden; position: relative; }
.thumb-box.upload-box { border: 1px dashed #ccc; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.thumb-box.selected { border-color: #0f0f0f; border-width: 2px; }
.thumb-img { width: 100%; height: 100%; object-fit: cover; }
.upload-placeholder { display: flex; flex-direction: column; align-items: center; font-size: 12px; color: #606060; gap: 4px; }
.skeleton { background: #f0f0f0; display: flex; align-items: center; justify-content: center; }

.mt-4 { margin-top: 24px; }
.form-row { display: flex; gap: 20px; }
.form-col { flex: 1; }
.tag-item { margin-right: 8px; margin-top: 8px; }

.element-row { display: flex; align-items: center; background: #f9f9f9; padding: 10px 20px; border-radius: 4px; margin-bottom: 10px; }
.ele-icon { margin-right: 15px; font-size: 24px; color: #606060; }
.ele-info { flex: 1; }
.ele-info h4 { margin: 0; font-size: 14px; }
.ele-info p { margin: 4px 0 0; font-size: 12px; color: #606060; }
.check-result { margin-top: 20px; }
.check-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #eee; }
.check-val.success { color: #606060; display: flex; align-items: center; gap: 5px; }

.vis-group { display: flex; flex-direction: column; align-items: flex-start; width: 100%; }
.vis-item { margin-bottom: 15px; border: 1px solid #ccc; padding: 15px; border-radius: 4px; width: 100%; box-sizing: border-box; }
.vis-desc { margin: 5px 0 0 28px; font-size: 12px; color: #606060; }

.right-preview-section { width: 300px; flex-shrink: 0; background: #f9f9f9; padding: 0; display: flex; flex-direction: column; }
.preview-card { position: sticky; top: 0; }
.video-placeholder { width: 100%; aspect-ratio: 16/9; background: #000; display: flex; align-items: center; justify-content: center; color: white; }
.preview-video { width: 100%; height: 100%; }
.preview-meta { padding: 16px; background: #f0f0f0; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px;}
.meta-row { display: flex; justify-content: space-between; font-size: 12px; color: #606060; margin-bottom: 8px; }
.link-val { color: #065fd4; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 150px; }

.dialog-footer { height: 60px; border-top: 1px solid #e5e5e5; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; background: #fff; }

/* End Screen Selection Styles */
.video-select-list { max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.video-select-item { display: flex; gap: 10px; padding: 10px; border: 1px solid #eee; border-radius: 4px; cursor: pointer; transition: background 0.2s; align-items: center; }
.video-select-item:hover { background: #f5f5f5; }
.video-select-item.selected { background: #e6f7ff; border-color: #1890ff; }
.select-thumb { width: 120px; height: 68px; object-fit: cover; border-radius: 4px; flex-shrink: 0; background: #eee; }
.select-info { flex: 1; min-width: 0; }
.select-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.select-meta { font-size: 12px; color: #999; }
.check-icon { font-size: 20px; font-weight: bold; }
</style>
