from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
from datetime import datetime
from lp import *
from flask import jsonify
import re

app = Flask(__name__)
app.secret_key = 'tere_kole'  # Zmeňte to na náhodný tajný kľúč

# Definujte pozície
positions = [('sestra', 'Sestra'), ('prakticka_sestra', 'Praktická sestra'), ('osetrovatel', 'Ošetrovateľ'), ('lekar', 'Lekár')]

column_mapping = {
    ('lekar', 'Obe'): 'lekari',
    ('osetrovatel', 'Oddelenie'): 'oset_odd',
    ('prakticka_sestra', 'Oddelenie'): 'prak_sestry_odd',
    ('osetrovatel', 'JIS'): 'oset_JIS',
    ('prakticka_sestra', 'JIS'): 'prak_sestry_JIS',
    ('sestra', 'Oddelenie'): 'sestry_odd',
    ('sestra', 'JIS'): 'sestry_JIS',
}
# Pripojenie k databáze SQLite a vytvorenie tabuľky users, ak neexistuje
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Použite generate_password_hash na zahashovanie hesla
hashed_password_admin = generate_password_hash('admin', method='pbkdf2:sha256')

# Skontrolujte, či užívateľ admin už existuje
cursor.execute("SELECT * FROM users WHERE email = 'admin@example.com'")
existing_admin = cursor.fetchone()
# print(existing_admin)


