import os
import time
import cv2
import random
import jwt
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..models import Video, User, ActionLog, Follow, db, Comment, playlist_video
from ..services.ai_summary_service import ai_summary_service
from flasgger import swag_from
from sqlalchemy import func

video_bp = Blueprint('video', __name__)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def can_access_video(video):
    if video.status == 1 and video.visibility != 'private':
        return True

    token = request.headers.get('Authorization')
    if not token:
        return False

    try:
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user_id = payload.get('user_id')
        current_user = User.query.get(current_user_id)
        return bool(
            current_user
            and (str(current_user.id) == str(video.uploader_id) or current_user.is_admin)
        )
    except Exception:
        return False

def generate_auto_thumbnails(video_path, output_folder, file_prefix):
    thumbnails = []
    duration = 0
    is_short = False
    
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        if fps > 0:
            duration = int(total_frames / fps)
            
        if duration <= 60 and height >= width:
            is_short = True
            
        percentages = [0.2, 0.5, 0.8]
        for idx, pct in enumerate(percentages):
            target_frame = int(total_frames * pct)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if ret:
                thumb_filename = f"{file_prefix}_auto_{idx}.jpg"
                save_path = os.path.join(output_folder, thumb_filename)
                cv2.imwrite(save_path, frame)
                url = f"/static/covers/{thumb_filename}"
                thumbnails.append(url)
        cap.release()
    except Exception as e:
        print(f"视频处理失败: {e}")
    
    return thumbnails, duration, is_short

@video_bp.route('/upload_chunk', methods=['POST'])
def upload_chunk():
    """
    分片上传接口
    """
    if 'file' not in request.files: return jsonify({'code': 400, 'msg': '无文件'})
    file = request.files['file']
    chunk_index = request.form.get('chunk_index')
    upload_id = request.form.get('upload_id') # 前端生成的唯一ID (如 timestamp_hash)

    if not chunk_index or not upload_id:
        return jsonify({'code': 400, 'msg': '参数缺失'})

    # 临时存储路径: static/temp/{upload_id}/{chunk_index}
    static_folder = os.path.join(os.getcwd(), 'app/static')
    temp_dir = os.path.join(static_folder, 'temp', upload_id)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    
    save_path = os.path.join(temp_dir, chunk_index)
    file.save(save_path)
    return jsonify({'code': 200, 'msg': 'Chunk uploaded'})

@video_bp.route('/merge_chunks', methods=['POST'])
def merge_chunks():
    """
    合并分片接口
    """
    data = request.get_json()
    upload_id = data.get('upload_id')
    filename = data.get('filename')
    total_chunks = data.get('total_chunks')
    uploader_id = data.get('uploader_id')

    if not upload_id or not filename or not total_chunks:
        return jsonify({'code': 400, 'msg': '参数缺失'})

    static_folder = os.path.join(os.getcwd(), 'app/static')
    temp_dir = os.path.join(static_folder, 'temp', upload_id)
    upload_folder = os.path.join(static_folder, 'uploads')
    cover_folder = os.path.join(static_folder, 'covers')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(cover_folder, exist_ok=True)

    # 1. 检查所有分片是否齐全
    for i in range(int(total_chunks)):
        chunk_path = os.path.join(temp_dir, str(i))
        if not os.path.exists(chunk_path):
             return jsonify({'code': 400, 'msg': f'缺少分片 {i}'})

    # 2. 合并文件
    timestamp = int(time.time())
    safe_name = secure_filename(filename)
    new_video_name = f"{timestamp}_{safe_name}"
    final_path = os.path.join(upload_folder, new_video_name)

    with open(final_path, 'wb') as outfile:
        for i in range(int(total_chunks)):
            chunk_path = os.path.join(temp_dir, str(i))
            with open(chunk_path, 'rb') as infile:
                outfile.write(infile.read())
    
    # 3. 删除临时文件
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

    # 4. 后续处理 (生成缩略图，创建DB记录)
    video_url = f"/static/uploads/{new_video_name}"
    auto_covers, duration, is_short = generate_auto_thumbnails(final_path, cover_folder, f"{timestamp}_{safe_name}")
    default_cover = auto_covers[0] if auto_covers else "https://via.placeholder.com/300x200"

    video = Video(
        title=filename, # 初始标题用原文件名
        description="",
        url=video_url,
        cover_url=default_cover,
        uploader_id=uploader_id,
        duration=duration,
        is_short=is_short, 
        status=-1, 
        visibility='private' 
    )
    db.session.add(video)
    db.session.commit()

    return jsonify({
        'code': 200, 
        'msg': '上传合并完成', 
        'data': {
            'id': video.id,
            'url': video.url,
            'title': video.title,
            'auto_covers': auto_covers,
            'is_short': is_short
        }
    })

