import json
from random import randrange
from flask import Flask, request, redirect, url_for, render_template, flash
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_bcrypt import Bcrypt
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
import base64
import uuid
import os

from ownlibs.utils import get_ayahnquran, get_ayahnsurah, get_juz_by_ayahnquran, list2str, req_juz, req_surah, list_surah, loc2utc, utc2loc, str2list, add_mem_juz
from ownlibs.utils import convert2wav, recog, req_murottal, predict, get_surah_by_ayahnquran, req_juz_stats, get_tier, sstr2list, get_total_ayahnsurah, disp_surahn_ayahn
from ownlibs.utils import sec2time
from ownlibs.forms import SignupForm, LoginForm, CKhatam, BKhatam, JKhatam, RulesForm, UsersForm, KhatamForm, SearchFriends

app = Flask(__name__)
app.secret_key = "mdkHSK\|2473428e(*&&(Ksdwod;DNJWwnogn29718347',/..;fbfew271*%*^&%$38y832"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(days=3)

hasher = Bcrypt(app)

db = SQLAlchemy(app)
from ownlibs.dbmodels import AppRules, AppDev, SeasonHistory, Users, Khatam, PKhatam, Friends, PDMission, UserKhatam

lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"

engine = create_engine('sqlite:///db.sqlite3')

@lm.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
    
def set_update_apprules():
    rules = AppRules.query.filter_by(id=1).first()
    if not rules:
        now = datetime.utcnow()
        apprules = AppRules(
            season_name = "1",
            season_start = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00")),
            season_duration = 60,
            season_end = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00")) + timedelta(days=60),
            ayah_points = "150,650,1400,2400,3900,5750,8000", #100,400,900,1600,2600,4100,6600
            tier_names = "Al Jannah,Darussalam,Darul Khuld,Darul Muqamah,Jannatul Maqwa,Adn,Firdaus",
            days = 1,
            next_day = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00")) + timedelta(days=1))
        db.session.add(apprules)
        db.session.commit()
    else:
        now = datetime.utcnow()
        res = rules.next_day - now
        if rules.days >= rules.season_duration and res.days < 0: #and res.days < 0
            rules.season_name = str(int(rules.season_name)+1)
            rules.season_start = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00"))
            rules.season_duration = 60
            rules.season_end = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00")) + timedelta(days=60)
            rules.ayah_points = "150,650,1400,2400,3900,5750,8000"
            rules.tier_names = "Al Jannah,Darussalam,Darul Khuld,Darul Muqamah,Jannatul Maqwa,Adn,Firdaus"
            rules.days = 1
            rules.next_day = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00")) + timedelta(days=1)

            update_season_history()

        elif res.days < 0:
            rules.days = rules.days+1
            rules.next_day = rules.next_day + timedelta(days=1)
            db.session.commit()

        if current_user.is_authenticated:
            if current_user.on_season != rules.season_name:
                update_season_history()
                update_khataman(chng_season=True)
                set_curr_usr2default()


def update_season_history():
    rules = AppRules.query.filter_by(id=1).first()
    users = Users.query.all()

    for i in users:
        sh = SeasonHistory.query.filter_by(owner_id=i.id).first()
        if sh:
            seas = []
            for j in sh:
                seas.append(int(j.season_name))
            
            if int(rules.season_name)-1 not in seas:
                tname, img = get_tier(str2list(rules.ayah_points), sstr2list(rules.tier_names), i.ap)
                sh = SeasonHistory(
                    owner=i,
                    season_name = str(int(rules.season_name)-1),
                    ap = i.ap,
                    tiername_max = tname,
                    tierimg_max = str(img),
                    visit_explore = i.visit_explore,
                    read_ayahs = i.read_ayahs,
                    read_ayahpday = float('{0:.2f}'.format(i.read_ayahs/60)),
                    read_juz = i.read_juz
                )
                db.session.add(sh)
                db.session.commit()

        else:
            tname, img = get_tier(str2list(rules.ayah_points), sstr2list(rules.tier_names), i.ap)

            sh = SeasonHistory(
                owner=i,
                season_name = str(int(rules.season_name)-1),
                ap = i.ap,
                tiername_max = tname,
                tierimg_max = str(img),
                visit_explore = i.visit_explore,
                read_ayahs = i.read_ayahs,
                read_ayahpday = float('{0:.2f}'.format(i.read_ayahs/60)),
                read_juz = i.read_juz
            )
            db.session.add(sh)
            db.session.commit()
    
        set_curr_usr2default(user=i)

    
def set_curr_usr2default(user=current_user):
    rules = AppRules.query.filter_by(id=1).first()
    user.ap = 0
    user.tier_title = -1
    user.read_ayahs = 0
    user.read_juz = 0
    user.retry_same_ayah = 0
    user.retried_ayahnquran = 0
    user.on_season = rules.season_name
    db.session.commit()

    for i in user.khatam_post:
        db.session.delete(i)
    db.session.commit()

    for i in user.progress_khatam:
        db.session.delete(i)
    db.session.commit()

    for i in user.progress_dmission:
        db.session.delete(i)
    db.session.commit()

def update_khataman(chng_season=False):
    """
    \n handle the deadline, extend deadline, auto kick user that incomplete in deadline
    \n if chng_season delete all record in progress khatam, userkhatam, and khataman,
    """
    khatams = Khatam.query.all()

    if chng_season:
        try:
            PKhatam.query.delete()

            db.session.query(UserKhatam).delete()

            Khatam.query.delete()
            db.session.commit()
            # flash('suks')
        except:
            pass
            # flash('error')
    else:
        for i in khatams:
            expire = i.deadline - datetime.utcnow()
            if expire.days < 0:
                memcomp = str2list(i.member_complete)
                if 0 in memcomp or len(memcomp)<30 : #incomplete
                    # extend the deadline
                    i.extended = i.extended+1
                    i.deadline = i.deadline+timedelta(days=3)
                    db.session.commit()
                    if current_user == i.author: #current_user.id == i.author.id:
                        flash(f"{i.title} extended for 3 days from now")
                    
                    # kick lazy member
                    for j in str2list(i.member_complete):
                        if j <= 0 and j!=0: #j!=0 ignore kick admin
                            kick_khatam_member(khatamid=i.id, userid=i.members[j].id)

                else: #complete all
                    i.extended = -1 #extends -1 for mark complete all
                    db.session.commit()
                    if current_user == i.author: #current_user.id == i.author.id:
                        flash(f"{i.title} complete")
                        ap_plus_custom(msg=f"{i.title} complete AP+", incr=300)

        # dl = utc2loc(i.deadline)
        # res = i.deadline - datetime.utcnow()
        # if res.days < 0:
        #     users = Users.query.all()
        #     for j in users:
        #         for k in j.progress_khatam:
        #             if k.for_khatam_id == khatams.id:
        #                 flash(f"deleted progress khatam {j.username} khatam id {k.for_khatam_id}")
        #                 db.session.delete(k)
        #                 db.session.commit()
        #     flash(f"deleted khatam id {i.id}")
        #     db.session.delete(i)
        #     db.session.commit()

def ap_plus_ayah():
    """
    \n ap+1
    \n read_ayahs+1
    \n reset retry_same_ayah and retried_ayahnquran
    \n flash Ayah Points +1
    """
    current_user.ap = current_user.ap+1
    current_user.read_ayahs = current_user.read_ayahs+1
    current_user.retry_same_ayah = 0
    current_user.retried_ayahnquran = None
    db.session.commit()
    flash("AP +1")
    
    # update_curr_usr()


def ap_plus_custom(msg="AP +", incr=0):
    """
    \n ap+{incr}
    \n flash {msg} +{incr}
    """
    current_user.ap = current_user.ap+incr
    db.session.commit()
    flash(f"{msg} +{incr}")
    # update_curr_usr()


def track_pkhatam(ayahnquran):
    """
    \n update user progress khatam
    \n check if completed then flash bonus point +10
    """
    surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)

    if current_user.progress_khatam:
        for i in range(len(current_user.progress_khatam)):
            ls_ayahnquran = str2list(current_user.progress_khatam[i].unread_ayahnquran)
            if ayahnquran in ls_ayahnquran:
                ls_ayahnquran.remove(ayahnquran)
                current_user.progress_khatam[i].unread_ayahnquran = list2str(ls_ayahnquran)
                current_user.progress_khatam[i].read = current_user.progress_khatam[i].read+1
                db.session.commit()
                flash(f"Record added, juz {current_user.progress_khatam[i].juz} surah {surah_disp} ayah {ayah_disp}")
                # flash(f"Record added, juz {current_user.progress_khatam[i].juz} ayah in quran number {ayahnquran}")

            if str2list(current_user.progress_khatam[i].unread_ayahnquran) == [] or str2list(current_user.progress_khatam[i].unread_ayahnquran) == None or len(str2list(current_user.progress_khatam[i].unread_ayahnquran)) <= 0:
                flash(f"Completed juz {current_user.progress_khatam[i].juz}")
                found_khatam = Khatam.query.filter_by(id=current_user.progress_khatam[i].for_khatam_id).first()
                ls_member_juz = str2list(found_khatam.member_juz)
                mem_compl = str2list(found_khatam.member_complete)
                for i in range(len(ls_member_juz)):
                    if  ls_member_juz[i] == current_user.progress_khatam[i].juz:
                        mem_compl[i] = 1
                        found_khatam.member_complete = list2str(mem_compl)
                        break
                
                current_user.read_juz = current_user.read_juz+1
                ap_plus_custom(msg=f"Khataman juz {current_user.progress_khatam[i].juz} complete AP bonus", incr=50)

                db.session.delete(current_user.progress_khatam[i])
                db.session.commit()
    
    # update_curr_usr()


