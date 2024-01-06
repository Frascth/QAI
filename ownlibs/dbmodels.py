from datetime import datetime
from flask_login import UserMixin
from __main__ import db


class AppRules(db.Model):
    __tablename__ = "AppRules"
    id = db.Column(db.Integer, primary_key=True)
    season_name = db.Column(db.String, nullable=False)
    season_start = db.Column(db.DateTime)
    season_end = db.Column(db.DateTime)
    season_duration = db.Column(db.Integer) #int of days
    ayah_points = db.Column(db.String, nullable=False, default="100,400,900,1600,2600,4100,6600")
    tier_names = db.Column(db.String, nullable=False, default="Al Jannah,Darussalam,Darul Khuld,Darul Muqamah,Jannatul Maqwa,Adn,Firdaus")
    days = db.Column(db.Integer, nullable=False, default=1)
    next_day = db.Column(db.DateTime)

class AppDev(db.Model):
    __tablename__ = "AppDev"
    id = db.Column(db.Integer, primary_key=True)
    reported_surah = db.Column(db.Integer)
    reported_ayah = db.Column(db.Integer)
    n_ayahnquran = db.Column(db.Integer)
    p_score = db.Column(db.String)

UserKhatam = db.Table("UserKhatam", 
    db.Column("user_id", db.ForeignKey("Users.id")),
    db.Column("khatam_id", db.ForeignKey("Khatam.id"))
    )

class Users(db.Model, UserMixin):
    __tablename__="Users"
    id = db.Column(db.Integer, primary_key=True)
    date_join = db.Column(db.DateTime, default=datetime.utcnow)
    username = db.Column(db.String(20), nullable=False, unique=True)
    gender = db.Column(db.String, nullable=False, default="Female")
    email = db.Column(db.String(20), nullable=False, unique=True) #unique=True
    password = db.Column(db.String(128), nullable=False)

    last_read = db.Column(db.Integer)
    bookmarks = db.Column(db.String)

    ap = db.Column(db.Integer, nullable=False, default=0)
    # tier_title = db.Column(db.Integer, nullable=False, default=0) #from -1 to 7

    read_ayahs = db.Column(db.Integer, nullable=False, default=0)
    read_juz = db.Column(db.Integer, nullable=False, default=0)

    anonym = db.Column(db.Boolean, nullable=False, default=False)

    #season_history
    on_season = db.Column(db.String, nullable=False, default="1")
    visit_explore = db.Column(db.Integer, nullable=False, default=0)

    #o2o
    khatam_post = db.relationship("Khatam", backref="author") #lazy = True
    progress_khatam = db.relationship("PKhatam", backref="owner")
    friends = db.relationship("Friends", backref="owner")
    progress_dmission = db.relationship("PDMission", backref="owner")
    season_history = db.relationship("SeasonHistory", backref="owner")

    #o2m
    khatam_member = db.relationship("Khatam", secondary=UserKhatam, backref="members")

    #development
    retry_same_ayah = db.Column(db.Integer, nullable=False, default=0)
    retried_ayahnquran = db.Column(db.Integer)
    
    def __init__(self, username, gender, email, password, ap=0, on_season="1", anonym=False):
        self.username = username
        self.gender = gender
        self.email = email
        self.password = password
        self.ap=ap
        self.on_season=on_season
        self.anonym = anonym

class Friends(db.Model):
    __tablename__="Friends"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("Users.id"),nullable=False)
    friend_id = db.Column(db.Integer, nullable=False)

class SeasonHistory(db.Model):
    __tablename__="SeasonHistory"
    id = db.Column(db.Integer, primary_key=True)
    #owner
    owner_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    season_name = db.Column(db.String, nullable=False)
    ap = db.Column(db.Integer, nullable=False, default=0)
    tiername_max = db.Column(db.String, nullable=False, default="Unclassified")
    tierimg_max = db.Column(db.String, nullable=False, default="0")

    # ckhatam = db.Column(db.Integer, nullable=False, default=0)
    # jkhatam = db.Column(db.Integer, nullable=False, default=0)
    visit_explore = db.Column(db.Integer, nullable=False, default=0)
    
    read_ayahs = db.Column(db.Integer, nullable=False, default=0)
    read_ayahpday = db.Column(db.Float(precision=5, decimal_return_scale=2), nullable=False, default=0.00)
    read_juz = db.Column(db.Integer, nullable=False, default=0)

class Khatam(db.Model):
    __tablename__="Khatam"
    id = db.Column(db.Integer, primary_key=True)
    #author
    author_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    title = db.Column(db.String(30), nullable=False)
    start = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    setpassword = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(20))
    member_rule = db.Column(db.String, nullable=False, default="random")
    #member
    member_juz = db.Column(db.String, nullable=False)
    member_complete = db.Column(db.String, nullable=False)
    extended = db.Column(db.Integer, nullable=False, default=0)
    
    def __init__(self, author, author_id, title, start, deadline, setpassword, password, member_rule, member_juz="0", member_complete="0"):
        self.author = author
        self.author_id = author_id
        self.title = title
        self.start = start
        self.deadline = deadline
        self.setpassword = setpassword
        self.password = password
        self.member_rule = member_rule
        self.member_juz = member_juz
        self.member_complete = member_complete

class PKhatam(db.Model):
    __tablename__ = "PKhatam"
    id = db.Column(db.Integer, primary_key=True)
    for_khatam_id = db.Column(db.Integer, nullable=False)
    #owner
    owner_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    juz = db.Column(db.Integer, nullable=False)
    read = db.Column(db.Integer, nullable=False, default=0)
    max_read = db.Column(db.Integer, nullable=False, default=0)
    unread_ayahnquran = db.Column(db.String)
    max_unread_ayahnquran = db.Column(db.String)

class PDMission(db.Model):
    __tablename__ = "PDMission"
    id = db.Column(db.Integer, primary_key=True)
    #owner backref
    owner_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    for_day = db.Column(db.Integer, nullable=False, default=1)

    jc_khatam_today = db.Column(db.Boolean, nullable=False, default=False)
    jc_khatam = db.Column(db.Boolean, nullable=False, default=False)

    juz_name = db.Column(db.Integer)
    juz_day = db.Column(db.String)
    max_juz_day = db.Column(db.String)

    visit_explore = db.Column(db.Integer, nullable=False, default=0)
    max_visit_explore = db.Column(db.Integer, nullable=False, default=0)

    surah_name = db.Column(db.String)
    surah_day = db.Column(db.String)
    max_surah_day = db.Column(db.String)

