# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:59
"""
import os
import click
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from flask.logging import default_handler
from flask import Flask, render_template, request
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from flaskdemo.blueprints.admin import admin_bp
from flaskdemo.blueprints.ajax import ajax_bp
from flaskdemo.blueprints.auth import auth_bp
from flaskdemo.blueprints.main import main_bp
from flaskdemo.blueprints.user import user_bp
from flaskdemo.extensions import db, login_manager, mail, dropzone, avatars, bootstrap, csrf, moment, whooshee, toolbar
from flaskdemo.models import Role, User, Notification
from flaskdemo.settings import config
from werkzeug.contrib.fixers import ProxyFix


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", default="development")
    app = Flask("flaskdemo")
    app.config.from_object(config[config_name])
    register_extensions(app)
    register_commands(app)
    register_blueprints(app)
    register_shell_context(app)
    register_template_context(app)
    register_errorhandlers(app)
    register_logging(app)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    return app


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    dropzone.init_app(app)
    csrf.init_app(app)
    avatars.init_app(app)
    bootstrap.init_app(app)
    whooshee.init_app(app)
    moment.init_app(app)
    toolbar.init_app(app)
    # cache.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(ajax_bp, url_prefix="/ajax")


def register_logging(app):
    # 文件日志
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(filename='./logs/flaskdemo.log', maxBytes=10*1024*1024, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.setLevel(logging.INFO)

    default_handler.setLevel(logging.INFO)

    class RequestFormatter(logging.Formatter):
        def format(self, record) -> str:
            record.url = request.url
            record.remote_addr = request.remote_addr
            return super(RequestFormatter, self).format(record)
    request_formatter = RequestFormatter('[%(asctime)s] %(remote_addr)s requested %(url)s\n%(levelname)s in %(module)s: %(message)s')
    mail_handler = SMTPHandler(
        mailhost=app.config['MAIL_SERVER'],
        fromaddr=app.config['MAIL_USERNAME'],
        toaddrs=app.config['ALBUMY_ADMIN_EMAIL'],
        subject='Application Error',
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(request_formatter)
    if not app.debug:
        app.logger.addHandler(file_handler)
        app.logger.addHandler(default_handler)
        app.logger.addHandler(mail_handler)


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template("errors/400.html", description=e.description), 500


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User)  # ToDo 添加其他shell变量


def register_commands(app):
    @app.cli.command()
    @click.option("--drop", is_flag=True, help="Create after drop.")
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm("This operation will delete the database, do you want to continue?", abort=True)
            db.drop_all()
            click.echo("Drop tables.")
        db.create_all()
        click.echo("Initialized database.")

    @app.cli.command()
    def init():
        """Initialize flaskdemo"""
        click.echo("Initializing the database...")
        db.create_all()
        click.echo("Initializing the roles and permissions...")
        Role.init_role()
        click.echo("Done.")

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--follow', default=30, help="Quantity of follows, default is 30.")
    @click.option('--photo', default=30, help="Quantity of photos, default is 30.")
    @click.option('--tag', default=20, help="Quantity of tags, default is 20.")
    @click.option('--collect', default=50, help="Quantity of collects, default is 50.")
    @click.option('--comment', default=100, help="Quantity of comments, default is 100.")
    def forge(user, follow, photo, tag, collect, comment):
        """Generate fake data."""
        from flaskdemo.fakes import fake_admin, fake_comment, fake_follow, fake_photo, fake_tag, fake_user, fake_collect
        db.drop_all()
        db.create_all()
        click.echo("Initializing the roles and permissions...")
        Role.init_role()
        click.echo("Generating the administrator...")
        fake_admin()
        click.echo("Generating %d users..." % user)
        fake_user(user)
        click.echo("Generating %d follows..." % follow)
        fake_follow(follow)
        click.echo("Generating %d tags..." % tag)
        fake_tag(tag)
        click.echo("Generating %d photos..." % photo)
        fake_photo(photo)
        click.echo("Generating %d collects..." % collect)
        fake_collect(collect)
        click.echo("Generating %d comments..." % comment)
        fake_comment(comment)
        click.echo("Done.")
