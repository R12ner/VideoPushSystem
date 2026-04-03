import random
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func
from ..models import Video, ActionLog, db

class RecommendationEngine:
    
    def get_user_preferred_categories(self, user_id, limit=15):
        # 1. 基础分类池 (不含 '全部'、'最近上传'、'已观看')
        default_cats = ['科技', '生活', '娱乐', '教育', '电影', '音乐', '游戏', '体育', '新闻']
        
        # 2. 特殊尾部分类
        tail_cats = ['最近上传', '已观看']
        
        sorted_cats = []
        
        if user_id:
            try:
                # 统计用户观看最多的分类
                query = db.session.query(Video.category, func.count(ActionLog.id).label('count'))\
                    .join(ActionLog, ActionLog.video_id == Video.id)\
                    .filter(ActionLog.user_id == user_id, ActionLog.action_type == 'view')\
                    .group_by(Video.category)\
                    .order_by(func.count(ActionLog.id).desc())\
                    .all() 
                
                # 提取用户常看的分类 (且必须在 default_cats 中，防止脏数据)
                top_cats = [r[0] for r in query if r[0] in default_cats]
                
                # A. 先放入用户喜欢的
                sorted_cats.extend(top_cats)
                
                # B. 再放入剩余的默认分类
                for c in default_cats:
                    if c not in sorted_cats:
                        sorted_cats.append(c)
            except Exception:
                # 出错降级
                sorted_cats = default_cats
        else:
            # 无用户登录，使用默认顺序
            sorted_cats = default_cats

        # 去重逻辑 (虽然上面的逻辑基本保证无重复，但保留作为保险)
        seen = set()
        unique_cats = [x for x in sorted_cats if not (x in seen or seen.add(x))]
        
        # 3. 最终组装：['全部'] + [排序后的常规分类] + ['最近上传', '已观看']
        # 注意：这里我们截取 unique_cats 的前 N 个，但保证 tail_cats 始终在最后
        final_list = ['全部'] + unique_cats[:limit] + tail_cats
        
        return final_list

    # 热门推荐：过滤已发布且公开
    def get_hot_videos(self, limit=20):
        videos = Video.query.filter_by(status=1, visibility='public').order_by(Video.views.desc()).limit(limit * 2).all()
        random.shuffle(videos)
        return [v.to_dict() for v in videos[:limit]]

    # 相关推荐：只从公开池中选择
    def recommend_similar_content(self, video_id, limit=10):
        all_videos = Video.query.filter_by(status=1, visibility='public').all()
        if not all_videos: return []
        
        target_video = Video.query.get(video_id)
        if target_video and target_video not in all_videos: all_videos.append(target_video)
        
        video_ids = [v.id for v in all_videos]
        corpus = [v.tags.replace(',', ' ') if v.tags else "" for v in all_videos]
        
        try:
            target_index = video_ids.index(video_id)
        except ValueError: return [] 

        cv = CountVectorizer()
        try:
            tfidf_matrix = cv.fit_transform(corpus)
        except ValueError: return []

        cosine_sim = cosine_similarity(tfidf_matrix[target_index], tfidf_matrix)
        similarity_scores = list(enumerate(cosine_sim[0]))
        sorted_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        
        recommend_res = []
        count = 0
        for idx, score in sorted_scores:
            if idx == target_index: continue
            if count >= limit: break
            v_obj = all_videos[idx]
            if v_obj.status == 1 and v_obj.visibility == 'public':
                recommend_res.append(v_obj.to_dict())
                count += 1
            
        return recommend_res

recommender = RecommendationEngine()
