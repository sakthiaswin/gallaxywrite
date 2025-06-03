import streamlit as st
import bcrypt
import streamlit_authenticator as stauth  # type: ignore
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Boolean,
    ForeignKey,
    relationship,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import uuid
import urllib.parse
import re
import base64
import time
import json
from typing import List, Dict, Optional
import hashlib
import bleach
# Lazy-load heavy libraries


def import_pdf_libraries():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from io import BytesIO
    return letter, SimpleDocTemplate, Paragraph, Spacer, Image, getSampleStyleSheet, BytesIO  # Hardcoded APP_URL


APP_URL = "https://gallaxywrite.streamlit.app/"

# Page configuration
st.set_page_config(
    page_title="GalaxyWrite",
    page_icon="🌌",
    layout="wide",
    initial_side_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/gallaxywrite/support',
        'Report a bug': 'https://github.com/gallaxywrite/issues',
        'About': "GalaxyWrite - Your Cosmic Blogging Platform"
    }
)
# Cache database engine and session factory


@st.cache_resource
def get_db_engine():
    start_time = time.time()
    engine = create_engine('sqlite:///galaxywrite.db', echo=False)
    st.write(f"get_db_engine took{time.time() - start_time:.2f} seconds")
    return engine


@st.cache_resource
def get_db_session(_engine):
    start_time = time.time()
    Session = sessionmaker(bind=_engine)
    st.write(f"get_db_session took{time.time() - start_time:.2f} seconds")
    return Session


# Database setup
Base = declarative_base()


class User(Base):
    __table__name__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    profile = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    blogs = relationship("Blog", back_populates="user")
    case_studies = relationship("CaseStudy", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    media = relationship("Media", back_populates="user")
    __table_args__ = (Index('idx_user_username', 'username'),)


class Blog(Base):
    __table__name__ = 'blogs'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tagscznym = Column(JSON, default=[])
    media = Column(JSON, default=[])
    font = Column(String(50), default='Inter')
    content_type = Column(String(20), default='blog')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    public_link = Column(String(255))
    is_published = Column(Boolean, default=True)
    user = relationship("User", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")
    __table_args__ = (Index('idx_blog_username', 'username', 'content_type'))


class CaseStudy(Base):
    __table__name__ = 'case_studies'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    results = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    media = Column(JSON, default=[])
    font = Column(String(50), default='Inter')
    content_type = Column(String(20), default='case_study')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    public_link = Column(String(255))
    is_published = Column(Boolean, default=True)
    user = relationship("User", back_populates="case_studies")
    comments = relationship("Comment", back_populates="case_study")
    __table_args__ = (Index('idx_case_username', 'username', 'content_type'),)


class Media(Base):
    __table__name__ = 'media'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)
    content = Column(String(255), nullable=False)
    filename = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="media")
    __table_args__ = (Index('idx_media_username', 'username'),)


class Comment(Base):
    __table__name__ = 'comments'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_type = Column(String(20), nullable=False)
    content_id = Column(String(36), nullable=False)
    username = Column(String(50), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="comments")
    blog = relationship("Blog", back_populates="comments")
    case_study = relationship("CaseStudy", back_populates="comments")
    __table_args__ = (Index('idx_comment_content', 'content_type', 'content_id'),)


engine = get_db_engine()
Base.metadata.create_all(engine)
Session = get_db_session(engine)

# Optimized Queries


@st.cache_data(ttl=3600)
def get_all_public_content():
    start_time = time.time()
    with Session() as session:
        blogs = session.query(Blog).filter_by(is_published=True).limit(30).all()
        case_studies = session.query(CaseStudy).filter_by(is_published=True).limit(30).all()
        all_content = [
            {'type': 'blog', 'author': blog.username, 'content': blog}
            for blog in blogs
        ] + [
            {'type': 'case_study', 'author': case.username, 'content': case}
            for case in case_studies
        ]
        all_content = sorted(all_content, key=lambda x: x['content'].created_at, reverse=True)
    st.write(f"get_all_public_content took {time.time() - start_time:.2f} seconds")
    return all_content


@st.cache_data(ttl=3600)
def get_comments(_content_type: str, content_id: str):
    start_time = time.time()
    with Session() as session:
        comments = session.query(Comment).filter_by(content_type=_content_type, content_id=content_id).limit(10).all()
    st.write(f"get_comments took {time.time() - start_time:.2f} seconds")
    return comments


@st.cache_data(ttl=3600)
def search_content(query: str, filters: Dict = None) -> List[Dict]:
    start_time = time.time()
    with Session() as session:
        search_pattern = f"%{query}%"
        blog_query = session.query(Blog).filter(Blog.title.ilike(search_pattern) | Blog.content.ilike(search_pattern))
        case_query = session.query(CaseStudy).filter(CaseStudy.title.ilike(
            search_pattern) | CaseStudy.problem.ilike(search_pattern))
        if filters:
            if filters.get('content_type') == 'blog':
                case_query = case_query.filter(False)
            elif filters.get('content_type') == 'case_study':
                blog_query = blog_query.filter(False)
            if filters.get('author'):
                blog_query = blog_query.filter(Blog.username == filters['author'])
                case_query = case_query.filter(CaseStudy.username == filters['author'])
            if filters.get('tags'):
                blog_query = blog_query.filter(Blog.tags.contains(filters['tags']))
                case_query = case_query.filter(CaseStudy.tags.contains(filters['tags']))
        blogs = blog_query.limit(30).all()
        case_studies = case_query.limit(30).all()
        results = [
            {'type': 'blog', 'author': blog.username, 'content': blog}
            for blog in blogs
        ] + [
            {'type': 'case_study', 'author': case.username, 'content': case}
            for case in case_studies
        ]
        results = sorted(results, key=lambda x: x['content'].created_at, reverse=True)
    st.write(f"search_content took {time.time() - start_time:.2f} seconds")
    return results

