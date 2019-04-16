#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver
To run locally: $ python server.py
Go to http://localhost:8111 in your browser
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for, session, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, Form
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from sets import Set
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
Bootstrap(app)


# connect to postgred databse
# psql -h w4111.cisxo09blonu.us-east-1.rds.amazonaws.com -U yz3477 w4111
DB_USER = "yz3477"
DB_PASSWORD = "2lDOtYFj29"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"
engine = create_engine(DATABASEURI)

# check access to database at the beginning of web request
@app.before_request
def before_request():
    try:
        # variable g is globally accessible
        g.conn = engine.connect()
    except:
        print "uh oh, problem connecting to database"
        import traceback; traceback.print_exc()
        g.conn = None

# close database connect at the end of web request
@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

# define forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=6, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('Remember me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=6, max=15)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=80)])

class WeaponCatForm(FlaskForm):
    category = SelectField('Weapon Catgory', choices=[('Rifle', 'Rifle'), ('Short Gun', 'Short Gun'), ('Machine Gun', 'Machine Gun'), ('Pistol', 'Pistol')])

class RifleForm(FlaskForm):
    weapon = SelectField('Weapon Name', choices=[('M16A4', 'M16A4'), ('M416', 'M416'), ('Beryl M762', 'Beryl M762'), ('AKM', 'AK 47')])

class ShortGunForm(FlaskForm):
    weapon = SelectField('Weapon Name', choices=[('SKS', 'SKS'), ('S12K', 'S12K'), ('S1897', 'S1897'), ('S686', 'S686')])

class MachineGunForm(FlaskForm):
    weapon = SelectField('Weapon Name', choices=[('Micro UZI', 'Micro UZI'), ('Vector', 'KRISS Vector'), ('UMP9', 'UMP9'), ('Tommy Gun', 'Tommy Gun')])

class PistolForm(FlaskForm):
    weapon = SelectField('Weapon Name', choices=[('Skorpion', 'Skorpion'), ('P18C', 'P18C'), ('P92', 'P92'), ('P1911', 'P1911')])

class HealingForm(FlaskForm):
    item = SelectField('Item Name', choices=[('Bandage', 'Bandage'), ('First Aid Kit', 'First Aid Kit'), ('Med Kit', 'Med Kit')])
    map_name = SelectField('Map', choices=[('Erangel', 'Erangel'), ('Miramar', 'Miramar'), ('Sanhok', 'Sanhok')])

class BoostingForm(FlaskForm):
    item = SelectField('Item Name', choices=[('Energy Drink', 'Energy Drink'), ('Painkiller', 'Painkiller'), ('Adrenaline Syringe', 'Adrenaline Syringe')])
    map_name = SelectField('Map', choices=[('Erangel', 'Erangel'), ('Miramar', 'Miramar'), ('Sanhok', 'Sanhok')])