def get_global_data(sort=False):
    """
    \nreturn id, username, gender, ap, tiernames, img, and ad in list 
    \nsort ap default false
    \nalso return current_user data first default
    """
    lsf_id = []
    lsf_username = []
    lsf_gender = []
    lsf_ap = []
    lsf_tiernames = []
    lsf_img = []
    lsf_ad = []

    rules = AppRules.query.filter_by(id=1).first()
    all_user = Users.query.limit(100).all()
    for i in all_user:
        lsf_id.append(i.id)
        lsf_username.append(i.username)
        lsf_gender.append(i.gender)
        lsf_ap.append(i.ap)
        tier, img = get_tier(aprules=str2list(rules.ayah_points), tier_names=sstr2list(rules.tier_names), ap=i.ap)
        lsf_tiernames.append(tier)
        lsf_img.append(img)
        lsf_ad.append(i.read_ayahs/rules.days)

    if sort:
        temp = {}
        for i in range(len(lsf_id)):
            temp.__setitem__(lsf_id[i], lsf_ap[i])
        marklist = sorted(temp.items(), key=lambda x:x[1], reverse=True)
        sortdict = dict(marklist)
        ls_sortid = list(sortdict.keys())

        id = []
        username = []
        gender = []
        ap = []
        tiernames = []
        img = []
        ad = []

        for i in ls_sortid:
            index = lsf_id.index(i)
            id.append(int(i))
            username.append(lsf_username[index])
            gender.append(lsf_gender[index])
            ap.append(lsf_ap[index])
            tiernames.append(lsf_tiernames[index])
            img.append(lsf_img[index])
            ad.append(lsf_ad[index])
        
        return id, username, gender, ap, tiernames, img, ad
    else:
        return lsf_id, lsf_username, lsf_gender, lsf_ap, lsf_tiernames, lsf_img, lsf_ad

def get_friends_data(userid=0, sort=False, id_only=False):
    """
    \nreturn id, username, gender, ap, tiernames, img, and ad in list 
    \nsort ap default false
    \nalso return current_user data first default
    """

    lsf_id = []
    lsf_username = []
    lsf_gender = []
    lsf_ap = []
    lsf_tiernames = []
    lsf_img = []
    lsf_ad = []

    user = Users.query.filter_by(id=int(userid)).first()
    friends = Friends.query.filter_by(friend_id=int(userid))

    rules = AppRules.query.filter_by(id=1).first()

    lsf_id.append(current_user.id)
    lsf_username.append(current_user.username)
    lsf_gender.append(current_user.gender)
    lsf_ap.append(current_user.ap)
    tier, img = get_tier(aprules=str2list(rules.ayah_points), tier_names=sstr2list(rules.tier_names), ap=current_user.ap)
    lsf_tiernames.append(tier)
    lsf_img.append(img)
    lsf_ad.append(current_user.read_ayahs/rules.days)

    for i in user.friends:
        temp = Users.query.filter_by(id=i.friend_id).first()
        lsf_id.append(temp.id)
        lsf_username.append(temp.username)
        lsf_gender.append(temp.gender)
        lsf_ap.append(temp.ap)
        tier, img = get_tier(aprules=str2list(rules.ayah_points), tier_names=sstr2list(rules.tier_names), ap=temp.ap)
        lsf_tiernames.append(tier)
        lsf_img.append(img)
        lsf_ad.append(float('{0:.2f}'.format(temp.read_ayahs/rules.days)))

    for i in friends:
        lsf_id.append(i.owner.id)
        lsf_username.append(i.owner.username)
        lsf_gender.append(i.owner.gender)
        lsf_ap.append(i.owner.ap)
        tier, img = get_tier(aprules=str2list(rules.ayah_points), tier_names=sstr2list(rules.tier_names), ap=i.owner.ap)
        lsf_tiernames.append(tier)
        lsf_img.append(img)
        lsf_ad.append(float('{0:.2f}'.format(i.owner.read_ayahs/rules.days)))

    if sort:
        temp = {}
        for i in range(len(lsf_id)):
            temp.__setitem__(lsf_id[i], lsf_ap[i])
        marklist = sorted(temp.items(), key=lambda x:x[1], reverse=True)
        sortdict = dict(marklist)
        ls_sortid = list(sortdict.keys())

        id = []
        username = []
        gender = []
        ap = []
        tiernames = []
        img = []
        ad = []

        for i in ls_sortid:
            index = lsf_id.index(i)
            id.append(int(i))
            username.append(lsf_username[index])
            gender.append(lsf_gender[index])
            ap.append(lsf_ap[index])
            tiernames.append(lsf_tiernames[index])
            img.append(lsf_img[index])
            ad.append(lsf_ad[index])
        
        if id_only:
            return id
        else:
            return id, username, gender, ap, tiernames, img, ad
            
    else:
        if id_only:
            return lsf_id
        else:
            return lsf_id, lsf_username, lsf_gender, lsf_ap, lsf_tiernames, lsf_img, lsf_ad

def set_dmission():

    ls_surah = [(100+i) for i in range(15)]
    rules = AppRules.query.filter_by(id=1).first()

    if not current_user.progress_dmission:

        if current_user.progress_khatam:
            juzn = current_user.progress_khatam[randrange(0,len(current_user.progress_khatam))].juz
            temp = current_user.progress_khatam[randrange(0,len(current_user.progress_khatam))]
            rnd_ajuz = str2list(temp.unread_ayahnquran)
            rnd_ajuz = rnd_ajuz[:int(0.1*len(rnd_ajuz))]

            surahn = ls_surah[randrange(0,len(ls_surah))]
            ls_surah_day = []
            for i in range(get_total_ayahnsurah(surahn)):
                ls_surah_day.append(get_ayahnquran(surahn, i))

            dm = PDMission(
                owner = current_user,
                owner_id = current_user.id,
                for_day = rules.days,
                jc_khatam_today = True,
                jc_khatam = True,
                juz_name = int(juzn),
                juz_day = list2str(rnd_ajuz),
                max_juz_day = list2str(rnd_ajuz),
                visit_explore = 0,
                max_visit_explore = 3,
                surah_name = req_surah(surahn)['name'],
                surah_day = list2str(ls_surah_day),
                max_surah_day = list2str(ls_surah_day)
            )

            db.session.add(dm)
            db.session.commit()
            flash("Check new daily mission for you")

        else:
            surahn = ls_surah[randrange(0,len(ls_surah))]
            ls_surah_day = []
            for i in range(get_total_ayahnsurah(surahn)):
                ls_surah_day.append(get_ayahnquran(surahn, i))

            dm = PDMission(
                owner = current_user,
                owner_id = current_user.id,
                for_day = rules.days,
                jc_khatam_today = False,
                jc_khatam = False,
                juz_name = 0,
                juz_day = "None",
                max_juz_day = "None",
                visit_explore = 0,
                max_visit_explore = 3,
                surah_name = req_surah(surahn)['name'],
                surah_day = list2str(ls_surah_day),
                max_surah_day = list2str(ls_surah_day)
            )

            db.session.add(dm)
            db.session.commit()
            flash("Check new daily mission for you")

    else:
        dm = current_user.progress_dmission[0]
        if dm.for_day < rules.days:
            db.session.delete(dm)
            db.session.commit()
            set_dmission()