@video_bp.route('/upload_file', methods=['POST'])
@swag_from('../docs/video/upload.yml') # <--- 修改
def upload_video_file():
    if 'file' not in request.files: return jsonify({'code': 400, 'msg': '无文件'})
    file = request.files['file']
    uploader_id = request.form.get('uploader_id')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        static_folder = os.path.join(os.getcwd(), 'app/static')
        upload_folder = os.path.join(static_folder, 'uploads')
        cover_folder = os.path.join(static_folder, 'covers')
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(cover_folder, exist_ok=True)
        
        new_video_name = f"{timestamp}_{filename}"
        video_path = os.path.join(upload_folder, new_video_name)
        file.save(video_path)
        
        base_url = ""
        video_url = f"{base_url}/static/uploads/{new_video_name}"
        
        auto_covers, duration, is_short = generate_auto_thumbnails(video_path, cover_folder, f"{timestamp}_{filename}")
        default_cover = auto_covers[0] if auto_covers else "https://via.placeholder.com/300x200"

        video = Video(
            title=file.filename,
            description="",
            url=video_url,
            cover_url=default_cover,
            uploader_id=uploader_id,
            duration=duration,
            is_short=is_short, 
            status=-1, 
            visibility='private' 
        )
        db.session.add(video)
        db.session.commit()
        
        return jsonify({
            'code': 200, 
            'msg': '上传完成', 
            'data': {
                'id': video.id,
                'url': video.url,
                'title': video.title,
                'auto_covers': auto_covers,
                'is_short': is_short
            }
        })
    return jsonify({'code': 400, 'msg': '格式不支持'})

@video_bp.route('/upload_subtitle', methods=['POST'])
def upload_subtitle():
    if 'file' not in request.files: return jsonify({'code': 400, 'msg': '无文件'})
    file = request.files['file']
    
    # 允许字幕格式
    original_name = file.filename or ''
    suffix = os.path.splitext(original_name)[1].lower()

    if file and suffix in {'.vtt', '.srt', '.json'}:
        safe_stem = secure_filename(os.path.splitext(original_name)[0]) or 'subtitle'
        timestamp = int(time.time())
        static_folder = os.path.join(os.getcwd(), 'app/static')
        subtitle_folder = os.path.join(static_folder, 'subtitles')
        os.makedirs(subtitle_folder, exist_ok=True)
        
        new_name = f"{timestamp}_{safe_stem}{suffix}"
        save_path = os.path.join(subtitle_folder, new_name)
        file.save(save_path)
        
        url = f"/static/subtitles/{new_name}"
        return jsonify({'code': 200, 'msg': '字幕上传成功', 'url': url})
        
    return jsonify({'code': 400, 'msg': '仅支持 .vtt、.srt 或 .json 格式'})

@video_bp.route('/publish', methods=['POST'])
@swag_from('../docs/video/publish.yml') # <--- 修改
def publish_video():
    data = request.get_json()
    video = Video.query.get(data.get('id'))
    if not video: return jsonify({'code': 404, 'msg': '视频不存在'})
    if 'title' in data: video.title = data['title']
    if 'description' in data: video.description = data['description']
    if 'category' in data: video.category = data['category']
    if 'tags' in data: video.tags = data['tags']
    if 'cover_url' in data: video.cover_url = data['cover_url']
    if 'visibility' in data: video.visibility = data['visibility']
    if 'subtitle_url' in data: video.subtitle_url = data['subtitle_url']
    if 'end_screen_video_ids' in data: video.end_screen_video_ids = data['end_screen_video_ids']
    
    action = data.get('action')
    if action == 'draft':
        video.status = -1
        msg = '已保存为草稿'
    else:
        if 'visibility' not in data or not data.get('visibility'):
            video.visibility = 'public'
        video.status = 0
        msg = '发布成功，等待审核'
    
    db.session.commit()
    return jsonify({'code': 200, 'msg': msg})