# Data Manager


class DataManager:
    def __init__(self):
        self.session_factory = Session

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def register_user(self, username: str, password: str, email: str) -> bool:
        username = bleach.clean(username)
        email = bleach.clean(email)
        with self.session_factory() as session:
            if session.query(User).filter_by(username=username).first():
                return False
            if session.query(User).filter_by(email=email).first():
                return False
            user = User(
                username=username,
                password=self.hash_password(password),
                email=email,
                profile={
                    'bio': '',
                    'avatar': '',
                    'social_links': {},
                    'preferred_font': 'Inter',
                    'theme': 'light',
                    'notifications': {'email_comments': True, 'email_follows': False}
                }
            )
            session.add(user)
            session.commit()
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username, is_active=True).first()
            if user and self.check_password(password, user.password):
                return True
        return False

    def save_blog(self, username: str, title: str, content: str, tags: str = "", media: Optional[List[str]] = None, font: str = 'Inter', content_type: str = 'blog', is_published: bool = True) -> str:
        title = bleach.clean(title)
        content = bleach.clean(content)
        tags = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
        blog_id = str(uuid.uuid4())
        public_link = f"{APP_URL}/content/blog/{urllib.parse.quote(username)}/{blog_id}"
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                raise ValueError("User not found")
            blog = Blog(
                id=blog_id,
                user_id=user.id,
                username=username,
                title=title,
                content=content,
                tags=tags,
                media=media or [],
                font=font,
                content_type=content_type,
                public_link=public_link,
                is_published=is_published
            )
            session.add(blog)
            session.commit()
        return blog_id

    def save_case_study(self, username: str, title: str, problem: str, solution: str, results: str, tags: str = "", media: Optional[List[str]] = None, font: str = 'Inter', is_published: bool = True) -> str:
        title = bleach.clean(title)
        problem = bleach.clean(problem)
        solution = bleach.clean(solution)
        results = bleach.clean(results)
        tags = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
        case_id = str(uuid.uuid4())
        public_link = f"{APP_URL}/content/case_study/{urllib.parse.quote(username)}/{case_id}"
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                raise ValueError("User not found")
            case_study = CaseStudy(
                id=case_id,
                user_id=user.id,
                username=username,
                title=title,
                problem=problem,
                solution=solution,
                results=results,
                tags=tags,
                media=media or [],
                font=font,
                content_type='case_study',
                public_link=public_link,
                is_published=is_published
            )
            session.add(case_study)
            session.commit()
        return case_id

    def save_media(self, username: str, file) -> str:
        file_type = 'image' if file.type.startswith('image') else 'video' if file.type.startswith('video') else 'gif'
        file_content = base64.b64encode(file.read()).decode('utf-8')
        file_id = str(uuid.uuid4())
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                raise ValueError("User not found")
            media = Media(
                id=file_id,
                user_id=user.id,
                username=username,
                type=file_type,
                content=file_content,
                filename=bleach.clean(file.name)
            )
            session.add(media)
            session.commit()
        return file_id

    def save_comment(self, content_type: str, content_id: str, username: str, comment: str) -> str:
        comment = bleach.clean(comment)
        comment_id = str(uuid.uuid4())
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                raise ValueError("User not found")
            comment_obj = Comment(
                id=comment_id,
                user_id=user.id,
                content_type=content_type,
                content_id=content_id,
                username=username,
                comment=comment
            )
            session.add(comment_obj)
            session.commit()
        return comment_id

    def update_profile(self, username: str, profile_data: Dict) -> bool:
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return False
            user.profile = {**user.profile, **profile_data}
            session.commit()
        return True

    def increment_views(self, content_type: str, content_id: str):
        with self.session_factory() as session:
            if content_type == 'blog':
                content = session.query(Blog).filter_by(id=content_id).first()
            else:
                content = session.query(CaseStudy).filter_by(id=content_id).first()
            if content:
                content.views += 1
                session.commit()

    def get_analytics(self, username: str) -> Dict:
        with self.session_factory() as session:
            blogs = session.query(Blog).filter_by(username=username).all()
            case_studies = session.query(CaseStudy).filter_by(username=username).all()
            total_views = sum(blog.views for blog in blogs) + sum(case.views for case in case_studies)
            total_comments = session.query(Comment).filter(
                Comment.content_id.in_([b.id for b in blogs] + [c.id for c in case_studies])
            ).count()
            return {
                'total_blogs': len(blogs),
                'total_case_studies': len(case_studies),
                'total_views': total_views,
                'total_comments': total_comments,
                'recent_blogs': sorted(blogs, key=lambda x: x.created_at, reverse=True)[:5],
                'recent_case_studies': sorted(case_studies, key=lambda x: x.created_at, reverse=True)[:5]
            }

    @st.cache_data(ttl=3600)
    def get_user_blogs(_self, username: str):
        start_time = time.time()
        with _self.session_factory() as session:
            blogs = session.query(Blog).filter_by(username=username).limit(30).all()
        st.write(f"get_user_blogs took {time.time() - start_time:.2f} seconds")
        return blogs

    @st.cache_data(ttl=3600)
    def get_user_case_studies(_self, username: str):
        start_time = time.time()
        with _self.session_factory() as session:
            cases = session.query(CaseStudy).filter_by(username=username).limit(30).all()
        st.write(f"get_user_case_studies took {time.time() - start_time:.2f} seconds")
        return cases

    @st.cache_data(ttl=3600)
    def get_media(_self, username: str, file_id: str):
        start_time = time.time()
        with _self.session_factory() as session:
            media = session.query(Media).filter_by(username=username, id=file_id).first()
        st.write(f"get_media took {time.time() - start_time:.2f} seconds")
        return media

    @st.cache_data(ttl=3600)
    def get_user_profile(_self, username: str):
        start_time = time.time()
        with _self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
        st.write(f"get_user_profile took {time.time() - start_time:.2f} seconds")
        return user.profile if user else {}

