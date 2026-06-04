import flask
import DBworker
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func

# Ensure Flask serves the project's top-level `static` folder (one level above `python/`)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
app = flask.Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'static'))
app.secret_key = 'your-secret-key-change-this'  # Измените на надежный ключ

# Класс для получения данных из БД
class DataManager:
    """Класс для управления данными из базы данных"""
    
    def __init__(self, db_worker):
        """
        Инициализация DataManager
        
        Args:
            db_worker: экземпляр DBworker для работы с БД
        """
        self.db_worker = db_worker
        self.user_getters = DBworker.UserGetters(db_worker)
        self.article_getters = DBworker.ArticleGetters(db_worker)
        self.comment_getters = DBworker.CommentGetters(db_worker)
    
    # ===== Методы для получения данных о пользователях =====
    
    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        return self.user_getters.get_user_by_id(user_id)
    
    def get_user_by_email(self, email):
        """Получить пользователя по email"""
        return self.user_getters.get_user_by_email(email)
    
    # ===== Методы для получения данных об статьях =====
    
    def get_article_by_id(self, article_id):
        """Получить статью по ID"""
        return self.article_getters.get_article_by_id(article_id)
    
    def get_all_articles(self):
        """Получить все статьи"""
        return self.article_getters.get_all_articles()
    
    def get_published_articles(self):
        """Получить все опубликованные статьи"""
        session = self.db_worker.get_session()
        articles = session.query(self.db_worker.article).filter_by(is_published=True).all()
        session.close()
        return articles
    
    def get_articles_by_chart(self, chart_id):
        """Получить все статьи определенной главы"""
        session = self.db_worker.get_session()
        articles = session.query(self.db_worker.article).filter_by(chart_id=chart_id).all()
        session.close()
        return articles
    
    # ===== Методы для получения данных о комментариях =====
    
    def get_comment_by_id(self, comment_id):
        """Получить комментарий по ID"""
        return self.comment_getters.get_comment_by_id(comment_id)
    
    def get_comments_by_article(self, article_id):
        """Получить все комментарии к статье"""
        return self.comment_getters.get_comments_by_article_id(article_id)
    
    # ===== Методы для получения данных о главах =====
    
    def get_chapter_by_id(self, chapter_id):
        """Получить главу по ID"""
        session = self.db_worker.get_session()
        chapter = session.query(self.db_worker.charts).filter_by(id=chapter_id).first()
        session.close()
        return chapter
    
    def get_all_chapters(self):
        """Получить все главы"""
        session = self.db_worker.get_session()
        chapters = session.query(self.db_worker.charts).all()
        session.close()
        return chapters

    # ===== Методы для песочницы и рейтингов =====
    def get_sandbox_articles(self):
        """Получить статьи в песочнице"""
        session = self.db_worker.get_session()
        articles = session.query(self.db_worker.article).filter_by(is_it_in_sandbox=True).all()
        session.close()
        return articles

    def set_article_rating(self, article_id, user_id, score):
        """Добавить или обновить оценку статьи от пользователя"""
        if score is None:
            return {'success': False, 'message': 'Оценка не указана'}
        try:
            score = int(score)
        except Exception:
            return {'success': False, 'message': 'Оценка должна быть числом'}
        if score < 1 or score > 5:
            return {'success': False, 'message': 'Оценка должна быть от 1 до 5'}

        session = self.db_worker.get_session()
        existing = session.query(self.db_worker.Rating).filter_by(article_id=article_id, user_id=user_id).first()
        if existing:
            existing.score = score
        else:
            new_r = self.db_worker.Rating(article_id=article_id, user_id=user_id, score=score)
            session.add(new_r)
        session.commit()

        # Вычисление новой средней оценки
        avg = session.query(func.avg(self.db_worker.Rating.score)).filter_by(article_id=article_id).scalar() or 0
        count = session.query(func.count(self.db_worker.Rating.id)).filter_by(article_id=article_id).scalar() or 0
        session.close()
        return {'success': True, 'average': float(avg), 'count': int(count)}

    def get_article_rating(self, article_id):
        """Получить средний рейтинг и количество оценок для статьи"""
        session = self.db_worker.get_session()
        avg = session.query(func.avg(self.db_worker.Rating.score)).filter_by(article_id=article_id).scalar() or 0
        count = session.query(func.count(self.db_worker.Rating.id)).filter_by(article_id=article_id).scalar() or 0
        session.close()
        return {'average': float(avg), 'count': int(count)}

    def remove_article_rating(self, article_id, user_id):
        """Удалить оценку пользователя для статьи"""
        session = self.db_worker.get_session()
        existing = session.query(self.db_worker.Rating).filter_by(article_id=article_id, user_id=user_id).first()
        if not existing:
            session.close()
            return {'success': False, 'message': 'Оценка не найдена'}
        session.delete(existing)
        session.commit()

        avg = session.query(func.avg(self.db_worker.Rating.score)).filter_by(article_id=article_id).scalar() or 0
        count = session.query(func.count(self.db_worker.Rating.id)).filter_by(article_id=article_id).scalar() or 0
        session.close()
        return {'success': True, 'average': float(avg), 'count': int(count)}