def track_dmission(ayahnquran=None, explore=None, jckhataman=None):
    """
    \n update progress dmission ayahnquran, explore, and jckhataman
    \n check if completed flash bonus point
    """
    dm = current_user.progress_dmission[0]
    if not dm:
        set_dmission()
    
    if ayahnquran or ayahnquran == 0:
        juz_day = str2list(dm.juz_day)
        surah_day = str2list(dm.surah_day)
        # print("here"*100)
        # print(juz_day)

        if ayahnquran in juz_day:
            juz_day.remove(ayahnquran)
            if len(juz_day) > 0:
                dm.juz_day = list2str(juz_day)
                db.session.commit()
                flash("Daily mission updated")
            elif len(juz_day) <= 0:
                dm.juz_day = "Complete"
                db.session.commit()
                ap_plus_custom(msg=f"10% Challenge complete AP", incr=15)

        if ayahnquran in surah_day:
            surah_day.remove(int(ayahnquran))
            if len(surah_day) > 0 : #surah_day != None or surah_day != []
                dm.surah_day = list2str(surah_day)
                db.session.commit()
                flash("Daily mission updated")

            elif len(surah_day) <= 0:
                dm.surah_day = "Complete"
                db.session.commit()
                ap_plus_custom(msg=f"Surah of the Day complete AP", incr=10)

    if explore:
        visit_explore = dm.visit_explore+int(explore)
        if visit_explore < dm.max_visit_explore:
            dm.visit_explore = visit_explore
            db.session.commit()
            flash("Daily mission updated")

        elif visit_explore == dm.max_visit_explore:
            dm.visit_explore = visit_explore
            db.session.commit()
            ap_plus_custom(msg=f"Upgrade Almaerifuh complete AP", incr=5)


        current_user.visit_explore = current_user.visit_explore+int(explore)
        db.session.commit()


    if jckhataman and not dm.jc_khatam:
        dm.jc_khatam = jckhataman
        db.session.commit()
        ap_plus_custom(msg=f"Let's Start Khataman complete AP", incr=15)

    # update_curr_usr()
    

def kick_khatam_member(khatamid=0, userid=0):
    """
    \n clear memjuz and memcompl in khatam
    \n clear progress khatam in pkhatam
    \n clear relation in userkhatam
    """

    try:
        khatamid = int(khatamid)
        userid = int(userid)
    except:
        pass

    found_khatam = Khatam.query.filter_by(id=khatamid).first()

    # removing from khatam
    memjuz = str2list(found_khatam.member_juz)
    memcomp = str2list(found_khatam.member_complete)

    index = 0
    for i in range(len(found_khatam.members)):
        if found_khatam.members[i].id == userid:
            index = i
            break
    
    # print(index, "here"*100)
    memjuz.pop(index)
    memcomp.pop(index)

    found_khatam.member_juz = list2str(memjuz)
    found_khatam.member_complete = list2str(memcomp)
    db.session.commit()

    #removing from pkhatam
    temp = PKhatam.query.filter_by(for_khatam_id=khatamid, owner_id=userid).first()
    db.session.delete(temp)
    db.session.commit()


    #removing from userkhatam
    comm = UserKhatam.delete(UserKhatam.c.user_id == userid and UserKhatam.c.khatam_id == khatamid)
    with engine.connect() as conn:
        conn.execute(comm)

    temp = Users.query.filter_by(id=userid).first()
    if current_user == found_khatam.author:
        flash(f'{temp.username} kicked from {found_khatam.title}')


@app.route("/admin")
@login_required
def admin():
    if current_user.username != "admin":
        flash("Invalid access")
        return redirect(url_for("home"))
    elif current_user.username == "admin":
        return render_template("admins/theme.html")
    
@app.route("/admin/<page>", methods=["GET", "POST"])
@login_required
def admin_page(page="rules"):
    if current_user.username != "admin":
        flash("Invalid access")
        return redirect(url_for("home"))
    elif current_user.username == "admin":
    
        rform = RulesForm()
        if rform.validate_on_submit():
            rules = AppRules.query.filter_by(id=1).first()
            if rules:
                rules.season_start = loc2utc(rform.season_start.data)
                rules.season_duration = int(rform.season_duration.data)
                rules.season_end = loc2utc(rform.season_start.data) + timedelta(days=int(rform.season_duration.data))
                rules.ayah_points = rform.ayah_points.data
                rules.tier_names = rform.tier_names.data
                rules.days = rform.days.data

                now = datetime.utcnow()
                rules.next_day = (datetime.strptime(f"{now.day}-{now.month}-{now.year} 03:00:00", "%d-%m-%Y %H:00:00")) + timedelta(days=1)
                db.session.commit()
                flash("Database update success")
            else:
                apprules = AppRules(
                    season_start = loc2utc(rform.season_start.data),
                    season_duration = int(rform.season_duration.data),
                    season_end = loc2utc(rform.season_start.data) + timedelta(days=int(rform.season_duration.data)),
                    ayah_points = rform.ayah_points.data,
                    tier_names = rform.tier_names.data,
                    days = rform.days.data)
                db.session.add(apprules)
                db.session.commit()
                flash("Database created success")
            

        if page == "rules":
            return render_template("admins/rules.html", rform = rform)
        elif page == "users":
            users = Users.query.all()
            rules = AppRules.query.filter_by(id=1).first()
            res = rules.season_end - datetime.utcnow()
            if res.days < 0:
                for i in users:
                    i.ap = 0
                    db.session.commit()

            users = Users.query.all()
            return render_template("admins/users.html", users=users)
        elif page == "khatams":
            khatams = Khatam.query.all()
            update_khataman()
            return render_template("admins/khatams.html", khatams=khatams)
        elif page == "report":
            pass
            return redirect(url_for("home"))


@app.route("/admin/users/<id>", methods=["GET", "POST"] )
@login_required
def edit_user(id=1):
    if current_user.username != "admin":
        flash("Invalid access")
        return redirect(url_for("home"))
    elif current_user.username == "admin":

        uform = UsersForm()
        users = Users.query.filter_by(id=int(id)).first()
        if uform.validate_on_submit():
            if uform.username.data != None:
                users.username = uform.username.data
            if uform.email.data != None:
                users.email = uform.email.data
            if uform.last_read.data != None:
                users.last_read = uform.last_read.data
            if uform.bookmarks.data != None:
                users.bookmarks = uform.bookmarks.data
            if uform.ap.data != None:
                users.ap = uform.ap.data
            if uform.read_ayahs.data != None:
                users.read_ayahs = uform.read_ayahs.data
            if uform.read_juz.data != None:
                users.read_juz = uform.read_juz.data
            if uform.anonym.data != None:
                users.anonym = uform.anonym.data
            users.ap = int(uform.ap.data)
            db.session.commit()
            flash("update complete")

        return render_template("admins/editusers.html", uform=uform, users=users)

@app.route("/admin/khatams/<id>", methods=["GET", "POST"] )
@login_required
def edit_khatams(id=1):
    if current_user.username != "admin":
        flash("Invalid access")
        return redirect(url_for("home"))
    elif current_user.username == "admin":
        return render_template("admins\\theme.html")

    kform = KhatamForm()
    khat = Khatam.query.filter_by(id=int(id)).first()

    if kform.validate_on_submit():
        db.session.delete(khat)
        db.session.commit()
        flash(f"khatam post deleted")

    return render_template("admins/editkhatams.html", kform=kform, khat=khat)

@app.route("/")
def gohome():
    return redirect(url_for("home"))

