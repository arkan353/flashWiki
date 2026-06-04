import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.ext.declarative import declarative_base



class DBworker:
    def __init__(self, db_url):
        self.engine = sqlalchemy.create_engine(db_url)
        self.Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        db = declarative_base()
        
        
        self.User = type('User', (db,), {
            
            '__tablename__': 'users',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'name': sqlalchemy.Column(sqlalchemy.String),
            'email': sqlalchemy.Column(sqlalchemy.String),
            "is_author": sqlalchemy.Column(sqlalchemy.Boolean, default=False),
            "password_hash": sqlalchemy.Column(sqlalchemy.String),                  
            "is_admin": sqlalchemy.Column(sqlalchemy.Boolean, default=False),
            "is_superadmin": sqlalchemy.Column(sqlalchemy.Boolean, default=False)
        })
        
        self.charts = type('Chapter', (db,), {
            '__tablename__': 'chapters',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'title': sqlalchemy.Column(sqlalchemy.String),
            'content': sqlalchemy.Column(sqlalchemy.String)
        })
        
        # Association table for many-to-many Article <-> Tag
        self.article_tags = sqlalchemy.Table('article_tags', db.metadata,
                                            sqlalchemy.Column('article_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id')),
                                            sqlalchemy.Column('tag_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('tags.id'))
                                            )

        self.organization = type('Organization', (db,), {
            '__tablename__': 'organizations',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'name': sqlalchemy.Column(sqlalchemy.String),
            'description': sqlalchemy.Column(sqlalchemy.String)
        })

        self.tag = type('Tag', (db,), {
            '__tablename__': 'tags',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'name': sqlalchemy.Column(sqlalchemy.String, unique=True)
        })

        self.article = type('Article', (db,), {
            '__tablename__': 'articles',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'title': sqlalchemy.Column(sqlalchemy.String),
            'content': sqlalchemy.Column(sqlalchemy.String),
            'mark_with_stars': sqlalchemy.Column(sqlalchemy.Integer),
            'is_published': sqlalchemy.Column(sqlalchemy.Boolean, default=False),
            'keywords': sqlalchemy.Column(sqlalchemy.String),
            'chart_id': sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('chapters.id')),
            'is_it_in_sandbox': sqlalchemy.Column(sqlalchemy.Boolean, default=True),
            'cover_image': sqlalchemy.Column(sqlalchemy.String),
            'organization_id': sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('organizations.id'))
        })
        
        self.comment = type('Comment', (db,), {
            '__tablename__': 'comments',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'article_id': sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id')),
            'user_id': sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
            'content': sqlalchemy.Column(sqlalchemy.String)
            
        })

        # Таблица оценок статей: один пользователь — одна оценка для статьи
        self.rating = type('Rating', (db,), {
            '__tablename__': 'ratings',
            'id': sqlalchemy.Column(sqlalchemy.Integer, primary_key=True),
            'article_id': sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id')),
            'user_id': sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
            'score': sqlalchemy.Column(sqlalchemy.Integer)
        })

        # Алиасы с заглавными именами для совместимости с кодом, который ожидает их
        # Aliases
        self.Article = self.article
        self.Comment = self.comment
        self.Rating = self.rating
        self.Tag = self.tag
        self.Organization = self.organization
        
        
        db.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()
    
    
class UserGetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def get_user_by_id(self, user_id):
        session = self.db_worker.get_session()
        user = session.query(self.db_worker.User).filter_by(id=user_id).first()
        session.close()
        return user
    
    def get_user_by_email(self, email):
        session = self.db_worker.get_session()
        user = session.query(self.db_worker.User).filter_by(email=email).first()
        session.close()
        return user
    
class UserSetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def add_user(self, name, email):
        session = self.db_worker.get_session()
        new_user = self.db_worker.User(name=name, email=email)
        session.add(new_user)
        session.commit()
        session.close()
        
class ArticleGetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def get_article_by_id(self, article_id):
        session = self.db_worker.get_session()
        article = session.query(self.db_worker.Article).filter_by(id=article_id).first()
        session.close()
        return article

    def get_all_articles(self):
        session = self.db_worker.get_session()
        articles = session.query(self.db_worker.Article).all()
        session.close()
        return articles
    
class ArticleSetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def add_article(self, title, content, mark_with_stars, is_published, keywords, chart_id):
        session = self.db_worker.get_session()
        new_article = self.db_worker.Article(title=title, content=content, mark_with_stars=mark_with_stars,
                                            is_published=is_published, keywords=keywords, chart_id=chart_id)
        session.add(new_article)
        session.commit()
        article_id = new_article.id
        session.close()
        return article_id

    def add_article_with_extra(self, title, content, mark_with_stars, is_published, keywords, chart_id, cover_image=None, organization_id=None, tags=None):
        session = self.db_worker.get_session()
        new_article = self.db_worker.Article(title=title, content=content, mark_with_stars=mark_with_stars,
                                            is_published=is_published, keywords=keywords, chart_id=chart_id,
                                            cover_image=cover_image, organization_id=organization_id)
        session.add(new_article)
        session.commit()
        article_id = new_article.id

        # Attach tags (create if missing)
        if tags:
            for t in tags:
                tag_obj = session.query(self.db_worker.Tag).filter_by(name=t).first()
                if not tag_obj:
                    tag_obj = self.db_worker.Tag(name=t)
                    session.add(tag_obj)
                    session.commit()
                session.execute(self.db_worker.article_tags.insert().values(article_id=article_id, tag_id=tag_obj.id))
            session.commit()

        session.close()
        return article_id
    
class CommentGetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def get_comment_by_id(self, comment_id):
        session = self.db_worker.get_session()
        comment = session.query(self.db_worker.Comment).filter_by(id=comment_id).first()
        session.close()
        return comment

    def get_comments_by_article_id(self, article_id):
        session = self.db_worker.get_session()
        comments = session.query(self.db_worker.Comment).filter_by(article_id=article_id).all()
        session.close()
        return comments
    
    
    
class CommentSetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def add_comment(self, article_id, user_id, content):
        session = self.db_worker.get_session()
        new_comment = self.db_worker.Comment(article_id=article_id, user_id=user_id, content=content)
        session.add(new_comment)
        session.commit()
        session.close()


class TagGetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def get_all_tags(self):
        session = self.db_worker.get_session()
        tags = session.query(self.db_worker.Tag).all()
        session.close()
        return tags


class TagSetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def add_tag(self, name):
        session = self.db_worker.get_session()
        existing = session.query(self.db_worker.Tag).filter_by(name=name).first()
        if existing:
            tag_id = existing.id
        else:
            new_tag = self.db_worker.Tag(name=name)
            session.add(new_tag)
            session.commit()
            tag_id = new_tag.id
        session.close()
        return tag_id


class OrganizationGetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def get_all_organizations(self):
        session = self.db_worker.get_session()
        orgs = session.query(self.db_worker.Organization).all()
        session.close()
        return orgs


class OrganizationSetters():
    def __init__(self, db_worker):
        self.db_worker = db_worker

    def add_organization(self, name, description=None):
        session = self.db_worker.get_session()
        new_org = self.db_worker.Organization(name=name, description=description)
        session.add(new_org)
        session.commit()
        org_id = new_org.id
        session.close()
        return org_id
        