# Класс для управления аутентификацией
class AuthManager:
    """Класс для управления входом и аутентификацией пользователей"""
    
    def __init__(self, db_worker):
        """
        Инициализация AuthManager
        
        Args:
            db_worker: экземпляр DBworker для работы с БД
        """
        self.db_worker = db_worker
        self.user_getters = DBworker.UserGetters(db_worker)
        self.user_setters = DBworker.UserSetters(db_worker)
    
    def register_user(self, name, email, password):
        """
        Регистрация нового пользователя
        
        Args:
            name: имя пользователя
            email: email пользователя
            password: пароль в открытом виде
            
        Returns:
            dict: результат операции
        """
        # Проверка, существует ли пользователь с таким email
        existing_user = self.user_getters.get_user_by_email(email)
        if existing_user:
            return {
                'success': False,
                'message': 'Пользователь с таким email уже зарегистрирован'
            }
        
        try:
            # Хеширование пароля
            hashed_password = generate_password_hash(password)
            
            # Добавление пользователя в БД
            session = self.db_worker.get_session()
            new_user = self.db_worker.User(
                name=name, 
                email=email,
                password_hash=hashed_password
            )
            session.add(new_user)
            session.commit()
            user_id = new_user.id
            session.close()
            
            return {
                'success': True,
                'message': 'Пользователь успешно зарегистрирован',
                'user_id': user_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при регистрации: {str(e)}'
            }
    
    def login_user(self, email, password):
        """
        Вход пользователя в систему
        
        Args:
            email: email пользователя
            password: пароль в открытом виде
            
        Returns:
            dict: результат операции с данными пользователя
        """
        # Получение пользователя по email
        user = self.user_getters.get_user_by_email(email)
        
        if not user:
            return {
                'success': False,
                'message': 'Пользователь не найден'
            }
        
        # Проверка пароля
        if not hasattr(user, 'password_hash') or not check_password_hash(user.password_hash, password):
            return {
                'success': False,
                'message': 'Неверный пароль'
            }
        
        # Успешный вход
        return {
            'success': True,
            'message': 'Вход выполнен успешно',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_author': user.is_author if hasattr(user, 'is_author') else False,
                'is_superadmin': user.is_superadmin if hasattr(user, 'is_superadmin') else False,
                'is_admin': user.is_admin if hasattr(user, 'is_admin') else False
            }
        }

    def approve_article(self, admin_user_id, article_id):
        """Одобрить статью (только для админов)"""
        session = self.db_worker.get_session()
        admin = session.query(self.db_worker.User).filter_by(id=admin_user_id).first()
        if not admin or not (getattr(admin, 'is_admin', False) or getattr(admin, 'is_superadmin', False)):
            session.close()
            return {'success': False, 'message': 'Нет прав для одобрения статьи'}

        article = session.query(self.db_worker.article).filter_by(id=article_id).first()
        if not article:
            session.close()
            return {'success': False, 'message': 'Статья не найдена'}

        article.is_published = True
        article.is_it_in_sandbox = False
        session.commit()
        session.close()
        return {'success': True, 'message': 'Статья одобрена', 'article_id': article_id}
    
    def verify_session(self, user_id):
        """
        Проверка сессии пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: данные пользователя или сообщение об ошибке
        """
        user = self.user_getters.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': 'Пользователь не найден'
            }
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_author': user.is_author if hasattr(user, 'is_author') else False,
                'is_superadmin': user.is_superadmin if hasattr(user, 'is_superadmin') else False,
                'is_admin': user.is_admin if hasattr(user, 'is_admin') else False
            }
        }


