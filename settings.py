# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 13:00
"""
import os


basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Operations:
    CONFIRM = "confirm"
    RESET_PASSWORD = "reset-password"
    CHANGE_EMAIL = "change-email"


class BaseConfig:
    # 配置 Mail 信息
    ALBUMY_ADMIN_EMAIL = os.getenv("ALBUMY_ADMIN", "1625888175@qq.com")
    ALBUMY_MAIL_SUBJECT_PREFIX = "[Albumy]"
    MAIL_SERVER = os.getenv("MAIL_SERVER", default="smtp.qq.com")
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", default="1625888175@qq.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", default="kachqswujdmmchhi")
    MAIL_DEFAULT_SENDER = ("Albumy Admin", MAIL_USERNAME)

    SECRET_KEY = os.getenv('SECRET_KEY', 'spring371327')
    # 配置文件上传信息 dropzone
    MAX_CONTENT_LENGTH = 3*1024*1024
    DROPZONE_ALLOWED_FILE_TYPE = "image"
    DROPZONE_MAX_FILE_SIZE = 3
    DROPZONE_MAX_FILES = 30
    DROPZONE_ENABLE_CSRF = True
    # 图片上传相关
    ALBUMY_PHOTO_SIZE = {"small": 400, "medium": 800}
    ALBUMY_PHOTO_SUFFIX = {ALBUMY_PHOTO_SIZE["small"]: "_s", ALBUMY_PHOTO_SIZE["medium"]: "_m"}
    ALBUMY_UPLOAD_PATH = os.path.join(basedir, 'uploads')

    BOOTSTRAP_SERVER_LOCAL = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 头像相关
    AVATARS_SAVE_PATH = os.path.join(ALBUMY_UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)

    ALBUMY_SEARCH_RESULT_PER_PAGE = 20

    ALBUMY_PHOTO_PER_PAGE = 12
    ALBUMY_COMMENT_PER_PAGE = 15
    ALBUMY_NOTIFICATION_PER_PAGE = 20
    ALBUMY_USER_PER_PAGE = 20

    ALBUMY_MANAGE_PHOTO_PER_PAGE = 20
    ALBUMY_MANAGE_USER_PER_PAGE = 30
    ALBUMY_MANAGE_TAG_PER_PAGE = 50
    ALBUMY_MANAGE_COMMENT_PER_PAGE = 30
    ALBUMY_MANAGE_RESULT_PER_PAGE = 20

    WHOOSHEE_MIN_STRING_LEN = 1


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = "mysql://root:Spring371327##@localhost/flask"
    DEBUG_TB_INTERCEPT_REDIRECTS = True
    WTF_CSRF_ENABLED = True
    DEBUG = True
    SSL_DISABLED = True


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "mysql://root:Spring371327##@localhost/flask"


class ProductionConfig(BaseConfig):
    SSL_DISABLED = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = "mysql://root:Spring371327##@localhost/flask"


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}