# Utility Functions


def export_to_pdf(content_type: str, content, media: Optional[List] = None):
    letter, SimpleDocTemplate, Paragraph, Spacer, Image, getSampleStyleSheet, BytesIO = import_pdf_libraries()
    from reportlab.lib.units import inch
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(bleach.clean(content.title), styles['Title']))
    story.append(Spacer(1, 12))

    if content_type == 'blog':
        story.append(Paragraph(bleach.clean(content.content), styles['BodyText']))
    else:
        story.append(Paragraph(f"<b>Problem:</b> {bleach.clean(content.problem)}", styles['BodyText']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Solution:</b> {bleach.clean(content.solution)}", styles['BodyText']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Results:</b> {bleach.clean(content.results)}", styles['BodyText']))

    if media:
        for media_item in media:
            if media_item.type == 'image':
                img_data = base64.b64decode(media_item.content)
                img_buffer = BytesIO(img_data)
                story.append(Image(img_buffer, width=2 * inch, height=2 * inch))
                story.append(Spacer(1, 12))

    doc.build(story)
    return buffer.getvalue()


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_gravatar_url(email: str) -> str:
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s=200&d=identicon"

# CSS Styling


def load_css():
    st.markdown("""
    <style>
        .header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(90deg, #1e3c72, #2a5298);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 1rem;
        }
        .card {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .sidebar-title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #1e3c72;
            margin-bottom: 1rem;
        }
        .content-card {
            background: #f9fafb;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #2a5298;
        }
        .comment-card {
            background: #f1f5f9;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .template-card {
            background: #e0f2fe;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .analytics-box {
            background: #e0f2fe;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .text-lg {
            font-size: 1.125rem;
        }
        .text-center {
            text-align: center;
        }
        .text-gray-400 {
            color: #9ca3af;
        }
        .py-4 {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .max-w-md {
            max-width: 28rem;
        }
        .mx-auto {
            margin-left: auto;
            margin-right: auto;
        }
        .mb-6 {
            margin-bottom: 1.5rem;
        }
        .font-semibold {
            font-weight: 600;
        }
        .avatar {
            border-radius: 50%;
            width: 120px;
            height: 120px;
        }
    </style>
    """, unsafe_allow_html=True)

# Pages


