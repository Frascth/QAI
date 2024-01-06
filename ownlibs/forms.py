from datetime import datetime, timedelta
import re
from flask_wtf import FlaskForm
import wtforms
from wtforms import StringField, PasswordField, DateTimeLocalField, BooleanField, SelectField, HiddenField, IntegerField, TimeField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Email

#custom validation username
def detect_space(form, field):
    if re.search("\s+", field.data):
        raise ValidationError("Username must not contain spaces!")

def detect_spec_char_usr(form, field):
    if re.search(r"[^a-zA-Z0-9_.\s]", field.data):
        raise ValidationError("Username must not contain special characters! except underscore (_) and period (.)")

#custom validation password
def detect_spec_char_pswd(form, field):
    if not re.search(r"[^a-zA-Z0-9]", field.data):
        raise ValidationError("Password must contain special character")

def detect_num(form, field):
    if not re.search(r"[0-9]", field.data):
        raise ValidationError("Password must contain number")

def detect_capital(form, field):
    if not re.search(r"[A-Z]", field.data):
        raise ValidationError("Password must contain capital letter")

def detect_lower(form, field):
    if not re.search(r"[a-z]", field.data):
        raise ValidationError("Password must contain lower letter")

# def start_today(form, field):
#     date = field.data.strftime("%d-%m-%Y %H:%M:00")
#     date = datetime.strptime(date, "%d-%m-%Y %H:%M:00")
#     dur = date - datetime.now()
#     if  dur.days < 0:
#         raise ValidationError("Invalid date")


class detect_start_deadline(object):
    def __init__(self, fieldname="start", message=None):
        self.fieldname = fieldname
        if not message:
            message = "Deadline must atleast +24 hours from now"
        self.message = message

    def __call__(self, form, field):
        other = form[self.fieldname]

        self.start = datetime.now()
        self.start = self.start.strftime("%d-%m-%Y %H:%M:00")
        self.start = datetime.strptime(self.start, "%d-%m-%Y %H:%M:00")
        self.deadline = field.data.strftime("%d-%m-%Y %H:%M:00")
        self.deadline = datetime.strptime(self.deadline, "%d-%m-%Y %H:%M:00")
        deltatime = self.deadline - self.start

        if deltatime.days < 1:
            raise ValidationError(self.message)
        
#ADMINS
class RulesForm(FlaskForm):
    season_start = DateTimeLocalField(format="%Y-%m-%dT%H:%M")
    # season_end = db.Column(db.DateTime) #automate from duration days
    season_duration = IntegerField() #int of days
    ayah_points = StringField(render_kw={"placeholder":"100,400,900,1600,2600,4100,6600"})
    tier_names = StringField(render_kw={"placeholder":"Al Jannah,Darussalam,Darul Khuld,Darul Muqamah,Jannatul Maqwa,Adn,Firdaus"})
    days = IntegerField()
    next_day = TimeField() #%H:%M

class UsersForm(FlaskForm):
    username = StringField()
    email = StringField(default="def")
    last_read = IntegerField()
    bookmarks = StringField()
    ap = IntegerField()
    read_ayahs = IntegerField()
    read_juz = IntegerField()
    anonym = IntegerField()

class KhatamForm(FlaskForm):
    ls_rule = ["Random", "Free to Choose", "In Order Ascending", "In Order Descending"]
    
    title = StringField()
    start = DateTimeLocalField(format="%Y-%m-%dT%H:%M")
    deadline = DateTimeLocalField(format="%Y-%m-%dT%H:%M")
    setpassword = BooleanField(label="setpassword")
    password = StringField()
    member_rule = SelectField(label="member read juz", choices=ls_rule)
    member_juz = StringField()
    stoped = BooleanField(default=False)

#class form
class SignupForm(FlaskForm):
    username = StringField(label="username", validators=[
        DataRequired(message="Username must not contain whitespace character only!"), 
        Length(min=3, max=30, message="Username must be between 3 to 30 character!"),
        detect_space,
        detect_spec_char_usr],
        render_kw={"placeholder":"Username"})

    gender = SelectField(label="gender", choices=["Female", "Male"], default=0)

    email = StringField(label="email", validators=[
        DataRequired(message="Username must not contain whitespace character only!"),
        Email()],
        render_kw={"placeholder":"email@example.com"})

    password = PasswordField(label="password", validators=[
        DataRequired(),
        Length(min=8, max=30, message="Password must be between 8 to 20 character!"),
        detect_capital,
        detect_lower,
        detect_num,
        detect_spec_char_pswd],
        render_kw={"placeholder":"Password"})
    
    confirm = PasswordField(label="confirm password", validators=[EqualTo("password", message="Password must match!")], render_kw={"placeholder":"Confirm Password"})

class LoginForm(FlaskForm):
    email = StringField(label="email", validators=[
        DataRequired(message="Username must not contain whitespace character only!"),
        Email()],
        render_kw={"placeholder":"email@example.com"})

    password = PasswordField(label="password", validators=[
        DataRequired()],
        render_kw={"placeholder":"Password"})

class CKhatam(FlaskForm):
    ls_juz = [1*i for i in range(1, 31)]
    ls_rule = ["Random", "Free to Choose", "In Order Ascending", "In Order Descending"]
    title = StringField(label="title", validators=[
        DataRequired("Tittle must not contain whitespace character only!"),
        Length(min=3, max=30, message="Title must be between 3 to 30 characters!")],
        render_kw={"placeholder":"Title"})

    start = DateTimeLocalField(format="%Y-%m-%dT%H:%M", default=datetime.now())#default after press create
    deadline = DateTimeLocalField(format="%Y-%m-%dT%H:%M", default=datetime.now(), validators=[
        DataRequired("Set the deadline datetime!"), detect_start_deadline(fieldname="start")])#,
        #detect_start_deadline(fieldname="start")])
    setpassword = BooleanField(label="setpassword", default=False)
    password = StringField(label="password", default=None)
    member_rule = SelectField(label="member read juz", choices=ls_rule)
    my_juz = SelectField(label="select juz", choices=ls_juz)

class BKhatam(FlaskForm):
    id = HiddenField(render_kw={"placeholder":"Id"})

class JKhatam(FlaskForm):
    id = HiddenField(render_kw={"placeholder":"Id"})
    password = StringField(render_kw={"placeholder":"Password"}, default="")
    # my_juz = SelectField(label="select juz", choices=get_unread_juz()) #cant be done, cant __init__, once call is set theres no way to edit

class SearchFriends(FlaskForm):
    username = StringField(render_kw={"placeholder":"Username"})


