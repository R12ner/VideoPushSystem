import os
from flask import Blueprint, request, jsonify
from ..models import Comment, User, Video, db, ActionLog, CommentLike, Notification, NotificationSetting
from datetime import datetime
from flasgger import swag_from
from .notification import create_notification

interaction_bp = Blueprint('interaction', __name__)


def _collect_comment_tree_ids(comment_id):
    comment_ids = []
    stack = [comment_id]

    while stack:
        current_id = stack.pop()
        comment_ids.append(current_id)
        child_ids = [item.id for item in Comment.query.filter_by(parent_id=current_id).all()]
        stack.extend(child_ids)

    return comment_ids

# --- 评论功能 (升级版) ---

@interaction_bp.route('/comments', methods=['GET'])
@swag_from('../docs/interaction/comments.yml') # <--- 修改
def get_comments():
    video_id = request.args.get('video_id')
    user_id = request.args.get('user_id', type=int) 
    sort_by = request.args.get('sort_by', 'hot')
    
    liked_comment_ids = set()
    if user_id:
        user_likes = CommentLike.query.filter_by(user_id=user_id).all()
        liked_comment_ids = {like.comment_id for like in user_likes}

    query = Comment.query.filter_by(video_id=video_id, parent_id=None)
    
    if sort_by == 'new':
        comments = query.order_by(Comment.is_pinned.desc(), Comment.timestamp.desc()).all()
    else:
        comments = query.order_by(Comment.is_pinned.desc(), Comment.likes.desc()).all()
    
    data = []
    for c in comments:
        replies_obj = c.replies.order_by(Comment.timestamp.asc()).all()
        replies_data = []
        for r in replies_obj:
            r_avatar = r.user.avatar
            if r_avatar and 'pay.aeasywink.top' in r_avatar:
                r_avatar = r_avatar.replace('http://pay.aeasywink.top', '').replace('https://pay.aeasywink.top', '')
                
            replies_data.append({
                'id': r.id,
                'content': r.content,
                'time': r.timestamp.strftime('%Y-%m-%d %H:%M'),
                'likes': r.likes,
                'is_liked': r.id in liked_comment_ids,
                'user': {'id': r.user.id, 'username': r.user.username, 'avatar': r_avatar, 'verification_type': r.user.verification_type}
            })

        c_avatar = c.user.avatar
        if c_avatar and 'pay.aeasywink.top' in c_avatar:
            c_avatar = c_avatar.replace('http://pay.aeasywink.top', '').replace('https://pay.aeasywink.top', '')

        data.append({
            'id': c.id,
            'content': c.content,
            'time': c.timestamp.strftime('%Y-%m-%d %H:%M'),
            'likes': c.likes,
            'is_pinned': c.is_pinned,
            'is_liked': c.id in liked_comment_ids,
            'user': {'id': c.user.id, 'username': c.user.username, 'avatar': c_avatar, 'verification_type': c.user.verification_type},
            'replies': replies_data
        })
        
    return jsonify({'code': 200, 'data': data})

@interaction_bp.route('/comment/add', methods=['POST'])
@swag_from('../docs/interaction/add_comment.yml') # <--- 修改
def add_comment():
    data = request.get_json()
    sender_id = data.get('user_id')
    video_id = data.get('video_id')
    content = data.get('content')
    parent_id = data.get('parent_id')
    
    new_comment = Comment(
        content=content,
        user_id=sender_id,
        video_id=video_id,
        parent_id=parent_id
    )
    db.session.add(new_comment)
    
    # 触发通知
    sender = User.query.get(sender_id)
    video = Video.query.get(video_id)
    
    if parent_id:
        # 回复评论通知
        parent_comment = Comment.query.get(parent_id)
        if parent_comment and str(parent_comment.user_id) != str(sender_id):
            try:
                create_notification(
                    user_id=parent_comment.user_id,
                    sender_id=sender_id,
                    type='comment', # 或 reply
                    content=f'{sender.username} 回复了你的评论: {content[:20]}...',
                    target_url=f'/video/{video_id}'
                )
            except Exception as e:
                print(f"Notification Error (Reply): {e}")
    else:
        # 视频评论通知 (通知作者)
        if str(video.uploader_id) != str(sender_id):
            try:
                create_notification(
                    user_id=video.uploader_id,
                    sender_id=sender_id,
                    type='interaction', 
                    content=f'{sender.username} 评论了你的视频: {content[:20]}...',
                    target_url=f'/video/{video_id}'
                )
            except Exception as e:
                print(f"Notification Error (Comment): {e}")
            
    db.session.commit()
    return jsonify({'code': 200, 'msg': '评论成功'})

