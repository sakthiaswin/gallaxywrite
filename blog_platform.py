import streamlit as st
import hashlib
import json
import os
from datetime import datetime
import re
from typing import Dict, List, Optional
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import uuid
import urllib.parse

# Page configuration
st.set_page_config(
    page_title="GalaxyWrite",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for space and galaxy theme


def load_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&family=Roboto:wght@300;400;700&family=Open+Sans:wght@300;400;700&family=Lora:wght@400;700&family=Poppins:wght@300;400;700&display=swap');

    /* Global Styles */
    .stApp {
        background: linear-gradient(180deg, #0a0a23 0%, #1a1a3d 100%);
        font-family: 'Montserrat', sans-serif;
        color: #e0e0ff;
    }

    /* Fixed Header */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: rgba(10, 10, 35, 0.95);
        backdrop-filter: blur(15px);
        padding: 1rem 2rem;
        z-index: 1000;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }

    .fixed-header .app-header {
        margin: 0;
        font-size: 2.5rem;
        background: linear-gradient(135deg, #5c5cff 0%, #d400d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        text-shadow: 0 2px 8px rgba(92, 92, 255, 0.3);
    }

    /* Content padding to avoid overlap with fixed header */
    .main-container {
        padding-top: 80px;
        background: rgba(10, 10, 35, 0.9);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Animated background with stars and asteroids */
    body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: url('https://www.transparenttextures.com/patterns/stardust.png');
        opacity: 0.2;
        z-index: -1;
        animation: moveStars 100s linear infinite;
    }

    @keyframes moveStars {
        0% { transform: translateY(0); }
        100% { transform: translateY(-1000px); }
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #5c5cff 0%, #d400d4 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(92, 92, 255, 0.4);
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(92, 92, 255, 0.6);
    }

    /* Input Styles */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #2a2a5e;
        background: rgba(255, 255, 255, 0.9);
        color: #000000;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #5c5cff;
        box-shadow: 0 0 0 3px rgba(92, 92, 255, 0.2);
    }

    /* Text Area Styles */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #2a2a5e;
        background: rgba(255, 255, 255, 0.9);
        color: #000000;
        font-family: 'Montserrat', sans-serif;
        line-height: 1.7;
    }

    .stTextArea textarea:focus {
        border-color: #5c5cff;
        box-shadow: 0 0 0 3px rgba(92, 92, 255, 0.2);
    }

    /* Sidebar Styles */
    .css-1d391kg {
        background: linear-gradient(180deg, #0a0a23 0%, #1a1a3d 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    .sidebar-title {
        color: #e0e0ff;
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        text-align: center;
        font-family: 'Playfair Display', serif;
    }

    /* Blog Card Styles */
    .blog-card {
        background: rgba(20, 20, 50, 0.95);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .blog-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(92, 92, 255, 0.3);
    }

    .blog-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, #5c5cff 0%, #d400d4 100%);
    }

    .blog-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #e0e0ff;
        margin-bottom: 0.5rem;
    }

    .blog-meta {
        color: #a0a0cc;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    .blog-content {
        color: #d0d0ff;
        line-height: 1.7;
    }

    /* Case Study Styles */
    .case-study-card {
        background: linear-gradient(135deg, #5c5cff 0%, #d400d4 100%);
        color: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(92, 92, 255, 0.4);
        transition: all 0.3s ease;
    }

    .case-study-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 25px 50px rgba(92, 92, 255, 0.5);
    }

    /* Editor Styles */
    .editor-container {
        background: rgba(20, 20, 50, 0.95);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin: 1rem 0;
    }

    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #00ddeb 0%, #92fe9d 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
    }

    .stError {
        background: linear-gradient(135deg, #fc466b 0%, #3f5efb 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
    }

    /* Dashboard Stats */
    .stat-card {
        background: rgba(20, 20, 50, 0.95);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        border-top: 4px solid #5c5cff;
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #5c5cff;
        margin-bottom: 0.5rem;
    }

    .stat-label {
        color: #a0a0cc;
        font-size: 1rem;
        font-weight: 500;
    }

    /* Tags */
    .tag {
        display: inline-block;
        background: linear-gradient(135deg, #5c5cff 0%, #d400d4 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Loading Animation */
    .loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(92, 92, 255, 0.3);
        border-radius: 50%;
        border-top-color: #5c5cff;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* Media Preview */
    .media-preview {
        max-width: 100%;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(92, 92, 255, 0.3);
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .fixed-header .app-header {
            font-size: 2rem;
        }

        .main-container {
            margin: 0.5rem;
            padding: 1rem;
            padding-top: 70px;
        }

        .blog-card, .case-study-card {
            padding: 1.5rem;
        }

        .login-container {
            padding: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Data storage class with enhanced security


class DataManager:
    def __init__(self):
        self.users_file = "users.json"
        self.blogs_file = "blogs.json"
        self.case_studies_file = "case_studies.json"
        self.media_file = "media.json"
        self.ensure_files_exist()

    def ensure_files_exist(self):
        for file in [self.users_file, self.blogs_file, self.case_studies_file, self.media_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)

    def load_data(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_data(self, data, file_path):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, email):
        users = self.load_data(self.users_file)
        if username in users:
            return False

        users[username] = {
            'password': self.hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'profile': {
                'bio': '',
                'avatar': '',
                'social_links': {},
                'preferred_font': 'Montserrat'
            }
        }
        self.save_data(users, self.users_file)
        return True

    def authenticate_user(self, username, password):
        users = self.load_data(self.users_file)
        if username in users:
            return users[username]['password'] == self.hash_password(password)
        return False

    def save_blog(self, username, title, content, tags="", media=None, font='Montserrat'):
        blogs = self.load_data(self.blogs_file)
        if username not in blogs:
            blogs[username] = []

        blog_id = str(uuid.uuid4())
        blog = {
            'id': blog_id,
            'title': title,
            'content': content,
            'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'views': 0,
            'media': media or [],
            'font': font,
            'public_link': f"/blog/{username}/{blog_id}"
        }
        blogs[username].append(blog)
        self.save_data(blogs, self.blogs_file)
        return blog_id

    def save_case_study(self, username, title, problem, solution, results, tags="", media=None, font='Montserrat'):
        case_studies = self.load_data(self.case_studies_file)
        if username not in case_studies:
            case_studies[username] = []

        case_id = str(uuid.uuid4())
        case_study = {
            'id': case_id,
            'title': title,
            'problem': problem,
            'solution': solution,
            'results': results,
            'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'views': 0,
            'media': media or [],
            'font': font,
            'public_link': f"/case_study/{username}/{case_id}"
        }
        case_studies[username].append(case_study)
        self.save_data(case_studies, self.case_studies_file)
        return case_id

    def save_media(self, username, file):
        media = self.load_data(self.media_file)
        if username not in media:
            media[username] = []

        file_id = str(uuid.uuid4())
        file_type = 'image' if file.type.startswith('image') else 'video' if file.type.startswith('video') else 'gif'
        file_content = base64.b64encode(file.read()).decode('utf-8')

        media[username].append({
            'id': file_id,
            'type': file_type,
            'content': file_content,
            'filename': file.name,
            'uploaded_at': datetime.now().isoformat()
        })
        self.save_data(media, self.media_file)
        return file_id

    def get_user_blogs(self, username):
        blogs = self.load_data(self.blogs_file)
        return blogs.get(username, [])

    def get_user_case_studies(self, username):
        case_studies = self.load_data(self.case_studies_file)
        return case_studies.get(username, [])

    def get_all_public_content(self):
        blogs = self.load_data(self.blogs_file)
        case_studies = self.load_data(self.case_studies_file)

        all_content = []
        for username, user_blogs in blogs.items():
            for blog in user_blogs:
                all_content.append({
                    'type': 'blog',
                    'author': username,
                    'content': blog
                })

        for username, user_cases in case_studies.items():
            for case in user_cases:
                all_content.append({
                    'type': 'case_study',
                    'author': username,
                    'content': case
                })

        return sorted(all_content, key=lambda x: x['content']['created_at'], reverse=True)

    def get_media(self, username, file_id):
        media = self.load_data(self.media_file)
        user_media = media.get(username, [])
        for item in user_media:
            if item['id'] == file_id:
                return item
        return None

# Initialize data manager


@st.cache_resource
def get_data_manager():
    return DataManager()


dm = get_data_manager()

# PDF Export Function


def export_to_pdf(content_type, content):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(content['title'], styles['Title']))
    story.append(Spacer(1, 12))

    if content_type == 'blog':
        story.append(Paragraph(content['content'], styles['BodyText']))
    else:
        story.append(Paragraph(f"<b>Problem:</b> {content['problem']}", styles['BodyText']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Solution:</b> {content['solution']}", styles['BodyText']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Results:</b> {content['results']}", styles['BodyText']))

    doc.build(story)
    return buffer.getvalue()

# Authentication functions


def login_page():
    st.markdown('<div class="fixed-header"><h1 class="app-header">🌌 GalaxyWrite</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-header">Welcome to GalaxyWrite</h2>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_btn"):
            if dm.authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials!")

    with tab2:
        st.subheader("Create new account")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Sign Up", key="signup_btn"):
            if not new_username or not new_email or not new_password:
                st.error("Please fill all fields!")
            elif new_password != confirm_password:
                st.error("Passwords don't match!")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters!")
            elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', new_email):
                st.error("Invalid email format!")
            elif dm.register_user(new_username, new_password, new_email):
                st.success("Account created successfully! Please login.")
            else:
                st.error("Username already exists!")

    st.markdown('</div>', unsafe_allow_html=True)


def dashboard():
    st.markdown('<div class="fixed-header"><h1 class="app-header">🌌 GalaxyWrite Dashboard</h1></div>', unsafe_allow_html=True)

    user_blogs = dm.get_user_blogs(st.session_state.username)
    user_case_studies = dm.get_user_case_studies(st.session_state.username)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-number">{len(user_blogs)}</div>
            <div class="stat-label">Blog Posts</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-number">{len(user_case_studies)}</div>
            <div class="stat-label">Case Studies</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        total_views = sum(blog.get('views', 0) for blog in user_blogs) + \
            sum(case.get('views', 0) for case in user_case_studies)
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-number">{total_views}</div>
            <div class="stat-label">Total Views</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Your Recent Content")

    recent_blogs = sorted(user_blogs, key=lambda x: x['created_at'], reverse=True)[:3]
    recent_cases = sorted(user_case_studies, key=lambda x: x['created_at'], reverse=True)[:3]

    if recent_blogs:
        st.write("**Recent Blogs:**")
        for blog in recent_blogs:
            st.markdown(f'''
            <div class="blog-card" style="font-family: {blog.get('font', 'Montserrat')};">
                <div class="blog-title">{blog['title']}</div>
                <div class="blog-meta">Created: {blog['created_at'][:10]} | Views: {blog.get('views', 0)}</div>
                <div class="blog-content">{blog['content'][:200]}...</div>
            </div>
            ''', unsafe_allow_html=True)

    if recent_cases:
        st.write("**Recent Case Studies:**")
        for case in recent_cases:
            st.markdown(f'''
            <div class="case-study-card" style="font-family: {case.get('font', 'Montserrat')};">
                <div class="blog-title">{case['title']}</div>
                <div class="blog-meta">Created: {case['created_at'][:10]} | Views: {case.get('views', 0)}</div>
                <div class="blog-content">{case['problem'][:200]}...</div>
            </div>
            ''', unsafe_allow_html=True)


def blog_editor():
    st.markdown('<div class="fixed-header"><h1 class="app-header">✍️ Blog Editor</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="editor-container">', unsafe_allow_html=True)

    title = st.text_input("Blog Title", value=st.session_state.get(
        'template_title', ''), placeholder="Enter an engaging title...")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        tags = st.text_input("Tags (comma-separated)", placeholder="space, tech, science")
    with col2:
        font = st.selectbox("Font", [
            'Montserrat', 'Playfair Display', 'Arial', 'Times New Roman', 'Courier New',
            'Roboto', 'Open Sans', 'Lora', 'Poppins'
        ])
    with col3:
        publish_date = st.date_input("Publish Date", datetime.now().date())

    st.subheader("Media Upload")
    uploaded_file = st.file_uploader("Upload Image, GIF, or Video", type=[
                                     'png', 'jpg', 'jpeg', 'gif', 'mp4'], key="blog_media")
    media_ids = []
    if uploaded_file:
        media_id = dm.save_media(st.session_state.username, uploaded_file)
        media_ids.append(media_id)
        media = dm.get_media(st.session_state.username, media_id)
        if media['type'] == 'image':
            st.image(f"data:image/png;base64,{media['content']}", caption=media['filename'], use_column_width=True)
        elif media['type'] == 'gif':
            st.image(f"data:image/gif;base64,{media['content']}", caption=media['filename'], use_column_width=True)
        else:
            st.video(f"data:video/mp4;base64,{media['content']}")

    st.subheader("Formatting Tools")
    format_col1, format_col2, format_col3, format_col4, format_col5, format_col6, format_col7, format_col8 = st.columns(
        8)
    with format_col1:
        if st.button("**Bold**"):
            st.info("Bold formatting applied! Use **text** in the content area.")
    with format_col2:
        if st.button("*Italic*"):
            st.info("Italic formatting applied! Use *text* in the content area.")
    with format_col3:
        if st.button("# Header"):
            st.info("Header formatting applied! Use #, ##, or ### for headers.")
    with format_col4:
        if st.button("🔗 Link"):
            st.info("Link formatting applied! Use [text](url) in the content area.")
    with format_col5:
        if st.button("📷 Media"):
            st.info("Media placeholder added! Use ![media](media_id) in the content area.")
    with format_col6:
        if st.button("📋 List"):
            st.info("List formatting applied! Use - or * for bullet points, 1. for numbered lists.")
    with format_col7:
        if st.button("💬 Quote"):
            st.info("Quote formatting applied! Use > text for blockquotes.")
    with format_col8:
        if st.button("📑 Code"):
            st.info("Code formatting applied! Use ```language\ncode\n``` for code blocks.")

    st.subheader("Content")
    content = st.text_area(
        "Write your blog content here...",
        value=st.session_state.get('template_content', ''),
        height=400,
        placeholder="Start writing your stellar blog post...\n\nYou can use Markdown formatting:\n- **bold** for bold text\n- *italic* for italic text\n- #, ##, ### for headers\n- [link](url) for links\n- ![media](media_id) for embedded media\n- - or * for bullet lists\n- 1. for numbered lists\n- > for blockquotes\n- ```language\ncode\n``` for code blocks"
    )

    if content:
        st.subheader("Preview")
        rendered_content = content
        for media_id in media_ids:
            media = dm.get_media(st.session_state.username, media_id)
            if media:
                if media['type'] in ['image', 'gif']:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<img src="data:image/{media["type"]};base64,{media["content"]}" class="media-preview">')
                else:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media["content"]}" class="media-preview" controls></video>')
        st.markdown(rendered_content, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Draft", key="save_draft"):
            if title and content:
                blog_id = dm.save_blog(st.session_state.username, title, content, tags, media_ids, font)
                st.success(f"Blog saved successfully! ID: {blog_id}")
            else:
                st.error("Please fill in title and content!")

    with col2:
        if st.button("🚀 Publish", key="publish_blog"):
            if title and content:
                blog_id = dm.save_blog(st.session_state.username, title, content, tags, media_ids, font)
                public_url = f"https://galaxywrite.app{urllib.parse.quote(dm.get_user_blogs(st.session_state.username)[-1]['public_link'])}"
                st.success(f"Blog published successfully! ID: {blog_id}")
                st.markdown(f"[Share your blog]({public_url})")
                st.balloons()
            else:
                st.error("Please fill in title and content!")

    with col3:
        if st.button("📄 Export PDF", key="export_pdf"):
            if title and content:
                blog = {'title': title, 'content': content}
                pdf_data = export_to_pdf('blog', blog)
                st.download_button(
                    "Download PDF",
                    pdf_data,
                    file_name=f"{title}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Please fill in title and content!")

    st.markdown('</div>', unsafe_allow_html=True)


def case_study_editor():
    st.markdown('<div class="fixed-header"><h1 class="app-header">🔬 Case Study Editor</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="editor-container">', unsafe_allow_html=True)

    title = st.text_input("Case Study Title", value=st.session_state.get(
        'case_template_title', ''), placeholder="Enter case study title...")

    col1, col2 = st.columns([3, 1])
    with col1:
        tags = st.text_input("Tags (comma-separated)", placeholder="business, strategy, analysis")
    with col2:
        font = st.selectbox("Font", [
            'Montserrat', 'Playfair Display', 'Arial', 'Times New Roman', 'Courier New',
            'Roboto', 'Open Sans', 'Lora', 'Poppins'
        ])

    st.subheader("Media Upload")
    uploaded_file = st.file_uploader("Upload Image, GIF, or Video", type=[
                                     'png', 'jpg', 'jpeg', 'gif', 'mp4'], key="case_media")
    media_ids = []
    if uploaded_file:
        media_id = dm.save_media(st.session_state.username, uploaded_file)
        media_ids.append(media_id)
        media = dm.get_media(st.session_state.username, media_id)
        if media['type'] == 'image':
            st.image(f"data:image/png;base64,{media['content']}", caption=media['filename'], use_column_width=True)
        elif media['type'] == 'gif':
            st.image(f"data:image/gif;base64,{media['content']}", caption=media['filename'], use_column_width=True)
        else:
            st.video(f"data:video/mp4;base64,{media['content']}")

    st.subheader("Formatting Tools")
    format_col1, format_col2, format_col3, format_col4, format_col5, format_col6, format_col7, format_col8 = st.columns(
        8)
    with format_col1:
        if st.button("**Bold**"):
            st.info("Bold formatting applied! Use **text** in the content area.")
    with format_col2:
        if st.button("*Italic*"):
            st.info("Italic formatting applied! Use *text* in the content area.")
    with format_col3:
        if st.button("# Header"):
            st.info("Header formatting applied! Use #, ##, or ### for headers.")
    with format_col4:
        if st.button("🔗 Link"):
            st.info("Link formatting applied! Use [text](url) in the content area.")
    with format_col5:
        if st.button("📷 Media"):
            st.info("Media placeholder added! Use ![media](media_id) in the content area.")
    with format_col6:
        if st.button("📋 List"):
            st.info("List formatting applied! Use - or * for bullet points, 1. for numbered lists.")
    with format_col7:
        if st.button("💬 Quote"):
            st.info("Quote formatting applied! Use > text for blockquotes.")
    with format_col8:
        if st.button("📑 Code"):
            st.info("Code formatting applied! Use ```language\ncode\n``` for code blocks.")

    st.subheader("Problem Statement")
    problem = st.text_area(
        "Describe the problem or challenge",
        value=st.session_state.get('case_template_problem', ''),
        height=150,
        placeholder="What problem were you trying to solve? Provide context and background...\n\nUse Markdown formatting:\n- **bold** for bold text\n- *italic* for italic text\n- #, ##, ### for headers\n- [link](url) for links\n- ![media](media_id) for embedded media\n- - or * for bullet lists\n- 1. for numbered lists\n- > for blockquotes\n- ```language\ncode\n``` for code blocks"
    )

    st.subheader("Solution Approach")
    solution = st.text_area(
        "Explain your solution methodology",
        value=st.session_state.get('case_template_solution', ''),
        height=200,
        placeholder="How did you approach the problem? What methods, tools, or strategies did you use?\n\nUse Markdown formatting:\n- **bold** for bold text\n- *italic* for italic text\n- #, ##, ### for headers\n- [link](url) for links\n- ![media](media_id) for embedded media\n- - or * for bullet lists\n- 1. for numbered lists\n- > for blockquotes\n- ```language\ncode\n``` for code blocks"
    )

    st.subheader("Results & Outcomes")
    results = st.text_area(
        "Share the results and impact",
        value=st.session_state.get('case_template_results', ''),
        height=150,
        placeholder="What were the outcomes? Include metrics, feedback, and lessons learned...\n\nUse Markdown formatting:\n- **bold** for bold text\n- *italic* for italic text\n- #, ##, ### for headers\n- [link](url) for links\n- ![media](media_id) for embedded media\n- - or * for bullet lists\n- 1. for numbered lists\n- > for blockquotes\n- ```language\ncode\n``` for code blocks"
    )

    if problem or solution or results:
        st.subheader("Preview")
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
                if media['type'] in ['image', 'gif']:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<img src="data:image/{media["type"]};base64,{media["content"]}" class="media-preview">')
                else:
                    rendered_content = rendered_content.replace(
                        f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media["content"]}" class="media-preview" controls></video>')

        st.markdown(rendered_content, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Draft", key="save_case_draft"):
            if title and problem and solution:
                case_id = dm.save_case_study(st.session_state.username, title, problem,
                                             solution, results, tags, media_ids, font)
                st.success(f"Case study saved successfully! ID: {case_id}")
            else:
                st.error("Please fill in title, problem, and solution!")

    with col2:
        if st.button("🚀 Publish", key="publish_case"):
            if title and problem and solution:
                case_id = dm.save_case_study(st.session_state.username, title, problem,
                                             solution, results, tags, media_ids, font)
                public_url = f"https://galaxywrite.app{urllib.parse.quote(dm.get_user_case_studies(st.session_state.username)[-1]['public_link'])}"
                st.success(f"Case study published successfully! ID: {case_id}")
                st.markdown(f"[Share your case study]({public_url})")
                st.balloons()
            else:
                st.error("Please fill in title, problem, and solution!")

    with col3:
        if st.button("📄 Export PDF", key="export_case_pdf"):
            if title and problem and solution:
                case = {'title': title, 'problem': problem, 'solution': solution, 'results': results}
                pdf_data = export_to_pdf('case_study', case)
                st.download_button(
                    "Download PDF",
                    pdf_data,
                    file_name=f"{title}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Please fill in title, problem, and solution!")

    st.markdown('</div>', unsafe_allow_html=True)


def my_content():
    st.markdown('<div class="fixed-header"><h1 class="app-header">📚 My Content</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["My Blogs", "My Case Studies"])

    with tab1:
        blogs = dm.get_user_blogs(st.session_state.username)
        if blogs:
            for blog in reversed(blogs):
                with st.expander(f"📝 {blog['title']} (ID: {blog['id']})"):
                    st.markdown(f"**Created:** {blog['created_at'][:19]}")
                    st.markdown(f"**Tags:** {', '.join(blog.get('tags', []))}")
                    st.markdown(f"**Views:** {blog.get('views', 0)}")
                    st.markdown(f"**Font:** {blog.get('font', 'Montserrat')}")
                    st.markdown(f"[Public Link](https://galaxywrite.app{urllib.parse.quote(blog['public_link'])})")
                    st.markdown("---")
                    rendered_content = blog['content']
                    for media_id in blog.get('media', []):
                        media = dm.get_media(st.session_state.username, media_id)
                        if media:
                            if media['type'] in ['image', 'gif']:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<img src="data:image/{media["type"]};base64,{media["content"]}" class="media-preview">')
                            else:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media["content"]}" class="media-preview" controls></video>')
                    st.markdown(rendered_content, unsafe_allow_html=True)
                    if st.button("📄 Export PDF", key=f"export_blog_{blog['id']}"):
                        pdf_data = export_to_pdf('blog', blog)
                        st.download_button(
                            "Download PDF",
                            pdf_data,
                            file_name=f"{blog['title']}.pdf",
                            mime="application/pdf"
                        )
        else:
            st.info("No blogs yet. Create your first blog post!")

    with tab2:
        case_studies = dm.get_user_case_studies(st.session_state.username)
        if case_studies:
            for case in reversed(case_studies):
                with st.expander(f"🔬 {case['title']} (ID: {case['id']})"):
                    st.markdown(f"**Created:** {case['created_at'][:19]}")
                    st.markdown(f"**Tags:** {', '.join(case.get('tags', []))}")
                    st.markdown(f"**Views:** {case.get('views', 0)}")
                    st.markdown(f"**Font:** {case.get('font', 'Montserrat')}")
                    st.markdown(f"[Public Link](https://galaxywrite.app{urllib.parse.quote(case['public_link'])})")
                    st.markdown("---")
                    rendered_content = f"**Problem:** {case['problem']}\n\n**Solution:** {case['solution']}\n\n**Results:** {case['results']}"
                    for media_id in case.get('media', []):
                        media = dm.get_media(st.session_state.username, media_id)
                        if media:
                            if media['type'] in ['image', 'gif']:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<img src="data:image/{media["type"]};base64,{media["content"]}" class="media-preview">')
                            else:
                                rendered_content = rendered_content.replace(
                                    f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media["content"]}" class="media-preview" controls></video>')
                    st.markdown(rendered_content, unsafe_allow_html=True)
                    if st.button("📄 Export PDF", key=f"export_case_{case['id']}"):
                        pdf_data = export_to_pdf('case_study', case)
                        st.download_button(
                            "Download PDF",
                            pdf_data,
                            file_name=f"{case['title']}.pdf",
                            mime="application/pdf"
                        )
        else:
            st.info("No case studies yet. Create your first case study!")


def public_view():
    st.markdown('<div class="fixed-header"><h1 class="app-header">🌠 Explore the Galaxy of Content</h1></div>',
                unsafe_allow_html=True)

    all_content = dm.get_all_public_content()

    if not all_content:
        st.info("No public content available yet. Be the first to share your cosmic insights!")
        return

    col1, col2 = st.columns(2)
    with col1:
        content_filter = st.selectbox("Filter by type", ["All", "Blogs", "Case Studies"])
    with col2:
        search_term = st.text_input("Search content", placeholder="Search titles, content...")

    filtered_content = all_content
    if content_filter == "Blogs":
        filtered_content = [c for c in all_content if c['type'] == 'blog']
    elif content_filter == "Case Studies":
        filtered_content = [c for c in all_content if c['type'] == 'case_study']

    if search_term:
        filtered_content = [
            c for c in filtered_content
            if search_term.lower() in c['content']['title'].lower() or
            search_term.lower() in str(c['content']).lower()
        ]

    st.markdown(f"**Showing {len(filtered_content)} cosmic creations**")

    for item in filtered_content:
        if item['type'] == 'blog':
            rendered_content = item['content']['content'][:300]
            for media_id in item['content'].get('media', []):
                media = dm.get_media(item['author'], media_id)
                if media:
                    if media['type'] in ['image', 'gif']:
                        rendered_content = rendered_content.replace(
                            f"![media]({media_id})", f'<img src="data:image/{media["type"]};base64,{media["content"]}" class="media-preview">')
                    else:
                        rendered_content = rendered_content.replace(
                            f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media["content"]}" class="media-preview" controls></video>')
            st.markdown(f'''
            <div class="blog-card" style="font-family: {item['content'].get('font', 'Montserrat')};">
                <div class="blog-title">📝 {item['content']['title']}</div>
                <div class="blog-meta">
                    By {item['author']} | {item['content']['created_at'][:10]} | 
                    Views: {item['content'].get('views', 0)}
                </div>
                <div class="blog-content">{rendered_content}...</div>
                <div>
                    {' '.join([f'<span class="tag">{tag}</span>' for tag in item['content'].get('tags', [])])}
                </div>
                <a href="https://galaxywrite.app{urllib.parse.quote(item['content']['public_link'])}" target="_blank">Read More</a>
            </div>
            ''', unsafe_allow_html=True)
        else:
            rendered_content = f"**Problem:** {item['content']['problem'][:200]}"
            for media_id in item['content'].get('media', []):
                media = dm.get_media(item['author'], media_id)
                if media:
                    if media['type'] in ['image', 'gif']:
                        rendered_content = rendered_content.replace(
                            f"![media]({media_id})", f'<img src="data:image/{media["type"]};base64,{media["content"]}" class="media-preview">')
                    else:
                        rendered_content = rendered_content.replace(
                            f"![media]({media_id})", f'<video src="data:video/mp4;base64,{media["content"]}" class="media-preview" controls></video>')
            st.markdown(f'''
            <div class="case-study-card" style="font-family: {item['content'].get('font', 'Montserrat')};">
                <div class="blog-title">🔬 {item['content']['title']}</div>
                <div class="blog-meta">
                    By {item['author']} | {item['content']['created_at'][:10]} | 
                    Views: {item['content'].get('views', 0)}
                </div>
                <div class="blog-content">{rendered_content}...</div>
                <div>
                    {' '.join([f'<span class="tag">{tag}</span>' for tag in item['content'].get('tags', [])])}
                </div>
                <a href="https://galaxywrite.app{urllib.parse.quote(item['content']['public_link'])}" target="_blank">Read More</a>
            </div>
            ''', unsafe_allow_html=True)


def profile_settings():
    st.markdown('<div class="fixed-header"><h1 class="app-header">👤 Profile Settings</h1></div>', unsafe_allow_html=True)

    users = dm.load_data(dm.users_file)
    user_data = users.get(st.session_state.username, {})
    profile = user_data.get('profile', {})

    bio = st.text_area("Bio", value=profile.get('bio', ''), placeholder="Tell us about your cosmic journey...")
    preferred_font = st.selectbox("Preferred Font", [
        'Montserrat', 'Playfair Display', 'Arial', 'Times New Roman', 'Courier New',
        'Roboto', 'Open Sans', 'Lora', 'Poppins'
    ], index=0 if profile.get('preferred_font') == 'Montserrat' else 1)

    col1, col2 = st.columns(2)
    with col1:
        twitter = st.text_input("Twitter", value=profile.get(
            'social_links', {}).get('twitter', ''), placeholder="@username")
    with col2:
        linkedin = st.text_input("LinkedIn", value=profile.get('social_links', {}).get(
            'linkedin', ''), placeholder="linkedin.com/in/username")

    github = st.text_input("GitHub", value=profile.get('social_links', {}).get(
        'github', ''), placeholder="github.com/username")
    website = st.text_input("Website", value=profile.get('social_links', {}).get(
        'website', ''), placeholder="https://yourwebsite.com")

    if st.button("💾 Save Profile"):
        users[st.session_state.username]['profile'] = {
            'bio': bio,
            'social_links': {
                'twitter': twitter,
                'linkedin': linkedin,
                'github': github,
                'website': website
            },
            'preferred_font': preferred_font
        }
        dm.save_data(users, dm.users_file)
        st.success("Profile updated successfully!")

    st.subheader("Security")
    new_password = st.text_input("New Password", type="password", key="new_password")
    confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")

    if st.button("🔒 Update Password"):
        if new_password and new_password == confirm_password and len(new_password) >= 8:
            users[st.session_state.username]['password'] = dm.hash_password(new_password)
            dm.save_data(users, dm.users_file)
            st.success("Password updated successfully!")
        elif new_password != confirm_password:
            st.error("Passwords don't match!")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters!")


def enhanced_main():
    load_css()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        login_page()
        return

    with st.sidebar:
        st.markdown('<div class="sidebar-title">🌌 GalaxyWrite</div>', unsafe_allow_html=True)

        page = st.selectbox(
            "Navigate",
            [
                "Dashboard",
                "Write Blog",
                "Create Case Study",
                "My Content",
                "Public View",
                "Templates",
                "Analytics",
                "Search & Filter",
                "Profile Settings",
                "Export Content",
                "Logout"
            ]
        )

        st.markdown("---")
        st.markdown(f"**👋 Welcome, {st.session_state.username}!**")

        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)

        st.markdown(f"📝 **Blogs:** {len(user_blogs)}")
        st.markdown(f"🔬 **Case Studies:** {len(user_cases)}")

        total_views = sum(blog.get('views', 0) for blog in user_blogs) + \
            sum(case.get('views', 0) for case in user_cases)
        st.markdown(f"👀 **Total Views:** {total_views}")

        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    if page == "Dashboard":
        dashboard()
    elif page == "Write Blog":
        blog_editor()
    elif page == "Create Case Study":
        case_study_editor()
    elif page == "My Content":
        my_content()
    elif page == "Public View":
        public_view()
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

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; color: #a0a0cc; padding: 1rem;'>
        <p>GalaxyWrite - Your Cosmic Blogging Platform</p>
        <p>Built with 🌠 using Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


def content_templates():
    st.markdown('<div class="fixed-header"><h1 class="app-header">📋 Content Templates</h1></div>', unsafe_allow_html=True)

    template_type = st.selectbox("Choose template type", ["Blog Templates", "Case Study Templates"])

    if template_type == "Blog Templates":
        templates = {
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
        }
    else:
        templates = {
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

    selected_template = st.selectbox("Select a template", list(templates.keys()))

    if st.button("📋 Use This Template"):
        template = templates[selected_template]
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

    st.subheader("Template Preview")
    template = templates[selected_template]
    if template_type == "Blog Templates":
        st.markdown(f"**Title:** {template['title']}")
        st.markdown("**Content:**")
        st.code(template['content'])
    else:
        st.markdown(f"**Title:** {template['title']}")
        st.markdown("**Problem:**")
        st.code(template['problem'])
        st.markdown("**Solution:**")
        st.code(template['solution'])
        st.markdown("**Results:**")
        st.code(template['results'])


def export_content():
    st.markdown('<div class="fixed-header"><h1 class="app-header">📤 Export Content</h1></div>', unsafe_allow_html=True)

    export_format = st.selectbox("Choose export format", ["JSON", "Markdown", "PDF"])
    content_type = st.selectbox("Content type", ["Blogs Only", "Case Studies Only", "All Content"])

    if st.button("Generate Export"):
        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)

        export_data = {}
        if content_type in ["Blogs Only", "All Content"]:
            export_data['blogs'] = user_blogs
        if content_type in ["Case Studies Only", "All Content"]:
            export_data['case_studies'] = user_cases

        if export_format == "JSON":
            st.download_button(
                "Download JSON",
                json.dumps(export_data, indent=2),
                file_name=f"{st.session_state.username}_content.json",
                mime="application/json"
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
                mime="text/markdown"
            )
        elif export_format == "PDF":
            for blog in export_data.get('blogs', []):
                pdf_data = export_to_pdf('blog', blog)
                st.download_button(
                    f"Download {blog['title']} PDF",
                    pdf_data,
                    file_name=f"{blog['title']}.pdf",
                    mime="application/pdf"
                )
            for case in export_data.get('case_studies', []):
                pdf_data = export_to_pdf('case_study', case)
                st.download_button(
                    f"Download {case['title']} PDF",
                    pdf_data,
                    file_name=f"{case['title']}.pdf",
                    mime="application/pdf"
                )


def analytics_dashboard():
    st.markdown('<div class="fixed-header"><h1 class="app-header">📊 Content Analytics</h1></div>', unsafe_allow_html=True)

    user_blogs = dm.get_user_blogs(st.session_state.username)
    user_cases = dm.get_user_case_studies(st.session_state.username)

    if not user_blogs and not user_cases:
        st.info("No content available for analytics.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_words = sum(len(blog['content'].split()) for blog in user_blogs)
        total_words += sum(len(f"{case['problem']} {case['solution']} {case['results']}".split())
                           for case in user_cases)
        st.metric("Total Words", f"{total_words:,}")

    with col2:
        avg_blog_length = sum(len(blog['content'].split())
                              for blog in user_blogs) / len(user_blogs) if user_blogs else 0
        st.metric("Avg Blog Length", f"{int(avg_blog_length)} words")

    with col3:
        total_tags = set()
        for blog in user_blogs:
            total_tags.update(blog.get('tags', []))
        for case in user_cases:
            total_tags.update(case.get('tags', []))
        st.metric("Unique Tags", len(total_tags))

    with col4:
        total_views = sum(blog.get('views', 0) for blog in user_blogs)
        total_views += sum(case.get('views', 0) for case in user_cases)
        st.metric("Total Views", total_views)

    st.subheader("Publishing Activity")
    dates = []
    for blog in user_blogs:
        dates.append(blog['created_at'][:10])
    for case in user_cases:
        dates.append(case['created_at'][:10])

    date_counts = {}
    for date in dates:
        date_counts[date] = date_counts.get(date, 0) + 1

    if date_counts:
        st.bar_chart(date_counts)


def content_search_and_filter():
    st.markdown('<div class="fixed-header"><h1 class="app-header">🔍 Advanced Search</h1></div>', unsafe_allow_html=True)

    search_query = st.text_input("Search your content", placeholder="Enter keywords...")

    col1, col2, col3 = st.columns(3)
    with col1:
        content_type_filter = st.selectbox("Content Type", ["All", "Blogs", "Case Studies"])
    with col2:
        date_from = st.date_input("From Date", datetime(2020, 1, 1).date())
    with col3:
        date_to = st.date_input("To Date", datetime.now().date())

    tag_filter = st.text_input("Filter by tags (comma-separated)", placeholder="tech, business")

    if st.button("🔍 Search"):
        user_blogs = dm.get_user_blogs(st.session_state.username)
        user_cases = dm.get_user_case_studies(st.session_state.username)

        results = []

        if content_type_filter in ["All", "Blogs"]:
            for blog in user_blogs:
                if search_query.lower() in blog['title'].lower() or search_query.lower() in blog['content'].lower():
                    blog_date = datetime.fromisoformat(blog['created_at']).date()
                    if date_from <= blog_date <= date_to:
                        if not tag_filter or any(tag.strip().lower() in [t.lower() for t in blog.get('tags', [])] for tag in tag_filter.split(',')):
                            results.append(('blog', blog))

        if content_type_filter in ["All", "Case Studies"]:
            for case in user_cases:
                search_text = f"{case['title']} {case['problem']} {case['solution']} {case['results']}"
                if search_query.lower() in search_text.lower():
                    case_date = datetime.fromisoformat(case['created_at']).date()
                    if date_from <= case_date <= date_to:
                        if not tag_filter or any(tag.strip().lower() in [t.lower() for t in case.get('tags', [])] for tag in tag_filter.split(',')):
                            results.append(('case_study', case))

        st.write(f"Found {len(results)} results:")
        for content_type, content in results:
            if content_type == 'blog':
                st.markdown(f"**📝 {content['title']}** - {content['created_at'][:10]}")
                st.write(content['content'][:200] + "...")
            else:
                st.markdown(f"**🔬 {content['title']}** - {content['created_at'][:10]}")
                st.write(content['problem'][:200] + "...")
            st.markdown("---")


if __name__ == "__main__":
    enhanced_main()
