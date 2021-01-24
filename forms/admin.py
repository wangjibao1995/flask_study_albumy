# _*_ coding: utf-8 _*_
"""
    @author: Jibao Wang
    @time: 2020/12/25 12:58
"""
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email

from flaskdemo.models import User, Role
from flaskdemo.forms.user import EditProfileForm


class EditProfileAdminForm(EditProfileForm):
    email = StringField(label='Email', validators=[DataRequired(), Length(1, 64), Email()])
    role = SelectField(label="Role", coerce=int)
    active = BooleanField(label="Active")
    confirmed = BooleanField(label="Confirmed")
    submit = SubmitField()

    def __init__(self, user, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data.lower() != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(message="The email is already in use.")

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError(message="The username is already in use.")