@app.route("/home", methods=["GET", "POST"])
def home():
    set_update_apprules()

    if current_user.is_authenticated:
        set_update_apprules()
        set_dmission()



        # flash("Database created success")
    # current_user.progress_khatam[0].unread_ayahnquran = list2str([])
    # db.session.commit()
    # flash(f"{current_user.progress_khatam[0].unread_ayahnquran}")
    # track_pkhatam(0)
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if current_user.is_authenticated:
        flash("Already logged in")
        return redirect(url_for("home"))
    else:
        rules = AppRules.query.filter_by(id=1).first()
        sform = SignupForm()
        if sform.validate_on_submit():
            found_user = Users.query.filter_by(username=sform.username.data).first()
            found_email = Users.query.filter_by(email=sform.email.data).first()

            if not found_user and not found_email:
                hpass = hasher.generate_password_hash(sform.password.data)
                user = Users(username=sform.username.data, gender=sform.gender.data, email=sform.email.data, password=hpass, on_season=rules.season_name)
                db.session.add(user)
                db.session.commit()



                flash("Account registration success, please login")
                return redirect(url_for("login"))
            elif found_user:
                flash("Username already exist please try another username")
            elif found_email:
                flash("Email already registered please choose another email or login")
            else:
                flash("Invalid input please try again")

        return render_template("signup.html", sform=sform)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("Already logged in")
        return redirect(url_for("home"))

    lform = LoginForm()
    if lform.validate_on_submit():
        found = Users.query.filter_by(email=lform.email.data).first()
        if found:
            if hasher.check_password_hash(found.password, lform.password.data):
                login_user(found)
                rules = AppRules.query.filter_by(id=1).first()
                # print(f'{i.username} here'*100)
                for i in range(1, int(rules.season_name)):
                    tname, img = get_tier(str2list(rules.ayah_points), sstr2list(rules.tier_names), 0)

                    sh = SeasonHistory(
                        owner=current_user,
                        season_name = str(i),
                        ap = 0,
                        tiername_max = tname,
                        tierimg_max = str(img),
                        visit_explore = 0,
                        read_ayahs = 0,
                        read_ayahpday = float('{0:.2f}'.format(0/60)),
                        read_juz = 0
                    )
                    db.session.add(sh)
                    db.session.commit()
                return redirect(url_for("dashboard"))
            else:
                flash("Wrong password please try again")
        else:
            flash("Email is not registered")

    return render_template("login.html", lform=lform)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():

    #curr_usr
    # update_curr_usr()

    # AppRules
    set_update_apprules()

    # Daily Mission
    set_dmission()

    #User Stats
    pkhatam = PKhatam.query.filter_by(owner=current_user)
    rules = AppRules.query.filter_by(id=1).first()
    tier, img = get_tier(
        aprules=str2list(rules.ayah_points),
        tier_names=sstr2list(rules.tier_names),
        ap=current_user.ap
    )

    friend = Friends.query.filter_by(friend_id=int(current_user.id))
    total_f = 0
    for i in friend:
        total_f+=1

    total_f += len(current_user.friends)

    return render_template("dashboard.html", 
    total_f=total_f,
    str2list=str2list, 
    sstr2list=sstr2list,
    utc2loc=utc2loc, 
    pkhatam=pkhatam,
    rules=rules, 
    tier=tier,
    img=img)

@app.route("/quran/surah/casual/browse")
def b_surah_c():
    surahs = list_surah()

    if current_user.is_authenticated:
        try:
            lastread = int(current_user.last_read)
            surahn = get_surah_by_ayahnquran(lastread)
            surah_disp = surahs[surahn]['name']
            ayahn = get_ayahnsurah(surahn, lastread)
        except:
            lastread = None
            surahn = None
            ayahn = None
        
        try:
            ls_bookmarks = str2list(current_user.bookmarks)
            ls_surahn = []
            ls_surah_disp = []
            ls_ayahn = []
            for i in range(len(ls_bookmarks)):
                ls_surahn.append(get_surah_by_ayahnquran(ls_bookmarks[i]))
                ls_surah_disp.append(surahs[ls_surahn[i]]['name'])
                ls_ayahn.append(get_ayahnsurah(ls_surahn[i], ls_bookmarks[i]))
        except:
            ls_bookmarks = None
            ls_surahn = None
            ls_surah_disp = None
            ls_ayahn = None

        return render_template("surah/b_surah_c.html", 
            surahs=surahs, 
            surahn=surahn,
            surah_disp=surah_disp,
            ayahn=ayahn,
            ls_bookmarks=ls_bookmarks,
            ls_surahn=ls_surahn,
            ls_surah_disp=ls_surah_disp,
            ls_ayahn=ls_ayahn)

    else:
        return render_template("surah/b_surah_c.html", 
            surahs=surahs)

@app.route("/quran/surah/trs/browse")
@login_required
def b_surah_t():
    surahs = list_surah()
    try:
        lastread = int(current_user.last_read)
        surahn = get_surah_by_ayahnquran(lastread)
        surah_disp = surahs[surahn]['name']
        ayahn = get_ayahnsurah(surahn, lastread)
    except:
        lastread = None
        surahn = None
        surah_disp = None
        ayahn = None
    
    try:
        ls_bookmarks = str2list(current_user.bookmarks)
        ls_surahn = []
        ls_surah_disp = []
        ls_ayahn = []
        for i in range(len(ls_bookmarks)):
            ls_surahn.append(get_surah_by_ayahnquran(ls_bookmarks[i]))
            ls_surah_disp.append(surahs[ls_surahn[i]]['name'])
            ls_ayahn.append(get_ayahnsurah(ls_surahn[i], ls_bookmarks[i]))
    except:
        ls_bookmarks = None
        ls_surahn = None
        ls_surah_disp = None
        ls_ayahn = None

    return render_template("surah/b_surah_t.html", 
    surahs=surahs, 
    surah_disp=surah_disp,
    surahn=surahn,
    ayahn=ayahn,
    ls_bookmarks=ls_bookmarks,
    ls_surahn=ls_surahn,
    ls_surah_disp=ls_surah_disp,
    ls_ayahn=ls_ayahn)

@app.route("/quran/juz/casual/browse")
def b_juz_c():
    with open("ownlibs/inf_juz.json", "r") as f:
        inf = json.load(f)
    if current_user.is_authenticated:
        surahs = list_surah()
        try:
            lastread = int(current_user.last_read)
            surahn = get_surah_by_ayahnquran(lastread)
            surah_disp = surahs[surahn]['name']
            ayahn = get_ayahnsurah(surahn, lastread)
            juzn = get_juz_by_ayahnquran(lastread)
        except:
            lastread = None
            surahn = None
            surah_disp = None
            ayahn = None
            juzn = None

        try:
            ls_bookmarks = str2list(current_user.bookmarks)
            ls_surahn = []
            ls_surah_disp = []
            ls_ayahn = []
            ls_juzn = []
            for i in range(len(ls_bookmarks)):
                ls_surahn.append(get_surah_by_ayahnquran(ls_bookmarks[i]))
                ls_surah_disp.append(surahs[ls_surahn[i]]['name'])
                ls_ayahn.append(get_ayahnsurah(ls_surahn[i], ls_bookmarks[i]))
                ls_juzn.append(get_juz_by_ayahnquran(ls_bookmarks[i]))
        except:
            ls_bookmarks = None
            ls_surahn = None
            ls_surah_disp = None
            ls_ayahn = None
            ls_juzn = None

        return render_template("juz/b_juz_c.html", 
        inf=inf,
        ayahnquran=lastread,
        surahn=surahn,
        surah_disp=surah_disp,
        ayahn=ayahn,
        juzn=juzn,
        ls_bookmarks=ls_bookmarks,
        ls_surahn=ls_surahn,
        ls_surah_disp=ls_surah_disp,
        ls_ayahn=ls_ayahn,
        ls_juzn=ls_juzn)
    else:
        return render_template("juz/b_juz_c.html", 
            inf=inf)

@app.route("/quran/juz/trs/browse")
@login_required
def b_juz_t():
    with open("ownlibs/inf_juz.json", "r") as f:
        inf = json.load(f)

    surahs = list_surah()
    try:
        lastread = int(current_user.last_read)
        surahn = get_surah_by_ayahnquran(lastread)
        surah_disp = surahs[surahn]['name']
        ayahn = get_ayahnsurah(surahn, lastread)
        juzn = get_juz_by_ayahnquran(lastread)
    except:
        lastread = None
        surahn = None
        surah_disp = None
        ayahn = None
        juzn = None

    try:
        ls_bookmarks = str2list(current_user.bookmarks)
        ls_surahn = []
        ls_surah_disp = []
        ls_ayahn = []
        ls_juzn = []
        for i in range(len(ls_bookmarks)):
            ls_surahn.append(get_surah_by_ayahnquran(ls_bookmarks[i]))
            ls_surah_disp.append(surahs[ls_surahn[i]]['name'])
            ls_ayahn.append(get_ayahnsurah(ls_surahn[i], ls_bookmarks[i]))
            ls_juzn.append(get_juz_by_ayahnquran(ls_bookmarks[i]))
    except:
        ls_bookmarks = None
        ls_surahn = None
        ls_surah_disp = None
        ls_ayahn = None
        ls_juzn = None

    return render_template("juz/b_juz_t.html", 
    inf=inf,
    ayahnquran=lastread,
    surahn=surahn,
    surah_disp=surah_disp,
    ayahn=ayahn,
    juzn=juzn,
    ls_bookmarks=ls_bookmarks,
    ls_surahn=ls_surahn,
    ls_surah_disp=ls_surah_disp,
    ls_ayahn=ls_ayahn,
    ls_juzn=ls_juzn)

