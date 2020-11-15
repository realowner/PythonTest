from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from bs4 import BeautifulSoup
import csv
import json
import xml.etree.ElementTree as ET


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

url = 'http://127.0.0.1:5000/db/id=1'
url_count = 'http://127.0.0.1:5000/db'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
               'accept': '*/*'}


####################################PARSER###########################################
def get_html(url, params=None):
    req = requests.get(url, headers=headers, params=params)
    return req


def get_pg_count(html_c):
    soup = BeautifulSoup(html_c, 'html.parser')
    pages = soup.find_all('td', class_='user-id')
    if pages:
        return int(pages[-1].get_text())
    else:
        return 1


def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='user-info-div')

    info = []
    for i in items:
        info.append({
            'id': i.find('li', class_='user-info-detail-id').get_text(),
            'name': i.find('li', class_='user-info-name').get_text(),
            'surname': i.find('li', class_='user-info-surname').get_text(),
            'mail': i.find('li', class_='user-info-detail-mail').get_text(),
            'password': i.find('li', class_='user-info-detail-password').get_text(),
            'ph_number': i.find('li', class_='user-info-detail-number').get_text(),
            'date': i.find('li', class_='user-info-detail-date').get_text(),
        })
    return info


def save(items, path_csv, path_json, path_xml):
    try:
        with open(path_csv, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'name', 'surname', 'mail', 'password', 'ph_number', 'date'])
            for item in items:
                writer.writerow([item['id'], item['name'], item['surname'], item['mail'], item['password'], item['ph_number'], item['date']])
            print("CSV success")
    except:
        print("CSV fail")

    try:
        with open(path_json, 'w') as file:
            json.dump(items, file, indent=2)
        print("JSON success")
    except:
        print("JSON fail")

    try:
        root = ET.Element('root')
        for item in items:
            user = ET.SubElement(root, 'user')
            ET.SubElement(user, 'id').text = item['id']
            ET.SubElement(user, 'name').text = item['name']
            ET.SubElement(user, 'surname').text = item['surname']
            ET.SubElement(user, 'mail').text = item['mail']
            ET.SubElement(user, 'password').text = item['password']
            ET.SubElement(user, 'ph_number').text = item['ph_number']
            ET.SubElement(user, 'date').text = item['date']

        tree = ET.ElementTree(root)
        tree.write(path_xml)
        print("XML success")
    except:
        print("XML fail")


def parse():
    html = get_html(url)
    html_c = get_html(url_count)
    if html.status_code == 200:
        all_info = []
        pg_count = get_pg_count(html_c.text)
        for p in range(1, pg_count+1):
            print(f'Прогресс {p}/{pg_count}')
            html = get_html(f'http://127.0.0.1:5000/db/id={p}')
            all_info.extend(get_content(html.text))
        print(all_info)
        save(all_info, 'db.csv', 'db.json', 'db.xml')
        return "SUCCESS"
    else:
        return "ERROR"
#####################################################################################


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    mail = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    ph_number = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return 'User %r' % self.id


@app.route('/', methods=["POST", "GET"])
def login_page():
    if request.method == "POST":
        return redirect('/homepage')
    else:
        return render_template("login.html")


@app.route('/homepage')
def index():
    return render_template("index.html")


@app.route('/register_page', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        name = request.form['user-name']
        surname = request.form['user-surname']
        mail = request.form['user-mail']
        password = request.form['user-pass']
        ph_number = request.form['user-ph']
        p_hash = generate_password_hash(password)
        userBD = User(name=name, surname=surname, mail=mail, password=p_hash, ph_number=ph_number)

        try:
            db.session.add(userBD)
            db.session.commit()
            return redirect('/')
        except:
            return "ERROR"
    else:
        return render_template("register_page.html")


@app.route('/db')
def db_view():
    users = User.query.order_by(User.date).all()
    return render_template("db.html", users=users)


@app.route('/db/id=<int:id>')
def db_view_detail(id):
    users_details = User.query.get(id)
    return render_template("db_detail.html", users_details=users_details)


@app.route('/db/id=<int:id>/del')
def user_del(id):
    users_details = User.query.get_or_404(id)
    try:
        db.session.delete(users_details)
        db.session.commit()
        return redirect('/db')
    except:
        return "ERROR"


@app.route('/db/export')
def ex_json():
    parse()
    json_file = open('db.json')
    json_file_read = json_file.read()
    json_file.close()
    csv_file = open('db.csv')
    csv_file_read = csv_file.read()
    csv_file.close()
    xml_file = open('db.xml')
    xml_file_read = xml_file.read()
    xml_file.close()
    return render_template("export.html", json_file_read=json_file_read, csv_file_read=csv_file_read, xml_file_read=xml_file_read)

@app.route('/fibonacci', methods=['POST', 'GET'])
def fib_page():
    if request.method == "POST":
        n = int(request.form['fibonacci-num'])
        num_1 = 0
        num_2 = 1
        i = 0
        try:
            while i < n - 1:
                num_sum = num_1 + num_2
                num_1 = num_2
                num_2 = num_sum
                i = i + 1

            number = str(num_2)
            return render_template("fibonacci.html", number=number)
        except:
            return "ERROR"

    else:
        return render_template("fibonacci.html")


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
