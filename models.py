# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:59
"""
import os
from datetime import datetime
from flask_login import UserMixin
from flask import current_app
from flask_avatars import Identicon
from flaskdemo.extensions import db, whooshee
from werkzeug.security import generate_password_hash, check_password_hash


# 权限和角色之间多对多关系表，表名、两个外键字段
roles_permissions = db.Table("roles_permissions",
                             db.Column("role_id", db.Integer, db.ForeignKey("role.id")),
                             db.Column("permission_id", db.Integer, db.ForeignKey("permission.id"))
                             )


class Permission(db.Model):  # 权限
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    roles = db.relationship("Role", secondary=roles_permissions, back_populates="permissions")


class Role(db.Model):  # 角色
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    permissions = db.relationship("Permission", secondary=roles_permissions, back_populates="roles")
    users = db.relationship("User", back_populates="role")

    @staticmethod
    def init_role():
        roles_permissions_map = {
            "Locked": ["FOLLOW", "COLLECT"],
            "User": ["FOLLOW", "COLLECT", "COMMENT", "UPLOAD"],
            "Moderator": ["FOLLOW", "COLLECT", "COMMENT", "UPLOAD", "MODERATE"],
            "Administrator": ["FOLLOW", "COLLECT", "COMMENT", "UPLOAD", "MODERATE", "ADMINISTER"]
        }
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()


# 使用关联模型表示用户与被关注用户的多对多关系
class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    follower = db.relationship("User", foreign_keys=[follower_id], back_populates="followings", lazy="joined")
    followed = db.relationship("User", foreign_keys=[followed_id], back_populates="followers", lazy="joined")


# 用户数据库表格, db.Model基类会为User类提供一个构造函数，接收匹配类属性名称的参数值并赋值给对应的类属性
@whooshee.register_model("username", "name")
class User(db.Model, UserMixin):  # flask_login要求表示用户的类必须实现is_authenticated、is_active、get_id()等属性和方法，继承UserMixin类是因为它包含了这些属性和方法的默认实现
    id = db.Column(db.Integer, primary_key=True)
    # 用户资料
    username = db.Column(db.String(20), unique=True, index=True)
    email = db.Column(db.String(254), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(30))
    website = db.Column(db.String(255))
    bio = db.Column(db.String(120))
    location = db.Column(db.String(50))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)  # 注册的时间
    # 用户状态
    confirmed = db.Column(db.Boolean, default=False)
    locked = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    # 头像
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    avatar_raw = db.Column(db.String(64))  # 用户自定义头像的原始文件
    # 三种题型的设置
    receive_comment_notification = db.Column(db.Boolean, default=True)
    receive_follow_notification = db.Column(db.Boolean, default=True)
    receive_collect_notification = db.Column(db.Boolean, default=True)
    public_collections = db.Column(db.Boolean, default=True)
    # 用户与角色的 多对一 关系
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    role = db.relationship("Role", back_populates="users")
    # 用户与图片的 一对多 关系
    photos = db.relationship("Photo", back_populates="author", cascade="all")
    # 用户与评论的 一对多 关系
    comments = db.relationship("Comment", back_populates="author", cascade="all")
    # 用户与收藏的 一对多 关系
    collects = db.relationship("Collect", back_populates="user", cascade="all")
    # 我关注的谁
    followings = db.relationship("Follow", foreign_keys=[Follow.follower_id], back_populates="follower", cascade="all", lazy="dynamic")
    # 谁关注的我
    followers = db.relationship("Follow", foreign_keys=[Follow.followed_id], back_populates="followed", cascade="all", lazy="dynamic")
    # 我的提醒
    notifications = db.relationship("Notification", back_populates="receiver", cascade="all")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.generate_avatar()
        self.follow(self)
        self.set_role()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_role(self):
        if self.role is None:
            if self.email == current_app.config["ALBUMY_ADMIN_EMAIL"]:
                self.role = Role.query.filter_by(name="Administrator").first()
            else:
                self.role = Role.query.filter_by(name="User").first()
            db.session.add(self)
            db.session.commit()  # ToDo 这里是否要 commit, buleprints/auth line 51 会 commit

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()  # ToDO 这里是否一定要 commit 呢？

    @property
    def is_admin(self):
        return self.role.name == "Administrator"

    @property
    def is_active(self):
        return self.active

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions

    def is_collecting(self, photo):
        return Collect.query.with_parent(self).filter_by(photo_id=photo.id).first() is not None

    def collect(self, photo):
        if not self.is_collecting(photo):
            collect = Collect(user=self, photo=photo)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, photo):
        collect = Collect.query.with_parent(self).filter_by(photo_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        follow = self.followings.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followings.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def lock(self):
        self.locked = True
        self.role = Role.query.filter_by(name='Locked').first()
        db.session.add(self)
        db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name="User").first()
        db.session.add(self)
        db.session.commit()

    def block(self):
        self.active = False
        db.session.add(self)
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.add(self)
        db.session.commit()


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    receiver = db.relationship("User", back_populates="notifications")


photos_tags = db.Table("photos_tags",
                       db.Column("photo_id", db.Integer, db.ForeignKey("photo.id")),
                       db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"))
                       )


@whooshee.register_model("description")
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500))
    filename = db.Column(db.String(64))
    filename_s = db.Column(db.String(64))
    filename_m = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    can_comment = db.Column(db.Boolean, default=True)
    flag = db.Column(db.Integer, default=0)  # 图片被举报次数
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    author = db.relationship("User", back_populates='photos')
    tags = db.relationship("Tag", secondary=photos_tags, back_populates="photos")
    comments = db.relationship("Comment", back_populates="photo")
    collects = db.relationship("Collect", back_populates="photo", cascade="all")


@whooshee.register_model("name")
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), index=True)
    photos = db.relationship("Photo", secondary=photos_tags, back_populates="tags")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    flag = db.Column(db.Integer, default=0)  # 评论被举报次数
    # 图片和评论的 1 对 多 关系
    photo_id = db.Column(db.Integer, db.ForeignKey("photo.id"))
    photo = db.relationship("Photo", back_populates="comments")
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    author = db.relationship("User", back_populates="comments")
    # 评论的邻接列表关系
    replied_id = db.Column(db.Integer, db.ForeignKey("comment.id"))  # 评论的父对象的id，多侧
    replied = db.relationship("Comment", back_populates="replies", remote_side=[id])
    replies = db.relationship("Comment", back_populates="replied", cascade="all")


# 使用关联模型表示多对多关系
class Collect(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photo.id"), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", back_populates="collects", lazy="joined")
    photo = db.relationship("Photo", back_populates="collects", lazy="joined")


@db.event.listens_for(Photo, "after_delete", named=True)
def delete_photos(**kwargs):
    """设置监听函数，当数据库中的photo记录被删除时，删除文件系统中的对应图片"""
    target = kwargs["target"]
    for filename in [target.filename, target.filename_s, target.filename_m]:
        if filename is not None:
            path = os.path.join(current_app.config["ALBUMY_UPLOAD_PATH"], filename)
            if os.path.exists(path):
                os.remove(path)


@db.event.listens_for(User, "after_delete", named=True)
def delete_avatars(**kwargs):
    target = kwargs["target"]
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:
            path = os.path.join(current_app.config["AVATARS_SAVE_PATH"], filename)
            if os.path.exists(path):
                os.remove(path)