@app.route("/quran/surah/casual/<surah_number>", methods=["GET", "POST"])
def q_b_s(surah_number):
    surahs=list_surah()

    if request.method == "POST":
        ayahn = request.form["ayah"]
        ayahn = int(ayahn)
        is_lastread = request.form["islastread"]

        ayahnquran = get_ayahnquran(surah_number, ayahn)
        surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)

        if is_lastread == '1':
            current_user.last_read = ayahnquran
            db.session.commit()
            flash(f"Last read marked at surah {surah_disp} ayah {ayah_disp}")
        else:
            ls_bookmarks = str2list(current_user.bookmarks)
            if ayahnquran not in ls_bookmarks:
                ls_bookmarks.append(ayahnquran)
                current_user.bookmarks = list2str(ls_bookmarks)
                db.session.commit()
                flash(f"Bookmarks added at surah {surah_disp} ayah {ayah_disp}")
            else:
                flash(f"Surah {surah_disp} ayah {ayah_disp} is already on your bookmarks")


    ls_murottal = req_murottal(surah_number)

    surah = req_surah(surah_number)
    ayahs = surah["ayahs"]

    return render_template("surah/cas_surah.html", 
    surahs=surahs,
    surah=surah, 
    surah_number=int(surah_number),
    ayahs=ayahs, 
    ls_murottal=ls_murottal,
    get_total_ayahnsurah=get_total_ayahnsurah)

@app.route("/quran/juz/casual/<juz_number>", methods=["GET", "POST"])
def q_b_j(juz_number):
    ls_surah, start_ayah, ls_ayah, ls_read, ls_trans, ls_murottal = req_juz(int(juz_number)-1)
    surahs = list_surah()

    with open("ownlibs\\n_ayahinquran.json", "r") as f:
        inf = json.load(f)

    if request.method == "POST":
        ayahnquran = request.form["ayahnquran"]
        ayahnquran = int(ayahnquran)
        surah_number = get_surah_by_ayahnquran(ayahnquran)
        ayahn = get_ayahnsurah(surah_number, ayahnquran)
        is_lastread = request.form["islastread"]
        surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)

        if is_lastread == '1':
            current_user.last_read = ayahnquran
            db.session.commit()
            flash(f"Last read marked at surah {surah_disp} ayah {ayah_disp}")
        elif is_lastread == '0':
            ls_bookmarks = str2list(current_user.bookmarks)
            if ayahnquran not in ls_bookmarks:
                ls_bookmarks.append(ayahnquran)
                current_user.bookmarks = list2str(ls_bookmarks)
                db.session.commit()
                flash(f"Bookmarks added at surah {surah_disp} ayah {ayah_disp}")
            else:
                flash(f"Surah {surah_disp} ayah {ayah_disp} is already on your bookmarks")

    return render_template("juz/cas_juz.html", 
    juzn = int(juz_number),
    surahs=surahs,
    ls_surah = ls_surah, 
    start_ayah=start_ayah,
    ls_ayah=ls_ayah, 
    ls_read=ls_read, 
    ls_trans=ls_trans, 
    ls_murottal=ls_murottal,
    get_ayahnquran=get_ayahnquran,
    get_surah_by_ayahnquran = get_surah_by_ayahnquran,
    get_total_ayahnsurah=get_total_ayahnsurah,
    inf = inf)

@app.route("/quran/surah/<surah_number>", methods=["GET", "POST"])
@login_required
def quran_by_surah(surah_number):
    surahs = list_surah()
    ls_murottal = req_murottal(surah_number)

    if request.method == "POST":
        ayahn = request.form["ayah"]
        ayahn = int(ayahn)
        is_lastread = request.form["islastread"]
        ayahnquran = get_ayahnquran(surah_number, ayahn)
        surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)

        if is_lastread == '1':
            current_user.last_read = ayahnquran
            db.session.commit()
            flash(f"Last read marked at surah {surah_disp} ayah {ayah_disp}")
        elif is_lastread == '0':
            ls_bookmarks = str2list(current_user.bookmarks)
            if ayahnquran not in ls_bookmarks:
                ls_bookmarks.append(ayahnquran)
                current_user.bookmarks = list2str(ls_bookmarks)
                db.session.commit()
                flash(f"Bookmarks added at surah {surah_disp} ayah {ayah_disp}")
            else:
                flash(f"Surah {surah_disp} ayah {ayah_disp} is already on your bookmarks")
        elif is_lastread == '999':
            try:
                data = request.form["aud"]
            except:
                pass

            try:
                fname = str(uuid.uuid4())
                webm_file = open("temps\\"+fname+".webm", "wb")
                decode_string = base64.b64decode(data)
                webm_file.write(decode_string)
                webm_file.close()

                convert2wav("temps\\"+fname)
                text = recog("temps\\"+fname)

                ayahnquran = get_ayahnquran(surah_number, ayahn)
                score, acc = predict(text, ayahnquran)
                surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)

                if acc:
                    ap_plus_ayah()
                    track_pkhatam(ayahnquran)
                    track_dmission(ayahnquran=ayahnquran)
                    with open("l.txt", "w") as f:
                        f.write(f"{score}")    
                    return redirect(url_for('r_surah', surah_number=surah_number, state=ayahn))

                else:
                    if not current_user.retried_ayahnquran or current_user.retried_ayahnquran!= ayahnquran or score <= 0.0001:
                        current_user.retried_ayahnquran = ayahnquran
                        current_user.retry_same_ayah = 0
                        db.session.commit()
                        with open("l.txt", "w") as f:
                            f.write(f"{score}")    
                        flash(f"Retry 3 times again ayah {int(ayahn)+1} to report AI miss prediction")
                        return redirect(url_for('r_surah', surah_number=surah_number, state=ayahn-1))

                    elif current_user.retried_ayahnquran==ayahnquran and current_user.retry_same_ayah < 2:
                        current_user.retry_same_ayah = current_user.retry_same_ayah+1
                        db.session.commit()
                        with open("l.txt", "w") as f:
                            f.write(f"{score}")   
                        flash(f"Retry {3 - current_user.retry_same_ayah} times again ayah {int(ayahn)+1} to report AI miss prediction")
                        return redirect(url_for('r_surah', surah_number=surah_number, state=ayahn-1))
                    
                    elif current_user.retry_same_ayah >= 2:
                        report = AppDev(
                            reported_surah = int(surah_number)-1,
                            reported_ayah = ayahn,
                            n_ayahnquran = ayahnquran,
                            p_score = score,
                        )
                        db.session.add(report)
                        current_user.retry_same_ayah = 0
                        db.session.commit()

                        track_pkhatam(ayahnquran)
                        ap_plus_ayah()
                        track_dmission(ayahnquran=ayahnquran)

                        flash(f"AI miss prediction reported at surah {surah_disp} ayah {ayah_disp}")
                        flash(f"Thank you for your feedback, you can continue to read")

                        return redirect(url_for('r_surah', surah_number=surah_number, state=ayahn))
            except Exception as e:
                flash(f"Sorry AI can't hear you, please try again {e}")
                for i in os.listdir("temps"):
                    try:
                        os.remove("temps\\"+i)
                    except:
                        pass


    surah = req_surah(surah_number)
    ayahs = surah["ayahs"]
    return render_template("surah/trs_surah.html", 
    surahs=surahs,
    surah=surah, 
    surah_number=int(surah_number),
    ayahs=ayahs, 
    ls_murottal=ls_murottal,
    get_total_ayahnsurah=get_total_ayahnsurah)

