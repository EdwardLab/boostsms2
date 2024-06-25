from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import random
import time

app = Flask(__name__)
app.secret_key = 'testkey'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        reason = request.form['reason']
        password = request.form['password']
        sunumber = random.randint(1000000000, 9999999999)

        os.makedirs(f"sms/{sunumber}.user")
        with open(f"sms/{sunumber}.user/loginpassword.txt", "w") as f:
            f.write(password)
        with open(f"sms/{sunumber}.user/msgbox.txt", "w"):
            pass

        return render_template('success.html', sunumber=sunumber)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sunumber = request.form['number']
        password = request.form['password']

        try:
            with open(f"sms/{sunumber}.user/loginpassword.txt", "r") as f:
                stored_password = f.read().strip()
            app.logger.debug(f'Trying to login user {sunumber}')
            if stored_password == password:
                user = User(sunumber)
                login_user(user)
                session['number'] = sunumber
                flash('Logged in successfully.')
                app.logger.debug(f'User {sunumber} logged in successfully.')
                return redirect(url_for('dashboard', sunumber=sunumber))
            else:
                flash('Password Incorrect')
                app.logger.debug('Password Incorrect')
        except FileNotFoundError:
            flash('User not found')
            app.logger.debug('User not found')
    return render_template('login.html')

@app.route('/dashboard/<sunumber>')
@login_required
def dashboard(sunumber):
    if current_user.id != sunumber:
        flash("Unauthorized access")
        app.logger.debug("Unauthorized access")
        return redirect(url_for('login'))
    return render_template('dashboard.html', sunumber=sunumber)

@app.route('/sendsms', methods=['POST'])
@login_required
def sendsms():
    timenow = time.strftime("%m-%d-%Y %H:%M", time.localtime())
    sendto = request.form['sendto']
    number = current_user.id
    content = request.form['content']

    try:
        line_data = sendto.split(',')
        for linedata in line_data:
            with open(f"sms/{linedata}.user/msgbox.txt", "a+") as writesms:
                writesms.write(f"{number}: {content} [{timenow}]\n")
        return render_template('alert.html', text="Message sent successfully")
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/listsms', methods=['GET'])
@login_required
def listsms():
    number = current_user.id

    try:
        with open(f"sms/{number}.user/msgbox.txt", "r") as readsms:
            getsms = readsms.read()
        return jsonify({'code': 200, 'smscontent': getsms})
    except FileNotFoundError:
        return jsonify({'code': 404, 'text': 'User not found'})
    except Exception as e:
        return jsonify({'code': 500, 'text': str(e)})

@app.route('/clearmsg', methods=['POST'])
@login_required
def clearmsg():
    number = current_user.id

    try:
        with open(f"sms/{number}.user/msgbox.txt", "w") as writesms:
            writesms.write("")
        return "Messages cleared successfully"
    except FileNotFoundError:
        return "User not found"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=2294)
