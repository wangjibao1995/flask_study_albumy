# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:59
"""
from functools import wraps
from flask import Markup, flash, url_for, redirect, abort
from flask_login import current_user


# 装饰器
def confirm_required(func):
    @wraps(func)  # 不更改 func 的名字
    def decorated_function(*args, **kwargs):  # 原本给 func 的参数，会传到这里
        if not current_user.confirmed:
            message = Markup('Please confirm your account first.'
                             'Not receive the email?'
                             '<a class="alert-link" href="%s">Resend Confirm Email</a>' % url_for("auth.resend_confirm_email"))
            flash(message, category="warning")
            return redirect(url_for("main.index"))
        return func(*args, **kwargs)  # 如果确认了，一切照旧
    return decorated_function


def permission_required(permission_name):   # 调用顺序相当于 permission_required(参数)(func)
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(func):
    return permission_required("ADMINISTER")(func)
