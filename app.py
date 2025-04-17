from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
import calendar
from datetime import datetime
from models import db, Event
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import locale

app = Flask(__name__)
app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'calendar'

mysql = MySQL(app)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'login' in request.form and 'password' in request.form:
        login = request.form['login']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE login = %s AND password = %s', (login, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['idusers'] = user['idusers']
            session['login'] = user['login']
            return redirect(url_for('calendar_view'))
        else:
            msg = 'Неправильный логин или пароль!'
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE login = %s', (login,))
        user = cursor.fetchone()
        if user:
            msg = 'Аккаунт уже существует!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Некорректный email!'
        elif not re.match(r'[A-Za-z0-9]+', login):
            msg = 'Логин может содержать только буквы и цифры!'
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s)', (email, login, password, firstname, lastname))
            mysql.connection.commit()
            msg = 'Вы успешно зарегистрированы!'
            return redirect(url_for('login'))
    return render_template('register.html', msg=msg)


@app.route('/calendar', methods=['GET', 'POST'])
def calendar_view():
    if 'loggedin' in session:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))

        month_days = calendar.monthcalendar(year, month)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        user_id = session['idusers']

        cursor.execute('SELECT * FROM events WHERE idusers = %s', (user_id,))
        events = cursor.fetchall()
        cursor.execute('SELECT * FROM meetings WHERE idusers = %s', (user_id,))
        meetings = cursor.fetchall()


        RU_MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                     'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        current_month_name = RU_MONTHS[month - 1]

        return render_template('calendar.html',
                               events=events,
                               meetings=meetings,
                               month=month,
                               year=year,
                               month_days=month_days,
                               current_month_name=current_month_name,
                               current_year=year,
                               now=datetime.now())
    return redirect(url_for('login'))

@app.route('/add_event', methods=['POST'])
def add_event():
    if 'loggedin' in session:
        name = request.form['event_name']
        date = request.form['event_date']
        description = request.form['description']
        location = request.form['location']
        user_id = session['idusers']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO events VALUES (NULL, %s, %s, %s, %s, %s)', (user_id, name, date, description, location))
        mysql.connection.commit()
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/add_meeting', methods=['POST'])
def add_meeting():
    if 'loggedin' in session:
        name = request.form['meeting_name']
        date = request.form['meeting_date']
        description = request.form['description']
        location = request.form['location']
        user_id = session['idusers']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO meetings VALUES (NULL, %s, %s, %s, %s, %s)', (user_id, name, date, description, location))
        mysql.connection.commit()
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/add_event')
def add_event_page():
    return render_template('add_event.html')

@app.route('/add_meeting')
def add_meeting_page():
    return render_template('add_meeting.html')

@app.route('/update_event/<int:event_id>', methods=['POST'])
def update_event(event_id):
    if 'loggedin' in session:
        name = request.form['event_name']
        date = request.form['event_date']
        description = request.form['description']
        location = request.form['location']
        user_id = session['idusers']
        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE events SET event_name=%s, event_date=%s, description=%s, location=%s
            WHERE idevents=%s AND idusers=%s
        ''', (name, date, description, location, event_id, user_id))
        mysql.connection.commit()
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/edit_event', methods=['POST'])
def edit_event():
    print("Редактируем событие...")
    print("Данные:", request.form)
    if 'loggedin' in session:
        event_id = request.form['event_id']
        name = request.form['event_name']
        date = request.form['event_date']
        description = request.form['description']
        location = request.form['location']
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE events SET event_name=%s, event_date=%s, description=%s, location=%s WHERE idevents=%s AND idusers=%s',
                       (name, date, description, location, event_id, session['idusers']))
        mysql.connection.commit()
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/edit_meeting', methods=['POST'])
def edit_meeting_post():
    if 'loggedin' in session:
        meeting_id = request.form['meeting_id']
        name = request.form['meeting_name']
        date = request.form['meeting_date']
        description = request.form['description']
        location = request.form['location']
        print("Редактируем встречу...")
        print(request.form)

        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE meetings
            SET meeting_name = %s, meeting_date = %s, description = %s, location = %s
            WHERE idmeetings = %s AND idusers = %s
        ''', (name, date, description, location, meeting_id, session['idusers']))
        mysql.connection.commit()
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/update_meeting/<int:meeting_id>', methods=['POST'])
def update_meeting(meeting_id):
    if 'loggedin' in session:
        name = request.form['meeting_name']
        date = request.form['meeting_date']
        description = request.form['description']
        location = request.form['location']
        user_id = session['idusers']
        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE meetings SET meeting_name=%s, meeting_date=%s, description=%s, location=%s
            WHERE idmeetings=%s AND idusers=%s
        ''', (name, date, description, location, meeting_id, user_id))
        mysql.connection.commit()
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM events WHERE idevents = %s AND idusers = %s', (event_id, session['idusers']))
        mysql.connection.commit()
        return '', 204  # Успешно, без контента
    return redirect(url_for('login'))

@app.route('/delete_meeting/<int:meeting_id>', methods=['POST'])
def delete_meeting(meeting_id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM meetings WHERE idmeetings = %s AND idusers = %s', (meeting_id, session['idusers']))
        mysql.connection.commit()
        return '', 204
    return redirect(url_for('login'))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route('/send_email', methods=['POST'])
def send_email():
    if 'loggedin' in session:
        subject = request.form['subject']
        message = request.form['message']
        recipient = request.form['recipient']


        smtp_server = "smtp.mail.ru"
        smtp_port = 25
        smtp_user = "emailformycalendar@mail.ru"
        smtp_password = "4eKhbUr7Lh2Zg1ujz6B9"

        # Формируем письмо
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        try:
            # Отправка письма через SMTP сервер Mail.ru
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Включаем шифрование
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, recipient, text)
            server.quit()

            flash('Письмо успешно отправлено!', 'success')
        except Exception as e:
            flash(f'Ошибка при отправке письма: {e}', 'danger')
            print(f'Ошибка при отправке письма: {e}')

    return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('idusers', None)
    session.pop('login', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