# Ak užívateľ admin neexistuje, vložte ho do databázy
if not existing_admin:
    cursor.execute('''
        INSERT INTO users (
            first_name, last_name, email, password, position,
            address, mobile, birthdate, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Admin', 'Admin', 'admin@example.com', hashed_password_admin, 'admin',
        'Admin Address', '123456789', '2000-01-01', 'prijatý'
    ))

# for i in [14,15]:
#     i = str(i+1)
#     # is_cer = random.choice(['Atestvaný', 'Neatestovaný'])
#     hashed_password = generate_password_hash('prasestra' + i, method='pbkdf2:sha256')
#     cursor.execute('''
#         INSERT INTO users (
#             first_name, last_name, email, password, max_hours, min_hours, position,
#                 address, mobile, birthdate, workplace, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     ''', (
#         'PraSestra' + i, 'PraSestra' + i, 'prasestra'+i+'@example.com', hashed_password, 180, 40, 'prakticka_sestra',
#         'Address 123', '123456789', '1984-02-02', 'JIS', 'prijatý'
#     ))

# cursor.execute("INSERT INTO prefer (user_id, day, shift_type) VALUES (?, ?, ?)",
#                         (8, 11, 'Nočná'))

# # Get the current timestamp
# current_timestamp = datetime.now()

#     # Convert the timestamp to a string in the format 'YYYY-MM-DD HH:MM:SS'
# current_timestamp_str = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')

#     # Execute the INSERT statement with the current timestamp
# cursor.execute("INSERT INTO submissions (user_id, submission_date) VALUES (?, ?)", (8, current_timestamp_str))


# for i in [24,25,26,27,28,29]:
#     # random_numbers = random.sample(range(1, 32), 10)
#     # for j in random_numbers[:5]:
#     #     shift = random.choice(['Nočná', 'Denná', 'Obe'])
#     #     reason = random.choice(['Slabý', 'Silný', 'Stredný'])
#     #     cursor.execute("INSERT INTO prefer (user_id, day, shift_type) VALUES (?, ?, ?)",
#     #                     (i, j, shift))
#     # for k in random_numbers[5:]:
#     cursor.execute("INSERT INTO non_prefer (user_id, day, shift_type, reason_strength) VALUES (?, ?, ?, ?)",
#                     (i, 12, 'Denná', 'Silný'))

#     # Get the current timestamp
#     current_timestamp = datetime.now()

#     # Convert the timestamp to a string in the format 'YYYY-MM-DD HH:MM:SS'
#     current_timestamp_str = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')

#     # Execute the INSERT statement with the current timestamp
#     cursor.execute("INSERT INTO submissions (user_id, submission_date) VALUES (?, ?)", (i, current_timestamp_str))

conn.commit()
conn.close()

def login_required(func):
    """
    Dekorátor na zabezpečenie toho, aby sa k route dostali len prihlásení používatelia.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Musíte sa najprv prihlásiť.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function

def admin_required(func):
    """
    Dekorátor na zabezpečenie toho, aby sa k route dostali len administrátori.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') != 1:  # Predpokladáme, že ID admina je 1
            flash('Nemáte oprávnenie pristupovať k tejto stránke.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function


# prihlasovanie
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        # presmerováva na adminovu stránku, inak na stránku zamestnanca
        if user_id == 1:  # Predpokladáme, že ID admina je 1
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('employee'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (username,))
            user = cursor.fetchone()
            # print(user)
            conn.close()

            if user and check_password_hash(user[4], password) and user[-1] == 'prijatý':  # Skontrolujte zahashované heslo a potvrdenie registracie
                session['user_id'] = user[0]  # Uložte ID užívateľa do session
                flash('Boli ste úspešne prihlásený.', 'success')
                # Presmerovanie po úspešnom prihlásení
                return redirect(url_for('index'))

            flash('Nesprávna e-mailová adresa alebo heslo', 'error')

        except Exception as e:
            flash('Pri načítavaní údajov z databázy sa vyskytla chyba.', 'error')
            print(f"Chyba: {e}")

    return render_template('index.html')

@app.route('/submit_preferences', methods=['POST'])
@login_required
def submit_preferences():
    user_id = session.get('user_id')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    selected_info = request.form.get('selectedInfoData')
    selected_info = selected_info.split('<br>')

    # Uloženie preferencií do databázy
    for line in selected_info[:-1]:
        line = line.split(', ')
        if line[1] == "Preferovaný":
            cursor.execute("INSERT INTO prefer (user_id, day, shift_type) VALUES (?, ?, ?)",
                            (user_id, line[0], line[2]))
        else:
            cursor.execute("INSERT INTO non_prefer (user_id, day, shift_type, reason_strength) VALUES (?, ?, ?, ?)",
                            (user_id, line[0], line[2], line[3]))

    # Get the current timestamp
    current_timestamp = datetime.now()

    # Convert the timestamp to a string in the format 'YYYY-MM-DD HH:MM:SS'
    current_timestamp_str = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    # Execute the INSERT statement with the current timestamp
    cursor.execute("INSERT INTO submissions (user_id, submission_date) VALUES (?, ?)", (user_id, current_timestamp_str))
    
    conn.commit()
    conn.close()

    # Návrat na hlavnú stránku s flash správou
    flash('Vaše preferencie boli úspešne odoslané.', 'success')
    return redirect(url_for('index'))

@app.route('/schedule', methods=['GET'])
@login_required
def schedule():
    user_id = session.get('user_id')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    history = request.args.get('history')

    if user_id == 1:
        position = request.args.get('position')
        if history == 'history':
            cursor.execute("SELECT MAX(month_year) FROM schedules")
            month_year = cursor.fetchone()[0]
            cursor.execute("SELECT {} FROM schedules WHERE month_year != ?".format(position), (month_year,))
            results = cursor.fetchall()
            vypisy = "\n".join(row[0] for row in results)
            conn.close()
            return render_template('schedule.html', vypis=vypisy, history=history)

        month = request.args.get('month')
        current_year = datetime.now().year
        current_month = datetime.now().month
        if month == 'next':
            if current_month == 12:
                next_year = current_year + 1
                next_month = 1
            else:
                next_year = current_year
                next_month = current_month + 1
            month_year = next_year * 100 + next_month
        else:
            month_year = current_year * 100 + current_month
        cursor.execute("SELECT {} FROM schedules WHERE month_year = ?".format(position), (month_year,))
        vypis = cursor.fetchone()
        if vypis:
            vypis = vypis[0]
            conn.close()
            generate = ''
        else:
            vypis = '<h3 style="text-align: center;">Rozvrh ešte nie je vygenerovaný</h3>'
            generate = 'generate'
        return render_template('schedule.html', vypis=vypis, position=position, month_year=month_year, generate=generate)

    cursor.execute("SELECT MAX(month_year) FROM schedules")
    month_year = cursor.fetchone()[0]

    cursor.execute("SELECT position, workplace FROM users WHERE id = ?", (user_id,))
    pos_wor = cursor.fetchone()
    position = pos_wor[0]
    workplace = pos_wor[1]

    column = column_mapping.get((position, workplace))

    if history == 'history':
        cursor.execute("SELECT {} FROM schedules WHERE month_year != ? ORDER BY month_year DESC".format(column), (month_year,))
        results = cursor.fetchall()
        vypisy = "\n".join(row[0] for row in results)
        conn.close()
        return render_template('schedule.html', vypis=vypisy)

    cursor.execute("SELECT {} FROM schedules WHERE month_year = ?".format(column), (month_year,))
    vypis = cursor.fetchone()[0]
    conn.close()

    return render_template('schedule.html', vypis=vypis)

def get_shift_info(month_year, column_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT {column_name} FROM schedules WHERE month_year = ?"
    cursor.execute(query, (month_year,))
    html_string = cursor.fetchone()[0]
    matches = re.findall(r"<td>(\d{2}.\d{2}.\d{4})</td><td>(.*?)</td><td>(.*?)</td>", html_string)
    last_date, last_night_shift = matches[-1][0], matches[-1][2]
    last_month = last_night_shift.split(", ")
    return last_month

def generate_schedule():
    current_date = datetime.now()
    
    if 20 <= current_date.day <= 31 and not is_schedule_generated():
        current_year = datetime.now().year
        current_month = datetime.now().month
        month_year = current_year * 100 + current_month
        if current_month == 12:
            next_year = current_year + 1  # Ak sme v decembri, nasledujúci mesiac bude v nasledujúcom roku
            next_month = 1  # Nasledujúci mesiac za decembrom je január
        else:
            next_year = current_year
            next_month = current_month + 1
        next_month_year = next_year * 100 + next_month  # Kombinujeme rok a mesiac do jedného čísla

        vypisy = []

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT lekari FROM schedules WHERE month_year = ?", (month_year,))
        html_string = cursor.fetchone()[0]
        matches = re.findall(r"<td>(\d{2}.\d{2}.\d{4})</td><td>(.*?)</td><td>(.*?)</td>", html_string)
        last_date, last_night_shift = matches[-1][0], matches[-1][2]
        last_month = last_night_shift.split(", ")
        pocet_na_sluzbe = [2, 2, 2, 2]

        cursor.execute("SELECT first_name, last_name FROM users WHERE position = ? AND is_certified = ? AND status = ?",
            ('lekar', 'Neatestovaný', 'prijatý'))
        uncertified_doctors_sql = cursor.fetchall()
        uncertified_doctors = [f"{first} {last}" for first, last in uncertified_doctors_sql]

        cursor.execute("SELECT first_name, last_name FROM users WHERE position = ? AND work_at_night = ? AND status = ?",
            ('lekar', 'Nie', 'prijatý'))
        not_workatnight_sql = cursor.fetchall()
        not_workatnight = [f"{first} {last}" for first, last in not_workatnight_sql]

        cursor.execute("SELECT first_name, last_name, max_hours, min_hours FROM users WHERE position = ? AND status = ?",
                    ('lekar', 'prijatý'))
        name_shifts_sql = cursor.fetchall()
        random.shuffle(name_shifts_sql)
        employees = [f"{first} {last}" for first, last, shifts_max, shifts_min in name_shifts_sql]
        num_of_min_shifts = [int(shifts_min)//12 for first, last, shifts_max, shifts_min in name_shifts_sql]
        num_of_max_shifts = [int(shifts_max)//12 for first, last, shifts_max, shifts_min in name_shifts_sql]

        cursor.execute("SELECT first_name, last_name, day, shift_type FROM prefer p LEFT JOIN users u ON p.user_id = u.id AND position = ?", ('lekar',))
        prefer_sql = cursor.fetchall()
        employee_preferences = {}

        for first_name, last_name, day, shift_type in prefer_sql:
            name = f"{first_name} {last_name}"
            if name not in employee_preferences:
                employee_preferences[name] = {}
            employee_preferences[name][day] = shift_type.strip()

        cursor.execute("SELECT first_name, last_name, day, shift_type, reason_strength FROM non_prefer np LEFT JOIN users u ON np.user_id = u.id AND position = ?", ('lekar',))
        non_prefer_sql = cursor.fetchall()
        employee_nonpreferences = {}

        for first_name, last_name, day, shift_type, reason_strength in non_prefer_sql:
            name = f"{first_name} {last_name}"
            if name not in employee_nonpreferences:
                employee_nonpreferences[name] = {}
            employee_nonpreferences[name][day] = {"strength": reason_strength.strip(), "shift": shift_type.strip()}

        vypis = vypis_rozvrhu('lekar', employees, num_of_max_shifts, num_of_min_shifts, last_month, employee_preferences, employee_nonpreferences, pocet_na_sluzbe, not_workatnight, uncertified_doctors)
        vypisy.append(vypis)

        for position, position_name in positions[:-1]:
            for workplace in ["JIS", "Oddelenie"]:
                if workplace == 'Oddelenie':
                    if position == 'osetrovatel':
                        last_month, pocet_na_sluzbe = get_shift_info(month_year, 'oset_odd'), [2, 1, 1, 1]
                    elif position == 'prakticka_sestra':
                        last_month, pocet_na_sluzbe = get_shift_info(month_year, 'prak_sestry_odd'), [3, 1, 2, 1]
                    elif position == 'sestra':
                        last_month, pocet_na_sluzbe = get_shift_info(month_year, 'sestry_odd'), [3, 2, 2, 2]
                elif workplace == 'JIS':
                    if position == 'osetrovatel':
                        last_month, pocet_na_sluzbe = get_shift_info(month_year, 'oset_JIS'), [2, 1, 1, 1]
                    elif position == 'prakticka_sestra':
                        last_month, pocet_na_sluzbe = get_shift_info(month_year, 'prak_sestry_JIS'), [2, 1, 2, 1]
                    elif position == 'sestra':
                        last_month, pocet_na_sluzbe = get_shift_info(month_year, 'sestry_JIS'), [4, 3, 4, 3]
                cursor.execute("SELECT first_name, last_name, max_hours, min_hours FROM users WHERE position = ? AND workplace = ? AND status = ?",
                        (position, workplace, 'prijatý'))
                name_shifts_sql = cursor.fetchall()
                random.shuffle(name_shifts_sql)
                employees = [f"{first} {last}" for first, last, shifts_max, shifts_min in name_shifts_sql]
                num_of_min_shifts = [int(shifts_min)//12 for first, last, shifts_max, shifts_min in name_shifts_sql]
                num_of_max_shifts = [int(shifts_max)//12 for first, last, shifts_max, shifts_min in name_shifts_sql]
                
                cursor.execute("SELECT first_name, last_name FROM users WHERE position = ? AND workplace = ? AND work_at_night = ? AND status = ?",
                    (position, workplace, 'Nie', 'prijatý'))
                not_workatnight_sql = cursor.fetchall()
                not_workatnight = [f"{first} {last}" for first, last in not_workatnight_sql]

                cursor.execute("SELECT first_name, last_name, day, shift_type FROM prefer p LEFT JOIN users u ON p.user_id = u.id AND position = ?", (position,))
                prefer_sql = cursor.fetchall()
                employee_preferences = {}

                for first_name, last_name, day, shift_type in prefer_sql:
                    name = f"{first_name} {last_name}"
                    if name not in employee_preferences:
                        employee_preferences[name] = {}
                    employee_preferences[name][day] = shift_type.strip()

                cursor.execute("SELECT first_name, last_name, day, shift_type, reason_strength FROM non_prefer np LEFT JOIN users u ON np.user_id = u.id AND position = ?", (position,))
                non_prefer_sql = cursor.fetchall()
                employee_nonpreferences = {}

                for first_name, last_name, day, shift_type, reason_strength in non_prefer_sql:
                    name = f"{first_name} {last_name}"
                    if name not in employee_nonpreferences:
                        employee_nonpreferences[name] = {}
                    employee_nonpreferences[name][day] = {"strength": reason_strength.strip(), "shift": shift_type.strip()}

                vypis = vypis_rozvrhu(position, employees, num_of_max_shifts, num_of_min_shifts, last_month, employee_preferences, employee_nonpreferences, pocet_na_sluzbe, not_workatnight)
                vypisy.append(vypis)

        # print(vypisy)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedules (
                month_year, lekari, sestry_JIS, sestry_odd, prak_sestry_JIS, prak_sestry_odd, oset_JIS, oset_odd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (next_month_year, vypisy[0], vypisy[1], vypisy[2], vypisy[3], vypisy[4], vypisy[5], vypisy[6]))

        # Odstránenie existujúcich kópií tabuliek non_prefer_old a prefer_old
        cursor.execute("DROP TABLE IF EXISTS non_prefer_old")
        cursor.execute("DROP TABLE IF EXISTS prefer_old")

        # Vytvorenie kópie tabuľky non_prefer
        cursor.execute("""
            CREATE TABLE non_prefer_old AS
            SELECT * FROM non_prefer
        """)

        # Vytvorenie kópie tabuľky prefer
        cursor.execute("""
            CREATE TABLE prefer_old AS
            SELECT * FROM prefer
        """)

        # Vyčistenie obsahu tabuliek prefer a non_prefer
        cursor.execute("DELETE FROM non_prefer")
        cursor.execute("DELETE FROM prefer")

        conn.commit()
        conn.close()

        # return render_template('schedule.html', vypis=vypis)
        print("Generovanie rozvrhu pre lekárov, sestry, ošetrovateľov a praktické sestry.")

def is_schedule_generated():
    current_year = datetime.now().year
    current_month = datetime.now().month
    if current_month == 12:
        next_month_year = current_year + 1  # Ak sme v decembri, nasledujúci mesiac bude v nasledujúcom roku
        next_month = 1  # Nasledujúci mesiac za decembrom je január
    else:
        next_month_year = current_year
        next_month = current_month + 1
    month_year = next_month_year * 100 + next_month  # Kombinujeme rok a mesiac do jedného čísla

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE month_year = ?", (month_year,))
    schedule = cursor.fetchone()
    conn.close()

    if schedule:
        return True
    else:
        return False

# Tento kód by sa mohol nachádzať v route, ktorý spracúva požiadavky od administrátora
@app.route('/generate_schedule', methods=['POST'])
@login_required
@admin_required
def trigger_generate_schedule():
    generate_schedule()
    return redirect(url_for('admin'))

@app.route('/save_changes', methods=['POST'])
def save_changes():
    data = request.json
    position = str(data.get('position'))
    edited_data = str(data.get('html')) 
    month_year = str(data.get('month_year'))

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("UPDATE schedules SET {} = ? WHERE month_year = ?".format(position), (edited_data, month_year))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Zmeny boli úspešne uložené"})



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Získanie údajov z formulára
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        address = request.form['address']
        mobile = request.form['mobile']
        birth_date = request.form['birth_date']
        position = request.form['position']
        workplace = request.form['workplace']
        workatnight = request.form['workatnight']
        max_hours = request.form['max_hours']
        min_hours = request.form['min_hours']

        if position != 'lekar':
            certified = None
        else:
            certified = request.form['certification']

        # Prevod birth_date na dátum vo formáte YYYY-MM-DD
        birthdate = birth_date  # Predpokladáme, že deň a mesiac nie sú k dispozícii

        # Kontrola zhody hesiel
        if password != confirm_password:
            flash('Heslá sa nezhodujú. Skúste to znova.', 'error')
            return redirect(url_for('register'))

        # Zahashovanie hesla pred uložením
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Pridanie zamestnanca do databázy
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (
                first_name, last_name, email, password, max_hours, min_hours, position, is_certified,
                address, mobile, birthdate, workplace, work_at_night, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            first_name, last_name, email, hashed_password, max_hours, min_hours, position, certified,
            address, mobile, birthdate, workplace, workatnight, 'čakajúci'
        ))

        conn.commit()
        conn.close()

        flash('Žiadosť o registráciu bola odoslaná. Počkajte na potvrdenie administrátora.', 'success')

        return redirect(url_for('index'))

    return render_template('register.html', positions=positions)

@app.route('/admin')
@login_required
@admin_required
def admin():
    # Načítanie údajov o používateľoch z databázy
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id != 1")
    employees = cursor.fetchall()
    conn.close()

    # Načítanie flash správ
    message = None
    if 'message' in request.args:
        message = request.args['message']

    # Zobrazenie adminovho dashboardu s údajmi o používateľoch a flash správou
    return render_template('admin.html', employees=employees, message=message)

@app.route('/employee')
@login_required
def employee():
    user_id = session.get('user_id')
    if user_id == 1:  # Predpokladáme, že ID admina je 1
        flash('Nemáte oprávnenie pristupovať k tejto stránke.', 'error')
        return redirect(url_for('index'))

    user_id = session.get('user_id')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Získanie aktuálneho mesiaca a roka
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Kontrola, či už boli preferencie odoslané pre aktuálny mesiac
    cursor.execute("SELECT MAX(submission_date) FROM submissions WHERE user_id = ?", (user_id,))
    last_submission_date_str = cursor.fetchone()[0]
    if last_submission_date_str:
        last_submission_date = datetime.strptime(last_submission_date_str, '%Y-%m-%d %H:%M:%S')
    else:
        last_submission_date = None
    preferences_submitted = last_submission_date and last_submission_date.month == current_month and last_submission_date.year == current_year


    # Render the template with the preferences_submitted variable
    return render_template('employee.html', preferences_submitted=preferences_submitted)

@app.route('/choose_schedule', methods=['GET', 'POST'])
@login_required
@admin_required
def choose_schedule():
    return render_template('choose_schedule.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    # Odstránenie všetkých údajov zo session
    session.clear()
    flash('Boli ste odhlásený.', 'success')
    return redirect(url_for('index'))

@app.route('/change_status/<int:user_id>', methods=['POST'])
@login_required
def change_status(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    try:
        new_status = request.form['status']
        
        if new_status == 'zamietnuty':
            # Ak je vybratá možnosť "Zamietnuť", vymažte používateľa z databázy
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            flash('Používateľ bol úspešne zamietnutý a vymazaný.', 'success')
        else:
            # Inak aktualizujte status na základe vybranej možnosti
            cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
            flash(f'Status bol úspešne aktualizovaný na "{new_status}".', 'success')

        conn.commit()
    except Exception as e:
        flash('Pri aktualizácii statusu sa vyskytla chyba.', 'error')
        print(f"Chyba: {e}")
    finally:
        conn.close()

    return redirect(url_for('admin'))


@app.after_request
def add_header(response):
    """
    Pridá hlavičku, ktorá zakazuje ukladanie do medzipamäti a cache.
    """
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)