class RatingForm(FlaskForm):
    rating = SelectField('Rating', coerce=int, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
    map_name = SelectField('Map', choices=[('Erangel', 'Erangel'), ('Miramar', 'Miramar'), ('Sanhok', 'Sanhok')])



def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'uid' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first')
            return redirect(url_for('login'))
    return wrap


# homepage
@app.route('/')
def index():
    session['url'] = url_for('index')
    return render_template('index.html')

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        uid = request.form['username']
        cursor = g.conn.execute(text('SELECT * FROM USERS WHERE UID=:uid'), uid=uid)
        record = cursor.fetchone()
        cursor.close()
        if record:
            if record.password == request.form['password']:
                session['uid'] = request.form['username']
                if session['url']:
                    return redirect(session['url'])
                return redirect(url_for('index'))
        context = dict(form=form, check=False)
        return render_template('login.html', **context)
    return render_template('login.html', form=form)


# logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    flash('Successfully logout!')
    return render_template('index.html')


# signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        uid = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = g.conn.execute(text('SELECT UID FROM Users WHERE UID=:uid'), uid=uid)
        record = cursor.fetchone()
        cursor.close()
        if record:
            # return '<h1> User already exists. Please enter another one. </h1>'
            context = dict(form=form, check=False)
            return render_template('signup.html', **context)

        cmd = 'INSERT INTO Users(UID, Email, Password) VALUES(:uid, :email, :password)'
        cursor = g.conn.execute(text(cmd), uid=uid, email=email, password=password)
        cursor.close()
        return redirect(url_for('login'))
        
    return render_template('signup.html', form=form)

# weapon category
@app.route('/weapon', methods=['GET', 'POST'])
def weapon():
    form = WeaponCatForm()
    session['url'] = url_for('weapon')
    if form.validate_on_submit():
        if form.category.data == 'Rifle':
            return redirect(url_for('rifle'))
        if form.category.data == 'Short Gun':
            return redirect(url_for('short_gun'))
        if form.category.data == 'Machine Gun':
            return redirect(url_for('machine_gun'))
        if form.category.data == 'Pistol':
            return redirect(url_for('pistol'))
    return render_template('weapon.html', form=form)


# rifle
@app.route('/weapon/rifle', methods=['GET', 'POST'])
def rifle():
    form = RifleForm()
    if form.validate_on_submit():
        return redirect(url_for('attribute', wid=form.weapon.data))
    return render_template('rifle.html', form=form)


# short gun
@app.route('/weapon/short_gun', methods=['GET', 'POST'])
def short_gun():
    form = ShortGunForm()
    if form.validate_on_submit():
        return redirect(url_for('attribute', wid=form.weapon.data))
    return render_template('short_gun.html', form=form)


# machine gun
@app.route('/weapon/machine_gun', methods=['GET', 'POST'])
def machine_gun():
    form = MachineGunForm()
    if form.validate_on_submit():
        return redirect(url_for('attribute', wid=form.weapon.data))
    return render_template('machine_gun.html', form=form)

# pistol
@app.route('/weapon/pistol', methods=['GET', 'POST'])
def pistol():
    form = PistolForm()
    if form.validate_on_submit():
        return redirect(url_for('attribute', wid=form.weapon.data))
    return render_template('pistol.html', form=form)



# weapon attribute and attachment
@app.route('/weapon/attribute/<wid>', methods=['GET', 'POST'])
def attribute(wid):
    form = RatingForm()
    # weapon attributes
    cmd = 'SELECT AmmoType, HitDamage, ZeroingRangeLB, ZeroingRangeUB FROM Weapon WHERE WID=:wid'
    cursor = g.conn.execute(text(cmd), wid=wid)
    attribute = cursor.fetchone()
    cursor.close()
    # average rating
    cmd = 'SELECT ROUND(SUM(Rating)/COUNT(*), 1) Average_Rating FROM (SELECT Rating FROM Weapon_Rating WHERE WID =:wid) T;'
    cursor = g.conn.execute(text(cmd), wid=wid)
    average_rating = cursor.fetchone().average_rating
    cursor.close()
    # attachable attachments
    cmd = 'SELECT T1.AttID, T2.SubCategory FROM Weapon_Attch_Match T1 JOIN Attachment T2 ON T1.AttID = T2.AttID WHERE WID =:wid'
    cursor = g.conn.execute(text(cmd), wid=wid)
    scope = Set()
    magzine = Set()
    muzzle = Set()
    grip = Set()
    for record in cursor:
        if record.subcategory == 'Scope':
            scope.add(record.attid)
        if record.subcategory == 'Magazine':
            magzine.add(record.attid)
        if record.subcategory == 'Muzzle':
            muzzle.add(record.attid)
        if record.subcategory == 'Grip':
            grip.add(record.attid)
    cursor.close()
    # submit redirection
    if form.validate_on_submit():
        # submit rating
        if 'rate' in request.form:
            return redirect(url_for('rating', wid=wid, rating=form.rating.data))
        # explore location
        if 'map' in request.form:
            return redirect(url_for('location', item=wid, map=form.map_name.data))

    context = dict(form=form, wid=wid, attribute=attribute, average_rating=average_rating, scope=scope, magzine=magzine, muzzle=muzzle, grip=grip)
    return render_template('attribute.html', **context)



@app.route('/weapon/rating/<wid>&<rating>', methods=['GET', 'POST'])
@login_required
def rating(wid, rating):
    uid = session['uid']

    cmd = 'SELECT Rating FROM Weapon_Rating WHERE UID=:uid AND WID=:wid'
    cursor = g.conn.execute(text(cmd), uid=uid, wid=wid)
    record = cursor.fetchone()
    cursor.close()
    if record:
        old_rating = record.rating
        cmd = 'UPDATE Weapon_Rating SET Rating =:rating WHERE UID=:uid AND WID=:wid'
        cursor = g.conn.execute(text(cmd), uid=uid, wid=wid, rating=rating)
        cursor.close()
        return render_template('rating.html', uid=uid, wid=wid, rating=rating, old_rating=old_rating)

    cmd = 'INSERT INTO Weapon_Rating (UID, WID, Rating) VALUES (:uid, :wid, :rating)'
    cursor = g.conn.execute(text(cmd), uid=uid, wid=wid, rating=int(rating))
    cursor.close()

    return render_template('rating.html', uid=uid, wid=wid, rating=rating, old_rating=None)



# healing
@app.route('/healing', methods=['GET', 'POST'])
def healing():
    form = HealingForm()
    session['url'] = url_for('healing')
    if form.validate_on_submit():
        return redirect(url_for('location', item=form.item.data, map=form.map_name.data))
    return render_template('healing.html', form=form)

# boosting
@app.route('/boosting', methods=['GET', 'POST'])
def boosting():
    form = BoostingForm() 
    session['url'] = url_for('boosting')
    if form.validate_on_submit():
        return redirect(url_for('location', item=form.item.data, map=form.map_name.data))
    return render_template('boosting.html', form=form)

 
# location
@app.route('/location/<item>/<map>')
def location(item, map):
    context = dict(item=item, map=map)
    return render_template("location.html", **context)




if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help
    """
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()