@video_bp.route('/update', methods=['POST'])
def update_video():
    data = request.get_json()
    video_id = data.get('id')
    user_id = data.get('user_id')
    action = data.get('action')

    video = Video.query.get(video_id)
    if not video: return jsonify({'code': 404, 'msg': '视频不存在'})
    current_user = User.query.get(user_id)
    if not current_user or (str(current_user.id) != str(video.uploader_id) and not current_user.is_admin):
         return jsonify({'code': 403, 'msg': '无权操作'})

    if 'title' in data: video.title = data['title']
    if 'description' in data: video.description = data['description']
    if 'visibility' in data: video.visibility = data['visibility']
    if 'category' in data: video.category = data['category']
    if 'tags' in data: video.tags = data['tags']
    if 'cover_url' in data: video.cover_url = data['cover_url']
    if 'subtitle_url' in data: video.subtitle_url = data['subtitle_url']
    if 'end_screen_video_ids' in data: video.end_screen_video_ids = data['end_screen_video_ids']
    
    if action == 'draft':
        video.status = -1
        msg = '已撤回为草稿'
    else:
        if video.status != -1: video.status = 0
        msg = '更新成功'
    
    db.session.commit()
    return jsonify({'code': 200, 'msg': msg})

@video_bp.route('/list', methods=['GET'])
@swag_from('../docs/video/list.yml') # <--- 修改
def get_video_list():
    category = request.args.get('category')
    search_query = request.args.get('q')
    query = Video.query.filter_by(status=1, visibility='public')
    if category and category != '全部': query = query.filter_by(category=category)
    if search_query:
        rule = f"%{search_query}%"
        query = query.join(User).filter((Video.title.like(rule)) | (Video.description.like(rule)) | (User.username.like(rule)))
    videos = query.order_by(Video.upload_time.desc()).all()
    return jsonify({'code': 200, 'data': [v.to_dict() for v in videos]})

@video_bp.route('/batch_info', methods=['POST'])
def get_videos_by_ids():
    data = request.get_json()
    ids_str = data.get('ids') # "1,2,3"
    if not ids_str: return jsonify({'code': 200, 'data': []})
    
    id_list = [int(i) for i in ids_str.split(',') if i.isdigit()]
    if not id_list: return jsonify({'code': 200, 'data': []})
    
    videos = Video.query.filter(Video.id.in_(id_list)).all()
    return jsonify({'code': 200, 'data': [v.to_dict() for v in videos]})

@video_bp.route('/<int:video_id>', methods=['GET'])
@swag_from('../docs/video/detail.yml') # <--- 修改
def get_video_detail(video_id):
    video = Video.query.get(video_id)
    if not video: return jsonify({'code': 404, 'msg': '视频不存在'}), 404
    if not can_access_video(video):
        return jsonify({'code': 403, 'msg': '该视频为私享视频或已下架'}), 403
    video.views += 1
    db.session.commit()
    likes_count = ActionLog.query.filter_by(video_id=video_id, action_type='like').count()
    uploader = User.query.get(video.uploader_id)
    video_data = video.to_dict()
    video_data['uploader_name'] = uploader.username if uploader else '未知'
    
    # 修复 uploader_avatar 混合内容
    up_avatar = uploader.avatar if uploader else ''
    if up_avatar and 'pay.aeasywink.top' in up_avatar:
        up_avatar = up_avatar.replace('http://pay.aeasywink.top', '').replace('https://pay.aeasywink.top', '')
    video_data['uploader_avatar'] = up_avatar
    
    video_data['likes'] = likes_count
    return jsonify({'code': 200, 'data': video_data})


@video_bp.route('/<int:video_id>/ai_summary', methods=['POST'])
def generate_ai_summary(video_id):
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'code': 404, 'msg': '视频不存在'}), 404
    if not can_access_video(video):
        return jsonify({'code': 403, 'msg': '无权访问该视频'}), 403
    if video.is_short:
        return jsonify({'code': 400, 'msg': '短视频暂不支持 AI 总结'}), 400

    payload = request.get_json(silent=True) or {}
    force_refresh = bool(payload.get('refresh'))

    try:
        summary_data = ai_summary_service.summarize_video(video, force_refresh=force_refresh)
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        print(f"AI Summary Error: {exc}")
        return jsonify({'code': 500, 'msg': 'AI 总结生成失败'}), 500

    return jsonify({'code': 200, 'data': summary_data})