@interaction_bp.route('/comment/delete', methods=['POST'])
def delete_comment():
    data = request.get_json() or {}
    comment_id = data.get('comment_id')
    user_id = data.get('user_id')

    if not comment_id or not user_id:
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'code': 404, 'msg': '评论不存在'}), 404

    if str(comment.user_id) != str(user_id):
        return jsonify({'code': 403, 'msg': '只能删除自己的评论'}), 403

    comment_ids = _collect_comment_tree_ids(comment.id)

    try:
        CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids)).delete(synchronize_session=False)

        for cid in reversed(comment_ids):
            Comment.query.filter_by(id=cid).delete()

        db.session.commit()
        return jsonify({'code': 200, 'msg': '评论已删除'})
    except Exception:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除评论失败'}), 500


@interaction_bp.route('/comment/like', methods=['POST'])
@swag_from('../docs/interaction/like_comment.yml') # <--- 修改
def like_comment():
    data = request.get_json()
    comment_id = data.get('comment_id')
    user_id = data.get('user_id')
    
    if not user_id or not comment_id:
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'code': 404, 'msg': '评论不存在'}), 404

    existing_like = CommentLike.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    
    action = ''
    if existing_like:
        db.session.delete(existing_like)
        comment.likes = max(0, comment.likes - 1)
        action = 'unlike'
    else:
        new_like = CommentLike(user_id=user_id, comment_id=comment_id)
        db.session.add(new_like)
        comment.likes += 1
        action = 'like'
        
        # 通知评论作者 (如果不是自己点赞)
        if str(comment.user_id) != str(user_id):
            sender = User.query.get(user_id)
            try:
                create_notification(
                    user_id=comment.user_id,
                    sender_id=user_id,
                    type='comment',
                    content=f'{sender.username} 赞了你的评论',
                    target_url=f'/video/{comment.video_id}'
                )
            except Exception as e:
                print(f"Notification Error (Like Comment): {e}")
        
    db.session.commit()
    return jsonify({'code': 200, 'msg': '操作成功', 'likes': comment.likes, 'action': action})

@interaction_bp.route('/comment/pin', methods=['POST'])
@swag_from('../docs/interaction/pin_comment.yml') # <--- 修改
def pin_comment():
    data = request.get_json()
    comment_id = data.get('comment_id')
    user_id = data.get('user_id')
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'code': 404, 'msg': '评论不存在'}), 404
        
    video = Video.query.get(comment.video_id)
    if str(video.uploader_id) != str(user_id):
        return jsonify({'code': 403, 'msg': '无权操作'}), 403
        
    if comment.is_pinned:
        comment.is_pinned = False
    else:
        old_pinned = Comment.query.filter_by(video_id=video.id, is_pinned=True).first()
        if old_pinned: old_pinned.is_pinned = False
        comment.is_pinned = True
        
    db.session.commit()
    return jsonify({'code': 200, 'msg': '操作成功'})

@interaction_bp.route('/check_status', methods=['GET'])
@swag_from('../docs/interaction/check_status.yml') # <--- 修改
def check_status():
    user_id = request.args.get('user_id')
    video_id = request.args.get('video_id')
    is_fav = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='favorite').first()
    is_like = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='like').first()
    view_log = ActionLog.query.filter_by(user_id=user_id, video_id=video_id, action_type='view')\
        .order_by(ActionLog.timestamp.desc()).first()
    last_progress = view_log.progress if view_log else 0
    return jsonify({
        'code': 200, 
        'data': {
            'is_fav': bool(is_fav), 
            'is_like': bool(is_like),
            'last_progress': last_progress
        }
    })
