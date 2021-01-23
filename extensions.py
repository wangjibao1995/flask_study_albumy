# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:59
"""
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, AnonymousUserMixin
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect
from flask_avatars import Avatars
from flask_moment import Moment
from flask_whooshee import Whooshee
from flask_debugtoolbar import DebugToolbarExtension


db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
dropzone = Dropzone()
csrf = CSRFProtect()
avatars = Avatars()
bootstrap = Bootstrap()
moment = Moment()
whooshee = Whooshee()
toolbar = DebugToolbarExtension()


@login_manager.user_loader
def load_user(user_id):  # p276，因为session中只存储用户的id，设置一个用户加载函数返回对应的用户对象
    from flaskdemo.models import User
    user = User.query.get(int(user_id))
    return user


# 当未登录用户访问使用了 login_required 装饰器的视图时，程序会自动重定向到登录视图，并闪现一个消息提示
login_manager.login_view = "auth.login"
login_manager.login_message = "Please login to access this page."
login_manager.login_message_category = "warning"
login_manager.refresh_view = "auth.re_authenticate"
login_manager.needs_refresh_message_category = "warning"


# p324,匿名用户可以使用类似 User 类的can和is_admin方法，接口一致
class Guest(AnonymousUserMixin):
    @property
    def is_admin(self):
        return False

    def can(self, permission_name):
        return False


# 匿名访客类
login_manager.anonymous_user = Guest