@video_bp.route('/delete/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    video = Video.query.get(video_id)
    if not video: return jsonify({'code': 404, 'msg': '视频不存在'}), 404
    try:
        db.session.execute(playlist_video.delete().where(playlist_video.c.video_id == video_id))
        Comment.query.filter_by(video_id=video_id).delete()
        ActionLog.query.filter_by(video_id=video_id).delete()
        db.session.delete(video)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败'})

@video_bp.route('/action', methods=['POST'])
@swag_from('../docs/video/action.yml')
def video_action():
    data = request.get_json()
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    action_type = data.get('type')
    
    if not all([user_id, video_id, action_type]):
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400

    video = Video.query.get(video_id)
    if not video:
        return jsonify({'code': 404, 'msg': '视频不存在'}), 404
        
    sender = User.query.get(user_id)
    if not sender:
        return jsonify({'code': 404, 'msg': '操作用户不存在'}), 404

    # --- View & Progress Logic ---
    if action_type == 'view':
        log = ActionLog(user_id=user_id, video_id=video_id, action_type='view', progress=0)
        db.session.add(log)
    elif action_type == 'progress':
        progress = data.get('progress', 0)
        log = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='view').first()
        if log:
            log.progress = int(progress)
            log.timestamp = datetime.utcnow()
        else:
            log = ActionLog(user_id=user_id, video_id=video_id, action_type='view', progress=int(progress))
            db.session.add(log)

    # --- Favorite Logic ---
    elif action_type == 'favorite':
        exists = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='favorite').first()
        if not exists:
            log = ActionLog(user_id=user_id, video_id=video_id, action_type='favorite', weight=5)
            db.session.add(log)
            if str(video.uploader_id) != str(user_id):
                try:
                    create_notification(video.uploader_id, user_id, 'interaction', f'{sender.username} 收藏了你的视频: {video.title}', f'/video/{video_id}')
                except Exception as e:
                    print(f"Notification Error (Favorite): {e}")

    elif action_type == 'unfavorite':
        ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='favorite').delete()

    # --- Like Logic ---
    elif action_type == 'like':
        exists = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='like').first()
        if not exists:
            log = ActionLog(user_id=user_id, video_id=video_id, action_type='like', weight=3)
            db.session.add(log)
            dislike = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='dislike').first()
            if dislike:
                db.session.delete(dislike)
            if str(video.uploader_id) != str(user_id):
                try:
                    create_notification(video.uploader_id, user_id, 'interaction', f'{sender.username} 赞了你的视频: {video.title}', f'/video/{video_id}')
                except Exception as e:
                    print(f"Notification Error (Like): {e}")

    elif action_type == 'unlike':
        ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='like').delete()
        
    db.session.commit()
    return jsonify({'code': 200, 'msg': '操作成功'})

@video_bp.route('/check_fav', methods=['GET'])
def check_fav():
    user_id = request.args.get('user_id')
    video_id = request.args.get('video_id')
    exists = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='favorite').first()
    return jsonify({'is_fav': bool(exists)})

@video_bp.route('/creator/stats', methods=['GET'])
def get_creator_stats():
    user_id = request.args.get('user_id')
    if not user_id: return jsonify({'code': 400, 'msg': '缺少 user_id'})
    total_videos = Video.query.filter_by(uploader_id=user_id).count()
    total_views = db.session.query(func.sum(Video.views)).filter(Video.uploader_id == user_id).scalar() or 0
    total_fans = Follow.query.filter_by(followed_id=user_id).count()
    total_likes = db.session.query(func.count(ActionLog.id)).join(Video, ActionLog.video_id == Video.id).filter(Video.uploader_id == user_id, ActionLog.action_type == 'like').scalar() or 0
    total_watch_seconds = db.session.query(func.sum(Video.views * Video.duration)).filter(Video.uploader_id == user_id).scalar() or 0
    total_watch_hours = round(total_watch_seconds / 3600, 2)
    all_videos = Video.query.filter_by(uploader_id=user_id).order_by(Video.upload_time.desc()).all()
    cat_stats = db.session.query(Video.category, func.count(Video.id)).filter(Video.uploader_id == user_id).group_by(Video.category).all()
    chart_category = [{'name': r[0], 'value': r[1]} for r in cat_stats]
    return jsonify({
        'code': 200,
        'data': {
            'total_videos': total_videos, 'total_views': total_views, 'total_fans': total_fans, 'total_likes': total_likes, 'total_watch_hours': total_watch_hours,
            'recent_videos': [v.to_dict() for v in all_videos[:5]], 'all_videos': [v.to_dict() for v in all_videos], 'chart_category': chart_category
        }
    })
