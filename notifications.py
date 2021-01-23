# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 13:00
"""
from flask import url_for
from flaskdemo.models import Notification
from flaskdemo.extensions import db


def push_follow_notification(follower, receiver):
    """推送关注提醒"""
    message = 'User <a href="%s">%s</a> follow you.' % (url_for("user.index", username=follower.username), follower.username)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_collect_notification(collector, receiver, photo_id):
    """推动收藏提醒"""
    message = 'User <a href="%s">%s</a> collected your <a href="%s">photo</a>' % (url_for("user.index", username=collector.username), collector.username, url_for("main.show_photo", photo_id=photo_id))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_comment_notification(photo_id, receiver, page=1):
    """推送评论提醒"""
    message = '<a href="%s"#comments">This photo</a> has new comment/reply.' % (url_for("main.show_photo", photo_id=photo_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()
