# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:57
"""
import os
from flask import render_template, flash, redirect, url_for, current_app, send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user
from flask_dropzone import random_filename
from sqlalchemy.sql.expression import func

from flaskdemo.decorators import permission_required, confirm_required
from flaskdemo.extensions import db
from flaskdemo.forms.main import DescriptionForm, TagForm, CommentForm
from flaskdemo.models import User, Photo, Tag, Comment, Collect, Notification, Follow
from flaskdemo.notifications import push_comment_notification
from flaskdemo.utils import redirect_back, resize_image, flash_errors


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        followed_photos = Photo.query.join(Follow, Follow.followed_id == Photo.author_id).filter(Follow.follower_id == current_user.id).order_by(Photo.timestamp.desc())
        page = request.args.get("page", default=1, type=int)
        per_page = current_app.config["ALBUMY_PHOTO_PER_PAGE"]
        pagination = followed_photos.paginate(page, per_page)
        photos = pagination.items
    else:
        pagination = None
        photos = None
    tags = Tag.query.join(Tag.photos).group_by(Tag.id).order_by(func.count(Photo.id).desc()).limit(10)
    return render_template("main/index.html", pagination=pagination, photos=photos, tags=tags, Collect=Collect)


@main_bp.route("/upload", methods=["GET", "POST"])
@login_required
@confirm_required
@permission_required("UPLOAD")
def upload():
    if request.method == "POST" and "file" in request.files:
        f = request.files.get("file")
        filename = random_filename(f.filename)  # 随机生成文件名
        f.save(os.path.join(current_app.config["ALBUMY_UPLOAD_PATH"], filename))
        filename_s = resize_image(f, filename, current_app.config["ALBUMY_PHOTO_SIZE"]["small"])
        filename_m = resize_image(f, filename, current_app.config["ALBUMY_PHOTO_SIZE"]["medium"])
        photo = Photo(filename=filename, filename_s=filename_s, filename_m=filename_m, author=current_user._get_current_object())
        db.session.add(photo)
        db.session.commit()
    return render_template("main/upload.html")


@main_bp.route("/avatars/<path:filename>")
def get_avatar(filename):
    return send_from_directory(current_app.config["AVATARS_SAVE_PATH"], filename)


@main_bp.route("/uploads/<path:filename>")
def get_image(filename):
    return send_from_directory(current_app.config["ALBUMY_UPLOAD_PATH"], filename)


@main_bp.route("/photo/<int:photo_id>")
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ALBUMY_COMMENT_PER_PAGE"]
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    description_form = DescriptionForm()
    description_form.description.data = photo.description
    comment_form = CommentForm()
    tag_form = TagForm()
    return render_template("main/photo.html", photo=photo, comment_form=comment_form, description_form=description_form, tag_form=tag_form, pagination=pagination, comments=comments)


@main_bp.route("/photo/n/<int:photo_id>")
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo.id).order_by(Photo.id.desc()).first()
    if photo_n is None:
        flash("This is already the last one.", category="info")
        return redirect(url_for("main.show_photo", photo_id=photo_id))
    return redirect(url_for("main.show_photo", photo_id=photo_n.id))


@main_bp.route("/photo/p/<int:photo_id>")
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo.id).order_by(Photo.id.asc()).first()
    if photo_p is None:
        flash("This is already the first one.", category="info")
        return redirect(url_for("main.show_photo", photo_id=photo_id))
    return redirect(url_for("main.show_photo", photo_id=photo_p.id))


@main_bp.route("/delete/photo/<int:photo_id>", methods=["POST"])
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can("MODERATE"):  # 验证当前用户是否是图片作者
        abort(403)
    db.session.delete(photo)
    db.session.commit()
    flash("Photo deleted.", category="info")
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.timestamp.desc()).first()
    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.timestamp.asc()).first()
        if photo_p is None:
            return redirect(url_for("user.index", username=photo.author.username))
        return redirect(url_for("main.show_photo", photo_id=photo_p.id))
    return redirect(url_for("main.show_photo", photo_id=photo_n.id))


@main_bp.route("/report/photo/<int:photo_id>", methods=["POST"])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash("Photo reported.", category="success")
    return redirect(url_for("main.show_photo", photo_id=photo.id))


@main_bp.route("/photo/<int:photo_id>/description", methods=["POST"])
@login_required
def edit_description(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash("Description updated.", category="success")
    flash_errors(form)
    return redirect(url_for("main.show_photo", photo_id=photo_id))


@main_bp.route("/photo/<int:photo_id>/tag/new", methods=["POST"])
@login_required
def new_tag(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash("Tag added.", category="success")
    flash_errors(form)
    return redirect(url_for("main.show_photo", photo_id=photo_id))


@main_bp.route("/delete/tag/<int:photo_id>/<int:tag_id>", methods=["POST"])
@login_required
def delete_tag(photo_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can("MODERATE"):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()
    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()
    flash("Tag deleted.", category="info")
    return redirect(url_for("main.show_photo", photo_id=photo_id))


@main_bp.route("/tag/<int:tag_id>", defaults={"order": "by_time"})
@main_bp.route("/tag/<int:tag_id>/<order>")
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get("page", default=1, type=int)
    per_page = current_app.config["ALBUMY_PHOTO_PER_PAGE"]
    order_rule = "time"
    pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items
    if order == "by_collects":
        photos.sort(key=lambda x: len(x.collects), reverse=True)
        order_rule = "collects"
    return render_template("main/tag.html", tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route("/photo/<int:photo_id>/comment/new", methods=["POST"])
@login_required
@permission_required("COMMENT")
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get("page", 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get("reply")
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.author.receive_comment_notification:
                push_comment_notification(photo_id=photo.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash("Comment published.", category="success")
        if current_user != photo.author and photo.author.receive_comment_notification:
            push_comment_notification(photo_id, receiver=photo.author, page=page)
    flash_errors(form)
    return redirect(url_for("main.show_photo", photo_id=photo_id, page=page))


@main_bp.route("/delete/comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author and not current_user.can("MODERATE"):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", category="success")
    return redirect(url_for("main.show_photo", photo_id=comment.photo_id))


@main_bp.route("/reply/comment/<int:comment_id>")
@login_required
@permission_required("COMMENT")
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(url_for("main.show_photo", photo_id=comment.photo_id, reply=comment_id, author=comment.author.name)+"#comment-form")


@main_bp.route("/set-comment/<int:photo_id>", methods=["POST"])
@login_required
def set_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)
    if photo.can_comment:
        photo.can_comment = False
        flash("Comment disabled", category="info")
    else:
        photo.can_comment = True
        flash("Comment enabled.", category="info")
    db.session.commit()
    return redirect(url_for("main.show_photo", photo_id=photo_id))


@main_bp.route("/report/comment/<int:comment_id>", methods=["POST"])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash("Comment reported.", category='success')
    return redirect(url_for('main.show_photo', photo_id=comment.photo_id))


@main_bp.route("/collect/<int:photo_id>", methods=["POST"])
@login_required
@confirm_required
@permission_required("COLLECT")
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash("Already collected.", category="info")
        return redirect(url_for("main.show_photo", photo_id=photo_id))
    current_user.collect(photo)
    flash("Photo collected.", category="success")
    return redirect(url_for("main.show_photo", photo_id=photo_id))


@main_bp.route("/uncollect/<int:photo_id>", methods=["POST"])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash("Not collect yet.", category="info")
        return redirect(url_for("main.show_photo", photo_id=photo_id))
    current_user.uncollect(photo)
    flash("Photo uncollected.", category="info")
    return redirect(url_for("main.show_photo", photo_id=photo_id))


@main_bp.route("/photo/<int:photo_id>/collectors")
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get("page", default=1, type=int)
    per_page = current_app.config["ALBUMY_USER_PER_PAGE"]
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collectors = pagination.items
    return render_template("main/collectors.html", collectors=collectors, photo=photo, pagination=pagination)


@main_bp.route("/<username>/collections")
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", default=1, type=int)
    per_page = current_app.config["ALBUMY_PHOTO_PER_PAGE"]
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).pagination(page, per_page)
    collects = pagination.items
    return render_template("user/collections.html", user=user, pagination=pagination, collects=collects)


@main_bp.route("/notifications")
@login_required
def show_notifications():
    page = request.args.get("page", default=1, type=int)
    per_page = current_app.config["ALBUMY_NOTIFICATION_PER_PAGE"]
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get("filter")
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)
    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template("main/notifications.html", pagination=pagination, notifications=notifications)


@main_bp.route("/notification/read/<int:notification_id>", methods=["POST"])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)
    notification.is_read = True
    db.session.commit()
    flash("Notification archived.", category="success")
    return redirect(url_for("main.show_notifications"))


@main_bp.route("/notifications/read/all", methods=["POST"])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash("All notifications archived.", category="success")
    return redirect(url_for("main.show_notifications"))


@main_bp.route("/explore")
def explore():
    photos = Photo.query.order_by(func.rand()).limit(12)
    return render_template("main/explore.html", photos=photos)


@main_bp.route("/search")
def search():
    q = request.args.get('q', default="").strip()  # url 查询字符串的形式传递参数
    if q == "":
        flash("Enter keyword about photo, user or tag.", category="warning")
        return redirect_back()
    category = request.args.get("category", default="photo")
    page = request.args.get("page", default=1, type=int)
    per_page = current_app.config["ALBUMY_SEARCH_RESULT_PER_PAGE"]
    if category == "user":
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == "tag":
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Photo.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template("main/search.html", q=q, results=results, pagination=pagination, category=category)