@app.route("/quran/juz/<juz_number>", methods=["GET", "POST"])
@login_required
def quran_by_juz(juz_number):
    ls_surah, start_ayah, ls_ayah, ls_read, ls_trans, ls_murottal = req_juz(int(juz_number)-1)
    surahs = list_surah()

    with open("ownlibs\\n_ayahinquran.json", "r") as f:
        inf = json.load(f)
    
    if request.method == "POST":
        is_lastread = request.form["islastread"]
        ayahnquran = request.form["ayahnquran"]
        ayahnquran = int(ayahnquran)
        surah_number = get_surah_by_ayahnquran(ayahnquran)
        ayahn = get_ayahnsurah(surah_number, ayahnquran)

        surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)


        if is_lastread == '1':
            current_user.last_read = ayahnquran
            db.session.commit()
            flash(f"Last read marked at surah {surah_disp} ayah {ayah_disp}")
            # flash(f"Last read marked at surah {surah_number+1} ayah {ayahn}")
        elif is_lastread == '0':
            ls_bookmarks = str2list(current_user.bookmarks)
            if ayahnquran not in ls_bookmarks:
                ls_bookmarks.append(ayahnquran)
                current_user.bookmarks = list2str(ls_bookmarks)
                db.session.commit()
                flash(f"Bookmarks added at surah {surah_disp} ayah {ayah_disp}")
                # flash(f"Bookmarks added at surah {surah_number+1} ayah {ayahn}")
            else:
                flash(f"Surah {surah_disp} ayah {ayah_disp} is already on your bookmarks")
                # flash(f"Surah {surah_number+1} ayah {ayahn} is already on your bookmarks")
        elif is_lastread == '999':
            try:
                data = request.form["aud"]
                # ayahn = request.form["ayah"]
                ayahnquran = request.form["ayahnquran"]
                ayahnjuz = request.form["ayahnjuz"]
                ayahn = int(ayahn)
                ayahnquran = int(ayahnquran)
                ayahnjuz = int(ayahnjuz)

                surah_disp, ayah_disp = disp_surahn_ayahn(ayahnquran)
            except:
                pass

            try :
                fname = str(uuid.uuid4())
                webm_file = open("temps\\"+fname+".webm", "wb")
                decode_string = base64.b64decode(data)
                webm_file.write(decode_string)
                webm_file.close()
                convert2wav("temps\\"+fname)
                text = recog("temps\\"+fname)
                score, acc = predict(text, int(ayahnquran))
                surah_number = get_surah_by_ayahnquran(int(ayahnquran))

                
                if acc:
                    ap_plus_ayah()
                    track_pkhatam(ayahnquran)
                    track_dmission(ayahnquran=ayahnquran)
                    with open("l.txt", "w") as f:
                        f.write(f"{score}")
                    return redirect(url_for('r_juz', juz_number=juz_number, state=ayahnquran))
                else:
                    if not current_user.retried_ayahnquran or current_user.retried_ayahnquran != int(ayahnquran):
                        current_user.retried_ayahnquran = ayahnquran
                        current_user.retry_same_ayah = 0
                        db.session.commit()
                        flash(f"Retry {3 - current_user.retry_same_ayah} times again surah {surah_disp} ayah {ayah_disp} to report AI miss prediction")
                        # flash(f"Retry {3 - current_user.retry_same_ayah} times again surah {surah} ayah {ayahnjuz} to report AI miss prediction")
                        with open("l.txt", "w") as f:
                            f.write(f"{score}")
                        return redirect(url_for('r_juz', juz_number=juz_number, state=ayahnquran-1))
                    elif current_user.retried_ayahnquran == ayahnquran and current_user.retry_same_ayah < 2:
                        current_user.retry_same_ayah = current_user.retry_same_ayah+1
                        db.session.commit()
                        # flash(f"Retry {3 - current_user.retry_same_ayah} times again surah {surah_number+1} ayah {int(ayahn)+1} to report AI miss prediction")
                        flash(f"Retry {3 - current_user.retry_same_ayah} times again surah {surah_disp} ayah {ayah_disp} to report AI miss prediction")
                        # flash(f"Retry {3 - current_user.retry_same_ayah} times again ayah {ayahnjuz} to report AI miss prediction")
                        with open("l.txt", "w") as f:
                            f.write(f"{score}")
                        return redirect(url_for('r_juz', juz_number=juz_number, state=ayahnquran-1))
                    
                    elif current_user.retry_same_ayah >= 2:
                        report = AppDev(
                            reported_surah = int(surah_number)-1,
                            reported_ayah = ayahn,
                            n_ayahnquran = ayahnquran,
                            p_score = score,
                        )
                        db.session.add(report)
                        flash(f"AI miss prediction reported surah {surah_disp} ayah {ayah_disp}. \nThank you for your feedback, you can continue to read.")
                        # flash(f"AI miss prediction reported ayah {ayahnjuz}. \nThank you for your feedback, you can continue to read.")
                        # flash(f"AI miss prediction reported at surah {surah_number+1} ayah {ayahn}")

                        ap_plus_ayah()
                        track_pkhatam(ayahnquran)
                        track_dmission(ayahnquran=ayahnquran)

                        with open("l.txt", "w") as f:
                            f.write(f"{score}")

                        return redirect(url_for('r_juz', juz_number=juz_number, state=ayahnquran))

            except:
                flash("Sorry AI can't hear you, please try again")
                for i in os.listdir("temps"):
                    try:
                        os.remove("temps\\"+i)
                    except:
                        pass

    return render_template("juz/trs_juz.html", 
    juzn = int(juz_number),
    surahs=surahs,
    ls_surah = ls_surah, 
    start_ayah=start_ayah,
    ls_ayah=ls_ayah, 
    ls_read=ls_read, 
    ls_trans=ls_trans, 
    ls_murottal=ls_murottal,
    get_ayahnquran=get_ayahnquran,
    get_surah_by_ayahnquran = get_surah_by_ayahnquran,
    get_total_ayahnsurah=get_total_ayahnsurah,
    inf = inf)

@app.route("/tlniaacubadiiltaaa/juz/<juz_number>/<state>", methods=["GET", "POST"])
@login_required
def r_juz(juz_number = 0, state=0):
    return redirect(url_for('quran_by_juz', juz_number=juz_number, _anchor=f'ayah-{int(state)+1}'))

@app.route("/nlatbaiiluachdaita/surah/<surah_number>/<state>", methods=["GET", "POST"])
@login_required
def r_surah(surah_number = 0, state=0):
    return redirect(url_for('quran_by_surah', surah_number=surah_number, _anchor=f'ayah-{int(state)+1}'))

@app.route("/khatam", methods=["GET", "POST"])
@login_required
def ckhatam():
    ckform = CKhatam()
    if ckform.validate_on_submit():
        ls_my_juz = []
        for i in current_user.progress_khatam:
            ls_my_juz.append(i.juz)

        auth_juz = add_mem_juz(member_rule=ckform.member_rule.data, mem_juz="", data=ckform.my_juz.data)
        auth_juz = str2list(auth_juz)
        auth_juz = int(auth_juz[0])

        if len(ls_my_juz) < 30:
            if ckform.member_rule.data != "Free to Choose":
                if ckform.member_rule.data == "Random":
                    while auth_juz in ls_my_juz:
                        auth_juz = add_mem_juz(member_rule=ckform.member_rule.data, mem_juz="", data=ckform.my_juz.data)
                        auth_juz = str2list(auth_juz)
                        auth_juz = int(auth_juz[0])
                else:
                    if auth_juz in ls_my_juz:
                        flash(f"You have incomplete progress for juz {auth_juz}, cant create khataman with this rule")
                        return redirect(url_for("ckhatam"))

                khatamp = Khatam(
                    author=current_user,#author
                    author_id=current_user.id, 
                    title=ckform.title.data, 
                    start=loc2utc(ckform.start.data),
                    deadline=loc2utc(ckform.deadline.data),
                    setpassword=ckform.setpassword.data,
                    password=ckform.password.data,
                    member_rule=ckform.member_rule.data,
                    #member
                    member_juz=str(auth_juz),
                    member_complete = "0" 
                )

                db.session.add(khatamp)
                current_user.khatam_member.append(khatamp)
                db.session.commit()

                ls_ayah, long = req_juz_stats(int(auth_juz)-1) #in !free
                pkhatam = PKhatam(
                    for_khatam_id = khatamp.id,
                    owner = current_user,
                    owner_id = current_user.id,
                    juz = auth_juz,
                    read = 0,
                    max_read = long,
                    unread_ayahnquran = list2str(ls_ayah),
                    max_unread_ayahnquran = list2str(ls_ayah)
                )
                db.session.add(pkhatam)
                db.session.commit()


                flash("Khatam registration success")
                track_dmission(jckhataman=True)
                return redirect(url_for("bkhatam"))

            else:
                if auth_juz in ls_my_juz:
                    flash(f"You have incomplete progress for juz {auth_juz}, please choose another juz")
                    return redirect(url_for("ckhatam"))
                else:
                    khatamp = Khatam(
                        author=current_user,#author
                        author_id=current_user.id, 
                        title=ckform.title.data, 
                        start=loc2utc(ckform.start.data),
                        deadline=loc2utc(ckform.deadline.data),
                        setpassword=ckform.setpassword.data,
                        password=ckform.password.data,
                        member_rule=ckform.member_rule.data,
                        #member
                        member_juz=auth_juz,
                        member_complete = "0" 
                    )

                    db.session.add(khatamp)
                    current_user.khatam_member.append(khatamp)
                    db.session.commit()

                    ls_ayah, long = req_juz_stats(auth_juz-1)
                    pkhatam = PKhatam(
                        for_khatam_id = khatamp.id,
                        owner = current_user,
                        owner_id = current_user.id,
                        juz = auth_juz,
                        read = 0,
                        max_read = long,
                        unread_ayahnquran = list2str(ls_ayah),
                        max_unread_ayahnquran = list2str(ls_ayah)
                    )
                    db.session.add(pkhatam)
                    db.session.commit()
                    flash("Khatam registration success")
                    track_dmission(jckhataman=True)

                    return redirect(url_for("bkhatam"))
        else:
            flash(f"You have incomplete 1-30 juz, please complete your progress first")
            return redirect(url_for("dashboard"))

    return render_template("/khatam/ckhatam.html", ckform=ckform)

