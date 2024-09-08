from flask import Flask, request, render_template, redirect, url_for
import os
import pandas as pd  # For data processing
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd  # For data processing
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import sys
import socket
import locale
from datetime import datetime
import logging

os.environ['PYTHONIOENCODING'] = 'utf-8'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
print(f"System default encoding: {sys.getdefaultencoding()}")
print(f"Preferred encoding: {locale.getpreferredencoding(False)}")

try:
    hostname, aliases, ipaddrs = socket.gethostbyaddr('127.0.0.1')
    print(f"Hostname: {hostname}")
except Exception as e:
    print(f"Error resolving hostname: {e}")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}

app.config['JSON_AS_ASCII'] = False  # Для JSON в UTF-8
app.config['SECRET_KEY'] = '28bd221a82eb653d12fb8b92ad18d19a'  # Замените на ваш секретный ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///G:/hack-зарплаты/instance/yourdatabase.db'
# Ensure the upload folder exists


# Инициализация базы данных и менеджера сессий
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar_url = db.Column(db.String(300))  # Добавьте это поле для URL аватара
    uploads = db.relationship('Upload', backref='user', lazy=True)


# Модель для загруженных документов
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)   

# Форма для входа
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

# Форма для регистрации
class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6, max=150)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

@app.route('/profile')
@login_required
def profile():
    user_uploads = Upload.query.filter_by(user_id=current_user.id).all()
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")  # Текущее время для обновления URL
    return render_template('profile.html', uploads=user_uploads, user=current_user, current_time=current_time)
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Проверка, существует ли пользователь с таким именем
            if User.query.filter_by(username=form.username.data).first():
                flash('Пользователь с таким именем уже существует.', 'danger')
                return render_template('register.html', form=form)

            # Хэширование пароля с использованием корректного метода
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

            # Создание нового пользователя
            new_user = User(username=form.username.data, password=hashed_password)

            # Добавление пользователя в базу данных
            db.session.add(new_user)
            db.session.commit()

            flash('Аккаунт создан, можете войти в систему', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            # Логирование ошибки и отображение сообщения пользователю
            logging.exception("Ошибка при регистрации пользователя")
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.', 'danger')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def allowed_image(filename):
    allowed_image_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_image_extensions


@app.route('/')
def index():
    return render_template('index.html')  # Render your HTML file here

# Маршрут для загрузки файлов
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('Нет файла для загрузки')
        return redirect(url_for('profile'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Файл не выбран')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Добавьте код для сохранения информации о загрузке в базу данных
        new_upload = Upload(filename=filename, filepath=filepath, user_id=current_user.id)
        db.session.add(new_upload)
        db.session.commit()
        
        flash('Документ успешно загружен')
        return redirect(url_for('profile'))

    flash('Неверный тип файла. Разрешены только PDF, DOC, и DOCX.')
    return redirect(url_for('profile'))



@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Нет файла для загрузки', 'error')
        return redirect(url_for('profile'))

    file = request.files['avatar']

    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('profile'))

    # Проверяем, разрешен ли тип файла (например, jpg, png)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Путь для сохранения аватара в папку static/avatars
        avatar_path = os.path.join('static', 'avatars', filename)
        file.save(avatar_path)

        # Сохраняем относительный путь к аватару
        current_user.avatar_url = f'avatars/{filename}'
        db.session.commit()

        flash('Аватар успешно загружен', 'success')
        return redirect(url_for('profile'))

    flash('Неверный тип файла. Разрешены только изображения.', 'error')
    return redirect(url_for('profile'))




def process_file(filepath):
    # Example processing: Log the file path (expand with actual processing as needed)
    print(f'Processing file: {filepath}')
    # Example: If working with CSV, load into DataFrame
    # if filepath.endswith('.csv'):
    #     df = pd.read_csv(filepath)
    #     # Perform processing with DataFrame
    #     print(df.head())


@app.route('/about')
def about():
    return render_template('about.html')  # Используйте имя файла, который содержит HTML код страницы "О проекте"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
    #app.run(debug=True)





    ####ssh -R 80:localhost:8080 serveo.net
