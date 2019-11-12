from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', 
				validators=[DataRequired()], 
				render_kw={"placeholder": "Email", "class": "form-control"})
    password = PasswordField('Password', 
				validators=[DataRequired()], 
				render_kw={"placeholder": "Password", "class": "form-control"})
    submit = SubmitField('Login', 
				render_kw={"class": "btn btn-primary"})

class RegistrationForm(FlaskForm):
    studentid = StringField('Student ID', 
				validators=[DataRequired()], 
				render_kw={"placeholder": "Student ID", "class": "form-control"})
    email = StringField('Email', 
				validators=[DataRequired(), Email()], 
				render_kw={"placeholder": "Email", "class": "form-control"})
    password = PasswordField('Password', 
				validators=[DataRequired()], 
				render_kw={"placeholder": "Password", "class": "form-control"})
    password2 = PasswordField('Confirm Password', 
				validators=[DataRequired(), EqualTo('password', message='Passwords must match')], 
				render_kw={"placeholder": "Confirm Password", "class": "form-control"})
    firstname = StringField('First Name', 
				validators=[DataRequired()], 
				render_kw={"placeholder": "First Name", "class": "form-control"})
    lastname = StringField('Last Name',	
				validators=[DataRequired()], 
				render_kw={"placeholder": "Last Name", "class": "form-control"})
    submit = SubmitField('Register', 
				render_kw={"class": "btn btn-primary"})

    def validate_studentid(self, studentid):
        studentid = User.query.filter_by(studentid=studentid.data).first()
        if studentid is not None:
            raise ValidationError('Your student ID is already registered.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
			
class ResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Password2')
    submit = SubmitField('Submit')