@app.route("/bkhatam", methods=["GET", "POST"])
@login_required
def bkhatam():
    bkform = BKhatam()
    khatams = Khatam.query.order_by(Khatam.extended.desc()).all()
    update_khataman()

    # testing juz+1 if complete
    # try:
    #     temp = PKhatam.query.filter_by(owner=current_user).first()
    #     temp.unread_ayahnquran = "0"
    #     db.session.commit()
    #     track_pkhatam(ayahnquran=0)
    # except:
    #     pass


    #testing khatam season change
    # update_khataman(chng_season=True)
    # khatams = Khatam.query.order_by(Khatam.extended.desc()).all()

    #testing
    # try:
    #     found_khatam = Khatam.query.filter_by(id=1).first()
    #     pkhatam = PKhatam.query.filter_by(owner=current_user).first()
    #     found_khatam.member_complete = "1"
    #     pkhatam.unread_ayahnquran = ""
    #     pkhatam.read = 170
    #     db.session.commit()
    #     track_pkhatam(0)
    # except:
    #     pass

    return render_template("/khatam/bkhatam.html", 
    bkform=bkform, 
    khatams=khatams,
    utc2loc=utc2loc, 
    str2list=str2list)

@app.route("/bkhatam/join/<id>", methods=["GET", "POST"])
@login_required
def jkhatam(id=1):
    found_khatam = Khatam.query.filter_by(id=int(id)).first()
    ls_juz = [1*i for i in range(1, 31)]
    readed_juz = str2list(found_khatam.member_juz)
    for i in readed_juz:
        ls_juz.remove(i)
    jkform = JKhatam()

    if request.method == 'POST':
        my_juz = request.form.get("my_juz")
        if my_juz == None:
            my_juz = 9999 #cause not free to choose none dt
        if jkform.password.data == None:
            jkform.password.data = "pass" #cause no pass none dt
        
        my_juz = add_mem_juz(member_rule=found_khatam.member_rule, mem_juz=found_khatam.member_juz, data=my_juz)
        my_juz = str2list(my_juz)
        my_juz = int(my_juz[-1])
    
    ls_my_juz = []
    for i in current_user.progress_khatam:
        ls_my_juz.append(i.juz)
    
    if jkform.validate_on_submit():
        if found_khatam.setpassword: #password
            if jkform.password.data == found_khatam.password:
                if found_khatam.member_rule == "Random":
                    while my_juz in ls_my_juz:
                        my_juz = add_mem_juz(member_rule=found_khatam.member_rule, mem_juz=found_khatam.member_juz, data=my_juz)
                        my_juz = str2list(my_juz)
                        my_juz = int(my_juz[-1])
                else:
                    if my_juz in ls_my_juz:
                        flash(f"You have incomplete progress for juz {my_juz}, you can't join with this khataman")
                        return redirect(url_for("bkhatam"))

                if current_user not in found_khatam.members:
                    current_user.khatam_member.append(found_khatam)
                    found_khatam.member_juz = add_mem_juz(member_rule=found_khatam.member_rule, mem_juz=found_khatam.member_juz, data=my_juz)
                    mem_compl = str2list(found_khatam.member_complete)
                    mem_compl.append(0)
                    found_khatam.member_complete = list2str(mem_compl)
                    db.session.commit()

                    ls_ayah, long = req_juz_stats(str2list(found_khatam.member_juz)[-1]-1)
                    pkhatam = PKhatam(
                        for_khatam_id = found_khatam.id,
                        owner = current_user,
                        owner_id = current_user.id,
                        juz = str2list(found_khatam.member_juz)[-1],
                        read = 0,
                        max_read = long,
                        unread_ayahnquran = list2str(ls_ayah),
                        max_unread_ayahnquran = list2str(ls_ayah)

                    )
                    db.session.add(pkhatam)
                    db.session.commit()
                    flash("Join succes")
                    track_dmission(jckhataman=True)

                else:
                    flash("Already joined")
            else:
                flash("Invalid password")

        else: # no password
            if found_khatam.member_rule == "Random":
                while my_juz in ls_my_juz:
                    my_juz = add_mem_juz(member_rule=found_khatam.member_rule, mem_juz=found_khatam.member_juz, data=my_juz)
                    my_juz = str2list(my_juz)
                    my_juz = int(my_juz[-1])
            else:
                if my_juz in ls_my_juz:
                    flash(f"You have incomplete progress for juz {my_juz}, you can't join with this khataman")
                    return redirect(url_for("bkhatam"))

            if current_user not in found_khatam.members:
                current_user.khatam_member.append(found_khatam)
                found_khatam.member_juz = add_mem_juz(member_rule=found_khatam.member_rule, mem_juz=found_khatam.member_juz, data=my_juz)
                mem_compl = str2list(found_khatam.member_complete)
                mem_compl.append(0)
                found_khatam.member_complete = list2str(mem_compl)
                db.session.commit()

                ls_ayah, long = req_juz_stats(str2list(found_khatam.member_juz)[-1]-1)
                pkhatam = PKhatam(
                    for_khatam_id = found_khatam.id,
                    owner = current_user,
                    owner_id = current_user.id,
                    juz = str2list(found_khatam.member_juz)[-1],
                    read = 0,
                    max_read = long,
                    unread_ayahnquran = list2str(ls_ayah),
                    max_unread_ayahnquran = list2str(ls_ayah)
                )
                db.session.add(pkhatam)
                db.session.commit()
                flash("Join succes")
                track_dmission(jckhataman=True)

            else:
                flash("Already joined")


    return render_template("/khatam/jkhatam.html", 
    jkform=jkform, 
    found_khatam=found_khatam, 
    utc2loc=utc2loc,
    str2list=str2list,
    sstr2list=sstr2list,
    ls_juz=ls_juz)

@app.route("/bkhatam/edit/<id>", methods=["GET", "POST"])
@login_required
def ekhatam(id=1):
    found_khatam = Khatam.query.filter_by(id=id).first()
    ckform = CKhatam()

    if current_user.id == found_khatam.author.id:
        # flash("Khatam deleted successfully")
        if ckform.validate_on_submit():
            found_khatam = Khatam.query.filter_by(id=id).first()
            found_khatam.title = ckform.title.data
            found_khatam.deadline = loc2utc(ckform.deadline.data)
            found_khatam.setpassword = ckform.setpassword.data
            found_khatam.password = ckform.password.data
            found_khatam.member_rule = ckform.member_rule.data
            db.session.commit()
            flash("Khataman updated successfully")
            return redirect(url_for("bkhatam"))
        return render_template("khatam/ekhatam.html",    
            ckform=ckform, 
            found_khatam=found_khatam, 
            utc2loc=utc2loc,
            str2list=str2list,
            sstr2list=sstr2list)
    else:
        flash("Restricted Access")
        return redirect(url_for("bkhatam"))

@app.route("/bkhatam/edit/members/<id>", methods=["GET", "POST"])
@login_required
def ekhatam_members(id=1):
    found_khatam = Khatam.query.filter_by(id=id).first()

    if request.method == "POST":
        if current_user.id == found_khatam.author.id:
            userid = request.form["userid"]
            kick_khatam_member(khatamid=int(id), userid=int(userid))
            # print(userid, "here"*100)
            # fuser = UserKhatam.query.filter_by(user_id=int(userid))
            # print(fuser)

            return redirect(url_for('ekhatam_members', id=id))

        else:
            flash("Restricted Access")
            return redirect(url_for("bkhatam"))

    if current_user.id == found_khatam.author.id:
        # for i in found_khatam.members:
        #     print(i.username)


        return render_template('khatam/ekhatam_members.html',
        found_khatam=found_khatam,
        str2list=str2list)



    else:
        flash("Restricted Access")
        return redirect(url_for("bkhatam"))


