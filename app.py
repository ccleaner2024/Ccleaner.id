import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from pymongo import MongoClient
import requests
import jwt
import hashlib
from bson import ObjectId
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os

# database mongodb
dotenv_path = join(dirname(__file__),'.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "SPARTA"

@app.route("/", methods=["GET"])
def home():
    galeri_data = list(db.update_data.find({}))
    return render_template('index.html', galeri_data=galeri_data)

@app.route("/shop")
def shopProduct():
    return render_template("shop.html")

@app.route("/contactus")
def contactUs():
    return render_template("contact.html")

@app.route("/feedback", methods=["GET"])
def show_feedback():
    content = list(db.feedback.find({}, {'_id': False}))
    return jsonify({'content': content})

@app.route("/feedback", methods=["POST"])
def save_feedback():
    name_receive = request.form.get('name')
    email_receive = request.form.get('email')
    number_receive = request.form.get('number')
    subject_receive = request.form.get('subject')
    message_receive = request.form.get('message')  
    doc = {
        'name': name_receive,
        'email': email_receive,
        'number': number_receive,
        'subject': subject_receive,
        'message': message_receive,
    }
    db.feedback.insert_one(doc)
    return jsonify({'msg': 'Pesan berhasil terkirim !'})


@app.route("/faq")
def faq():
    return render_template("faq.html")   

@app.route("/cek")
def cekSelengkapnya():
    return render_template("cek.html")

# login & signup ######

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if db.users.find_one({'email': email}):
            return 'User already exists!'

        db.users.insert_one({'name': name, 'email': email,
                            'password': hashed_password})
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = db.users.find_one({'email': email, 'password': hashed_password})
        if user:
            token = jwt.encode({'email': email, 'name': user['name'], 'exp': datetime.utcnow(
            ) + timedelta(minutes=30)}, app.config["SECRET_KEY"], algorithm="HS256")
            return redirect(url_for('dashboard', token=token))
        else:
            return 'Invalid username/password'

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    token = request.args.get('token')
    try:
        decoded_token = jwt.decode(
            token, app.config["SECRET_KEY"], algorithms=["HS256"])
        email = decoded_token['email']
        name = decoded_token['name']

        feedback_data = list(db.feedback.find({}))

        return render_template('dashboard.html', email=email, name=name, feedback_data=feedback_data)
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'
    
@app.route('/delete_feedback/<id>', methods=['POST'])
def delete_feedback(id):
    db.feedback.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('update_page'))
    
# Add & Update #####
@app.route('/update', methods=['GET', 'POST'])
def update_page():
    if request.method == 'POST':
        # Ambil semua data dari formulir
        nama = request.form['nama']
        nama_paket = request.form['paket']
        deskripsi = request.form['deskripsi']
        gambar1 = request.files['gambar1']
        gambar2 = request.files['gambar2']
        
        nama_file_gambar1 = None
        nama_file_gambar2 = None

        # Direktori tempat menyimpan gambar
        img_dir = 'static/assets/update_img/'

        # Buat direktori jika belum ada
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        # Jika ada gambar yang diunggah, proses dan simpan gambar tersebut
        if gambar1:
            nama_file_asli1 = gambar1.filename
            nama_file_gambar1 = nama_file_asli1.split('/')[-1]
            file_path1 = os.path.join(img_dir, nama_file_gambar1)
            gambar1.save(file_path1)

        if gambar2:
            nama_file_asli2 = gambar2.filename
            nama_file_gambar2 = nama_file_asli2.split('/')[-1]
            file_path2 = os.path.join(img_dir, nama_file_gambar2)
            gambar2.save(file_path2)

        # Buat dokumen untuk disimpan ke database
        doc = {
            'nama': nama,
            'nama_paket': nama_paket,
            'deskripsi': deskripsi,
            'gambar1': nama_file_gambar1,
            'gambar2': nama_file_gambar2  # Tambahkan gambar2 ke dokumen
        }

        # Simpan dokumen ke koleksi yang sesuai di database
        db.update_data.insert_one(doc)

        # Alihkan pengguna ke halaman yang sesuai
        return redirect(url_for('update_page'))

    galeri_data = db.update_data.find()  # Ambil data dari database untuk ditampilkan
    return render_template('update.html', galeri_data=galeri_data)


@app.route('/delete_update/<id>', methods=['POST'])
def delete_update(id):
    db.update_data.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('update_page'))


@app.route('/edit_update/<id>', methods=['GET', 'POST'])
def edit_update(id):
    if request.method == 'POST':
        # Ambil data dari formulir
        nama = request.form['nama']
        nama_paket = request.form['nama_paket']
        deskripsi = request.form['deskripsi']
        gambar1 = request.files['gambar1']
        gambar2 = request.files['gambar2']
        
        doc = {
            'nama': nama,
            'nama_paket': nama_paket,
            'deskripsi': deskripsi,
        }

        img_dir = 'static/assets/update_img/'
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        # Jika ada gambar baru, simpan dan tambahkan ke dokumen
        if gambar1:
            nama_file_asli1 = gambar1.filename
            nama_file_gambar1 = secure_filename(nama_file_asli1)
            file_path1 = os.path.join(img_dir, nama_file_gambar1)
            gambar1.save(file_path1)
            doc['gambar1'] = nama_file_gambar1

        if gambar2:
            nama_file_asli2 = gambar2.filename
            nama_file_gambar2 = secure_filename(nama_file_asli2)
            file_path2 = os.path.join(img_dir, nama_file_gambar2)
            gambar2.save(file_path2)
            doc['gambar2'] = nama_file_gambar2

        # Update dokumen di database
        db.update_data.update_one({"_id": ObjectId(id)}, {"$set": doc})
        return redirect(url_for('update_page'))

    # Jika permintaan GET, ambil data dari database dan kirimkan ke template
    data = db.update_data.find_one({"_id": ObjectId(id)})
    return render_template('edit_update.html', data=data)



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True) 