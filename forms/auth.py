# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:58
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from flaskdemo.models import User


# 注册表单
class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired(), Length(min=1, max=30)])
    email = StringField(label="Email", validators=[DataRequired(), Length(min=1, max=254), Email()])
    username = StringField(label="Username", validators=[DataRequired(), Length(min=1, max=20),
                                                         Regexp(regex="^[a-zA-Z0-9]*$", message="The username should contain only a-z, A-Z and 0-9.")])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8, max=128)])
    password_again = PasswordField(label="Confirm password", validators=[DataRequired(), EqualTo(fieldname="password")])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("The email is already in use.")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("The username is already in use.")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    remember_me = BooleanField(label="Remember me")
    submit = SubmitField(label="Log in")


class ResetPasswordForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(8, 128)])
    password_again = PasswordField(label="Confirm password", validators=[DataRequired(), EqualTo(fieldname="password")])
    submit = SubmitField()


class ForgetPasswordForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()