@app.route("/bkhatam/del/<id>", methods=["GET", "POST"])
@login_required
def dkhatam(id=1):
    found_khatam = Khatam.query.filter_by(id=id).first()
    pkhatam = PKhatam.query.filter_by(for_khatam_id=id)

    ls_member = []
    for i in found_khatam.members:
        ls_member.append(i.id)

    if current_user.id == found_khatam.author.id:
        db.session.delete(found_khatam)
        db.session.commit()

        for i in pkhatam:
            if i.owner_id in ls_member :
                db.session.delete(i)
                db.session.commit()
        
        # dm = current_user.progress_dmission[0]
        # if dm.jc_khatam_today:
        #     db.session.delete(dm)
        #     db.session.commit()
        #     set_dmission()


        flash("Khatam deleted successfully")
        return redirect(url_for("bkhatam"))
    else:
        flash("Restricted Access")
        return redirect(url_for("bkhatam"))


@app.route("/explore", methods=["GET", "POST"])
def explore():
    with open("ownlibs/explore_prophet.json") as f:
        inf = json.load(f)

    if current_user.is_authenticated:
        track_dmission(explore=1)

    return render_template("explore/explore.html", inf=inf) 

@app.route("/stalk/id/<id>", methods=["GET", "POST"])
@login_required
def stalk(id=0):
    rules = AppRules.query.filter_by(id=1).first()
    user = Users.query.filter_by(id=int(id)).first()
    friends = Friends.query.filter_by(friend_id=int(id))
    pkhatam = PKhatam.query.filter_by(owner_id=id)
    total_f = 0
    for i in friends:
        total_f+=1

    total_f += len(user.friends)

    curr_usr_f = Friends.query.filter_by(friend_id=current_user.id)

    tier, img = get_tier(
        aprules=str2list(rules.ayah_points),
        tier_names=sstr2list(rules.tier_names),
        ap=user.ap)

    return render_template("socials/stalk.html", 
    user=user, 
    curr_usr_f = curr_usr_f,
    total_f=total_f,
    str2list=str2list, 
    sstr2list=sstr2list,
    utc2loc=utc2loc, 
    pkhatam=pkhatam,
    rules=rules, 
    tier=tier,
    img=img) 

@app.route("/addfriends/id/<id>", methods=["GET", "POST"])
@login_required
def add_friends(id=1):
    user = Users.query.filter_by(id=int(id)).first()
    if user:
        friend = Friends(
            owner_id = current_user.id, 
            friend_id = id)

        db.session.add(friend)
        db.session.commit()
        flash(f"{user.username} added to your friends list")
        return redirect(url_for('stalk', id=int(id)))
    else:
        flash(f'there is no user with id {id}')
        return redirect(url_for('dashboard'))

@app.route("/viewfriends/id/<id>", methods=["GET", "POST"])
@login_required
def view_friends(id=1):
    rules = AppRules.query.filter_by(id=1).first()
    owner = Users.query.filter_by(id=int(id)).first()
    friends = Friends.query.filter_by(friend_id=int(id))

    curr_usr_f = Friends.query.filter_by(friend_id=current_user.id)

    ls_id = []
    ls_usernames = []
    ls_ad = []
    ls_gender = []
    
    curr_usr_f_id = []

    for i in owner.friends:
        temp = Users.query.filter_by(id=i.friend_id).first()
        ls_id.append(temp.id)
        ls_usernames.append(temp.username)
        ls_ad.append(temp.read_ayahs/rules.days)
        ls_gender.append(temp.gender)
    
    for i in friends:
        ls_id.append(i.owner.id)
        ls_usernames.append(i.owner.username)
        ls_ad.append(i.owner.read_ayahs/rules.days)
        ls_gender.append(i.owner.gender)

    for i in current_user.friends:
        curr_usr_f_id.append(i.friend_id)
    
    for i in curr_usr_f:
        curr_usr_f_id.append(i.owner_id)

    # print(owner.friends[0].friend_id)
    # print(friends[0].owner.username)
    # print(friends[0].owner.ap)


    # return render_template("socials/view_friends.html")
    return render_template("socials/view_friends.html",
    id=int(id),
    owner=owner,
    ls_id=ls_id,
    ls_usernames=ls_usernames,
    ls_ad=ls_ad,
    ls_gender=ls_gender,
    curr_usr_f_id=curr_usr_f_id)

@app.route("/search-friends/usr", methods=["GET", "POST"])
@login_required
def search_friends():
    sff = SearchFriends()
    found_users = None
    if sff.validate_on_submit():
        sff = SearchFriends()
        lsf_id = get_friends_data(userid=current_user.id, sort=False, id_only=True)
        rules = AppRules.query.filter_by(id=1).first()
        found_users = Users.query.filter(Users.username.like('%' + sff.username.data + '%')).all()
        # for i in found_users:
        #     print(i.username)

        return render_template('socials/search_friends.html',
        sff=sff,
        rules=rules,
        found_users=found_users,
        lsf_id=lsf_id)
    
    return render_template('socials/search_friends.html', 
    sff=sff,
    found_users=found_users)
        
    # sform = SignupForm()
    # if sform.validate_on_submit():
    #     found_user = Users.query.filter_by(username=sform.username.data).first()
    #     found_email = Users.query.filter_by(email=sform.email.data).first()

    #     if not found_user and not found_email:
    #         hpass = hasher.generate_password_hash(sform.password.data)
    #         user = Users(username=sform.username.data, gender=sform.gender.data, email=sform.email.data, password=hpass, on_season=rules.season_name)
    #         db.session.add(user)
    #         db.session.commit()
    #         flash("Account registration success, please login")
    #         return redirect(url_for("login"))
    #     elif found_user:
    #         flash("Username already exist please try another username")
    #     elif found_email:
    #         flash("Email already registered please choose another email or login")
    #     else:
    #         flash("Invalid input please try again")


@app.route("/season/<page>", methods=["GET", "POST"])
@login_required
def season(page="galery"):

    set_update_apprules()
    rules = AppRules.query.filter_by(id=1).first()

    if page == "rank":
        ls_id, ls_username, ls_gender, ls_ap, ls_tiernames, ls_img, ls_ad = get_friends_data(userid=current_user.id, sort=True)
        lsg_id, lsg_username, lsg_gender, lsg_ap, lsg_tiernames, lsg_img, lsg_ad = get_global_data(True)

        return render_template("season/rank.html",
        ls_id=ls_id,
        ls_username=ls_username,
        ls_gender=ls_gender,
        ls_ap=ls_ap,
        ls_tiernames=ls_tiernames,
        ls_img=ls_img,
        ls_ad=ls_ad,
        lsg_id=lsg_id,
        lsg_username=lsg_username,
        lsg_gender=lsg_gender,
        lsg_ap=lsg_ap,
        lsg_tiernames=lsg_tiernames,
        lsg_img=lsg_img,
        lsg_ad=lsg_ad)

    elif page == "mission":
        set_dmission()
        dm = current_user.progress_dmission[0]
        res = rules.next_day - datetime.utcnow()
        time, h, m, s = sec2time(res.seconds)

        return render_template(
            "season/mission.html",
            time=time,
            dm=dm,
            h=h,
            m=m,
            s=s,
            utc2loc=utc2loc,
            str2list=str2list)
    
    elif page == "galery":
        rules = AppRules.query.filter_by(id=1).first()

        sh = SeasonHistory.query.filter_by(owner=current_user)

        return render_template("season/galery.html",
        sh=sh,
        rules=rules,
        utc2loc=utc2loc)






# for development
@app.route("/create/<username>", methods=["GET", "POST"])
def add_user(username='user1'):
    set_update_apprules()
    rules = AppRules.query.filter_by(id=1).first()
    user = Users(
        username=username,
        gender="Male",
        email=f"{username}@gmail.com",
        on_season=rules.season_name,
        password=f"UserPass{username};",
    )

    db.session.add(user)
    db.session.commit()
    flash("user created")

    user = Users.query.filter_by(username=username).first()
    login_user(user)
    return redirect(url_for("dashboard"))

@app.route("/login/<username>", methods=["GET", "POST"])
def auto_login(username='user1'):
    fuser = Users.query.filter_by(username=username).first()
    login_user(fuser)
    flash("login succsess")
    return redirect(url_for("dashboard"))







if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)