def login_page():
    st.markdown("""
    <div class="header">
        <h1>🌌 GalaxyWrite</h1>
        <p>Your Cosmic Blogging Platform</p>
    </div>
    <div class="container">
        <div class="card max-w-md mx-auto">
            <h2 class="text-2xl font-semibold mb-6 text-center">Welcome Back</h2>
    """, unsafe_allow_html=True)

    credentials = {
        'usernames': {
            user.username: {
                'name': user.username,
                'password': user.password,
                'email': user.email
            }
            for user in Session().query(User).all()
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="galaxywrite",
        key="abcdef",
        cookie_expiry_days=30
    )

    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        st.session_state.authenticated = True
        st.session_state.username = username
        with Session() as session:
            user = session.query(User).filter_by(username=username).first()
            if user:
                st.session_state.user_password = user.password
        st.success("Login successful!")
        st.rerun()
    elif authentication_status == False:
        st.error("Invalid username or password!")
    elif authentication_status == None:
        st.warning("Please enter your username and password")

    with st.expander("Create a New Account", expanded=False):
        st.markdown("<h3 class='text-lg font-semibold'>Sign Up</h3>", unsafe_allow_html=True)
        new_username = st.text_input("Username", key="signup_username", placeholder="Choose a unique username")
        new_email = st.text_input("Email", key="signup_email", placeholder="your.email@example.com")
        new_password = st.text_input("Password", type="password", key="signup_password",
                                     placeholder="At least 8 characters")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Sign Up", key="signup_btn", type="primary"):
            if not new_username or not new_email or not new_password:
                st.error("Please fill all fields!")
            elif new_password != confirm_password:
                st.error("Passwords don't match!")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters!")
            elif not validate_email(new_email):
                st.error("Invalid email format!")
            elif dm.register_user(new_username, new_password, new_email):
                st.success("Account created successfully! Please login.")
                credentials['usernames'][new_username] = {
                    'name': new_username,
                    'password': dm.hash_password(new_password),
                    'email': new_email
                }
            else:
                st.error("Username or email already exists!")

    st.markdown("</div></div>", unsafe_allow_html=True)


def dashboard():
    st.markdown("""
    <div class="header">
        <h1>📊 Dashboard</h1>
        <p>Your personalized content hub</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Write New Blog", key="quick_blog"):
            st.query_params.page = "Write Blog"
            st.rerun()
    with col2:
        if st.button("Create Case Study", key="quick_case"):
            st.query_params.page = "Create Case Study"
            st.rerun()
    with col3:
        if st.button("View Analytics", key="quick_analytics"):
            st.query_params.page = "Analytics"
            st.rerun()

    st.subheader("Recent Content")
    blogs = dm.get_user_blogs(st.session_state.username)[:5]
    case_studies = dm.get_user_case_studies(st.session_state.username)[:5]
    recent_content = sorted(
        [{'type': 'blog', 'content': b} for b in blogs] + [{'type': 'case_study', 'content': c} for c in case_studies],
        key=lambda x: x['content'].created_at,
        reverse=True
    )[:5]
    for item in recent_content:
        content = item['content']
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <h4>{bleach.clean(content.title)}</h4>
        <p><b>{item['type'].title()}</b> | Created: {content.created_at.strftime('%B %d, %Y')} | Views: {content.views}</p>
        """, unsafe_allow_html=True)
        st.link_button("View", content.public_link)
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("Notifications")
    profile = dm.get_user_profile(st.session_state.username)
    if profile.get('notifications', {}).get('email_comments'):
        comments = []
        with Session() as session:
            user_content_ids = [b.id for b in blogs] + [c.id for c in case_studies]
            comments = session.query(Comment).filter(Comment.content_id.in_(user_content_ids)
                                                     ).order_by(Comment.created_at.desc()).limit(5).all()
        for comment in comments:
            st.markdown(
                f"<p><b>{bleach.clean(comment.username)}</b> commented on your content: {bleach.clean(comment.comment[:50])}...</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def main_page():
    st.markdown("""
    <div class="header">
        <h1>🌌 Explore GalaxyWrite</h1>
        <p>Discover stories, case studies, and ideas from our cosmic community</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    all_content = get_all_public_content()
    for content in all_content:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            if content['type'] == 'blog':
                st.markdown(f"""
                <h3>{bleach.clean(content['content'].title)}</h3>
                <p><strong>By {bleach.clean(content['author'])}</strong> | {content['content'].created_at.strftime('%B %d, %Y')} | 👀 {content['content'].views} views</p>
                <p>{bleach.clean(content['content'].content[:200])}...</p>
                """, unsafe_allow_html=True)
                st.link_button("Read More", content['content'].public_link)
                if content['content'].media:
                    media = dm.get_media(content['author'], content['content'].media[0])
                    if media and media.type == 'image':
                        st.image(base64.b64decode(media.content), width=300)
            else:
                st.markdown(f"""
                <h3>{bleach.clean(content['content'].title)}</h3>
                <p><strong>By {bleach.clean(content['author'])}</strong> | {content['content'].created_at.strftime('%B %d, %Y')} | 👀 {content['content'].views} views</p>
                <p><strong>Problem:</strong> {bleach.clean(content['content'].problem[:100])}...</p>
                """, unsafe_allow_html=True)
                st.link_button("Read More", content['content'].public_link)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def blog_editor():
    st.markdown("""
    <div class="header">
        <h1>✍️ Write a Blog</h1>
        <p>Share your thoughts with the universe</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    template = st.selectbox("Choose a Template", ["None", "Tech Blog",
                            "Personal Story", "Tutorial"], key="blog_template")
    title = st.text_input("Blog Title", placeholder="Enter your blog title", key="blog_title")
    content = st.text_area("Blog Content", placeholder="Write your blog content here...",
                           height=300, key="blog_content")
    tags = st.text_input("Tags (comma-separated)", placeholder="e.g., tech, ai, coding", key="blog_tags")
    font = st.selectbox("Font Style", ["Inter", "Roboto", "Merriweather", "Lora"], index=0, key="blog_font")
    is_published = st.checkbox("Publish immediately", value=True, key="blog_publish")
    uploaded_files = st.file_uploader("Upload Media (Images/Videos)", accept_multiple_files=True,
                                      type=['png', 'jpg', 'jpeg', 'gif', 'mp4'], key="blog_media")

    if template != "None":
        if template == "Tech Blog":
            content = "## Introduction\n\n## Technical Details\n\n## Conclusion"
        elif template == "Personal Story":
            content = "## The Beginning\n\n## The Journey\n\n## Reflections"
        elif template == "Tutorial":
            content = "## Prerequisites\n\n## Step-by-Step Guide\n\n## Summary"
        st.session_state['blog_content'] = content

    media_ids = []
    if uploaded_files:
        for file in uploaded_files:
            media_id = dm.save_media(st.session_state.username, file)
            media_ids.append(media_id)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Draft" if not is_published else "Publish Blog", type="primary", key="blog_save"):
            if not title or not content:
                st.error("Title and content are required!")
            else:
                blog_id = dm.save_blog(st.session_state.username, title, content, tags,
                                       media_ids, font, is_published=is_published)
                st.success(
                    f"Blog {'published' if is_published else 'saved as draft'}! View it [here]({APP_URL}/content/blog/{urllib.parse.quote(st.session_state.username)}/{blog_id})")
                st.balloons()
    with col2:
        if st.button("Preview", key="blog_preview"):
            st.markdown(f"<h3>{bleach.clean(title)}</h3>", unsafe_allow_html=True)
            st.markdown(bleach.clean(content), unsafe_allow_html=True)
            if media_ids:
                for media_id in media_ids[:1]:
                    media = dm.get_media(st.session_state.username, media_id)
                    if media and media.type == 'image':
                        st.image(base64.b64decode(media.content), width=300)

    st.markdown("</div>", unsafe_allow_html=True)


def case_study_editor():
    st.markdown("""
    <div class="header">
        <h1>📚 Create a Case Study</h1>
        <p>Document your successes and lessons learned</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    template = st.selectbox("Choose a Template", ["None", "Business Case", "Project Analysis"], key="case_template")
    title = st.text_input("Case Study Title", placeholder="Enter your case study title", key="case_title")
    problem = st.text_area("Problem Statement", placeholder="Describe the problem...", height=150, key="case_problem")
    solution = st.text_area("Solution", placeholder="Describe the solution...", height=150, key="case_solution")
    results = st.text_area("Results", placeholder="Describe the results...", height=150, key="case_results")
    tags = st.text_input("Tags (comma-separated)", placeholder="e.g., business, tech", key="case_tags")
    font = st.selectbox("Font Style", ["Inter", "Roboto", "Merriweather", "Lora"], index=0, key="case_font")
    is_published = st.checkbox("Publish immediately", value=True, key="case_publish")
    uploaded_files = st.file_uploader("Upload Media (Images/Videos)", accept_multiple_files=True,
                                      type=['png', 'jpg', 'jpeg', 'gif', 'mp4'], key="case_media")

    if template != "None":
        if template == "Business Case":
            problem = "Describe the business challenge..."
            solution = "Outline the implemented strategy..."
            results = "Summarize the outcomes..."
        elif template == "Project Analysis":
            problem = "Identify the project issue..."
            solution = "Detail the project approach..."
            results = "Evaluate the project impact..."
        st.session_state['case_problem'] = problem
        st.session_state['case_solution'] = solution
        st.session_state['case_results'] = results

    media_ids = []
    if uploaded_files:
        for file in uploaded_files:
            media_id = dm.save_media(st.session_state.username, file)
            media_ids.append(media_id)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Draft" if not is_published else "Publish Case Study", type="primary", key="case_save"):
            if not all([title, problem, solution, results]):
                st.error("All fields are required!")
            else:
                case_id = dm.save_case_study(st.session_state.username, title, problem,
                                             solution, results, tags, media_ids, font, is_published)
                st.success(
                    f"Case Study {'published' if is_published else 'saved as draft'}! View it [here]({APP_URL}/content/case_study/{urllib.parse.quote(st.session_state.username)}/{case_id})")
                st.balloons()
    with col2:
        if st.button("Preview", key="case_preview"):
            st.markdown(f"<h3>{bleach.clean(title)}</h3>", unsafe_allow_html=True)
            st.markdown(f"<b>Problem:</b> {bleach.clean(problem)})", unsafe_allow_html=True)
            st.markdown(f"<b>Solution:</b> {bleach.clean(solution)})", unsafe_allow_html=True)
            st.markdown(f"<b>Results:</b> {bleach.clean(results)})", unsafe_allow_html=True)
            if media_ids:
                for media_id in media_ids[:1]:
                    media = dm.get_media(st.session_state.username, media_id)
                    if media and media.type == 'image':
                        st.image(base64.b64decode(media.content), width=300)

    st.markdown("</div>", unsafe_allow_html=True)


def my_content():
    st.markdown("""
    <div class="header">
        <h1>📚 My Content</h1>
        <p>Manage your blogs and case studies</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    st.subheader("Your Blogs")
    blogs = dm.get_user_blogs(st.session_state.username)
    for blog in blogs:
        with st.expander(f"{bleach.clean(blog.title)} | {'Published' if blog.is_published else 'Draft'}"):
            st.markdown(f"""
            <p><b>Created:</b> {blog.created_at.strftime('%B %d, %Y')}</p>
            <p><b>Views:</b> {blog.views}</p>
            <p>{bleach.clean(blog.content[:200])}...</p>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button("View", blog.public_link)
            with col2:
                if st.button("Edit", key=f"edit_blog_{blog.id}"):
                    st.session_state.edit_content = {'type': 'blog', 'id': blog.id}
                    st.query_params.page = "Edit Content"
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_blog_{blog.id}"):
                    with Session() as session:
                        session.delete(blog)
                        session.commit()
                    st.success("Blog deleted!")
                    st.rerun()

    st.subheader("Your Case Studies")
    case_studies = dm.get_user_case_studies(st.session_state.username)
    for case in case_studies:
        with st.expander((f"{bleach.clean(case.title)}") | {'Published' if case.is_published else 'Draft'}):
            st.markdown(f"""
            <p><b>Created:</b> {case.created_at.strftime('%B %d, %Y')}</p>
            <p><b>Views:</b> {case.views}</p>
            <p><b>Problem:</b> {bleach.clean(case.problem[:200])}...</p>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button("View", case.public_link)
            with col2:
                if st.button("Edit", key=f"edit_case_{case.id}"):
                    st.session_state.edit_content = {'type': 'case_study', 'id': case.id}
                    st.query_params.page = "Edit Content"
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_case_{case.id}"):
                    with Session() as session:
                        session.delete(case)
                        session.commit()
                    st.success("Case study deleted!")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def content_templates():
    st.markdown("""
    <div class="header">
        <h1>📄 Templates</h1>
        <p>Explore pre-built templates for your content</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    templates = [
        {
            'name': 'Tech Blog',
            'type': 'blog',
            'content': "## Introduction\n\n## Technical Details\n\n## Conclusion\n",
            'description': 'Ideal for tech articles and tutorials'
        },
        {
            'name': 'Personal Story',
            'type': 'blog',
            'content': "## The Beginning\n\n## The Journey\n\n## Reflections\n",
            'description': 'Perfect for narrative-driven posts'
        },
        {
            'name': 'Business Case',
            'type': 'case_study',
            'problem': "Describe the business challenge...",
            'solution': "Outline the implemented strategy...",
            'results': "Summarize the outcomes...",
            'description': 'Structured for business analysis'
        }
    ]

    for template in templates:
        st.markdown('<div class="template-card"', unsafe_allow_html=True)
        st.markdown(f"""
        <h3>{template['name']}</h3>
        <p>{template['description']}</p>
        """, unsafe_allow_html=True)
        if st.button(f"Use {template['name']} Template", key=f"template_{template['name']}"):
            if template['type'] == 'blog':
                st.session_state['blog_content'] = template['content']
                st.query_params.page = "Write Blog"
            else:
                st.session_state['case_problem'] = template['problem']
                st.session_state['case_solution'] = template['solution']
                st.session_state['case_results'] = template['results']
                st.query_params.page = "Create Case Study"
            st.rerun()
        st.markdown('</div>', unsafe_template=True)

    st.markdown("</div>", unsafe_allow_html=True)


def analytics_dashboard():
    st.markdown("""
    <div class="header">
        <h1>📈 Analytics Dashboard</h1>
        <p>Track your content's performance</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    analytics = dm.get_analytics(st.session_state.username)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"<div class='analytics-box'><p><strong>Total Blogs:</strong> {analytics['total_blogs']}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            f"<div class='analytics-box'><p><strong>Case Studies:</strong> {analytics['total_case_studies']}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(
            f"<div class='analytics-box'><p><strong>Total Views:</strong> {analytics['total_views']}</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(
            f"<div class='analytics-box'><p><strong>Comments:</strong> {analytics['total_comments']}</p></div>", unsafe_allow_html=True)

    st.subheader("Recent Content Performance")
    for blog in analytics['recent_blogs']:
        st.markdown(
            f"<p><b>Blog:</b> {bleach.clean(blog.title)} | Views: {blog.views} | Created: {blog.created_at.strftime('%B %d, %Y')}</p>", unsafe_allow_html=True)
    for case in analytics['recent_case_studies']:
        st.markdown(
            f"<p><b>Case Study:</b> {bleach.clean(case.title)} | Views: {case.views} | Created: {case.created_at.strftime('%B %d, %Y')}</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def content_search_and_filter():
    st.markdown("""
    <div class="header">
        <h1>🔍 Search & Filter</h1>
        <p>Find content that inspires you</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    query = st.text_input("Search Keywords", placeholder="Enter keywords...")
    content_type = st.selectbox("Content Type", ["All", "Blog", "Case Study"], key="filter_type")
    author = st.text_input("Author", placeholder="Enter username (optional)", key="filter_author")
    tags = st.text_input("Tags (comma-separated)", placeholder="e.g., tech, ai", key="filter_tags")
    if st.button("Search"):
        filters = {}
        if content_type != "All":
            filters['content_type'] = content_type.lower()
        if author:
            filters['author'] = author
        if tags:
            filters['tags'] = [tag.strip() for tag in tags.split(',')]
        results = search_content(query, filters)
        st.markdown(f"<p class='text-lg'>Found {len(results)} results</p>", unsafe_allow_html=True)
        for content in results:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            if content['type'] == 'blog':
                st.markdown(f"""
                <h3>{bleach.clean(content['content'].title)}</h3>
                <p><strong>By {bleach.clean(content['author'])}</strong> | {content['content'].created_at.strftime('%B %d, %Y')}</p>
                <p>{bleach.clean(content['content'].content[:100])}...</p>
                """, unsafe_allow_html=True)
                st.link_button("Read More", content['content'].public_link)
            else:
                st.markdown(f"""
                <h3>{bleach.clean(content['content'].title)}</h3>
                <p><strong>By {bleach.clean(content['author'])}</strong> | {content['content'].created_at.strftime('%B %d, %Y')}</p>
                <p><strong>Problem:</strong> {bleach.clean(content['content'].problem[:100])}...</p>
                """, unsafe_allow_html=True)
                st.link_button("Read More", content['content'].public_link)
            st.markdown('</div>', unsafe_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def profile_settings():
    st.markdown("""
    <div class="header">
        <h1>⚙️ Profile Settings</h1>
        <p>Customize your profile and preferences</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    profile = dm.get_user_profile(st.session_state.username)
    with st.form("profile_form"):
        bio = st.text_area("Bio", value=profile.get('bio', ''), key="bio")
        avatar = st.text_input("Avatar URL", value=profile.get('avatar', ''), key="avatar")
        preferred_font = st.selectbox("Preferred Font", ["Inter", "Roboto", "Merriweather", "Lora"], index=[
                                      "Inter"].index(profile.get('preferred_font', 'Inter')), key="font")
        theme = st.selectbox("Theme", ["light"], index=["light"].index(profile.get('theme', 'light')), key="theme")
        social_links = {}
        for i in range(3):
            platform = st.text_input(f"Social Platform {i + 1}", key=f"platform_{i}")
            url = st.text_input(f"Social URL {i + 1}", key=f"url_{i}")
            if platform and url:
                social_links[platform] = url
        if st.form_submit_button("Save Profile"):
            profile_data = {
                'bio': bio,
                'avatar': avatar,
                'preferred_font': preferred_font,
                'theme': social_links
            }
            if dm.update_profile(st.session_state.username, profile_data):
                st.success("Profile updated!")
                st.rerun()

    st.subheader("Account Settings")
    with st.form("account_form"):
        current_password = st.text_input("Current Password", type="password", key="current_password")
        new_password = st.text_input("New Password", type="password", key="new_password")
        confirm_new = st.text_input("Confirm New Password", type="password", key="confirm_new")
        if st.form_submit_button("Change Password"):
            if not all([current_password, new_password, confirm_new]):
                st.error("All fields are required!")
            elif new_password != confirm_new:
                st.error("New passwords don't match!")
            elif len(new_password) < 8:
                st.error("New password must be at least 8 characters!")
            elif not dm.check_password(current_password, st.session_state.user_password):
                st.error("Incorrect current password!")
            else:
                with Session() as session:
                    user = session.query(User).filter_by(username=st.session_state.username).first()
                    user.password = dm.hash_password(new_password)
                    session.commit()
                st.session_state.user_password = user.password
                st.success("Password changed successfully!")

    st.subheader("Notification Preferences")
    notifications = profile.get('notifications', {'email_comments': True, 'email_follows': False})
    with st.form("notifications_form"):
        email_comments = st.checkbox("Email notifications for comments",
                                     value=notifications.get('email_comments', True))
        email_follows = st.checkbox("Email notifications for follows", value=notifications.get('email_follows', False))
        if st.form_submit_button("Save Notifications"):
            profile['notifications'] = {'email_comments': email_comments, 'email_follows': email_follows}
            dm.update_profile(st.session_state.username, profile)
            st.success("Notification preferences saved!")

    st.markdown("</div>", unsafe_allow_html=True)


def export_content():
    st.markdown("""
    <div class="header">
        <h1>📤 Export Content</h1>
        <p>Download your blogs and case studies</p>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    content_type = st.selectbox("Content Type", ["Blog", "Case Study"], key="export_type")
    blogs = dm.get_user_blogs(st.session_state.username) if content_type == "Blog" else dm.get_user_case_studies(
        st.session_state.username)
    selected_content = st.multiselect("Select Content to Export", [b.title for b in blogs], key="export_select")

    if st.button("Export Selected", type="primary"):
        for title in selected_content:
            content = next(b for b in selected_content if b.title == title)
            media_items = [dm.get_media(st.session_state.username, mid) for mid in content.media]
            pdf_data = export_to_pdf(content_type.lower(), content, [m for m in media_items if m])
            st.download_button(
                label=f"Download {title} as PDF",
                data=pdf_data,
                file_name=f"{bleach.clean(title)}.pdf",
                mime="application/pdf",
                key=f"export_{title}"
            )

    st.markdown("</div>", unsafe_allow_html=True)


def content_view():
    query_params = st.query_params
    content_type = query_params.get('content_type', [''])[0]
    username = query_params.get('username', [''])[0]
    content_id = query_params.get('content_id', [''])[0]

    if not all([content_type, username, content_id]):
        st.error("Invalid content URL!")
        return

    with Session() as session:
        if content_type == 'blog':
            content = session.query(Blog).filter_by(id=content_id, username=username).first()
        else:
            content = session.query(CaseStudy).filter_by(id=content_id, username=username).first()

        if not content:
            st.error("Content not found!")
            return

        dm.increment_views(content_type, content_id)

        st.markdown(f"""
        <div class="header">
            <h1>{bleach.clean(content.title)}</h1>
            <p>By {bleach.clean(username)} | {content.created_at.strftime('%B %d, %Y')} | 👀 {content.views} views</p>
        </div>
        <div class="container">
        """, unsafe_allow_html=True)

        if content_type == 'blog':
            st.markdown(bleach.clean(content.content), unsafe_allow_html=True)
        else:
            st.markdown(f"<b>Problem:</b> {bleach.clean(content.problem)}", unsafe_allow_html=True)
            st.markdown(f"<b>Solution:</b> {bleach.clean(content.solution)}", unsafe_allow_html=True)
            st.markdown(f"<b>Results:</b> {bleach.clean(content.results)}", unsafe_allow_html=True)

        if content.tags:
            st.markdown(
                f"<p><b>Tags:</b> {', '.join(bleach.clean(tag) for tag in content.tags)}</p>", unsafe_allow_html=True)

        if content.media:
            st.subheader("Media Gallery")
            cols = st.columns(3)
            for idx, media_id in enumerate(content.media):
                media = dm.get_media(username, media_id)
                if media:
                    with cols[idx % 3]:
                        if media.type == 'image':
                            st.image(base64.b64decode(media.content), caption=bleach.clean(media.filename), width=200)
                        elif media.type == 'video':
                            st.video(base64.b64decode(media.content))
                        elif media.type == 'gif':
                            st.image(base64.b64decode(media.content), caption="")

        media_items = [dm.get_media(username, mid) for mid in content.media]
        pdf_data = export_to_pdf(content_type, content, [m for m in media_items if m])
        st.download_button(
            label="Download as PDF",
            data=pdf_data,
            file_name=f"{bleach.clean(content.title)}.pdf",
            mime="application/pdf"
        )

        st.subheader("Comments")
        comments = get_comments(content_type, content_id)
        for comment in comments:
            st.markdown('<div class="comment-card">', unsafe_allow_html=True)
            st.markdown(f"""
            <p><strong>{bleach.clean(comment.username)}</strong> | {comment.created_at.strftime('%B %d, %Y %H:%M')}</p>
            <p>{bleach.clean(comment.comment)}</p>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.authenticated:
            with st.form(f"comment_form_{content_id}", clear_on_submit=True):
                comment_text = st.text_area("Add a Comment", placeholder="Write your comment here...", height=100)
                if st.form_submit_button("Post Comment"):
                    if comment_text:
                        dm.save_comment(content_type, content_id, st.session_state.username, comment_text)
                        st.success("Comment posted!")
                        st.rerun()
                    else:
                        st.error("Comment cannot be empty!")

        st.markdown("</div>", unsafe_allow_html=True)


def edit_content():
    if 'edit_content' not in st.session_state:
        st.error("No content selected for editing!")
        return

    content_type = st.session_state.edit_content['type']
    content_id = st.session_state.edit_content['id']

    with Session() as session:
        if content_type == 'blog':
            content = session.query(Blog).filter_by(id=content_id).first()
        else:
            content = session.query(CaseStudy).filter_by(id=content_id).first()

        if not content:
            st.error("Content not found!")
            return

        st.markdown(f"""
        <div class="header">
            <h1>✎ Edit {content_type.capitalize()}</h1>
        </div>
        <div class="container">
        """, unsafe_allow_html=True)

        if content_type == 'blog':
            title = st.text_input("Blog Title", value=content.title, key="edit_title")
            content_text = st.text_area("Content", value=content.content, height=300, key="edit_content")
            tags = st.text_input("Tags (comma-separated)", value=", ".join(content.tags), key="edit_tags")
            font = st.selectbox("Font Style", ["Inter", "Roboto", "Merriweather", "Lora"], index=[
                                "Inter", "Roboto", "Merriweather", "Lora"].index(content.font), key="edit_font")
            is_published = st.checkbox("Publish", value=content.is_published, key="edit_publish")
            uploaded_files = st.file_uploader("Upload New Media", accept_multiple_files=True, type=[
                                              'png', 'jpg', 'jpeg', 'gif', 'mp4'], key="edit_media")

            media_ids = content.media
            if uploaded_files:
                for file in uploaded_files:
                    media_id = dm.save_media(st.session_state.username, file)
                    media_ids.append(media_id)

            if st.button("Update Blog", type="primary"):
                content.title = bleach.clean(title)
                content.content = bleach.clean(content_text)
                content.tags = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
                content.font = font
                content.media = media_ids
                content.is_published = is_published
                content.updated_at = datetime.utcnow()
                session.commit()
                st.success("Blog updated!")
                st.rerun()

        else:
            title = st.text_input("Title", value=content.title, key="edit_title")
            problem = st.text_area("Problem", value=content.problem, height=150, key="edit_problem")
            solution = st.text_area("Solution", value=content.solution, height=150, key="edit_solution")
            results = st.text_area("Results", value=content.results, height=150, key="edit_results")
            tags = st.text_input("Tags (comma-separated)", value=", ".join(content.tags), key="edit_tags")
            font = st.selectbox("Font Style", ["Inter", "Roboto", "Merriweather", "Lora"],
                                index=["Inter", "Roboto", "Merriweather", "Lora"].index(content.font),
                                key="edit_font")
            is_published = st.checkbox("Publish", value=content.is_published, key="edit_publish")
            uploaded_files = st.file_uploader("Upload New Media", accept_multiple_files=True, type=[
                                              'png', 'jpg', 'jpeg', 'gif', 'mp4'], key="edit_media")

            media_ids = content.media
            if uploaded_files:
                for file in uploaded_files:
                    media_id = dm.save_media(st.session_state.username, file)
                    media_ids.append(media_id)

            if st.button("Update Case Study", type="primary"):
                content.title = bleach.clean(title)
                content.problem = bleach.clean(problem)
                content.solution = bleach.clean(solution)
                content.results = bleach.clean(results)
                content.tags = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
                content.font = font
                content.media = media_ids
                content.is_published = is_published
                content.updated_at = datetime.utcnow()
                session.commit()
                st.success("Case study updated!")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
# Main Function


def get_data_manager():
    return DataManager()


def enhanced_main():
    load_css()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_password = None

    start_time = time.time()
    query_params = st.query_params
    page = query_params.get('page', [''])[0]
    username = query_params.get('username', [''])[0]
    content_type = query_params.get('content_type', [''])[0]
    content_id = query_params.get('content_id', [''])[0]

    if page == 'content' and username and content_type and content_id:
        content_view()
        st.write(f"Content view took {time.time() - start_time:.2f} seconds")
        return

    if not st.session_state.authenticated:
        login_page()
        st.write(f"Login page took {time.time() - start_time:.2f} seconds")
        return

    with st.sidebar:
        st.markdown('<div class="sidebar-title">🌌 GalaxyWrite</div>', unsafe_allow_html=True)
        page_options = [
            "Main Page",
            "Dashboard",
            "Write Blog",
            "Create Case Study",
            "My Content",
            "Templates",
            "Analytics",
            "Search & Filter",
            "Profile Settings",
            "Export Content",
            "Logout"
        ]
        page = st.selectbox("Navigate", options=page_options, key="nav_select")
        st.markdown(
            f'<p class="text-lg font-semibold">👋 Welcome, {st.session_state.username}!</p>', unsafe_allow_html=True)
        dm = get_data_manager()
        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)
        st.markdown(f'<p>📖 <strong>Blogs:</strong> {len(user_blogs)}</p>', unsafe_allow_html=True)
        st.markdown(f'<p>📚 <strong>Case Studies:</strong> {len(user_cases)}</p>', unsafe_allow_html=True)
        total_views = sum(blog.views for blog in user_blogs) + sum(case.views for case in user_cases)
        st.markdown(f'<p>👀 <strong>Total Views:</strong> {total_views}</p>', unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn", type="primary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_password = None
            st.query_params.clear()
            st.rerun()

    if page == "Main Page":
        main_page()
    elif page == "Dashboard":
        dashboard()
    elif page == "Write Blog":
        blog_editor()
    elif page == "Create Case Study":
        case_study_editor()
    elif page == "My Content":
        my_content()
    elif page == "Templates":
        content_templates()
    elif page == "Analytics":
        analytics_dashboard()
    elif page == "Search & Filter":
        content_search_and_filter()
    elif page == "Profile Settings":
        profile_settings()
    elif page == "Export Content":
        export_content()
    elif page == "Edit Content":
        edit_content()
    elif page == "Logout":
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_password = None
        st.query_params.clear()
        st.rerun()

    st.write(f"Page {page} loaded in {time.time() - start_time:.2f} seconds")
    st.markdown("""
    <div class="text-center text-gray-400 py-4">
        <p>GalaxyWrite - Your Cosmic Blogging Platform</p>
        <p>Built with 🌠 by passionate developers</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    dm = get_data_manager()
    enhanced_main()
