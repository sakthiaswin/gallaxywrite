import streamlit as st
import bcrypt
import streamlit_authenticator as stauth
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid
import urllib.parse
import bleach
import base64
import time  # For profiling

# Lazy-load heavy libraries only when needed


def import_pdf_libraries():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    return letter, SimpleDocTemplate, Paragraph, Spacer, getSampleStyleSheet, BytesIO


# Environment variable for Streamlit Cloud URL
APP_URL = "https://gallaxywrite.streamlit.app"


# Page configuration
st.set_page_config(
    page_title="GalaxyWrite",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Cache database engine and session
@st.cache_resource
def get_db_engine():
    engine = create_engine('sqlite:///galaxywrite.db')
    return engine


@st.cache_resource
def get_db_session(_engine):
    Session = sessionmaker(bind=_engine)
    return Session
# Professional UI with Tailwind CSS


def load_css():
    st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(180deg, #0a0a23 0%, #1a1a3d 100%);
            color: #e0e0ff;
        }

        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(10, 10, 35, 0.95);
            backdrop-filter: blur(15px);
            z-index: 50;
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .header h1 {
            font-family: 'Playfair Display', serif;
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #5c5cff, #d400d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
        }

        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 6rem 1rem 2rem;
        }

        .card {
            background: rgba(20, 20, 50, 0.95);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(92, 92, 255, 0.3);
        }

        .case-card {
            background: linear-gradient(135deg, #5c5cff, #d400d4);
            color: white;
        }

        .btn-primary {
            background: linear-gradient(135deg, #5c5cff, #d400d4);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.75rem;
            font-weight: 600;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(92, 92, 255, 0.4);
        }

        .input-field {
            border: 2px solid #2a2a5e;
            border-radius: 0.75rem;
            padding: 0.75rem;
            background: rgba(255, 255, 255, 0.9);
            color: #000;
            transition: border-color 0.3s ease;
        }

        .input-field:focus {
            border-color: #5c5cff;
            box-shadow: 0 0 0 3px rgba(92, 92, 255, 0.2);
        }

        .textarea-field {
            border: 2px solid #2a2a5e;
            border-radius: 0.75rem;
            padding: 0.75rem;
            background: rgba(255, 255, 255, 0.9);
            color: #000;
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
        }

        .sidebar {
            background: linear-gradient(180deg, #0a0a23, #1a1a3d);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
        }

        .sidebar-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.75rem;
            font-weight: 700;
            color: #e0e0ff;
            text-align: center;
            margin-bottom: 2rem;
        }

        .tag {
            display: inline-block;
            background: linear-gradient(135deg, #5c5cff, #d400d4);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.85rem;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .media-preview {
            max-width: 100%;
            border-radius: 0.75rem;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(92, 92, 255, 0.3);
        }

        .comment-section {
            background: rgba(20, 20, 50, 0.95);
            border-radius: 0.75rem;
            padding: 1rem;
            margin-top: 1rem;
        }

        .hero {
            background: linear-gradient(135deg, rgba(92, 92, 255, 0.2), rgba(212, 0, 212, 0.2));
            border-radius: 1rem;
            padding: 3rem;
            text-align: center;
            margin-bottom: 2rem;
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True)


# Database Setup
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    profile = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_user_username', 'username'),)


class Blog(Base):
    __tablename__ = 'blogs'
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    media = Column(JSON, default=[])
    font = Column(String, default='Inter')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    public_link = Column(String)
    __table_args__ = (Index('idx_blog_username', 'username'),)


class CaseStudy(Base):
    __tablename__ = 'case_studies'
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    title = Column(String, nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    results = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    media = Column(JSON, default=[])
    font = Column(String, default='Inter')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    public_link = Column(String)
    __table_args__ = (Index('idx_case_username', 'username'),)


class Media(Base):
    __tablename__ = 'media'
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_media_username', 'username'),)


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(String, primary_key=True)
    content_type = Column(String, nullable=False)
    content_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_comment_content', 'content_type', 'content_id'),)


engine = get_db_engine()
Base.metadata.create_all(engine)
Session = get_db_session(engine)
# Data Manager


class DataManager:
    def __init__(self):
        self.session_factory = Session  # Store the sessionmaker factory

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def register_user(self, username, password, email):
        username = bleach.clean(username)
        email = bleach.clean(email)
        with self.session_factory() as session:
            if session.query(User).filter_by(username=username).first():
                return False
            user = User(
                username=username,
                password=self.hash_password(password),
                email=email,
                profile={
                    'bio': '',
                    'avatar': '',
                    'social_links': {},
                    'preferred_font': 'Inter'
                }
            )
            session.add(user)
            session.commit()
        return True

    def authenticate_user(self, username, password):
        with self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
            if user and self.check_password(password, user.password):
                return True
        return False

    def save_blog(self, username, title, content, tags="", media=None, font='Inter'):
        title = bleach.clean(title)
        content = bleach.clean(content)
        tags = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
        blog_id = str(uuid.uuid4())
        public_link = f"{APP_URL}/blog/{urllib.parse.quote(username)}/{blog_id}"
        with self.session_factory() as session:
            blog = Blog(
                id=blog_id,
                username=username,
                title=title,
                content=content,
                tags=tags,
                media=media or [],
                font=font,
                public_link=public_link
            )
            session.add(blog)
            session.commit()
        return blog_id

    def save_case_study(self, username, title, problem, solution, results, tags="", media=None, font='Inter'):
        title = bleach.clean(title)
        problem = bleach.clean(problem)
        solution = bleach.clean(solution)
        results = bleach.clean(results)
        tags = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
        case_id = str(uuid.uuid4())
        public_link = f"{APP_URL}/case_study/{urllib.parse.quote(username)}/{case_id}"
        with self.session_factory() as session:
            case_study = CaseStudy(
                id=case_id,
                username=username,
                title=title,
                problem=problem,
                solution=solution,
                results=results,
                tags=tags,
                media=media or [],
                font=font,
                public_link=public_link
            )
            session.add(case_study)
            session.commit()
        return case_id

    def save_media(self, username, file):
        file_type = 'image' if file.type.startswith('image') else 'video' if file.type.startswith('video') else 'gif'
        file_content = base64.b64encode(file.read()).decode('utf-8')
        file_id = str(uuid.uuid4())
        with self.session_factory() as session:
            media = Media(
                id=file_id,
                username=username,
                type=file_type,
                content=file_content,
                filename=bleach.clean(file.name)
            )
            session.add(media)
            session.commit()
        return file_id

    def save_comment(self, content_type, content_id, username, comment):
        comment = bleach.clean(comment)
        comment_id = str(uuid.uuid4())
        with self.session_factory() as session:
            comment_obj = Comment(
                id=comment_id,
                content_type=content_type,
                content_id=content_id,
                username=username,
                comment=comment
            )
            session.add(comment_obj)
            session.commit()
        return comment_id

    @st.cache_data(ttl=3600)
    def get_user_blogs(_self, username):
        start_time = time.time()
        with _self.session_factory() as session:
            blogs = session.query(Blog).filter_by(username=username).limit(30).all()
        st.write(f"get_user_blogs took {time.time() - start_time:.2f} seconds")
        return blogs

    @st.cache_data(ttl=3600)
    def get_user_case_studies(_self, username):
        start_time = time.time()
        with _self.session_factory() as session:
            cases = session.query(CaseStudy).filter_by(username=username).limit(30).all()
        st.write(f"get_user_case_studies took {time.time() - start_time:.2f} seconds")
        return cases
    # Cache data queries

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_all_public_content():
        start_time = time.time()
        with Session() as session:
            blogs = session.query(Blog).limit(30).all()  # Changed to 30
            case_studies = session.query(CaseStudy).limit(30).all()  # Changed to 30
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
    def get_media(_self, username, file_id):
        start_time = time.time()
        with _self.session_factory() as session:
            media = session.query(Media).filter_by(username=username, id=file_id).first()
        st.write(f"get_media took {time.time() - start_time:.2f} seconds")
        return media

    @st.cache_data(ttl=3600)
    def get_user_profile(_self, username):
        start_time = time.time()
        with _self.session_factory() as session:
            user = session.query(User).filter_by(username=username).first()
        st.write(f"get_user_profile took {time.time() - start_time:.2f} seconds")
        return user.profile if user else {}

    @st.cache_data(ttl=3600)
    def get_comments(_self, content_type, content_id):
        start_time = time.time()
        with _self.session_factory() as session:
            comments = session.query(Comment).filter_by(content_type=content_type,
                                                        content_id=content_id).limit(30).all()  # Changed to 30
        st.write(f"get_comments took {time.time() - start_time:.2f} seconds")
        return comments


@st.cache_resource
def get_data_manager():
    return DataManager()


dm = get_data_manager()

# PDF Export


def export_to_pdf(content_type, content):
    letter, SimpleDocTemplate, Paragraph, Spacer, getSampleStyleSheet, BytesIO = import_pdf_libraries()
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

    doc.build(story)
    return buffer.getvalue()

# Authentication


def login_page():
    st.markdown("""
    <div class="header">
        <h1>🌌 GalaxyWrite</h1>
    </div>
    <div class="container">
        <div class="card max-w-md mx-auto">
            <h2 class="text-2xl font-semibold mb-6 text-center">Welcome to GalaxyWrite</h2>
    """, unsafe_allow_html=True)

    credentials = {
        'usernames': {
            user.username: {
                'name': user.username,
                'password': user.password,
                'email': user.email
            }
            for user in dm.session_factory.query(User).all()
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="galaxywrite",
        key="abcdef",
        cookie_expiry_days=30
    )

    # Reverted login call to use location parameter
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.success("Login successful!")
        st.rerun()
    elif authentication_status == False:
        st.error("Invalid credentials!")
    elif authentication_status == None:
        st.warning("Please enter your username and password")

    with st.expander("Create an Account", expanded=False):
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
            elif not new_email or '@' not in new_email:
                st.error("Invalid email format!")
            elif dm.register_user(new_username, new_password, new_email):
                st.success("Account created successfully! Please login.")
                credentials['usernames'][new_username] = {
                    'name': new_username,
                    'password': dm.hash_password(new_password),
                    'email': new_email
                }
            else:
                st.error("Username already exists!")

    st.markdown("</div></div>", unsafe_allow_html=True)
# Main Page


def main_page():
    st.markdown("""
    <div class="header">
        <h1>🌌 GalaxyWrite Community</h1>
    </div>
    <div class="container">
        <div class="hero">
            <h2 class="text-3xl font-bold mb-4">Connect Through Cosmic Insights</h2>
            <p class="text-lg text-gray-300 mb-6">
                Discover a universe of blogs and case studies shared by our vibrant community. 
                Share your story, comment, and connect with creators worldwide.
            </p>
            <a href="?page=Write Blog" class="btn-primary">Start Writing</a>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        content_filter = st.selectbox("Content Type", ["All", "Blogs", "Case Studies"], key="content_filter")
    with col2:
        sort_by = st.selectbox("Sort By", ["Recent", "Most Viewed"], key="sort_by")
    with col3:
        search_term = st.text_input("Search", placeholder="Search titles, content...", key="search_main")

    all_content = dm.get_all_public_content()
    filtered_content = all_content

    if content_filter == "Blogs":
        filtered_content = [c for c in all_content if c['type'] == 'blog']
    elif content_filter == "Case Studies":
        filtered_content = [c for c in all_content if c['type'] == 'case_study']

    if search_term:
        filtered_content = [
            c for c in filtered_content
            if search_term.lower() in c['content'].title.lower() or
            search_term.lower() in (
                c['content'].content if c['type'] == 'blog'
                else f"{c['content'].problem} {c['content'].solution} {c['content'].results}"
            ).lower()
        ]

    if sort_by == "Most Viewed":
        filtered_content = sorted(filtered_content, key=lambda x: x['content'].views, reverse=True)

    st.markdown(
        f'<p class="text-lg font-semibold">{len(filtered_content)} Cosmic Creations</p>', unsafe_allow_html=True)

    for item in filtered_content:
        content = item['content']
        rendered_content = content.content[:300] if item['type'] == 'blog' else content.problem[:300]
        for media_id in content.media:
            media = dm.get_media(item['author'], media_id)
            if media:
                if media.type in ['image', 'gif']:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})",
                        f'<img src="data:image/{media.type};base64,{media.content}" class="media-preview">'
                    )
                else:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})",
                        f'<video src="data:video/mp4;base64,{media.content}" class="media-preview" controls></video>'
                    )
        card_class = "card" if item['type'] == 'blog' else "card case-card"
        st.markdown(f'''
        <div class="{card_class}">
            <h3 class="text-xl font-semibold">{'📝' if item['type'] == 'blog' else '🔬'} {content.title}</h3>
            <p class="text-sm text-gray-400">
                By <a href="{APP_URL}/?page=profile&username={urllib.parse.quote(item['author'])}" class="text-blue-300 hover:underline">{item['author']}</a> | 
                {content.created_at.strftime('%Y-%m-%d')} | Views: {content.views}
            </p>
            <p class="text-gray-200 mt-2">{rendered_content}...</p>
            <div class="mt-2">
                {' '.join([f'<span class="tag">{tag}</span>' for tag in content.tags])}
            </div>
            <a href="{content.public_link}" class="text-blue-300 hover:underline mt-2 inline-block">Read More</a>
        </div>
        ''', unsafe_allow_html=True)

        with st.expander("Comments"):
            comments = dm.get_comments(item['type'], content.id)
            for comment in comments:
                st.markdown(f'''
                <div class="comment-section">
                    <p><strong>{comment.username}</strong> ({comment.created_at.strftime('%Y-%m-%d %H:%M')}): {comment.comment}</p>
                </div>
                ''', unsafe_allow_html=True)

            if st.session_state.get('authenticated', False):
                comment_text = st.text_area(
                    f"Add a comment to {content.title}",
                    key=f"comment_{item['type']}_{content.id}",
                    placeholder="Share your thoughts..."
                )
                if st.button("Post Comment", key=f"post_comment_{item['type']}_{content.id}", type="primary"):
                    if comment_text:
                        dm.save_comment(item['type'], content.id, st.session_state.username, comment_text)
                        st.success("Comment posted!")
                        st.rerun()
                    else:
                        st.error("Comment cannot be empty!")

    st.markdown("</div>", unsafe_allow_html=True)

# Dashboard


def dashboard():
    st.markdown("""
    <div class="header">
        <h1>🌌 GalaxyWrite Dashboard</h1>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    user_blogs = dm.get_user_blogs(st.session_state.username)
    user_case_studies = dm.get_user_case_studies(st.session_state.username)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        <div class="card text-center">
            <h3 class="text-2xl font-bold text-blue-400">{len(user_blogs)}</h3>
            <p class="text-gray-400">Blog Posts</p>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="card text-center">
            <h3 class="text-2xl font-bold text-blue-400">{len(user_case_studies)}</h3>
            <p class="text-gray-400">Case Studies</p>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        total_views = sum(blog.views for blog in user_blogs) + sum(case.views for case in user_case_studies)
        st.markdown(f'''
        <div class="card text-center">
            <h3 class="text-2xl font-bold text-blue-400">{total_views}</h3>
            <p class="text-gray-400">Total Views</p>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('<h2 class="text-xl font-semibold mt-8">Your Recent Content</h2>', unsafe_allow_html=True)
    recent_blogs = sorted(user_blogs, key=lambda x: x.created_at, reverse=True)[:3]
    recent_cases = sorted(user_case_studies, key=lambda x: x.created_at, reverse=True)[:3]

    if recent_blogs:
        st.markdown('<p class="text-lg font-medium">Recent Blogs</p>', unsafe_allow_html=True)
        for blog in recent_blogs:
            st.markdown(f'''
            <div class="card">
                <h3 class="text-lg font-semibold">{blog.title}</h3>
                <p class="text-sm text-gray-400">Created: {blog.created_at.strftime('%Y-%m-%d')} | Views: {blog.views}</p>
                <p class="text-gray-200">{blog.content[:200]}...</p>
            </div>
            ''', unsafe_allow_html=True)

    if recent_cases:
        st.markdown('<p class="text-lg font-medium">Recent Case Studies</p>', unsafe_allow_html=True)
        for case in recent_cases:
            st.markdown(f'''
            <div class="card case-card">
                <h3 class="text-lg font-semibold">{case.title}</h3>
                <p class="text-sm text-gray-200">Created: {case.created_at.strftime('%Y-%m-%d')} | Views: {case.views}</p>
                <p class="text-gray-100">{case.problem[:200]}...</p>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Blog Editor


def blog_editor():
    st.markdown("""
    <div class="header">
        <h1>✍️ Blog Editor</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    title = st.text_input("Blog Title", value=st.session_state.get('template_title', ''),
                          placeholder="Enter an engaging title...", key="blog_title")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        tags = st.text_input("Tags (comma-separated)", placeholder="space, tech, science", key="blog_tags")
    with col2:
        font = st.selectbox("Font", [
            'Inter', 'Playfair Display', 'Arial', 'Times New Roman', 'Courier New',
            'Roboto', 'Open Sans', 'Lora', 'Poppins'
        ], key="blog_font")
    with col3:
        publish_date = st.date_input("Publish Date", datetime.now().date(), key="blog_date")

    st.markdown('<h3 class="text-lg font-semibold mt-6">Media Upload</h3>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Image, GIF, or Video", type=[
                                     'png', 'jpg', 'jpeg', 'gif', 'mp4'], key="blog_media")
    media_ids = []
    if uploaded_file:
        media_id = dm.save_media(st.session_state.username, uploaded_file)
        media_ids.append(media_id)
        media = dm.get_media(st.session_state.username, media_id)
        if media.type == 'image':
            st.image(f"data:image/png;base64,{media.content}", caption=media.filename, use_column_width=True)
        elif media.type == 'gif':
            st.image(f"data:image/gif;base64,{media.content}", caption=media.filename, use_column_width=True)
        else:
            st.video(f"data:video/mp4;base64,{media.content}")

    st.markdown('<h3 class="text-lg font-semibold mt-6">Formatting Tools</h3>', unsafe_allow_html=True)
    cols = st.columns(8)
    formatting = [
        ("**Bold**", "Use **text** for bold"),
        ("*Italic*", "Use *text* for italic"),
        ("# Header", "Use #, ##, ### for headers"),
        ("🔗 Link", "Use [text](url) for links"),
        ("📷 Media", "Use ![media](media_id) for media"),
        ("📋 List", "Use - or * for bullets, 1. for numbered"),
        ("💬 Quote", "Use > text for quotes"),
        ("📑 Code", "Use ```language\ncode\n``` for code")
    ]
    for i, (label, info) in enumerate(formatting):
        with cols[i]:
            if st.button(label, key=f"format_{i}"):
                st.info(info)

    st.markdown('<h3 class="text-lg font-semibold mt-6">Content</h3>', unsafe_allow_html=True)
    content = st.text_area(
        "Write your blog content here...",
        value=st.session_state.get('template_content', ''),
        height=400,
        placeholder="Start writing your stellar blog post...\n\nUse Markdown formatting:\n- **bold** for bold text\n- *italic* for italic text\n- #, ##, ### for headers\n- [link](url) for links\n- ![media](media_id) for embedded media\n- - or * for bullet lists\n- 1. for numbered lists\n- > for blockquotes\n- ```language\ncode\n``` for code blocks",
        key="blog_content"
    )

    if content:
        st.markdown('<h3 class="text-lg font-semibold mt-6">Preview</h3>', unsafe_allow_html=True)
        rendered_content = content
        for media_id in media_ids:
            media = dm.get_media(st.session_state.username, media_id)
            if media:
                if media.type in ['image', 'gif']:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<img src="data:image/{media.type};base64,{media.content}" class="media-preview">')
                else:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media.content}" class="media-preview" controls></video>')
        st.markdown(rendered_content, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Draft", key="save_draft", type="primary"):
            if title and content:
                blog_id = dm.save_blog(st.session_state.username, title, content, tags, media_ids, font)
                st.success(f"Blog saved successfully! ID: {blog_id}")
            else:
                st.error("Please fill in title and content!")
    with col2:
        if st.button("🚀 Publish", key="publish_blog", type="primary"):
            if title and content:
                blog_id = dm.save_blog(st.session_state.username, title, content, tags, media_ids, font)
                blog = dm.session_factory.query(Blog).filter_by(id=blog_id).first()
                st.success(f"Blog published successfully! ID: {blog_id}")
                st.markdown(
                    f'<a href="{blog.public_link}" class="text-blue-300 hover:underline">Share your blog</a>', unsafe_allow_html=True)
                st.balloons()
            else:
                st.error("Please fill in title and content!")
    with col3:
        if st.button("📄 Export PDF", key="export_pdf", type="primary"):
            if title and content:
                blog = Blog(title=title, content=content)
                pdf_data = export_to_pdf('blog', blog)
                st.download_button(
                    "Download PDF",
                    pdf_data,
                    file_name=f"{title}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.error("Please fill in title and content!")

    st.markdown("</div></div>", unsafe_allow_html=True)

# Case Study Editor


def case_study_editor():
    formatting = [
        ("**", "Bold text"),
        ("*", "Italic text"),
        ("#", "Heading 1"),
        ("##", "Heading 2"),
        ("- ", "Bullet point"),
        ("> ", "Blockquote"),
        ("```", "Code block"),
        ("---", "Horizontal line")
    ]

    st.markdown("""
    <div class="header">
        <h1>🔬 Case Study Editor</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    title = st.text_input("Case Study Title", value=st.session_state.get(
        'case_template_title', ''), placeholder="Enter case study title...", key="case_title")
    col1, col2 = st.columns([3, 1])
    with col1:
        tags = st.text_input("Tags (comma-separated)", placeholder="business, strategy, analysis", key="case_tags")
    with col2:
        font = st.selectbox("Font", [
            'Inter', 'Playfair Display', 'Arial', 'Times New Roman', 'Courier New',
            'Roboto', 'Open Sans', 'Lora', 'Poppins'
        ], key="case_font")

    st.markdown('<h3 class="text-lg font-semibold mt-6">Media Upload</h3>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Image, GIF, or Video", type=[
                                     'png', 'jpg', 'jpeg', 'gif', 'mp4'], key="case_media")
    media_ids = []
    if uploaded_file:
        media_id = dm.save_media(st.session_state.username, uploaded_file)
        media_ids.append(media_id)
        media = dm.get_media(st.session_state.username, media_id)
        if media.type == 'image':
            st.image(f"data:image/png;base64,{media.content}", caption=media.filename, use_column_width=True)
        elif media.type == 'gif':
            st.image(f"data:image/gif;base64,{media.content}", caption=media.filename, use_column_width=True)
        else:
            st.video(f"data:video/mp4;base64,{media.content}")

    st.markdown('<h3 class="text-lg font-semibold mt-6">Formatting Tools</h3>', unsafe_allow_html=True)
    cols = st.columns(8)
    for i, (label, info) in enumerate(formatting):
        with cols[i]:
            if st.button(label, key=f"case_format_{i}"):
                st.info(info)

    st.markdown('<h3 class="text-lg font-semibold mt-6">Problem Statement</h3>', unsafe_allow_html=True)
    problem = st.text_area(
        "Describe the problem or challenge",
        value=st.session_state.get('case_template_problem', ''),
        height=150,
        placeholder="What problem were you trying to solve? Provide context and background...\n\nUse Markdown formatting...",
        key="case_problem"
    )

    st.markdown('<h3 class="text-lg font-semibold mt-6">Solution Approach</h3>', unsafe_allow_html=True)
    solution = st.text_area(
        "Explain your solution methodology",
        value=st.session_state.get('case_template_solution', ''),
        height=200,
        placeholder="How did you approach the problem? What methods, tools, or strategies did you use?\n\nUse Markdown formatting...",
        key="case_solution"
    )

    st.markdown('<h3 class="text-lg font-semibold mt-6">Results & Outcomes</h3>', unsafe_allow_html=True)
    results = st.text_area(
        "Share the results and impact",
        value=st.session_state.get('case_template_results', ''),
        height=150,
        placeholder="What were the outcomes? Include metrics, feedback, and lessons learned...\n\nUse Markdown formatting...",
        key="case_results"
    )

    if problem or solution or results:
        st.markdown('<h3 class="text-lg font-semibold mt-6">Preview</h3>', unsafe_allow_html=True)
        rendered_content = ""
        if problem:
            rendered_content += f"**Problem:** {problem}\n\n"
        if solution:
            rendered_content += f"**Solution:** {solution}\n\n"
        if results:
            rendered_content += f"**Results:** {results}\n\n"
        for media_id in media_ids:
            media = dm.get_media(st.session_state.username, media_id)
            if media:
                if media.type in ['image', 'gif']:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<img src="data:image/{media.type};base64,{media.content}" class="media-preview">')
                else:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media.content}" class="media-preview" controls></video>')
        st.markdown(rendered_content, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Draft", key="save_case_draft", type="primary"):
            if title and problem and solution:
                case_id = dm.save_case_study(st.session_state.username, title, problem,
                                             solution, results, tags, media_ids, font)
                st.success(f"Case study saved successfully! ID: {case_id}")
            else:
                st.error("Please fill in title, problem, and solution!")
    with col2:
        if st.button("🚀 Publish", key="publish_case", type="primary"):
            if title and problem and solution:
                case_id = dm.save_case_study(st.session_state.username, title, problem,
                                             solution, results, tags, media_ids, font)
                case = dm.session_factory.query(CaseStudy).filter_by(id=case_id).first()
                st.success(f"Case study published successfully! ID: {case_id}")
                st.markdown(
                    f'<a href="{case.public_link}" class="text-blue-300 hover:underline">Share your case study</a>', unsafe_allow_html=True)
                st.balloons()
            else:
                st.error("Please fill in title, problem, and solution!")
    with col3:
        if st.button("📄 Export PDF", key="export_case_pdf", type="primary"):
            if title and problem and solution:
                case = CaseStudy(title=title, problem=problem, solution=solution, results=results)
                pdf_data = export_to_pdf('case_study', case)
                st.download_button(
                    "Download PDF",
                    pdf_data,
                    file_name=f"{title}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.error("Please fill in title, problem, and solution!")

    st.markdown("</div></div>", unsafe_allow_html=True)
# My Content


def my_content():
    st.markdown("""
    <div class="header">
        <h1>📚 My Content</h1>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["My Blogs", "My Case Studies"])
    with tab1:
        blogs = dm.get_user_blogs(st.session_state.username)
        if blogs:
            for blog in reversed(blogs):
                with st.expander(f"📝 {blog.title} (ID: {blog.id})"):
                    st.markdown(f"""
                    <p class="text-sm text-gray-400">
                        <strong>Created:</strong> {blog.created_at.strftime('%Y-%m-%d %H:%M')} | 
                        <strong>Tags:</strong> {', '.join(blog.tags)} | 
                        <strong>Views:</strong> {blog.views} | 
                        <strong>Font:</strong> {blog.font}
                    </p>
                    <p><a href="{blog.public_link}" class="text-blue-300 hover:underline">Public Link</a></p>
                    <hr class="border-gray-600">
                    """, unsafe_allow_html=True)
                    rendered_content = blog.content
                    for media_id in blog.media:
                        media = dm.get_media(st.session_state.username, media_id)
                        if media:
                            if media.type in ['image', 'gif']:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<img src="data:image/{media.type};base64,{media.content}" class="media-preview">')
                            else:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media.content}" class="media-preview" controls></video>')
                    st.markdown(rendered_content, unsafe_allow_html=True)
                    if st.button("📄 Export PDF", key=f"export_blog_{blog.id}", type="primary"):
                        pdf_data = export_to_pdf('blog', blog)
                        st.download_button(
                            "Download PDF",
                            pdf_data,
                            file_name=f"{blog.title}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
        else:
            st.info("No blogs yet. Create your first blog post!")

    with tab2:
        case_studies = dm.get_user_case_studies(st.session_state.username)
        if case_studies:
            for case in reversed(case_studies):
                with st.expander(f"🔬 {case.title} (ID: {case.id})"):
                    st.markdown(f"""
                    <p class="text-sm text-gray-400">
                        <strong>Created:</strong> {case.created_at.strftime('%Y-%m-%d %H:%M')} | 
                        <strong>Tags:</strong> {', '.join(case.tags)} | 
                        <strong>Views:</strong> {case.views} | 
                        <strong>Font:</strong> {case.font}
                    </p>
                    <p><a href="{case.public_link}" class="text-blue-300 hover:underline">Public Link</a></p>
                    <hr class="border-gray-600">
                    """, unsafe_allow_html=True)
                    rendered_content = f"**Problem:** {case.problem}\n\n**Solution:** {case.solution}\n\n**Results:** {case.results}"
                    for media_id in case.media:
                        media = dm.get_media(st.session_state.username, media_id)
                        if media:
                            if media.type in ['image', 'gif']:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<img src="data:image/{media.type};base64,{media.content}" class="media-preview">')
                            else:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media.content}" class="media-preview" controls></video>')
                    st.markdown(rendered_content, unsafe_allow_html=True)
                    if st.button("📄 Export PDF", key=f"export_case_{case.id}", type="primary"):
                        pdf_data = export_to_pdf('case_study', case)
                        st.download_button(
                            "Download PDF",
                            pdf_data,
                            file_name=f"{case.title}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
        else:
            st.info("No case studies yet. Create your first case study!")

    st.markdown("</div>", unsafe_allow_html=True)

# Profile View


def profile_view(username):
    st.markdown(f"""
    <div class="header">
        <h1>👤 {username}'s Profile</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    profile = dm.get_user_profile(username)
    st.markdown(f"""
    <h3 class="text-lg font-semibold">Bio</h3>
    <p class="text-gray-200">{profile.get('bio', 'No bio available.')}</p>
    """, unsafe_allow_html=True)
    social_links = profile.get('social_links', {})
    if social_links:
        st.markdown('<h3 class="text-lg font-semibold mt-4">Connect</h3>', unsafe_allow_html=True)
        for platform, link in social_links.items():
            if link:
                st.markdown(
                    f'<p>- <a href="{link}" class="text-blue-300 hover:underline">{platform.capitalize()}</a></p>', unsafe_allow_html=True)

    st.markdown('<h3 class="text-lg font-semibold mt-6">Their Content</h3>', unsafe_allow_html=True)
    blogs = dm.get_user_blogs(username)
    case_studies = dm.get_user_case_studies(username)

    if blogs:
        st.markdown('<p class="text-md font-medium">Blogs</p>', unsafe_allow_html=True)
        for blog in blogs:
            st.markdown(f'<p>- {blog.title} ({blog.created_at.strftime("%Y-%m-%d")})</p>', unsafe_allow_html=True)

    if case_studies:
        st.markdown('<p class="text-md font-medium mt-4">Case Studies</p>', unsafe_allow_html=True)
        for case in case_studies:
            st.markdown(f'<p>- {case.title} ({case.created_at.strftime("%Y-%m-%d")})</p>', unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

# Profile Settings


def profile_settings():
    st.markdown("""
    <div class="header">
        <h1>👤 Profile Settings</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    profile = dm.get_user_profile(st.session_state.username)
    bio = st.text_area("Bio", value=profile.get('bio', ''),
                       placeholder="Tell us about your cosmic journey...", key="profile_bio")
    preferred_font = st.selectbox("Preferred Font", [
        'Inter', 'Playfair Display', 'Arial', 'Times New Roman', 'Courier New',
        'Roboto', 'Open Sans', 'Lora', 'Poppins'
    ], index=0 if profile.get('preferred_font') == 'Inter' else 1, key="profile_font")

    col1, col2 = st.columns(2)
    with col1:
        twitter = st.text_input("Twitter", value=profile.get('social_links', {}).get(
            'twitter', ''), placeholder="@username", key="twitter")
    with col2:
        linkedin = st.text_input("LinkedIn", value=profile.get('social_links', {}).get(
            'linkedin', ''), placeholder="linkedin.com/in/username", key="linkedin")

    github = st.text_input("GitHub", value=profile.get('social_links', {}).get(
        'github', ''), placeholder="github.com/username", key="github")
    website = st.text_input("Website", value=profile.get('social_links', {}).get(
        'website', ''), placeholder="https://yourwebsite.com", key="website")

    if st.button("💾 Save Profile", key="save_profile", type="primary"):
        user = dm.session_factory.query(User).filter_by(username=st.session_state.username).first()
        user.profile = {
            'bio': bleach.clean(bio),
            'social_links': {
                'twitter': bleach.clean(twitter),
                'linkedin': bleach.clean(linkedin),
                'github': bleach.clean(github),
                'website': bleach.clean(website)
            },
            'preferred_font': bleach.clean(preferred_font)
        }
        dm.session_factory.commit()
        st.success("Profile updated successfully!")

    st.markdown('<h3 class="text-lg font-semibold mt-6">Security</h3>', unsafe_allow_html=True)
    new_password = st.text_input("New Password", type="password", key="new_password")
    confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")

    if st.button("🔒 Update Password", key="update_password", type="primary"):
        if new_password and new_password == confirm_password and len(new_password) >= 8:
            user = dm.session_factory.query(User).filter_by(username=st.session_state.username).first()
            user.password = dm.hash_password(new_password)
            dm.session_factory.commit()
            st.success("Password updated successfully!")
        elif new_password != confirm_password:
            st.error("Passwords don't match!")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters!")

    st.markdown("</div></div>", unsafe_allow_html=True)

# Content Templates


def content_templates():
    st.markdown("""
    <div class="header">
        <h1>📋 Content Templates</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    template_type = st.selectbox("Choose template type", [
                                 "Blog Templates", "Case Study Templates"], key="template_type")
    templates = {
        "Blog Templates": {
            "How-To Guide": {
                "title": "How to [Do Something]: A Complete Guide",
                "content": """# Introduction
Briefly explain what this guide covers and why it's useful.

## What You'll Need
- List any prerequisites
- Tools or materials needed

## Step-by-Step Instructions

### Step 1: [First Step]
Detailed explanation of the first step.

### Step 2: [Second Step]
Detailed explanation of the second step.

## Conclusion
Summarize what was accomplished and next steps.

## Additional Resources
- Link to related articles
- Useful tools or websites"""
            },
            "Product Review": {
                "title": "[Product Name] Review: Is It Worth It?",
                "content": """# Introduction
Brief overview of the product and why you're reviewing it.

## Pros
- List the positive aspects
- What works well
- Value proposition

## Cons
- Areas for improvement
- Limitations or drawbacks

## My Experience
Share your personal experience using the product.

## Final Verdict
Overall rating and recommendation.

## Alternatives
Mention similar products worth considering."""
            }
        },
        "Case Study Templates": {
            "Business Case Study": {
                "title": "[Company/Project Name]: [Brief Description of Challenge]",
                "problem": """Describe the business challenge or problem:
- What was the situation?
- What were the key pain points?
- What was at stake?
- Who were the stakeholders involved?""",
                "solution": """Explain your approach:
- What methodology did you use?
- What tools or frameworks were applied?
- What was your role in the solution?
- How did you implement the solution?""",
                "results": """Share the outcomes:
- Quantifiable results (metrics, percentages, cost savings)
- Qualitative improvements
- Stakeholder feedback
- Lessons learned
- Long-term impact"""
            },
            "Technical Case Study": {
                "title": "[Project Name]: [Technology/Framework] Implementation",
                "problem": """Technical challenge overview:
- What system or process needed improvement?
- What were the technical constraints?
- What were the performance requirements?
- What was the existing architecture?""",
                "solution": """Technical approach:
- Architecture decisions and rationale
- Technologies and tools selected
- Implementation strategy
- Code examples or diagrams (if applicable)""",
                "results": """Technical outcomes:
- Performance improvements
- System reliability metrics
- Scalability achievements
- Code quality measures
- User adoption and feedback"""
            }
        }
    }

    selected_template = st.selectbox("Select a template", list(
        templates[template_type].keys()), key="selected_template")
    if st.button("📋 Use This Template", key="use_template", type="primary"):
        template = templates[template_type][selected_template]
        if template_type == "Blog Templates":
            st.session_state.template_title = template["title"]
            st.session_state.template_content = template["content"]
            st.success("Template loaded! Go to 'Write Blog' to use it.")
        else:
            st.session_state.case_template_title = template["title"]
            st.session_state.case_template_problem = template["problem"]
            st.session_state.case_template_solution = template["solution"]
            st.session_state.case_template_results = template["results"]
            st.success("Template loaded! Go to 'Create Case Study' to use it.")

    st.markdown('<h3 class="text-lg font-semibold mt-6">Template Preview</h3>', unsafe_allow_html=True)
    template = templates[template_type][selected_template]
    if template_type == "Blog Templates":
        st.markdown(f'<p class="font-semibold">Title:</p><p>{template["title"]}</p>', unsafe_allow_html=True)
        st.markdown('<p class="font-semibold mt-4">Content:</p>', unsafe_allow_html=True)
        st.code(template['content'])
    else:
        st.markdown(f'<p class="font-semibold">Title:</p><p>{template["title"]}</p>', unsafe_allow_html=True)
        st.markdown('<p class="font-semibold mt-4">Problem:</p>', unsafe_allow_html=True)
        st.code(template['problem'])
        st.markdown('<p class="font-semibold mt-4">Solution:</p>', unsafe_allow_html=True)
        st.code(template['solution'])
        st.markdown('<p class="font-semibold mt-4">Results:</p>', unsafe_allow_html=True)
        st.code(template['results'])

    st.markdown("</div></div>", unsafe_allow_html=True)

# Export Content


def export_content():
    import json

    st.markdown("""
    <div class="header">
        <h1>📤 Export Content</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    export_format = st.selectbox("Choose export format", ["JSON", "Markdown", "PDF"], key="export_format")
    content_type = st.selectbox(
        "Content type", ["Blogs Only", "Case Studies Only", "All Content"], key="export_content_type")

    if st.button("Generate Export", key="generate_export", type="primary"):
        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)
        export_data = {}
        if content_type in ["Blogs Only", "All Content"]:
            export_data['blogs'] = [{
                'id': blog.id, 'title': blog.title, 'content': blog.content,
                'tags': blog.tags, 'created_at': blog.created_at.isoformat(),
                'views': blog.views, 'font': blog.font
            } for blog in user_blogs]
        if content_type in ["Case Studies Only", "All Content"]:
            export_data['case_studies'] = [{
                'id': case.id, 'title': case.title, 'problem': case.problem,
                'solution': case.solution, 'results': case.results,
                'tags': case.tags, 'created_at': case.created_at.isoformat(),
                'views': case.views, 'font': case.font
            } for case in user_cases]

        if export_format == "JSON":
            st.download_button(
                "Download JSON",
                json.dumps(export_data, indent=2),
                file_name=f"{st.session_state.username}_content.json",
                mime="application/json",
                type="primary"
            )
        elif export_format == "Markdown":
            md_content = "# My Content Export\n\n"
            for blog in export_data.get('blogs', []):
                md_content += f"## {blog['title']}\n\n{blog['content']}\n\n---\n\n"
            for case in export_data.get('case_studies', []):
                md_content += f"## {case['title']}\n\n**Problem:** {case['problem']}\n\n**Solution:** {case['solution']}\n\n**Results:** {case['results']}\n\n---\n\n"
            st.download_button(
                "Download Markdown",
                md_content,
                file_name=f"{st.session_state.username}_content.md",
                mime="text/markdown",
                type="primary"
            )
        elif export_format == "PDF":
            for blog in export_data.get('blogs', []):
                pdf_data = export_to_pdf('blog', Blog(**blog))
                st.download_button(
                    f"Download {blog['title']} PDF",
                    pdf_data,
                    file_name=f"{blog['title']}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            for case in export_data.get('case_studies', []):
                pdf_data = export_to_pdf('case_study', CaseStudy(**case))
                st.download_button(
                    f"Download {case['title']} PDF",
                    pdf_data,
                    file_name=f"{case['title']}.pdf",
                    mime="application/pdf",
                    type="primary"
                )

    st.markdown("</div></div>", unsafe_allow_html=True)
# Analytics Dashboard


def analytics_dashboard():
    st.markdown("""
    <div class="header">
        <h1>📊 Content Analytics</h1>
    </div>
    <div class="container">
    """, unsafe_allow_html=True)

    user_blogs = dm.get_user_blogs(st.session_state.username)
    user_cases = dm.get_user_case_studies(st.session_state.username)

    if not user_blogs and not user_cases:
        st.info("No content available for analytics.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_words = sum(len(blog.content.split()) for blog in user_blogs)
        total_words += sum(len(f"{case.problem} {case.solution} {case.results}".split()) for case in user_cases)
        st.markdown(
            f'<div class="card text-center"><h3 class="text-2xl font-bold text-blue-400">{total_words:,}</h3><p class="text-gray-400">Total Words</p></div>', unsafe_allow_html=True)
    with col2:
        avg_blog_length = sum(len(blog.content.split()) for blog in user_blogs) / len(user_blogs) if user_blogs else 0
        st.markdown(
            f'<div class="card text-center"><h3 class="text-2xl font-bold text-blue-400">{int(avg_blog_length)}</h3><p class="text-gray-400">Avg Blog Length</p></div>', unsafe_allow_html=True)
    with col3:
        total_tags = set()
        for blog in user_blogs:
            total_tags.update(blog.tags)
        for case in user_cases:
            total_tags.update(case.tags)
        st.markdown(
            f'<div class="card text-center"><h3 class="text-2xl font-bold text-blue-400">{len(total_tags)}</h3><p class="text-gray-400">Unique Tags</p></div>', unsafe_allow_html=True)
    with col4:
        total_views = sum(blog.views for blog in user_blogs) + sum(case.views for case in user_cases)
        st.markdown(
            f'<div class="card text-center"><h3 class="text-2xl font-bold text-blue-400">{total_views}</h3><p class="text-gray-400">Total Views</p></div>', unsafe_allow_html=True)

    st.markdown('<h2 class="text-xl font-semibold mt-8">Publishing Activity</h2>', unsafe_allow_html=True)
    dates = [blog.created_at.strftime('%Y-%m-%d') for blog in user_blogs] + \
        [case.created_at.strftime('%Y-%m-%d') for case in user_cases]
    date_counts = {}
    for date in dates:
        date_counts[date] = date_counts.get(date, 0) + 1
    if date_counts:
        st.bar_chart(date_counts)

    st.markdown("</div>", unsafe_allow_html=True)

# Search and Filter


def content_search_and_filter():
    st.markdown("""
    <div class="header">
        <h1>🔍 Advanced Search</h1>
    </div>
    <div class="container">
        <div class="card">
    """, unsafe_allow_html=True)

    search_query = st.text_input("Search your content", placeholder="Enter keywords...", key="search_query")
    col1, col2, col3 = st.columns(3)
    with col1:
        content_type_filter = st.selectbox("Content Type", ["All", "Blogs", "Case Studies"], key="content_type_filter")
    with col2:
        date_from = st.date_input("From Date", datetime(2020, 1, 1).date(), key="date_from")
    with col3:
        date_to = st.date_input("To Date", datetime.now().date(), key="date_to")

    tag_filter = st.text_input("Filter by tags (comma-separated)", placeholder="tech, business", key="tag_filter")

    if st.button("🔍 Search", key="search_btn", type="primary"):
        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)
        results = []

        if content_type_filter in ["All", "Blogs"]:
            for blog in user_blogs:
                if search_query.lower() in blog.title.lower() or search_query.lower() in blog.content.lower():
                    blog_date = blog.created_at.date()
                    if date_from <= blog_date <= date_to:
                        if not tag_filter or any(tag.strip().lower() in [t.lower() for t in blog.tags] for tag in tag_filter.split(',')):
                            results.append(('blog', blog))

        if content_type_filter in ["All", "Case Studies"]:
            for case in user_cases:
                search_text = f"{case.title} {case.problem} {case.solution} {case.results}"
                if search_query.lower() in search_text.lower():
                    case_date = case.created_at.date()
                    if date_from <= case_date <= date_to:
                        if not tag_filter or any(tag.strip().lower() in [t.lower() for t in case.tags] for tag in tag_filter.split(',')):
                            results.append(('case_study', case))

        st.markdown(f'<p class="text-lg font-semibold">Found {len(results)} results:</p>', unsafe_allow_html=True)
        for content_type, content in results:
            if content_type == 'blog':
                st.markdown(
                    f'<p class="font-semibold">📝 {content.title}</p><p class="text-sm text-gray-400">{content.created_at.strftime("%Y-%m-%d")}</p><p>{content.content[:200]}...</p><hr class="border-gray-600">', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<p class="font-semibold">🔬 {content.title}</p><p class="text-sm text-gray-400">{content.created_at.strftime("%Y-%m-%d")}</p><p>{content.problem[:200]}...</p><hr class="border-gray-600">', unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

# Main Function


def enhanced_main():
    load_css()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    start_time = time.time()
    page = st.query_params.get('page', ['main'])[0]
    username = st.query_params.get('username', [''])[0]

    if page == 'profile' and username:
        profile_view(username)
        st.write(f"Profile page loaded in {time.time() - start_time:.2f} seconds")
        return

    if not st.session_state.authenticated:
        login_page()
        st.write(f"Login page loaded in {time.time() - start_time:.2f} seconds")
        return

    with st.sidebar:
        st.markdown('<div class="sidebar-title">🌌 Galaxy Blog</div>',
                    unsafe_allow_html=True)
        page = st.selectbox(
            "Navigate",
            ["Main Page", "Write Blog", "Create Case Study", "Logout"],
            key="nav_select"
        )
        st.markdown(
            f'<p class="text-lg font-semibold">👋 Welcome, {st.session_state.username}!</p>',
            unsafe_allow_html=True)
        dm = get_data_manager()
        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)
        st.markdown(f'<p>📖 <strong>Blogs:</strong> {len(user_blogs)}</p>',
                    unsafe_allow_html=True)
        st.markdown(f'<p>📚 <strong>Case Studies:</strong> {len(user_cases)}</p>',
                    unsafe_allow_html=True)
        total_views = sum(blog.views for blog in user_blogs) + sum(
            case.views for case in user_cases)
        st.markdown(f'<p>👀 <strong>Total Views:</strong> {total_views}</p>',
                    unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn", type="primary"):
            st.session_state.authenticated = False
            st.session_state.username = None
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
    elif page == "Logout":
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    st.markdown("""
    <div class="text-center text-gray-400 py-4">
        <p>GalaxyWrite - Your Cosmic Blogging Platform</p>
        <p>Built with 🌠 by passionate creators</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    enhanced_main()
