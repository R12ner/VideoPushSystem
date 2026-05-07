<template>
  <div>
    <el-dialog 
      v-model="visible" 
      width="960px" 
      :show-close="false" 
      class="yt-edit-modal" 
      align-center 
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="edit-header">
           <span class="header-title">{{ form.title || '视频详情' }}</span>
           <div class="header-btns">
              <el-button round @click="handleClose">取消更改</el-button>
              <el-button type="primary" round @click="save" :loading="loading">保存</el-button>
              <el-dropdown trigger="click" @command="handleMenuCommand">
                 <el-icon class="more-btn"><MoreFilled /></el-icon>
                 <template #dropdown>
                   <el-dropdown-menu>
                     <el-dropdown-item command="delete" style="color:red">永久删除</el-dropdown-item>
                   </el-dropdown-menu>
                 </template>
              </el-dropdown>
           </div>
        </div>
      </template>
      
      <div class="edit-body" v-loading="loadingData">
         <!-- 左侧：表单 -->
         <div class="edit-left">
            <div class="yt-input-box">
              <label>标题 (必填)</label>
              <el-input v-model="form.title" type="textarea" autosize maxlength="100" show-word-limit />
            </div>
            <div class="yt-input-box mt-4">
              <label>说明</label>
              <el-input v-model="form.description" type="textarea" :rows="8" maxlength="5000" show-word-limit />
            </div>
            
            <div class="form-section-title mt-4">缩略图</div>
            <div class="thumb-selector">
               <div class="thumb-preview-box" @click="triggerCoverChange">
                  <img v-if="form.cover_url" :src="form.cover_url" class="thumb-img">
                  <div class="thumb-overlay"><el-icon><Picture /></el-icon> 更改</div>
               </div>
               <div class="helper-text">点击图片以上传新封面</div>
            </div>

            <div class="form-section-title mt-4">分类</div>
            <el-select v-model="form.category" placeholder="选择分类" style="width:100%">
               <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
            </el-select>
            
            <div class="form-section-title mt-4">标签</div>
            <el-input v-model="form.tags" placeholder="输入标签，用逗号分隔" />

            <!-- 视频元素编辑 -->
            <div class="form-section-title mt-4">视频元素</div>
            
            <!-- 字幕 -->
            <div class="element-row">
              <div class="ele-icon"><el-icon><List /></el-icon></div>
              <div class="ele-info"><h4>字幕</h4><p>添加字幕文件</p></div>
              <el-button plain size="small" @click="triggerSubtitle" v-if="!form.subtitle_url">添加</el-button>
              <div v-else style="display:flex;align-items:center;gap:10px">
                  <el-tag type="success" size="small">已添加</el-tag>
                  <el-button link type="danger" size="small" @click="form.subtitle_url = ''">删除</el-button>
              </div>
              <input type="file" ref="subtitleInput" accept=".vtt,.srt,.json" style="display:none" @change="handleSubtitleSelected" />
            </div>

            <!-- 片尾画面 -->
            <div class="element-row" style="margin-top: 10px;">
              <div class="ele-icon"><el-icon><VideoPlay /></el-icon></div>
              <div class="ele-info"><h4>片尾画面</h4><p>添加片尾推荐视频</p></div>
              <el-button plain size="small" @click="openEndScreenModal" v-if="!form.end_screen_video_ids">添加</el-button>
              <div v-else style="display:flex;align-items:center;gap:10px">
                  <el-tag type="success" size="small">已选 {{ form.end_screen_video_ids.split(',').length }} 个</el-tag>
                  <el-button link type="primary" size="small" @click="openEndScreenModal">修改</el-button>
                  <el-button link type="danger" size="small" @click="form.end_screen_video_ids = ''">删除</el-button>
              </div>
            </div>

         </div>
         
         <!-- 右侧：预览与设置 -->
         <div class="edit-right">
            <div class="preview-player-card">
               <video v-if="videoUrl" :src="videoUrl" controls class="preview-video"></video>
               <div class="preview-meta">
                  <div class="meta-row"><span class="label">视频链接</span> <span class="val link">/video/{{ videoId }}</span></div>
                  <div class="meta-row"><span class="label">文件名</span> <span class="val">{{ form.title }}.mp4</span></div>
               </div>
            </div>
            
            <div class="setting-box">
               <div class="setting-label">公开范围</div>
               <el-select v-model="form.visibility" style="width:100%">
                  <el-option label="公开" value="public"><div class="vis-opt"><el-icon><View /></el-icon> 公开</div></el-option>
                  <el-option label="私享" value="private"><div class="vis-opt"><el-icon><Lock /></el-icon> 私享</div></el-option>
               </el-select>
               <div class="audit-warning">
                  <el-icon><Warning /></el-icon> 修改标题、简介或可见性后，视频需<b>重新审核</b>。
               </div>
            </div>
         </div>
      </div>
    </el-dialog>

    <!-- 图片裁剪组件 -->
    <ImageCropper ref="cropperRef" title="更换封面" :aspect-ratio="16/9" @upload="doUploadCover" />

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
import { ref, reactive } from 'vue';
import { getVideoDetail, updateVideo, deleteVideo, getCreatorStats, uploadSubtitle } from '../api/video';
import { uploadBanner } from '../api/user'; // 复用上传图片
import { ElMessage, ElMessageBox } from 'element-plus';
import { MoreFilled, Picture, View, Lock, Warning, Camera, List, VideoPlay, Check } from '@element-plus/icons-vue';
import ImageCropper from './ImageCropper.vue';
import { useUserStore } from '../store/user';
import { useRouter } from 'vue-router';