db_worker = DBworker.DBworker('sqlite:///flashwiki.db')  # Раскомментируйте и настройте URL БД
DM__ = DataManager(db_worker)
AM__ = AuthManager(db_worker)
AS__ = DBworker.ArticleSetters(db_worker)
TS__ = DBworker.TagSetters(db_worker)
TG__ = DBworker.TagGetters(db_worker)
OG__ = DBworker.OrganizationGetters(db_worker)
OS__ = DBworker.OrganizationSetters(db_worker)

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return flask.send_from_directory(app.static_folder, 'index.html')

@app.route('/api/charts', methods=['GET'])
def all_charts():
    return DM__.get_all_chapters()


@app.route('/api/articles', methods=['GET'])
def all_articles():
    return DM__.get_all_articles()

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def article_by_id(article_id):
    return DM__.get_article_by_id(article_id)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def user_by_id(user_id):
    return DM__.get_user_by_id(user_id)


@app.route('/api/articles/sandbox', methods=['GET'])
def sandbox_articles():
    """Список статей в песочнице (только для админов)"""
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    user_res = AM__.verify_session(user_id)
    if not user_res['success'] or not (user_res['user'].get('is_admin') or user_res['user'].get('is_superadmin')):
        return {'success': False, 'message': 'Нет прав'}, 403
    return DM__.get_sandbox_articles()


@app.route('/api/articles/<int:article_id>/approve', methods=['POST'])
def approve_article_route(article_id):
    """Одобрение статьи админом"""
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    result = AM__.approve_article(user_id, article_id)
    return result, 200 if result.get('success') else 403


@app.route('/api/articles/<int:article_id>/rate', methods=['POST'])
def rate_article(article_id):
    """Поставить оценку статье (от авторизованного пользователя)"""
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    data = flask.request.get_json()
    score = data.get('score') if data else None
    result = DM__.set_article_rating(article_id, user_id, score)
    return result, 200 if result.get('success') else 400


@app.route('/api/articles/<int:article_id>/rating', methods=['GET'])
def article_rating(article_id):
    """Получить рейтинг статьи"""
    return DM__.get_article_rating(article_id)


@app.route('/api/articles/<int:article_id>/rate', methods=['DELETE'])
def remove_article_rating_route(article_id):
    """Удалить свою оценку статьи (только авторизованный пользователь)"""
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    result = DM__.remove_article_rating(article_id, user_id)
    return result, 200 if result.get('success') else 400


@app.route('/api/articles', methods=['POST'])
def create_article():
    """Создание статьи (авторы) — отправляется в песочницу на проверку"""
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    user_res = AM__.verify_session(user_id)
    if not user_res['success'] or not (user_res['user'].get('is_author') or user_res['user'].get('is_admin') or user_res['user'].get('is_superadmin')):
        return {'success': False, 'message': 'Нет прав'}, 403

    data = flask.request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags', [])
    cover_image = data.get('cover_image')
    organization_id = data.get('organization_id')
    chart_id = data.get('chart_id')

    if not title or not content:
        return {'success': False, 'message': 'Отсутствует заголовок или содержание'}, 400

    article_id = AS__.add_article_with_extra(title=title, content=content, mark_with_stars=None,
                                              is_published=False, keywords=None, chart_id=chart_id,
                                              cover_image=cover_image, organization_id=organization_id, tags=tags)

    return {'success': True, 'article_id': article_id}, 201


