from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func, or_
from flasgger import swag_from
from flask_mail import Message
import datetime
import json
import jwt
import os

from .. import mail
from ..models import (
    ActionLog,
    Comment,
    Order,
    PasswordResetRequest,
    User,
    Video,
    db,
    playlist_video,
)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/reset_requests', methods=['GET'])
def get_reset_requests():
    reqs = PasswordResetRequest.query.order_by(PasswordResetRequest.created_at.desc()).all()
    return jsonify({'code': 200, 'data': [r.to_dict() for r in reqs]})


@admin_bp.route('/send_reset_email', methods=['POST'])
def send_reset_email():
    data = request.get_json() or {}
    req_id = data.get('id')

    req = PasswordResetRequest.query.get(req_id)
    if not req:
        return jsonify({'code': 404, 'msg': '请求不存在'}), 404

    user = User.query.get(req.user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    payload = {
        'reset_user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    domain = os.getenv('SITE_DOMAIN', 'http://localhost:5173')
    reset_link = f'{domain}/reset-password?token={token}'

    try:
        msg = Message('VideoHub 密码重置', recipients=[req.email])
        msg.body = (
            f'亲爱的 {user.username}：\n\n'
            '管理员已批准您的密码重置申请。\n'
            f'请点击以下链接重置密码：\n{reset_link}\n\n'
            '该链接 1 小时内有效。'
        )
        mail.send(msg)

        req.status = 'sent'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '邮件已发送'})
    except Exception as e:
        print(e)
        return jsonify({'code': 500, 'msg': '邮件发送失败'}), 500


@admin_bp.route('/stats', methods=['GET'])
@swag_from('../docs/admin/stats.yml')
def get_stats():
    total_users = User.query.count()
    total_videos = Video.query.count()
    pending_videos = Video.query.filter_by(status=0).count()

    daily_users = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id)
    ).group_by('date').order_by('date').limit(7).all()

    chart_users = {
        'dates': [str(r[0]) for r in daily_users],
        'counts': [r[1] for r in daily_users]
    }

    category_stats = db.session.query(
        Video.category, func.count(Video.id)
    ).group_by(Video.category).all()

    chart_category = [{'name': r[0], 'value': r[1]} for r in category_stats]

    top_videos = Video.query.order_by(Video.views.desc()).limit(10).all()
    chart_top10 = {
        'titles': [v.title[:10] + '...' for v in top_videos],
        'views': [v.views for v in top_videos]
    }

    return jsonify({
        'code': 200,
        'data': {
            'total_users': total_users,
            'total_videos': total_videos,
            'pending_videos': pending_videos,
            'chart_users': chart_users,
            'chart_category': chart_category,
            'chart_top10': chart_top10
        }
    })


@admin_bp.route('/two_tower_metrics', methods=['GET'])
def get_two_tower_metrics():
    metrics_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'services',
        'model_data',
        'two_tower_metrics.json'
    )

    if not os.path.exists(metrics_path):
        return jsonify({'code': 404, 'msg': '尚未生成双塔模型训练指标，请先运行训练脚本'}), 404

    try:
        with open(metrics_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        return jsonify({'code': 200, 'data': payload})
    except Exception as e:
        print(f'Load two tower metrics failed: {e}')
        return jsonify({'code': 500, 'msg': '读取双塔模型训练指标失败'}), 500


@admin_bp.route('/orders', methods=['GET'])
def get_admin_orders():
    q = (request.args.get('q') or '').strip()
    status = (request.args.get('status') or '').strip()
    page = request.args.get('page', default=1, type=int) or 1
    page_size = request.args.get('page_size', default=10, type=int) or 10
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    query = db.session.query(Order, User).outerjoin(User, Order.user_id == User.id)

    if status:
        query = query.filter(Order.trade_status == status)

    if q:
        keyword = f'%{q}%'
        query = query.filter(
            or_(
                Order.order_no.like(keyword),
                Order.subject.like(keyword),
                User.username.like(keyword),
                User.email.like(keyword)
            )
        )

    total = query.count()
    rows = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'list': [
                {
                    'id': order.id,
                    'order_no': order.order_no,
                    'user_id': order.user_id,
                    'username': user.username if user else '未知用户',
                    'email': user.email if user else '',
                    'subject': order.subject,
                    'total_amount': order.total_amount,
                    'trade_status': order.trade_status,
                    'target_ver_type': order.target_ver_type,
                    'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else ''
                }
                for order, user in rows
            ],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@admin_bp.route('/videos', methods=['GET'])
@swag_from('../docs/admin/videos.yml')
def get_admin_videos():
    status = request.args.get('status')
    q = request.args.get('q')

    query = Video.query
    if status is not None and status != '':
        query = query.filter_by(status=int(status))
    if q:
        query = query.filter(Video.title.like(f'%{q}%'))

    videos = query.order_by(Video.upload_time.desc()).all()
    return jsonify({'code': 200, 'data': [v.to_dict() for v in videos]})


@admin_bp.route('/video/audit', methods=['POST'])
@swag_from('../docs/admin/audit_video.yml')
def audit_video():
    data = request.get_json() or {}
    video_id = data.get('id')
    new_status = data.get('status')

    video = Video.query.get(video_id)
    if not video:
        return jsonify({'code': 404, 'msg': '视频不存在'})

    video.status = new_status
    db.session.commit()
    return jsonify({'code': 200, 'msg': '操作成功'})


@admin_bp.route('/video/delete', methods=['POST'])
@swag_from('../docs/admin/delete_video.yml')
def delete_video_admin():
    data = request.get_json() or {}
    video_id = data.get('id')

    video = Video.query.get(video_id)
    if video:
        try:
            db.session.execute(playlist_video.delete().where(playlist_video.c.video_id == video_id))
            Comment.query.filter_by(video_id=video_id).delete()
            ActionLog.query.filter_by(video_id=video_id).delete()

            db.session.delete(video)
            db.session.commit()
            return jsonify({'code': 200, 'msg': '删除成功'})
        except Exception as e:
            db.session.rollback()
            print(f'删除失败: {e}')
            return jsonify({'code': 500, 'msg': '删除失败，数据库错误'})

    return jsonify({'code': 404, 'msg': '视频不存在'})


@admin_bp.route('/users', methods=['GET'])
@swag_from('../docs/admin/users.yml')
def get_admin_users():
    q = request.args.get('q')
    query = User.query
    if q:
        query = query.filter(User.username.like(f'%{q}%') | User.email.like(f'%{q}%'))

    users = query.all()
    return jsonify({'code': 200, 'data': [u.to_dict() for u in users]})


@admin_bp.route('/user/ban', methods=['POST'])
@swag_from('../docs/admin/ban_user.yml')
def ban_user():
    data = request.get_json() or {}
    user = User.query.get(data.get('id'))
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'})

    user.is_banned = not user.is_banned
    db.session.commit()

    msg = '已封禁' if user.is_banned else '已解除'
    return jsonify({'code': 200, 'msg': msg})
