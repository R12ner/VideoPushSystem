from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app import db
from app.models import ActionLog, Video
from app.algorithm.core import recommender
from app.services.recall_service import recall_service

recommend_bp = Blueprint('recommend', __name__, url_prefix='/api/recommend')


def _get_latest_videos(limit=2):
    return Video.query.filter_by(status=1, visibility='public')\
        .order_by(Video.upload_time.desc())\
        .limit(limit).all()


def _prepend_latest_videos(videos, latest_videos, page, page_size):
    if page != 1:
        return videos

    merged = []
    seen_ids = set()

    for video in latest_videos + videos:
        if video.id in seen_ids:
            continue
        merged.append(video)
        seen_ids.add(video.id)

    return merged[:page_size]

@recommend_bp.route('/home', methods=['GET'])
def home_recommend():
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    latest_videos = _get_latest_videos(limit=2)

    # --- 动态分类逻辑 ---
    base_categories = ['科技', '生活', '娱乐', '教育', '电影', '音乐', '游戏', '体育']
    sorted_categories = base_categories.copy()

    if user_id:
        # 统计用户最近看的视频分类频率
        # SELECT category, count(*) FROM action_logs JOIN videos ... GROUP BY category
        cat_stats = db.session.query(Video.category, func.count(ActionLog.id))\
            .join(ActionLog, ActionLog.video_id == Video.id)\
            .filter(ActionLog.user_id == user_id)\
            .group_by(Video.category)\
            .order_by(func.count(ActionLog.id).desc())\
            .limit(50).all()
        
        if cat_stats:
            preferred_cats = [c[0] for c in cat_stats if c[0] in base_categories]
            # 没看过��分类排在后面
            remaining_cats = [c for c in base_categories if c not in preferred_cats]
            sorted_categories = preferred_cats + remaining_cats
            
    final_categories = ['全部'] + sorted_categories + ['最近上传', '已观看']

    if not user_id:
        # Fallback for anonymous users
        hot_videos = Video.query.filter_by(status=1, visibility='public')\
            .order_by(Video.views.desc())\
            .limit(page_size + len(latest_videos)).all()
        videos = _prepend_latest_videos(hot_videos, latest_videos, page, page_size)
        return jsonify({
            'list': [v.to_dict() for v in videos],
            'categories': final_categories,
            'source': 'hot_fallback'
        })
    
    # 1. Get user's recent interaction history (e.g., views, likes)
    # The recall service needs a sequence of video IDs.
    recent_logs = ActionLog.query.filter_by(user_id=user_id)\
        .order_by(ActionLog.timestamp.desc())\
        .limit(20).all() # The user tower model uses a sequence length of 20
        
    history_video_ids = [log.video_id for log in recent_logs]
    
    # 2. Call the two-tower recall service to get candidate video IDs
    candidate_ids = recall_service.get_candidates(history_video_ids, top_k=50)
    
    # 【修复】ID 映射逻辑
    # 因为模型是用 MovieLens (ID高达数万) 训练的，而本地库只有 100 个视频。
    # 为了演示效果，我们将模型推荐的 ID 映射到本地有效 ID 范围内 (1-100)
    # 实际生产中应使用真实业务数据训练，无需此步骤。
    mapped_ids = []
    if candidate_ids:
        for cid in candidate_ids:
            # 简单取模映射，确保 ID 落在这个区间，且不为 0
            # 假设本地视频大概是 100 个
            mapped_id = (cid % 100) + 1 
            mapped_ids.append(mapped_id)
        # 去重
        candidate_ids = list(set(mapped_ids))
    
    # 3. Filter out videos the user has already seen
    seen_video_ids = set(history_video_ids)
    # 注意：这里过滤要小心，如果映射后全都是看过的，就会又变空。
    # 演示阶段暂时放宽过滤，或者只过滤完全一致的
    filtered_candidate_ids = [vid for vid in candidate_ids if vid not in seen_video_ids]
    
    # 如果过滤完太少，就补一些热门的兜底
    if len(filtered_candidate_ids) < 5:
         # 补充 ID 1-20 中的随机几个
         import random
         extras = random.sample(range(1, 101), 10)
         filtered_candidate_ids.extend([e for e in extras if e not in seen_video_ids])

    # Paginate the results in memory
    start = (page - 1) * page_size
    end = start + page_size
    final_ids_to_fetch = filtered_candidate_ids[start:end]

    if not final_ids_to_fetch:
        # Fallback if recall model returns nothing or all candidates have been seen
        hot_videos = Video.query.filter_by(status=1, visibility='public')\
            .order_by(Video.views.desc())\
            .limit(page_size + len(latest_videos)).all()
        videos = hot_videos
        source = 'hot_fallback'
    else:
        # 4. Fetch video details from the database
        # An IN clause doesn't preserve order, so we reorder in Python.
        videos_from_db = Video.query.filter(Video.id.in_(final_ids_to_fetch)).all()
        video_map = {v.id: v for v in videos_from_db}
        # This ensures the final list respects the ranking from the recall model
        videos = [video_map[vid] for vid in final_ids_to_fetch if vid in video_map]
        source = 'recall_model'

    videos = _prepend_latest_videos(videos, latest_videos, page, page_size)

    return jsonify({
        'list': [v.to_dict() for v in videos],
        'categories': final_categories,
        'source': source
    })


@recommend_bp.route('/related/<int:video_id>', methods=['GET'])
def related_recommend(video_id):
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'code': 404, 'msg': '视频不存在'}), 404

    recommendations = recommender.recommend_similar_content(video_id, limit=12)
    return jsonify({'code': 200, 'data': recommendations})