const emit = defineEmits(['saved', 'deleted']);
const userStore = useUserStore();
const router = useRouter();

const visible = ref(false);
const loading = ref(false);
const loadingData = ref(false);
const videoId = ref(null);
const videoUrl = ref('');
const cropperRef = ref(null);
const subtitleInput = ref(null);

// End Screen
const endScreenVisible = ref(false);
const myVideos = ref([]);
const loadingMyVideos = ref(false);
const tempSelectedIds = ref([]);

const form = reactive({
  title: '',
  description: '',
  visibility: 'public',
  category: '',
  tags: '',
  cover_url: '',
  subtitle_url: '',
  end_screen_video_ids: ''
});

const categories = ["宠物和动物", "电影和动画", "公益和社会活动", "教育", "科学和技术", "旅游和活动", "汽车和其他交通工具", "人物和博客", "体育", "喜剧", "新闻和政治", "音乐", "游戏", "娱乐", "DIY和生活百科"];

// 对外暴露的打开方法
const open = async (id) => {
  videoId.value = id;
  visible.value = true;
  loadingData.value = true;
  
  try {
    const res = await getVideoDetail(id, userStore.userInfo.id);
    if (res.data.code === 200) {
      const v = res.data.data;
      form.title = v.title;
      form.description = v.description;
      form.visibility = v.visibility;
      form.category = v.category;
      form.tags = v.tags;
      form.cover_url = v.cover_url;
      form.subtitle_url = v.subtitle_url || '';
      form.end_screen_video_ids = v.end_screen_video_ids || '';
      videoUrl.value = v.url;
    }
  } catch (e) {
    ElMessage.error('获取视频信息失败');
    visible.value = false;
  } finally {
    loadingData.value = false;
  }
};

// ... save, handleMenuCommand, triggerCoverChange, doUploadCover ... (keep as is)

// 保存更改
const save = async () => {
  if (!form.title) return ElMessage.warning('标题不能为空');
  
  loading.value = true;
  try {
    const res = await updateVideo({
      id: videoId.value,
      user_id: userStore.userInfo.id,
      ...form
    });
    
    if (res.data.code === 200) {
      ElMessage.success('保存成功，已提交审核');
      visible.value = false;
      emit('saved'); // 通知父组件刷新数据
    } else {
      ElMessage.error(res.data.msg);
    }
  } catch (e) {
    ElMessage.error('保存失败');
  } finally {
    loading.value = false;
  }
};

const handleMenuCommand = (cmd) => {
  if (cmd === 'delete') {
    ElMessageBox.confirm('确定永久删除此视频？', '警告', { type: 'warning' }).then(async () => {
      await deleteVideo(videoId.value);
      ElMessage.success('已删除');
      visible.value = false;
      emit('deleted'); // 通知父组件
    });
  }
};

const triggerCoverChange = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = (e) => {
    if (e.target.files[0]) cropperRef.value.open(e.target.files[0]);
  };
  input.click();
};

const doUploadCover = async (blob, done) => {
  const formData = new FormData();
  formData.append('file', blob, 'cover.jpg');
  try {
    const res = await uploadBanner(formData);
    if (res.data.code === 200) {
      form.cover_url = res.data.url;
      done();
    }
  } catch (e) { ElMessage.error('上传失败'); }
};

// Subtitle Logic
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

