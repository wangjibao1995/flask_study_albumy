# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:58
"""
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp
from flaskdemo.models import User

# flask_wtf 继承自 wtforms,并且提供了CSRF保护，表单验证和文件上传的功能


class EditProfileForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired(), Length(1, 30)])
    username = StringField(label="username", validators=[DataRequired(), Length(1, 20), Regexp('^[a-zA-Z0-9]*$', message='The username should contain only a-z, A-Z and 0-9.')])
    website = StringField(label="Website", validators=[Optional(), Length(0, 254)])
    location = StringField(label="City", validators=[Optional(), Length(0, 50)])
    bio = StringField(label="Bio", validators=[Optional(), Length(0, 120)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError(message='The username is already in use.')


class UploadAvatarForm(FlaskForm):
    image = FileField(label="Upload (<=3M)", validators=[FileRequired(), FileAllowed(upload_set=['jpg', 'png'], message='The file format should be .jpg or .png.')])
    submit = SubmitField()


class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField(label="Crop and Update")


class ChangeEmailForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError(message='The email is already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(label="Old Password", validators=[DataRequired()])
    new_password = PasswordField(label='New Password', validators=[DataRequired(), Length(8, 128)])
    new_password_confirm = PasswordField(label='New Password Confirm', validators=[DataRequired(), EqualTo("new_password")])
    submit = SubmitField()


class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField(label="New comment")
    receive_follow_notification = BooleanField(label="New follow")
    receive_collect_notification = BooleanField(label="New collect")
    submit = SubmitField()


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField(label="Public my collections")
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError("Wrong username")