@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    """Загрузка изображения — сохраняется в static/uploads и возвращается URL"""
    if 'file' not in flask.request.files:
        return {'success': False, 'message': 'Файл не найден в запросе'}, 400
    f = flask.request.files['file']
    if f.filename == '':
        return {'success': False, 'message': 'Имя файла пустое'}, 400
    filename = secure_filename(f.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(save_path)
    url = '/static/uploads/' + filename
    return {'success': True, 'url': url}, 200


@app.route('/api/tags', methods=['GET'])
def get_tags():
    tags = TG__.get_all_tags()
    return [{'id': t.id, 'name': t.name} for t in tags]


@app.route('/api/tags', methods=['POST'])
def create_tag():
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    user_res = AM__.verify_session(user_id)
    if not user_res['success'] or not (user_res['user'].get('is_admin') or user_res['user'].get('is_superadmin')):
        return {'success': False, 'message': 'Нет прав'}, 403
    data = flask.request.get_json() or {}
    name = data.get('name')
    if not name:
        return {'success': False, 'message': 'Имя тега не указано'}, 400
    tag_id = TS__.add_tag(name)
    return {'success': True, 'tag_id': tag_id}, 201


@app.route('/api/organizations', methods=['GET'])
def get_organizations():
    orgs = OG__.get_all_organizations()
    return [{'id': o.id, 'name': o.name, 'description': o.description} for o in orgs]


@app.route('/api/organizations', methods=['POST'])
def create_organization():
    user_id = flask.session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Не авторизован'}, 401
    user_res = AM__.verify_session(user_id)
    if not user_res['success'] or not (user_res['user'].get('is_admin') or user_res['user'].get('is_superadmin')):
        return {'success': False, 'message': 'Нет прав'}, 403
    data = flask.request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    if not name:
        return {'success': False, 'message': 'Имя организации не указано'}, 400
    org_id = OS__.add_organization(name=name, description=description)
    return {'success': True, 'organization_id': org_id}, 201

@app.route('/api/register', methods=['POST'])
def register():
    """Маршрут для регистрации нового пользователя"""
    try:
        data = flask.request.get_json()
        
        if not all(key in data for key in ['name', 'email', 'password']):
            return {'success': False, 'message': 'Отсутствуют требуемые поля'}, 400
        
        result = AM__.register_user(data['name'], data['email'], data['password'])
        
        if result['success']:
            # Сохранение ID пользователя в сессию
            flask.session['user_id'] = result['user_id']
            return result, 200
        else:
            return result, 400
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


@app.route('/api/login', methods=['POST'])
def login():
    """Маршрут для входа пользователя"""
    try:
        data = flask.request.get_json()
        
        if not all(key in data for key in ['email', 'password']):
            return {'success': False, 'message': 'Отсутствуют email и пароль'}, 400
        
        result = AM__.login_user(data['email'], data['password'])
        
        if result['success']:
            # Сохранение ID пользователя в сессию
            flask.session['user_id'] = result['user']['id']
            return result, 200
        else:
            return result, 401
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


@app.route('/api/logout', methods=['GET'])
def logout():
    """Маршрут для выхода пользователя"""
    flask.session.pop('user_id', None)
    return {'success': True, 'message': 'Вы успешно вышли из системы'}, 200


@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Получить профиль текущего пользователя"""
    user_id = flask.session.get('user_id')
    
    if not user_id:
        return {'success': False, 'message': 'Пользователь не авторизован'}, 401
    
    result = AM__.verify_session(user_id)
    return result, 200 if result['success'] else 401


@app.route('/api/handle_login', methods=['POST'])
def handle_login():
    """Альтернативный маршрут для входа (в теле запроса)"""
    try:
        data = flask.request.get_json()
        
        if not all(key in data for key in ['email', 'password']):
            return {'success': False, 'message': 'Отсутствуют email и пароль'}, 400
        
        result = AM__.login_user(data['email'], data['password'])
        
        if result['success']:
            flask.session['user_id'] = result['user']['id']
            return result, 200
        else:
            return result, 401
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

@app.route('/api/verify_session', methods=['GET'])
def verify_session():
    """Маршрут для проверки сессии пользователя"""
    user_id = flask.session.get('user_id')
    
    if not user_id:
        return {'success': False, 'message': 'Пользователь не авторизован'}, 401
    
    result = AM__.verify_session(user_id)
    return result, 200 if result['success'] else 401





if __name__ == '__main__':
    app.run(debug=True)