// End Screen Logic
const openEndScreenModal = async () => {
  endScreenVisible.value = true;
  loadingMyVideos.value = true;
  tempSelectedIds.value = form.end_screen_video_ids ? form.end_screen_video_ids.split(',').map(Number) : [];
  
  try {
     const res = await getCreatorStats(userStore.userInfo.id);
     if (res.data.code === 200) {
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

const handleClose = () => {
    visible.value = false;
};

defineExpose({ open });
</script>

<style scoped>
/* ... existing styles ... */
/* Add new styles for video selector if needed, reused classes from Upload.vue might need defining here if scoped */
.video-select-list { max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.video-select-item { display: flex; gap: 10px; padding: 10px; border: 1px solid #eee; border-radius: 4px; cursor: pointer; align-items: center; }
.video-select-item:hover { background: #f9f9f9; }
.video-select-item.selected { border-color: #409EFF; background: #ecf5ff; }
.select-thumb { width: 120px; height: 68px; object-fit: cover; border-radius: 4px; }
.select-info { flex: 1; }
.select-title { font-size: 14px; font-weight: 500; margin-bottom: 5px; }
.select-meta { font-size: 12px; color: #999; }
.check-icon { font-size: 20px; font-weight: bold; }

/* Existing styles below */
:deep(.yt-edit-modal) { border-radius: 12px; overflow: hidden; margin-top: 5vh !important; }
:deep(.el-dialog__header) { padding: 0; margin: 0; }
:deep(.el-dialog__body) { padding: 0; }

.edit-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 24px; border-bottom: 1px solid #eee; }
.header-title { font-size: 20px; font-weight: 600; }
.header-btns { display: flex; align-items: center; gap: 10px; }
.more-btn { cursor: pointer; font-size: 20px; color: #606060; margin-left: 10px; }

.edit-body { display: flex; height: 70vh; } 
.edit-left { flex: 1; padding: 24px; overflow-y: auto; border-right: 1px solid #eee; }
.edit-right { width: 320px; padding: 24px; background: #f9f9f9; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }

.yt-input-box { border: 1px solid #ccc; border-radius: 4px; padding: 10px; transition: border-color 0.2s; }
.yt-input-box:focus-within { border-color: #065fd4; }
.yt-input-box label { font-size: 12px; color: #606060; display: block; margin-bottom: 4px; }
:deep(.el-input__wrapper), :deep(.el-textarea__inner) { box-shadow: none !important; padding: 0; font-size: 15px; color: #0f0f0f; }

.mt-4 { margin-top: 20px; }
.form-section-title { font-weight: 500; margin-bottom: 8px; color: #0f0f0f; font-size: 14px; }

.thumb-selector { margin-bottom: 20px; }
.thumb-preview-box { width: 192px; aspect-ratio: 16/9; background: #eee; border-radius: 4px; overflow: hidden; cursor: pointer; position: relative; border: 1px solid #ddd; }
.thumb-img { width: 100%; height: 100%; object-fit: cover; }
.thumb-overlay { position: absolute; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; color: white; opacity: 0; transition: opacity 0.2s; gap: 5px; font-size: 13px; }
.thumb-preview-box:hover .thumb-overlay { opacity: 1; }
.helper-text { font-size: 12px; color: #606060; margin-top: 5px; }

.preview-player-card { background: #f0f0f0; border-radius: 4px; overflow: hidden; }
.preview-video { width: 100%; aspect-ratio: 16/9; background: #000; }
.preview-meta { padding: 12px; }
.meta-row { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; }
.meta-row .label { color: #606060; }
.meta-row .val { font-weight: 500; color: #0f0f0f; text-align: right; word-break: break-all; }
.meta-row .val.link { color: #065fd4; }

.setting-box { background: white; padding: 15px; border-radius: 4px; border: 1px solid #e5e5e5; }
.setting-label { font-size: 14px; font-weight: 500; margin-bottom: 10px; color: #0f0f0f; }
.vis-opt { display: flex; align-items: center; gap: 5px; }
.audit-warning { font-size: 12px; color: #E6A23C; margin-top: 10px; display: flex; align-items: flex-start; gap: 5px; background: #fdf6ec; padding: 8px; border-radius: 4px; line-height: 1.4; }

.element-row { display: flex; align-items: center; background: #f9f9f9; padding: 10px 20px; border-radius: 4px; margin-bottom: 10px; }
.ele-icon { margin-right: 15px; font-size: 24px; color: #606060; }
.ele-info { flex: 1; }
.ele-info h4 { margin: 0; font-size: 14px; }
.ele-info p { margin: 4px 0 0; font-size: 12px; color: #606060; }
</style>
