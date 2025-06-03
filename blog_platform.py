
"""
GalaxyWrite Blog Platform
A comprehensive blogging platform with user management, content creation, media uploads,
comments, likes, search, analytics, and admin tools.
"""

import streamlit as st
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import bleach
import uuid
import base64
import urllib.parse
import pandas as pd
import re
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import (
    ForeignKeyConstraint,
    Table,
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Boolean,
    ForeignKey,
    Index,
    Float,
    and_,
    or_,
    text,
)
from sqlalchemy.orm import foreign, relationship, sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import func
from PIL import Image
import io
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
APP_URL = "https://gallaxywrite.streamlit.app"

# Database Setup


def get_db_engine():
    """
    Initialize SQLAlchemy engine for SQLite database.
    Returns:
        Engine: SQLAlchemy engine instance.
    """
    return create_engine("sqlite:///galaxywrite.db", echo=False)


def get_db_session(engine):
    """
    Create session factory for database interactions.
    Args:
        engine: SQLAlchemy engine instance.
    Returns:
        sessionmaker: Session factory.
    """
    return sessionmaker(bind=engine)

# Models


class User(Base):
    """
    User model for storing user information.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    profile = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    blogs = relationship("Blog", back_populates="user", overlaps="user")
    case_studies = relationship("CaseStudy", back_populates="user", overlaps="user")
    comments = relationship("Comment", back_populates="user", overlaps="user")
    media = relationship("Media", back_populates="user", overlaps="user")
    likes = relationship("Like", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")
    drafts = relationship("Draft", back_populates="user")
    __table_args__ = (Index('idx_user_username', 'username'),)


class Tag(Base):
    """
    Tag model for categorizing content.
    """
    __tablename__ = 'tags'
    id = Column(String(36), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    blogs = relationship("Blog", secondary="blog_tags", back_populates="tag_objects")
    case_studies = relationship("CaseStudy", secondary="case_study_tags", back_populates="tag_objects")
    __table_args__ = (Index('idx_tag_name', 'name'),)


class Blog(Base):
    """
    Blog model for blog posts.
    """
    __tablename__ = 'blogs'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    media = Column(JSON, default=[])
    font = Column(String(50), default='Inter')
    content_type = Column(String(20), default='blog')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    public_link = Column(String(255))
    is_published = Column(Boolean, default=True)
    is_draft = Column(Boolean, default=False)
    user = relationship("User", back_populates="blogs", overlaps="blogs")
    comments = relationship(
        "Comment",
        back_populates="blog",
        primaryjoin=and_(
            text("Blog.id == foreign(Comment.content_id)"),
            text("Comment.content_type == 'blog'")
        )
    )
    media_rel = relationship("Media", back_populates="blog")
    likes = relationship("Like", back_populates="blog")
    tag_objects = relationship("Tag", secondary="blog_tags", back_populates="blogs")
    drafts = relationship("Draft", back_populates="blog")
    __table_args__ = (Index('idx_blog_username', 'username', 'content_type'),)


class CaseStudy(Base):
    """
    CaseStudy model for case studies.
    """
    __tablename__ = 'case_studies'
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
    is_draft = Column(Boolean, default=False)
    user = relationship("User", back_populates="case_studies", overlaps="case_studies")
    comments = relationship(
        "Comment",
        back_populates="case_study",
        primaryjoin=and_(
            text("CaseStudy.id == foreign(Comment.content_id)"),
            text("Comment.content_type == 'case_study'")
        )
    )
    media_rel = relationship("Media", back_populates="case_study")
    likes = relationship("Like", back_populates="case_study")
    tag_objects = relationship("Tag", secondary="case_study_tags", back_populates="case_studies")
    drafts = relationship("Draft", back_populates="case_study")
    __table_args__ = (Index('idx_case_username', 'username', 'content_type'),)


class Media(Base):
    """
    Media model for uploaded files.
    """
    __tablename__ = 'media'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String(50), nullable=False)
    content_type = Column(String(20))
    content_id = Column(String(36))
    type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="media", overlaps="media")
    blog = relationship(
        "Blog",
        back_populates="media_rel",
        primaryjoin=and_(
            text("Media.content_id == foreign(Blog.id)"),
            text("Media.content_type == 'blog'")
        )
    )
    case_study = relationship(
        "CaseStudy",
        back_populates="media_rel",
        primaryjoin=and_(
            text("Media.content_id == foreign(CaseStudy.id)"),
            text("Media.content_type == 'case_study'")
        )
    )
    __table_args__ = (Index('idx_media_username', 'username'),)


class Comment(Base):
    """
    Comment model for content comments.
    """
    __tablename__ = 'comments'
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


class Like(Base):
    """
    Like model for content likes.
    """
    __tablename__ = 'likes'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_type = Column(String(20), nullable=False)
    content_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="likes")
    blog = relationship(
        "Blog",
        back_populates="likes",
        primaryjoin="and_(Like.content_id == foreign(Blog.id), Like.content_type == 'blog')"
    )
    case_study = relationship(
        "CaseStudy",
        back_populates="likes",
        primaryjoin="and_(Like.content_id == foreign(CaseStudy.id), Like.content_type == 'case_study')"
    )
    __table_args__ = (
        Index('idx_like_content', 'content_type', 'content_id'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_like_user_id'),
    )


class Notification(Base):
    """
    Notification model for user alerts.
    """
    __tablename__ = 'notifications'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    content_type = Column(String(20))
    content_id = Column(String(36))
    user = relationship("User", back_populates="notifications")
    __table_args__ = (Index('idx_notification_user', 'user_id'),)


class AnalyticsEvent(Base):
    """
    AnalyticsEvent model for tracking user interactions.
    """
    __tablename__ = 'analytics_events'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    event_type = Column(String(50), nullable=False)
    content_type = Column(String(20))
    content_id = Column(String(36))
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    user = relationship("User", back_populates="analytics_events")
    __table_args__ = (Index('idx_analytics_event', 'event_type', 'timestamp'),)


class Draft(Base):
    """
    Draft model for content versions.
    """
    __tablename__ = 'drafts'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_type = Column(String(20), nullable=False)
    content_id = Column(String(36))
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="drafts")
    blog = relationship("Blog", back_populates="drafts")
    case_study = relationship("CaseStudy", back_populates="drafts")
    __table_args__ = (Index('idx_draft_user', 'user_id', 'content_type'),)


# Association Tables
blog_tags = Table(
    'blog_tags', Base.metadata,
    Column('blog_id', String(36), ForeignKey('blogs.id'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id'), primary_key=True)
)

case_study_tags = Table(
    'case_study_tags', Base.metadata,
    Column('case_study_id', String(36), ForeignKey('case_studies.id'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id'), primary_key=True)
)

# Table Creation
engine = get_db_engine()
User.__table__.create(engine, checkfirst=True)
Tag.__table__.create(engine, checkfirst=True)
Blog.__table__.create(engine, checkfirst=True)
CaseStudy.__table__.create(engine, checkfirst=True)
Media.__table__.create(engine, checkfirst=True)
Comment.__table__.create(engine, checkfirst=True)
Like.__table__.create(engine, checkfirst=True)
Notification.__table__.create(engine, checkfirst=True)
AnalyticsEvent.__table__.create(engine, checkfirst=True)
Draft.__table__.create(engine, checkfirst=True)
blog_tags.create(engine, checkfirst=True)
case_study_tags.create(engine, checkfirst=True)
Session = get_db_session(engine)

# Data Manager


class DataManager:
    """
    Manages database operations for the blog platform.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_user(self, username: str, password: str, email: str, is_admin: bool = False) -> bool:
        """
        Save a new user with hashed password.
        Args:
            username: User's unique username.
            password: User's password.
            email: User's email address.
            is_admin: Whether the user is an admin.
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                hashed_password = stauth.Hasher([password]).generate()[0]
                user = User(
                    username=bleach.clean(username),
                    password=hashed_password,
                    email=bleach.clean(email),
                    is_admin=is_admin
                )
                session.add(user)
                session.commit()
                logger.info(f"User {username} registered successfully")
                return True
        except IntegrityError:
            logger.error(f"User {username} or email {email} already exists")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error saving user: {str(e)}")
            return False

    def update_user_profile(self, username: str, profile: Dict[str, Any]) -> bool:
        """
        Update user profile information.
        Args:
            username: User's username.
            profile: Dictionary of profile data.
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    logger.error(f"User {username} not found")
                    return False
                user.profile = {**user.profile, **profile}
                session.commit()
                logger.info(f"Profile updated for user {username}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating profile for {username}: {str(e)}")
            return False

    def update_password(self, username: str, new_password: str) -> bool:
        """
        Update user password.
        Args:
            username: User's username.
            new_password: New password.
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    logger.error(f"User {username} not found")
                    return False
                user.password = stauth.Hasher([new_password]).generate()[0]
                session.commit()
                logger.info(f"Password updated for user {username}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating password for {username}: {str(e)}")
            return False

    def save_tag(self, name: str) -> str:
        """
        Save a new tag.
        Args:
            name: Tag name.
        Returns:
            str: Tag ID.
        """
        tag_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                tag = Tag(id=tag_id, name=bleach.clean(name))
                session.add(tag)
                session.commit()
                logger.info(f"Tag {name} saved with ID {tag_id}")
                return tag_id
        except IntegrityError:
            with self.session_factory() as session:
                tag = session.query(Tag).filter_by(name=bleach.clean(name)).first()
                if tag:
                    return tag.id
                logger.error(f"Error saving tag {name}")
                raise
        except SQLAlchemyError as e:
            logger.error(f"Error saving tag {name}: {str(e)}")
            raise

    def save_media(self, username: str, file, content_type: Optional[str] = None, content_id: Optional[str] = None) -> str:
        """
        Save media file with base64 encoding.
        Args:
            username: Uploader's username.
            file: Uploaded file object.
            content_type: Associated content type (blog/case_study).
            content_id: Associated content ID.
        Returns:
            str: Media ID.
        """
        file_type = 'image' if file.type.startswith('image') else 'video' if file.type.startswith('video') else 'gif'
        file_content = base64.b64encode(file.read()).decode('utf-8')
        file_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    raise ValueError("User not found")
                media = Media(
                    id=file_id,
                    user_id=user.id,
                    username=username,
                    content_type=content_type,
                    content_id=content_id,
                    type=file_type,
                    content=file_content,
                    filename=bleach.clean(file.name)
                )
                session.add(media)
                session.commit()
                logger.info(f"Media {file_id} saved by {username}")
                return file_id
        except SQLAlchemyError as e:
            logger.error(f"Error saving media: {str(e)}")
            raise

    def save_blog(self, username: str, title: str, content: str, tags: str = "", media: Optional[List[str]] = None, font: str = 'Inter', is_published: bool = True, is_draft: bool = False) -> str:
        """
        Save a new blog post.
        Args:
            username: Author's username.
            title: Blog title.
            content: Blog content.
            tags: Comma-separated tags.
            media: List of media IDs.
            font: Font style.
            is_published: Publish status.
            is_draft: Draft status.
        Returns:
            str: Blog ID.
        """
        title = bleach.clean(title)
        content = bleach.clean(content)
        tag_list = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
        blog_id = str(uuid.uuid4())
        public_link = f"{APP_URL}/content/blog/{urllib.parse.quote(username)}/{blog_id}"
        try:
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
                    tags=tag_list,
                    media=media or [],
                    font=font,
                    public_link=public_link,
                    is_published=is_published,
                    is_draft=is_draft
                )
                session.add(blog)
                for tag_name in tag_list:
                    tag_id = self.save_tag(tag_name)
                    tag = session.query(Tag).filter_by(id=tag_id).first()
                    blog.tag_objects.append(tag)
                session.commit()
                if media:
                    for media_id in media:
                        media_record = session.query(Media).filter_by(id=media_id).first()
                        if media_record:
                            media_record.content_type = 'blog'
                            media_record.content_id = blog_id
                    session.commit()
                logger.info(f"Blog {blog_id} saved by {username}")
                self.notify_followers(username, 'blog', blog_id, f"New blog: {title}")
                return blog_id
        except SQLAlchemyError as e:
            logger.error(f"Error saving blog: {str(e)}")
            raise

    def update_blog(self, blog_id: str, title: str, content: str, tags: str, media: List[str], font: str, is_published: bool, is_draft: bool) -> bool:
        """
        Update an existing blog post.
        Args:
            blog_id: Blog ID.
            title: Updated title.
            content: Updated content.
            tags: Updated tags.
            media: Updated media IDs.
            font: Updated font.
            is_published: Updated publish status.
            is_draft: Updated draft status.
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                blog = session.query(Blog).filter_by(id=blog_id).first()
                if not blog:
                    logger.error(f"Blog {blog_id} not found")
                    return False
                blog.title = bleach.clean(title)
                blog.content = bleach.clean(content)
                tag_list = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
                blog.tags = tag_list
                blog.media = media
                blog.font = font
                blog.is_published = is_published
                blog.is_draft = is_draft
                blog.updated_at = datetime.utcnow()
                blog.tag_objects.clear()
                for tag_name in tag_list:
                    tag_id = self.save_tag(tag_name)
                    tag = session.query(Tag).filter_by(id=tag_id).first()
                    blog.tag_objects.append(tag)
                if media:
                    for media_id in media:
                        media_record = session.query(Media).filter_by(id=media_id).first()
                        if media_record:
                            media_record.content_type = 'blog'
                            media_record.content_id = blog_id
                session.commit()
                logger.info(f"Blog {blog_id} updated")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating blog {blog_id}: {str(e)}")
            return False

    def save_case_study(self, username: str, title: str, problem: str, solution: str, results: str, tags: str = "", media: Optional[List[str]] = None, font: str = 'Inter', is_published: bool = True, is_draft: bool = False) -> str:
        """
        Save a new case study.
        Args:
            username: Author's username.
            title: Case study title.
            problem: Problem description.
            solution: Solution description.
            results: Results description.
            tags: Comma-separated tags.
            media: List of media IDs.
            font: Font style.
            is_published: Publish status.
            is_draft: Draft status.
        Returns:
            str: Case study ID.
        """
        title = bleach.clean(title)
        problem = bleach.clean(problem)
        solution = bleach.clean(solution)
        results = bleach.clean(results)
        tag_list = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
        case_id = str(uuid.uuid4())
        public_link = f"{APP_URL}/content/case_study/{urllib.parse.quote(username)}/{case_id}"
        try:
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
                    tags=tag_list,
                    media=media or [],
                    font=font,
                    public_link=public_link,
                    is_published=is_published,
                    is_draft=is_draft
                )
                session.add(case_study)
                for tag_name in tag_list:
                    tag_id = self.save_tag(tag_name)
                    tag = session.query(Tag).filter_by(id=tag_id).first()
                    case_study.tag_objects.append(tag)
                session.commit()
                if media:
                    for media_id in media:
                        media_record = session.query(Media).filter_by(id=media_id).first()
                        if media_record:
                            media_record.content_type = 'case_study'
                            media_record.content_id = case_id
                    session.commit()
                logger.info(f"Case study {case_id} saved by {username}")
                self.notify_followers(username, 'case_study', case_id, f"New case study: {title}")
                return case_id
        except SQLAlchemyError as e:
            logger.error(f"Error saving case study: {str(e)}")
            raise

    def update_case_study(self, case_id: str, title: str, problem: str, solution: str, results: str, tags: str, media: List[str], font: str, is_published: bool, is_draft: bool) -> bool:
        """
        Update an existing case study.
        Args:
            case_id: Case study ID.
            title: Updated title.
            problem: Updated problem.
            solution: Updated solution.
            results: Updated results.
            tags: Updated tags.
            media: Updated media IDs.
            font: Updated font.
            is_published: Updated publish status.
            is_draft: Updated draft status.
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                case_study = session.query(CaseStudy).filter_by(id=case_id).first()
                if not case_study:
                    logger.error(f"Case study {case_id} not found")
                    return False
                case_study.title = bleach.clean(title)
                case_study.problem = bleach.clean(problem)
                case_study.solution = bleach.clean(solution)
                case_study.results = bleach.clean(results)
                tag_list = [bleach.clean(tag.strip()) for tag in tags.split(',') if tag.strip()]
                case_study.tags = tag_list
                case_study.media = media
                case_study.font = font
                case_study.is_published = is_published
                case_study.is_draft = is_draft
                case_study.updated_at = datetime.utcnow()
                case_study.tag_objects.clear()
                for tag_name in tag_list:
                    tag_id = self.save_tag(tag_name)
                    tag = session.query(Tag).filter_by(id=tag_id).first()
                    case_study.tag_objects.append(tag)
                if media:
                    for media_id in media:
                        media_record = session.query(Media).filter_by(id=media_id).first()
                        if media_record:
                            media_record.content_type = 'case_study'
                            media_record.content_id = case_id
                session.commit()
                logger.info(f"Case study {case_id} updated")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating case study {case_id}: {str(e)}")
            return False

    def save_comment(self, username: str, content_type: str, content_id: str, comment: str) -> str:
        """
        Save a new comment.
        Args:
            username: Commenter's username.
            content_type: Content type (blog/case_study).
            content_id: Content ID.
            comment: Comment text.
        Returns:
            str: Comment ID.
        """
        comment = bleach.clean(comment)
        comment_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    raise ValueError("User not found")
                comment_obj = Comment(
                    id=comment_id,
                    user_id=user.id,
                    username=username,
                    content_type=content_type,
                    content_id=content_id,
                    comment=comment
                )
                session.add(comment_obj)
                session.commit()
                logger.info(f"Comment {comment_id} saved by {username}")
                content = self.get_content_by_id(content_type, content_id)
                if content:
                    self.notify_user(content.username, f"New comment on {content.title}", content_type, content_id)
                return comment_id
        except SQLAlchemyError as e:
            logger.error(f"Error saving comment: {str(e)}")
            raise

    def save_like(self, username: str, content_type: str, content_id: str) -> bool:
        """
        Save a like for content.
        Args:
            username: User's username.
            content_type: Content type (blog/case_study).
            content_id: Content ID.
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        like_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    logger.error(f"User {username} not found")
                    return False
                existing_like = session.query(Like).filter_by(
                    user_id=user.id, content_type=content_type, content_id=content_id
                ).first()
                if existing_like:
                    logger.info(f"User {username} already liked {content_type}:{content_id}")
                    return False
                like = Like(
                    id=like_id,
                    user_id=user.id,
                    content_type=content_type,
                    content_id=content_id
                )
                session.add(like)
                session.commit()
                logger.info(f"Like {like_id} saved by {username}")
                content = self.get_content_by_id(content_type, content_id)
                if content:
                    self.notify_user(content.username, f"New like on {content.title}", content_type, content_id)
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error saving like: {str(e)}")
            return False

    def remove_like(self, username: str, content_type: str, content_id: str) -> bool:
        """
        Remove a like from content.
        Args:
            username: User's username.
            content_type: Content type (blog/case_study).
            content_id: Content ID.
        Returns:
            bool: True if removed successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    logger.error(f"User {username} not found")
                    return False
                like = session.query(Like).filter_by(
                    user_id=user.id, content_type=content_type, content_id=content_id
                ).first()
                if not like:
                    logger.info(f"No like found for {username} on {content_type}:{content_id}")
                    return False
                session.delete(like)
                session.commit()
                logger.info(f"Like removed by {username} for {content_type}:{content_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error removing like: {str(e)}")
            return False

    def save_draft(self, username: str, content_type: str, content_id: Optional[str], data: Dict[str, Any]) -> str:
        """
        Save a draft version of content.
        Args:
            username: User's username.
            content_type: Content type (blog/case_study).
            content_id: Associated content ID.
            data: Draft data.
        Returns:
            str: Draft ID.
        """
        draft_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    raise ValueError("User not found")
                draft = Draft(
                    id=draft_id,
                    user_id=user.id,
                    content_type=content_type,
                    content_id=content_id,
                    data=data
                )
                session.add(draft)
                session.commit()
                logger.info(f"Draft {draft_id} saved by {username}")
                return draft_id
        except SQLAlchemyError as e:
            logger.error(f"Error saving draft: {str(e)}")
            raise

    def get_drafts(self, username: str, content_type: str) -> List[Draft]:
        """
        Retrieve drafts for a user.
        Args:
            username: User's username.
            content_type: Content type (blog/case_study).
        Returns:
            List[Draft]: List of drafts.
        """
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    return []
                return session.query(Draft).filter_by(
                    user_id=user.id, content_type=content_type
                ).order_by(Draft.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving drafts for {username}: {str(e)}")
            return []

    def notify_user(self, username: str, message: str, content_type: Optional[str] = None, content_id: Optional[str] = None) -> bool:
        """
        Send a notification to a user.
        Args:
            username: Recipient's username.
            message: Notification message.
            content_type: Associated content type.
            content_id: Associated content ID.
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        notification_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    logger.error(f"User {username} not found")
                    return False
                notification = Notification(
                    id=notification_id,
                    user_id=user.id,
                    message=bleach.clean(message),
                    content_type=content_type,
                    content_id=content_id
                )
                session.add(notification)
                session.commit()
                logger.info(f"Notification {notification_id} sent to {username}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error sending notification to {username}: {str(e)}")
            return False

    def notify_followers(self, username: str, content_type: str, content_id: str, message: str) -> None:
        """
        Notify followers of new content.
        Args:
            username: Content creator's username.
            content_type: Content type.
            content_id: Content ID.
            message: Notification message.
        """
        try:
            with self.session_factory() as session:
                followers = session.query(User).filter(
                    User.profile.contains({'following': [username]})
                ).all()
                for follower in followers:
                    self.notify_user(follower.username, message, content_type, content_id)
        except SQLAlchemyError as e:
            logger.error(f"Error notifying followers for {username}: {str(e)}")

    def get_notifications(self, username: str, unread_only: bool = False) -> List[Notification]:
        """
        Retrieve user notifications.
        Args:
            username: User's username.
            unread_only: Filter for unread notifications.
        Returns:
            List[Notification]: List of notifications.
        """
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    return []
                query = session.query(Notification).filter_by(user_id=user.id)
                if unread_only:
                    query = query.filter_by(is_read=False)
                return query.order_by(Notification.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving notifications for {username}: {str(e)}")
            return []

    def mark_notification_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        Args:
            notification_id: Notification ID.
        Returns:
            bool: True if marked successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                notification = session.query(Notification).filter_by(id=notification_id).first()
                if not notification:
                    logger.error(f"Notification {notification_id} not found")
                    return False
                notification.is_read = True
                session.commit()
                logger.info(f"Notification {notification_id} marked as read")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return False

    def log_analytics_event(self, username: Optional[str], event_type: str, content_type: Optional[str] = None, content_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Log an analytics event.
        Args:
            username: User's username, if authenticated.
            event_type: Type of event (e.g., view, click).
            content_type: Associated content type.
            content_id: Associated content ID.
            metadata: Additional event data.
        Returns:
            bool: True if logged successfully, False otherwise.
        """
        event_id = str(uuid.uuid4())
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first() if username else None
                event = AnalyticsEvent(
                    id=event_id,
                    user_id=user.id if user else None,
                    event_type=event_type,
                    content_type=content_type,
                    content_id=content_id,
                    metadata=metadata or {}
                )
                session.add(event)
                session.commit()
                logger.info(f"Analytics event {event_id} logged")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error logging analytics event: {str(e)}")
            return False

    def get_content_by_id(self, content_type: str, content_id: str) -> Optional[Any]:
        """
        Retrieve content by type and ID.
        Args:
            content_type: Content type (blog/case_study).
            content_id: Content ID.
        Returns:
            Optional[Any]: Content object or None.
        """
        try:
            with self.session_factory() as session:
                if content_type == 'blog':
                    return session.query(Blog).filter_by(id=content_id).first()
                elif content_type == 'case_study':
                    return session.query(CaseStudy).filter_by(id=content_id).first()
                logger.error(f"Invalid content type: {content_type}")
                return None
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving content {content_type}:{content_id}: {str(e)}")
            return None

    def get_user_content(self, username: str, content_type: Optional[str] = None) -> List[Any]:
        """
        Retrieve all content by user and type.
        Args:
            username: User's username.
            content_type: Content type (blog/case_study, or None for all).
        Returns:
            List[Any]: List of content objects.
        """
        try:
            with self.session_factory() as session:
                if content_type == 'blog':
                    return session.query(Blog).filter_by(username=username).all()
                elif content_type == 'case_study':
                    return session.query(CaseStudy).filter_by(username=username).all()
                elif content_type or content_type == 'all':
                    blogs = session.query(Blog).filter_by(username=username).all()
                    case_studies = session.query(CaseStudy).filter_by(username=username).all()
                    return blogs + case_studies
                return []
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving content for {username}: {str(e)}")
            return []

    def search_content(self, query: str, tags: Optional[List[str]] = None, content_type: Optional[str] = None) -> List[Any]:
        """
        Search content by query and tags.
        Args:
            query: Search query.
            tags: List of tags to filter by.
            content_type: Content type (blog/case_study, or None for all).
        Returns:
            List[Any]: List of matching content objects.
        """
        try:
            with self.session_factory() as session:
                blogs = session.query(Blog).filter(
                    and_(
                        Blog.is_published == True,
                        or_(
                            Blog.title.ilike(f"%{query}%"),
                            Blog.content.ilike(f"%{query}%")
                        )
                    )
                )
                case_studies = session.query(CaseStudy).filter(
                    and_(
                        CaseStudy.is_published == True,
                        or_(
                            CaseStudy.title.ilike(f"%{query}%"),
                            CaseStudy.problem.ilike(f"%{query}%"),
                            CaseStudy.solution.ilike(f"%{query}%"),
                            CaseStudy.results.ilike(f"%{query}%")
                        )
                    )
                )
                if tags:
                    blogs = blogs.filter(Blog.tags.contains(tags))
                    case_studies = case_studies.filter(CaseStudy.tags.contains(tags))
                if content_type == 'blog':
                    return blogs.all()
                elif content_type == 'case_study':
                    return case_studies.all()
                return blogs.all() + case_studies.all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching content: {str(e)}")
            return []

    def get_analytics(self, username: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Retrieve analytics for user content.
        Args:
            username: User's username.
            start_date: Start date filter.
            end_date: End date filter.
        Returns:
            Dict[str, Any]: Analytics data.
        """
        try:
            with self.session_factory() as session:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    return {}
                blog_views = session.query(func.sum(Blog.views)).filter_by(username=username).scalar() or 0
                case_study_views = session.query(func.sum(CaseStudy.views)).filter_by(username=username).scalar() or 0
                blog_likes = session.query(func.count(Like.id)).filter(
                    Like.content_type == 'blog',
                    Like.content_id.in_(session.query(Blog.id).filter_by(username=username))
                ).scalar() or 0
                case_study_likes = session.query(func.count(Like.id)).filter(
                    Like.content_type == 'case_study',
                    Like.content_id.in_(session.query(CaseStudy.id).filter_by(username=username))
                ).scalar() or 0
                events_query = session.query(AnalyticsEvent).filter_by(user_id=user.id)
                if start_date:
                    events_query = events_query.filter(AnalyticsEvent.timestamp >= start_date)
                if end_date:
                    events_query = events_query.filter(AnalyticsEvent.timestamp <= end_date)
                event_counts = events_query.group_by(AnalyticsEvent.event_type).count()
                return {
                    'total_views': blog_views + case_study_views,
                    'total_likes': blog_likes + case_study_likes,
                    'blog_count': session.query(Blog).filter_by(username=username).count(),
                    'case_study_count': session.query(CaseStudy).filter_by(username=username).count(),
                    'event_counts': event_counts
                }
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analytics for {username}: {str(e)}")
            return {}

    def delete_content(self, content_type: str, content_id: str) -> bool:
        """
        Delete content by type and ID.
        Args:
            content_type: Content type (blog/case_study).
            content_id: Content ID.
        Returns:
            bool: True if deleted successfully, False otherwise.
        """
        try:
            with self.session_factory() as session:
                if content_type == 'blog':
                    content = session.query(Blog).filter_by(id=content_id).first()
                elif content_type == 'case_study':
                    content = session.query(CaseStudy).filter_by(id=content_id).first()
                else:
                    logger.error(f"Invalid content type: {content_type}")
                    return False
                if not content:
                    logger.error(f"Content {content_type}:{content_id} not found")
                    return False
                session.query(Comment).filter_by(content_type=content_type, content_id=content_id).delete()
                session.query(Like).filter_by(content_type=content_type, content_id=content_id).delete()
                session.query(Media).filter_by(content_type=content_type, content_id=content_id).delete()
                session.query(Draft).filter_by(content_type=content_type, content_id=content_id).delete()
                session.query(Notification).filter_by(content_type=content_type, content_id=content_id).delete()
                session.delete(content)
                session.commit()
                logger.info(f"Deleted {content_type}:{content_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {content_type}:{content_id}: {str(e)}")
            return False


def get_data_manager():
    """
    Instantiate DataManager with session factory.
    Returns:
        DataManager: Data manager instance.
    """
    return DataManager(Session)

# Streamlit UI Components


def custom_css():
    """
    Apply custom CSS for UI styling.
    """
    st.markdown("""
        <style>
            .stApp { background-color: #f5f5f5; }
            .sidebar .sidebar-content { background-color: #2c3e50; color: white; }
            .stButton>button { background-color: #3498db; color: white; border-radius: 5px; }
            .stTextInput>div>input { border-radius: 5px; }
            .stTextArea>div>textarea { border-radius: 5px; }
            .content-card { background-color: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .comment { background-color: #ecf0f1; padding: 10px; margin: 5px 0; border-radius: 5px; }
            .notification { background-color: #d4edda; padding: 10px; margin: 5px 0; border-radius: 5px; }
            .tag { background-color: #e0e0e0; padding: 5px 10px; margin: 2px; border-radius: 15px; display: inline-block; }
        </style>
    """, unsafe_allow_html=True)


def login_page():
    """
    Render login page.
    """
    st.title("Login to GalaxyWrite")
    credentials = {
        "credentials": {
            "usernames": {
                user.username: {
                    "name": user.username,
                    "password": user.password,
                    "email": user.email
                }
                for user in Session().query(User).all()
            }
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        "blog_platform",
        "auth",
        cookie_expiry_days=30
    )
    name, authentication_status, username = authenticator.login("Login", "main")
    if authentication_status:
        try:
            with Session() as session:
                user = session.query(User).filter_by(username=username).first()
                if user:
                    user.last_login = datetime.utcnow()
                    session.commit()
                    dm = get_data_manager()
                    dm.log_analytics_event(username, 'login')
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.is_admin = user.is_admin
            st.rerun()
        except SQLAlchemyError as e:
            logger.error(f"Error during login for {username}: {str(e)}")
            st.error("An error occurred during login")
    elif authentication_status is False:
        st.error("Invalid username or password")
        st.error("Username or password is incorrect")
    elif authentication_status is None:
        st.warning("Please enter your username and password")


def signup_page():
    """
    Render signup page.
    """
    st.title("Sign Up for GalaxyWrite")
    st.subheader("Create Your Account")
    username = st.text_input("Username", help="Choose a unique username")
    password = st.text_input("Password", type="password", help="At least 6 characters")
    confirm_password = st.text_input("Confirm Password", type="password")
    email = st.text_input("Email", help="Enter a valid email address")
    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("Passwords do not match")
            logger.error("Password mismatch during signup")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters long")
            logger.error("Password too short during signup")
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Invalid email format")
            logger.error("Invalid email during signup")
            return
        dm = get_data_manager()
        try:
            if dm.save_user(username, password, email):
                st.success("User registered successfully! Please log in.")
                logger.info(f"User {username} signed up successfully")
                dm.log_analytics_event(username, 'signup')
            else:
                st.error("Username or email already exists")
                logger.error(f"Signup failed for {username}: duplicate username/email")
        except Exception as e:
            st.error("An error occurred during signup")
            logger.error(f"Signup error: {str(e)}")


def profile_page():
    """
    Render user profile page.
    """
    st.title("Edit Your Profile")
    username = st.session_state.username
    dm = get_data_manager()
    try:

        with Session() as session:
            user = session.query(User).filter_by(username=username).first()
            if not username:
                st.error("User not found")
                logger.error(f"Profile load failed for {user}")
                return
            profile = user.profile or {}
    except SQLAlchemyError as e:
        logger.error(f"Error loading profile for {user}: {str(e)}")
        st.error("Error loading profile")
        return

    with st.form("profile_form"):

        bio = st.text_area("Bio", value=profile.get('bio', ''), help="Tell us about yourself")
        website = st.text_input("Website", value=profile.get('website', ''), help="Your personal website")
        social_links = st.text_area("Social Links (JSON)", value=json.dumps(profile.get('social_links', {}), indent=2),
                                    help="Enter links as JSON, e.g., {'twitter': 'https://twitter.com/user'}")
        profile_picture = st.file_uploader("Upload Profile Picture")
        if st.form_submit_button("Save Profile"):
            try:
                new_profile = {
                    'bio': bleach.clean(bio),
                    'website': bleach.clean(website),
                    'social_links': json.loads(social_links)
                }
                if profile_picture:
                    media_id = dm.save_media(username, profile_picture, content_type='profile')
                    new_profile['profile_picture'] = media_id
                if dm.update_user_profile(username, new_profile):
                    st.success("Profile updated successfully")
                    logger.info(f"Profile updated for {username}")
                    dm.log_analytics_event(username, 'updated_profile')
                else:
                    st.error("Failed to update profile")
                    logger.error(f"Failed to update profile for {username}")
            except json.JSONDecodeError:
                st.error("Invalid JSON format for social links")
                logger.error(f"Invalid social links JSON for {username}")
            except Exception as e:
                st.error(f"Error updating profile: {str(e)}")
                logger.error(f"Profile update error for {username}: {str(e)}")

    st.subheader("Change Password")
    with st.form("password_form"):
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new_password != confirm_new_password:
                st.error("New passwords do not match")
                logger.error(f"Password mismatch for {username}")
                return
            authenticator = stauth.Authenticate(
                {"credentials": {"usernames": {username: {"password": user.password}}}},
                "blog_platform",
                "auth",
                cookie_expiry_days=30
            )
            try:
                if authenticator._check_credentials({username: old_password}):
                    if dm.update_password(username, new_password):
                        st.success("Password updated successfully")
                        logger.info(f"Password updated for {username}")
                        dm.log_analytics_event(username, 'password_change')
                    else:
                        st.error("Failed to update password")
                        logger.error(f"Failed to update password for {username}")
                else:
                    st.error("Incorrect old password")
                    logger.error(f"Incorrect old password for {username}")
            except Exception as e:
                st.error(f"Error updating password: {str(e)}")
                logger.error(f"Password update error for {username}: {str(e)}")


def create_content_page():
    """
    Render content creation page.
    Allows users to create blogs or case studies with media, tags, and draft options.
    """
    st.title("Create New Content")
    content_type = st.selectbox("Content Type", ["Blog", "Case Study"], help="Choose content type")
    title = st.text_input("Title", help="Enter a descriptive title")
    tags = st.text_input("Tags (comma-separated)", help="Add relevant tags, e.g., tech, ai")
    media_files = st.file_uploader("Upload Media", accept_multiple_files=True, help="Upload images or videos")
    font = st.selectbox("Font", ["Inter", "Arial", "Times New Roman", "Roboto"], help="Select font style")
    is_published = st.checkbox("Publish Immediately", value=True, help="Make post visible to public")
    is_draft = st.checkbox("Save as Draft", value=False, help="Save without publishing")

    dm = get_data_manager()
    username = st.session_state.username

    if content_type == "Blog":
        content = st.text_area("Content", height=300, help="Write your blog content here")
        if st.button("Save Blog", key="save_blog"):
            if not title.strip() or not content.strip():
                st.error("Title and content are required")
                logger.error(f"Blog creation failed for {username}: missing title/content")
                return
            media_ids = []
            if media_files:
                for file in media_files:
                    try:
                        media_id = dm.save_media(username, file)
                        media_ids.append(media_id)
                        logger.info(f"Media uploaded for blog by {username}: {media_id}")
                    except ValueError as e:
                        st.error(str(e))
                        logger.error(f"Media upload failed for {username}: {str(e)}")
                        return
            try:
                blog_data = {
                    'title': title,
                    'content': content,
                    'tags': tags,
                    'media': media_ids,
                    'font': font,
                    'is_published': is_published,
                    'is_draft': is_draft
                }
                if is_draft:
                    draft_id = dm.save_draft(username, 'blog', None, blog_data)
                    st.success(f"Draft saved! Draft ID: {draft_id}")
                    logger.info(f"Blog draft {draft_id} saved by {username}")
                else:
                    blog_id = dm.save_blog(
                        username,
                        title,
                        content,
                        tags,
                        media_ids,
                        font,
                        is_published,
                        is_draft
                    )
                    st.success(f"Blog saved! ID: {blog_id}")
                    st.markdown(f"[View Blog]({APP_URL}/content/blog/{urllib.parse.quote(username)}/{blog_id})")
                    logger.info(f"Blog {blog_id} created by {username}")
                    dm.log_analytics_event(username, 'create_blog', 'blog', blog_id)
            except ValueError as e:
                st.error(str(e))
                logger.error(f"Blog creation failed for {username}: {str(e)}")
            except Exception as e:
                st.error("An error occurred while saving the blog")
                logger.error(f"Unexpected error creating blog for {username}: {str(e)}")
    else:
        problem = st.text_area("Problem", height=200, help="Describe the problem")
        solution = st.text_area("Solution", height=200, help="Describe the solution")
        results = st.text_area("Results", height=200, help="Describe the results")
        if st.button("Save Case Study", key="save_case_study"):
            if not title.strip() or not problem.strip() or not solution.strip() or not results.strip():
                st.error("Title, problem, solution, and results are required")
                logger.error(f"Case study creation failed for {username}: missing required fields")
                return
            media_ids = []
            if media_files:
                for file in media_files:
                    try:
                        media_id = dm.save_media(username, file)
                        media_ids.append(media_id)
                        logger.info(f"Media uploaded for case study by {username}: {media_id}")
                    except ValueError as e:
                        st.error(str(e))
                        logger.error(f"Media upload failed for {username}: {str(e)}")
                        return
            try:
                case_data = {
                    'title': title,
                    'problem': problem,
                    'solution': solution,
                    'results': results,
                    'tags': tags,
                    'media': media_ids,
                    'font': font,
                    'is_published': is_published,
                    'is_draft': is_draft
                }
                if is_draft:
                    draft_id = dm.save_draft(username, 'case_study', None, case_data)
                    st.success(f"Draft saved! Draft ID: {draft_id}")
                    logger.info(f"Case study draft {draft_id} saved by {username}")
                else:
                    case_id = dm.save_case_study(
                        username,
                        title,
                        problem,
                        solution,
                        results,
                        tags,
                        media_ids,
                        font,
                        is_published,
                        is_draft
                    )
                    st.success(f"Case Study saved! ID: {case_id}")
                    st.markdown(
                        f"[View Case Study]({APP_URL}/content/case_study/{urllib.parse.quote(username)}/{case_id})")
                    logger.info(f"Case study {case_id} created by {username}")
                    dm.log_analytics_event(username, 'create_case_study', 'case_study', case_id)
            except ValueError as e:
                st.error(str(e))
                logger.error(f"Case study creation failed for {username}: {str(e)}")
            except Exception as e:
                st.error("An error occurred while saving the case study")
                logger.error(f"Unexpected error creating case study for {username}: {str(e)}")


def edit_content_page():
    """
    Render content editing page.
    Allows users to edit existing blogs or case studies, including drafts.
    """
    st.title("Edit Content")
    dm = get_data_manager()
    username = st.session_state.username
    content_type = st.selectbox("Content Type", ["Blog", "Case Study"], key="edit_content_type")
    content_source = st.radio("Source", ["Published Content", "Drafts"], key="content_source")

    contents = []
    if content_source == "Published Content":
        contents = dm.get_user_content(username, content_type.lower())
    else:
        contents = dm.get_drafts(username, content_type.lower())

    content_options = {
        f"{c.title if hasattr(c, 'title') else c.data.get('title')} (ID: {c.id})": c.id for c in contents}
    selected_content = st.selectbox("Select Content", list(content_options.keys())
                                    if content_options else ["No content available"])

    if selected_content == "No content available":
        st.warning("No content available to edit")
        return

    content_id = content_options[selected_content]
    is_draft = content_source == "Drafts"
    content = None
    if is_draft:
        content = next((c for c in contents if c.id == content_id), None)
        content_data = content.data
    else:
        content = dm.get_content_by_id(content_type.lower(), content_id)
        content_data = content.__dict__

    if not content:
        st.error("Content not found")
        logger.error(f"Content {content_type}:{content_id} not found for {username}")
        return

    with st.form("edit_content_form"):
        title = st.text_input("Title", value=content_data.get('title', ''))
        tags = st.text_input("Tags", value=', '.join(content_data.get('tags', [])))
        media_files = st.file_uploader("Upload New Media", accept_multiple_files=True)
        font = st.selectbox("Font", ["Inter", "Arial", "Times New Roman", "Roboto"], index=[
                            "Inter", "Arial", "Times New Roman", "Roboto"].index(content_data.get('font', 'Inter')))
        is_published = st.checkbox("Is Published", value=content_data.get('is_published', True))
        is_draft_save = st.checkbox("Save as Draft", value=content_data.get('is_draft', False))

        if content_type == "Blog":
            content_text = st.text_area("Content", value=content_data.get('content', ''), height=300)
            if st.form_submit_button("Update Blog"):
                media_ids = content_data.get('media', [])
                if media_files:
                    for file in media_files:
                        try:
                            media_id = dm.save_media(username, file)
                            media_ids.append(media_id)
                            logger.info(f"Media {media_id} uploaded for blog edit by {username}")
                        except ValueError as e:
                            st.error(str(e))
                            logger.error(f"Media upload failed for blog edit by {username}: {str(e)}")
                            return
                try:
                    if is_draft:
                        draft_data = {
                            'title': title,
                            'content': content_text,
                            'tags': tags,
                            'media': media_ids,
                            'font': font,
                            'is_published': is_published,
                            'is_draft': is_draft_save
                        }
                        new_draft_id = dm.save_draft(username, 'blog', content_id if content_data.get(
                            'content_id') else None, draft_data)
                        st.success(f"Draft updated! Draft ID: {new_draft_id}")
                        logger.info(f"Blog draft {new_draft_id} updated by {username}")
                    else:
                        if dm.update_blog(content_id, title, content_text, tags, media_ids, font, is_published, is_draft_save):
                            st.success("Blog updated successfully")
                            logger.info(f"Blog {content_id} updated by {username}")
                            dm.log_analytics_event(username, 'update_blog', 'blog', content_id)
                        else:
                            st.error("Failed to update blog")
                            logger.error(f"Failed to update blog {content_id} for {username}")
                except Exception as e:
                    st.error(f"Error updating blog: {str(e)}")
                    logger.error(f"Blog update error for {username}: {str(e)}")
        else:
            problem = st.text_area("Problem", value=content_data.get('problem', ''), height=200)
            solution = st.text_area("Solution", value=content_data.get('solution', ''), height=200)
            results = st.text_area("Results", value=content_data.get('results', ''), height=200)
            if st.form_submit_button("Update Case Study"):
                media_ids = content_data.get('media', [])
                if media_files:
                    for file in media_files:
                        try:
                            media_id = dm.save_media(username, file)
                            media_ids.append(media_id)
                            logger.info(f"Media {media_id} uploaded for case study edit by {username}")
                        except ValueError as e:
                            st.error(str(e))
                            logger.error(f"Media upload failed for case study edit by {username}: {str(e)}")
                            return
                try:
                    if is_draft:
                        draft_data = {
                            'title': title,
                            'problem': problem,
                            'solution': solution,
                            'results': results,
                            'tags': tags,
                            'media': media_ids,
                            'font': font,
                            'is_published': is_published,
                            'is_draft': is_draft_save
                        }
                        new_draft_id = dm.save_draft(username, 'case_study',
                                                     content_id if content_data.get('content_id') else None, draft_data)
                        st.success(f"Draft updated! Draft ID: {new_draft_id}")
                        logger.info(f"Case study draft {new_draft_id} updated by {username}")
                    else:
                        if dm.update_case_study(content_id, title, problem, solution, results, tags, media_ids, font, is_published, is_draft_save):
                            st.success("Case Study updated successfully")
                            logger.info(f"Case study {content_id} updated by {username}")
                            dm.log_analytics_event(username, 'update_case_study', 'case_study', content_id)
                        else:
                            st.error("Failed to update case study")
                            logger.error(f"Failed to update case study {content_id} for {username}")
                except Exception as e:
                    st.error(f"Error updating case study: {str(e)}")
                    logger.error(f"Case study update error for {username}: {str(e)}")


def view_content_page():
    """
    Render public content view page.
    Displays published blogs and case studies with search, tags, and interactions.
    """
    st.title("Explore Content")
    dm = get_data_manager()
    search_query = st.text_input("Search Content", help="Search by title or content")
    tag_options = [tag.name for tag in Session().query(Tag).all()]
    selected_tags = st.multiselect("Filter by Tags", tag_options, help="Select tags to filter content")
    content_type = st.selectbox("Content Type", ["All", "Blog", "Case Study"], help="Filter by content type")

    content_type_filter = None if content_type == "All" else content_type.lower()
    contents = dm.search_content(search_query, selected_tags, content_type_filter)

    with Session() as session:
        for content in contents:
            with st.container():
                st.markdown("<div class='content-card'>", unsafe_allow_html=True)
                st.subheader(content.title)
                if content.content_type == 'blog':
                    st.write(content.content[:300] + "..." if len(content.content) > 300 else content.content)
                    content.views += 1
                else:
                    st.write(f"Problem: {content.problem[:200]}...")
                    st.write(f"Solution: {content.solution[:200]}...")
                    st.write(f"Results: {content.results[:200]}...")
                    content.views += 1
                st.write(f"By {content.username} | {content.created_at.strftime('%Y-%m-%d')} | Views: {content.views}")
                st.markdown(
                    "**Tags:** " + ", ".join([f"<span class='tag'>{tag}</span>" for tag in content.tags]), unsafe_allow_html=True)

                if content.media:
                    cols = st.columns(min(len(content.media), 3))
                    for idx, media_id in enumerate(content.media):
                        media = session.query(Media).filter_by(id=media_id).first()
                        if media and media.type == 'image':
                            try:
                                img_data = base64.b64decode(media.content)
                                img = Image.open(io.BytesIO(img_data))
                                with cols[idx % 3]:
                                    st.image(img, caption=media.filename, width=200)
                            except Exception as e:
                                logger.error(f"Error rendering media {media_id}: {str(e)}")
                                st.warning(f"Could not display media: {media.filename}")

                like_count = session.query(Like).filter_by(
                    content_type=content.content_type, content_id=content.id
                ).count()
                st.write(f"Likes: {like_count}")
                if st.session_state.authenticated:
                    user = session.query(User).filter_by(username=st.session_state.username).first()
                    has_liked = session.query(Like).filter_by(
                        user_id=user.id,
                        content_type=content.content_type,
                        content_id=content.id
                    ).first()
                    col1, col2 = st.columns(2)
                    with col1:
                        if not has_liked:
                            if st.button(f"Like", key=f"like_{content.id}"):
                                dm.save_like(st.session_state.username, content.content_type, content.id)
                                dm.log_analytics_event(st.session_state.username, 'like',
                                                       content.content_type, content.id)
                                st.rerun()
                        else:
                            if st.button(f"Unlike", key=f"unlike_{content.id}"):
                                dm.remove_like(st.session_state.username, content.content_type, content.id)
                                dm.log_analytics_event(st.session_state.username, 'unlike',
                                                       content.content_type, content.id)
                                st.rerun()
                    with col2:
                        if st.button(f"Share", key=f"share_{content.id}"):
                            st.write(f"Share this {content.content_type}: {content.public_link}")
                            dm.log_analytics_event(st.session_state.username, 'share', content.content_type, content.id)

                st.subheader("Comments")
                comments = session.query(Comment).filter_by(
                    content_type=content.content_type, content_id=content.id
                ).order_by(Comment.created_at.desc()).limit(5).all()
                for comment in comments:
                    st.markdown(
                        f"<div class='comment'>{comment.username}: {comment.comment} ({comment.created_at.strftime('%Y-%m-%d %H:%M')})</div>",
                        unsafe_allow_html=True
                    )

                if st.session_state.authenticated:
                    comment_text = st.text_area(f"Comment on {content.title}", key=f"comment_{content.id}", height=100)
                    if st.button("Post Comment", key=f"post_{content.id}"):
                        try:
                            comment_id = dm.save_comment(st.session_state.username,
                                                         content.content_type, content.id, comment_text)
                            st.success("Comment posted!")
                            logger.info(f"Comment {comment_id} posted by {st.session_state.username}")
                            dm.log_analytics_event(st.session_state.username, 'comment',
                                                   content.content_type, content.id)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                            logger.error(f"Comment posting failed for {st.session_state.username}: {str(e)}")

                st.markdown(f"[View Full {content.content_type.capitalize()}]({content.public_link})")
                st.markdown("</div>", unsafe_allow_html=True)
        try:
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing view updates: {str(e)}")
            st.error("Error updating view counts")


def analytics_page():
    """
    Render user analytics dashboard.
    Displays content performance metrics and event logs.
    """
    st.title("Analytics Dashboard")
    dm = get_data_manager()
    username = st.session_state.username
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    end_date = st.date_input("End Date", value=datetime.now())

    try:
        analytics = dm.get_analytics(
            username,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time())
        )
        st.subheader("Content Performance")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Views", analytics.get('total_views', 0))
        with col2:
            st.metric("Total Likes", analytics.get('total_likes', 0))
        with col3:
            st.metric("Blogs", analytics.get('blog_count', 0))
        with col4:
            st.metric("Case Studies", analytics.get('case_study_count', 0))

        with Session() as session:
            blogs = session.query(Blog.id, Blog.title, Blog.views, Blog.created_at).filter_by(username=username).all()
            case_studies = session.query(CaseStudy.id, CaseStudy.title, CaseStudy.views,
                                         CaseStudy.created_at).filter_by(username=username).all()

            if blogs or case_studies:
                df = pd.DataFrame([
                    {'ID': b.id, 'Title': b.title, 'Views': b.views, 'Type': 'Blog', 'Created': b.created_at}
                    for b in blogs
                ] + [
                    {'ID': c.id, 'Title': c.title, 'Views': c.views, 'Type': 'Case Study', 'Created': c.created_at}
                    for c in case_studies
                ])
                st.subheader("Views Over Time")
                st.line_chart(df.groupby(df['Created'].dt.date)['Views'].sum())

                st.subheader("Top Performing Content")
                st.dataframe(df.sort_values('Views', ascending=False)[['Title', 'Type', 'Views']].head(5))

        st.subheader("Event Logs")
        events = session.query(AnalyticsEvent).filter_by(user_id=session.query(
            User).filter_by(username=username).first().id).limit(20).all()
        event_data = [
            {'Event Type': e.event_type, 'Content Type': e.content_type or 'N/A',
                'Content ID': e.content_id or 'N/A', 'Timestamp': e.timestamp, 'Metadata': json.dumps(e.metadata)}
            for e in events
        ]
        st.dataframe(event_data)
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving analytics for {username}: {str(e)}")
        st.error("Error loading analytics data")
    except Exception as e:
        logger.error(f"Unexpected error in analytics for {username}: {str(e)}")
        st.error("An unexpected error occurred")


def admin_dashboard():
    """
    Render admin dashboard for content and user management.
    Restricted to admin users.
    """
    if not st.session_state.get('is_admin', False):
        st.error("Access restricted to administrators")
        logger.warning(f"Non-admin {st.session_state.username} attempted to access admin dashboard")
        return

    st.title("Admin Dashboard")
    dm = get_data_manager()

    st.subheader("Manage Users")
    try:
        with Session() as session:
            users = session.query(User).all()
            user_data = [
                {
                    'ID': u.id,
                    'Username': u.username,
                    'Email': u.email,
                    'Active': u.is_active,
                    'Admin': u.is_admin,
                    'Last Login': u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'Never'
                }
                for u in users
            ]
            st.dataframe(user_data)

            st.subheader("Toggle User Status")
            user_to_toggle = st.selectbox("Select User", [u.username for u in users], key="toggle_user")
            new_status = st.selectbox("Set Status", ["Active", "Inactive"], key="user_status")
            if st.button("Update User Status"):
                user = session.query(User).filter_by(username=user_to_toggle).first()
                user.is_active = (new_status == "Active")
                session.commit()
                st.success(f"User {user_to_toggle} status updated to {new_status}")
                logger.info(f"Admin {st.session_state.username} updated {user_to_toggle} status to {new_status}")
                dm.log_analytics_event(st.session_state.username, 'admin_update_user',
                                       metadata={'user': user_to_toggle})
    except SQLAlchemyError as e:
        logger.error(f"Error managing users in admin dashboard: {str(e)}")
        st.error("Error managing users")

    st.subheader("Manage Content")
    content_type = st.selectbox("Content Type", ["Blog", "Case Study"], key="admin_content_type")
    try:
        contents = dm.get_user_content("all", content_type.lower())
        for content in contents:
            with st.expander(f"{content.title} by {content.username}"):
                st.write(f"Published: {content.is_published}, Draft: {content.is_draft}")
                st.write(f"Created: {content.created_at}, Updated: {content.updated_at}")
                if st.button(f"Delete {content.title}", key=f"delete_{content.id}"):
                    if dm.delete_content(content_type.lower(), content.id):
                        st.success(f"{content.title} deleted")
                        logger.info(f"Admin {st.session_state.username} deleted {content_type}:{content.id}")
                        dm.log_analytics_event(st.session_state.username,
                                               'admin_delete_content', content_type, content.id)
                        st.rerun()
                    else:
                        st.error("Failed to delete content")
                        logger.error(f"Failed to delete {content_type}:{content.id}")
    except SQLAlchemyError as e:
        logger.error(f"Error managing content in admin dashboard: {str(e)}")
        st.error("Error managing content")


def public_profile_page():
    """
    Render public profile page for a user.
    Displays user bio, social links, and public content.
    """
    st.title("View User Profile")
    username = st.text_input("Enter Username", help="Enter the username to view their profile")
    if not username:
        return

    dm = get_data_manager()
    try:
        with Session() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                st.error("User not found")
                logger.error(f"Public profile not found for {username}")
                return
            profile = user.profile or {}
            st.subheader(f"{username}'s Profile")
            st.write(f"**Bio**: {profile.get('bio', 'No bio available')}")
            st.write(f"**Website**: {profile.get('website', 'No website') or 'None'}")
            social_links = profile.get('social_links', {})
            if social_links:
                st.subheader("Social Links")
                for platform, link in social_links.items():
                    st.markdown(f"- [{platform}]({link})")

            profile_picture = profile.get('profile_picture')
            if profile_picture:
                media = session.query(Media).filter_by(id=profile_picture).first()
                if media and media.type == 'image':
                    try:
                        img_data = base64.b64decode(media.content)
                        img = Image.open(io.BytesIO(img_data))
                        st.image(img, caption="Profile Picture", width=150)
                    except Exception as e:
                        logger.error(f"Error rendering profile picture for {username}: {str(e)}")

            if st.session_state.authenticated and st.session_state.username != username:
                user_obj = session.query(User).filter_by(username=st.session_state.username).first()
                following = user_obj.profile.get('following', [])
                if username not in following:
                    if st.button(f"Follow {username}"):
                        following.append(username)
                        dm.update_user_profile(st.session_state.username, {'following': following})
                        st.success(f"You are now following {username}")
                        logger.info(f"{st.session_state.username} followed {username}")
                        dm.log_analytics_event(st.session_state.username, 'follow',
                                               metadata={'followed_user': username})
                        st.rerun()
                else:
                    if st.button(f"Unfollow {username}"):
                        following.remove(username)
                        dm.update_user_profile(st.session_state.username, {'following': following})
                        st.success(f"You have unfollowed {username}")
                        logger.info(f"{st.session_state.username} unfollowed {username}")
                        dm.log_analytics_event(st.session_state.username, 'unfollow',
                                               metadata={'unfollowed_user': username})
                        st.rerun()

            st.subheader("Public Content")
            blogs = session.query(Blog).filter_by(username=username, is_published=True).all()
            case_studies = session.query(CaseStudy).filter_by(username=username, is_published=True).all()
            if not (blogs or case_studies):
                st.info("No public content available")
            for content in blogs + case_studies:
                st.markdown(f"- [{content.title}]({content.public_link}) ({content.content_type.capitalize()})")
            dm.log_analytics_event(st.session_state.username if st.session_state.authenticated else None,
                                   'view_profile', metadata={'profile_user': username})
    except SQLAlchemyError as e:
        logger.error(f"Error loading public profile for {username}: {str(e)}")
        st.error("Error loading profile")


def notifications_page():
    """
    Render notifications page.
    Displays user notifications with read/unread status.
    """
    st.title("Notifications")
    if not st.session_state.authenticated:
        st.warning("Please log in to view notifications")
        return

    dm = get_data_manager()
    username = st.session_state.username
    show_unread = st.checkbox("Show Unread Only", value=True)

    try:
        notifications = dm.get_notifications(username, unread_only=show_unread)
        if not notifications:
            st.info("No notifications available")
            return

        for notification in notifications:
            with st.container():
                st.markdown(
                    f"<div class='notification'>{'📬 ' if not notification.is_read else ''}{notification.message} "
                    f"({notification.created_at.strftime('%Y-%m-%d %H:%M')})</div>",
                    unsafe_allow_html=True
                )
                if notification.content_type and notification.content_id:
                    content = dm.get_content_by_id(notification.content_type, notification.content_id)
                    if content:
                        st.markdown(f"[View {notification.content_type.capitalize()}]({content.public_link})")
                if not notification.is_read:
                    if st.button("Mark as Read", key=f"read_{notification.id}"):
                        dm.mark_notification_read(notification.id)
                        st.rerun()
        dm.log_analytics_event(username, 'view_notifications')
    except SQLAlchemyError as e:
        logger.error(f"Error loading notifications for {username}: {str(e)}")
        st.error("Error loading notifications")


def tag_explorer_page():
    """
    Render tag explorer page.
    Allows users to browse content by tags.
    """
    st.title("Explore by Tags")
    dm = get_data_manager()
    try:
        with Session() as session:
            tags = session.query(Tag).all()
            if not tags:
                st.info("No tags available")
                return
            selected_tag = st.selectbox("Select Tag", [tag.name for tag in tags])
            if selected_tag:
                tag = session.query(Tag).filter_by(name=selected_tag).first()
                blogs = tag.blogs
                case_studies = tag.case_studies
                st.subheader(f"Content tagged with '{selected_tag}'")
                for content in blogs + case_studies:
                    if content.is_published:
                        with st.container():
                            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
                            st.write(f"**{content.title}** ({content.content_type.capitalize()})")
                            st.write(f"By {content.username} | {content.created_at.strftime('%Y-%m-%d')}")
                            st.markdown(f"[View Content]({content.public_link})")
                            st.markdown("</div>", unsafe_allow_html=True)
                dm.log_analytics_event(
                    st.session_state.username if st.session_state.authenticated else None,
                    'explore_tag',
                    metadata={'tag': selected_tag}
                )
    except SQLAlchemyError as e:
        logger.error(f"Error exploring tags: {str(e)}")
        st.error("Error loading tag content")


def draft_management_page():
    """
    Render draft management page.
    Allows users to view, edit, or publish drafts.
    """
    st.title("Manage Drafts")
    if not st.session_state.authenticated:
        st.warning("Please log in to manage drafts")
        return

    dm = get_data_manager()
    username = st.session_state.username
    content_type = st.selectbox("Content Type", ["Blog", "Case Study"], key="draft_content_type")

    try:
        with Session() as session:
            drafts = dm.get_drafts(username, content_type.lower())
            if not drafts:
                st.info("No drafts available")
                return

            for draft in drafts:
                with st.expander(f"{draft.data.get('title', 'Untitled')} (Created: {draft.created_at.strftime('%Y-%m-%d')})"):
                    st.write(f"Content Type: {draft.content_type.capitalize()}")
                    if st.button("Edit Draft", key=f"edit_draft_{draft.id}"):
                        st.session_state.edit_draft_id = draft.id
                        st.session_state.edit_draft_type = content_type.lower()
                        st.rerun()
                    if st.button("Publish Draft", key=f"publish_draft_{draft.id}"):
                        data = draft.data
                        try:
                            if content_type.lower() == 'blog':
                                blog_id = dm.save_blog(
                                    username,
                                    data.get('title'),
                                    data.get('content'),
                                    ', '.join(data.get('tags', [])),
                                    data.get('media', []),
                                    data.get('font', 'Inter'),
                                    True,
                                    False
                                )
                                draft.content_id = blog_id
                                session.commit()
                                st.success(f"Blog published! ID: {blog_id}")
                                logger.info(f"Draft {draft.id} published as blog {blog_id} by {username}")
                                dm.log_analytics_event(username, 'publish_draft', 'blog', blog_id)
                            else:
                                case_id = dm.save_case_study(
                                    username,
                                    data.get('title'),
                                    data.get('problem'),
                                    data.get('solution'),
                                    data.get('results'),
                                    ', '.join(data.get('tags', [])),
                                    data.get('media', []),
                                    data.get('font', 'Inter'),
                                    True,
                                    False
                                )
                                draft.content_id = case_id
                                session.commit()
                                st.success(f"Case Study published! ID: {case_id}")
                                logger.info(f"Draft {draft.id} published as case study {case_id} by {username}")
                                dm.log_analytics_event(username, 'publish_draft', 'case_study', case_id)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                            logger.error(f"Error publishing draft {draft.id}: {str(e)}")
    except SQLAlchemyError as e:
        logger.error(f"Error managing drafts for {username}: {str(e)}")
        st.error("Error loading drafts")

    if 'edit_draft_id' in st.session_state:
        draft_id = st.session_state.edit_draft_id
        draft_type = st.session_state.edit_draft_type
        draft = next((d for d in drafts if d.id == draft_id), None)
        if draft:
            with st.form("edit_draft_form"):
                data = draft.data
                title = st.text_input("Title", value=data.get('title', ''))
                tags = st.text_input("Tags", value=', '.join(data.get('tags', [])))
                media_files = st.file_uploader("Upload New Media", accept_multiple_files=True)
                font = st.selectbox("Font", ["Inter", "Arial", "Times New Roman", "Roboto"], index=[
                                    "Inter", "Arial", "Times New Roman", "Roboto"].index(data.get('font', 'Inter')))
                is_published = st.checkbox("Publish Immediately", value=data.get('is_published', True))

                if draft_type == 'blog':
                    content = st.text_area("Content", value=data.get('content', ''), height=300)
                    if st.form_submit_button("Update Draft"):
                        media_ids = data.get('media', [])
                        if media_files:
                            for file in media_files:
                                media_id = dm.save_media(username, file)
                                media_ids.append(media_id)
                        new_data = {
                            'title': title,
                            'content': content,
                            'tags': [t.strip() for t in tags.split(',') if t.strip()],
                            'media': media_ids,
                            'font': font,
                            'is_published': is_published,
                            'is_draft': True
                        }
                        try:
                            new_draft_id = dm.save_draft(username, 'blog', draft.content_id, new_data)
                            st.success(f"Draft updated! New Draft ID: {new_draft_id}")
                            logger.info(f"Draft {draft_id} updated to {new_draft_id} by {username}")
                            del st.session_state.edit_draft_id
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                            logger.error(f"Error updating draft {draft_id}: {str(e)}")
                else:
                    problem = st.text_area("Problem", value=data.get('problem', ''), height=200)
                    solution = st.text_area("Solution", value=data.get('solution', ''), height=200)
                    results = st.text_area("Results", value=data.get('results', ''), height=200)
                    if st.form_submit_button("Update Draft"):
                        media_ids = data.get('media', [])
                        if media_files:
                            for file in media_files:
                                media_id = dm.save_media(username, file)
                                media_ids.append(media_id)
                        new_data = {
                            'title': title,
                            'problem': problem,
                            'solution': solution,
                            'results': results,
                            'tags': [t.strip() for t in tags.split(',') if t.strip()],
                            'media': media_ids,
                            'font': font,
                            'is_published': is_published,
                            'is_draft': True
                        }
                        try:
                            new_draft_id = dm.save_draft(username, 'case_study', draft.content_id, new_data)
                            st.success(f"Draft updated! New Draft ID: {new_draft_id}")
                            logger.info(f"Draft {draft_id} updated to {new_draft_id} by {username}")
                            del st.session_state.edit_draft_id
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                            logger.error(f"Error updating draft {draft_id}: {str(e)}")


def user_settings_page():
    """
    Render user settings page.
    Allows users to configure preferences and account settings.
    """
    st.title("User Settings")
    if not st.session_state.authenticated:
        st.warning("Please log in to access settings")
        return

    dm = get_data_manager()
    username = st.session_state.username
    try:
        with Session() as session:
            user = session.query(User).filter_by(username=username).first()
            profile = user.profile or {}

            st.subheader("Notification Preferences")
            with st.form("notification_prefs"):
                notify_comments = st.checkbox("Notify on new comments", value=profile.get('notify_comments', True))
                notify_likes = st.checkbox("Notify on new likes", value=profile.get('notify_likes', True))
                notify_followers = st.checkbox("Notify on new followers", value=profile.get('notify_followers', True))
                if st.form_submit_button("Save Notification Preferences"):
                    profile.update({
                        'notify_comments': notify_comments,
                        'notify_likes': notify_likes,
                        'notify_followers': notify_followers
                    })
                    dm.update_user_profile(username, profile)
                    st.success("Notification preferences updated")
                    logger.info(f"Notification preferences updated for {username}")
                    dm.log_analytics_event(username, 'update_settings')

            st.subheader("Account Management")
            if st.button("Deactivate Account"):
                if st.checkbox("Confirm Deactivation"):
                    user.is_active = False
                    session.commit()
                    st.session_state.authenticated = False
                    st.session_state.username = None
                    st.success("Account deactivated")
                    logger.info(f"Account deactivated for {username}")
                    dm.log_analytics_event(username, 'deactivate_account')
                    st.rerun()
    except SQLAlchemyError as e:
        logger.error(f"Error updating settings for {username}: {str(e)}")
        st.error("Error updating settings")


def enhanced_main():
    """
    Main application entry point.
    Orchestrates navigation and page rendering.
    """
    custom_css()
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.is_admin = False

    if not st.session_state.authenticated:
        st.title("Welcome to GalaxyWrite")
        st.markdown("A platform for sharing blogs, case studies, and ideas.")
        login_page()
        st.subheader("New User? Sign Up")
        signup_page()
        return

    st.sidebar.title(f"Welcome, {st.session_state.username}")
    pages = [
        "View Content",
        "Create Content",
        "Edit Content",
        "Analytics",
        "Profile",
        "Public Profile",
        "Notifications",
        "Tag Explorer",
        "Draft Management",
        "Settings",
        "Logout"
    ]
    if st.session_state.is_admin:
        pages.insert(-1, "Admin Dashboard")

    page = st.sidebar.selectbox("Navigate", pages, help="Select a page to view")

    try:
        if page == "View Content":
            view_content_page()
        elif page == "Create Content":
            create_content_page()
        elif page == "Edit Content":
            edit_content_page()
        elif page == "Analytics":
            analytics_page()
        elif page == "Profile":
            profile_page()
        elif page == "Public Profile":
            public_profile_page()
        elif page == "Notifications":
            notifications_page()
        elif page == "Tag Explorer":
            tag_explorer_page()
        elif page == "Draft Management":
            draft_management_page()
        elif page == "Settings":
            user_settings_page()
        elif page == "Admin Dashboard":
            admin_dashboard()
        elif page == "Logout":
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.is_admin = False
            st.success("Logged out successfully")
            logger.info(f"User {st.session_state.username} logged out")
            dm = get_data_manager()
            dm.log_analytics_event(st.session_state.username, 'logout')
            st.rerun()
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

# Helper Functions


def validate_input(text: str, max_length: int = 1000) -> bool:
    """
    Validate input text for length and content.
    Args:
        text: Input text to validate.
        max_length: Maximum allowed length.
    Returns:
        bool: True if valid, False otherwise.
    """
    if not text:
        return False
    if len(text) > max_length:
        logger.warning(f"Input text exceeds max length: {len(text)}")
        return False
    return True


def render_media(media: Media, width: int = 300) -> None:
    """
    Render media content in Streamlit.
    Args:
        media: Media object.
        width: Image width in pixels.
    """
    try:
        if media.type == 'image':
            img_data = base64.b64decode(media.content)
            img = Image.open(io.BytesIO(img_data))
            st.image(img, caption=media.filename, width=width)
        elif media.type == 'video':
            st.video(base64.b64decode(media.content))
        else:
            st.warning(f"Unsupported media type: {media.type}")
    except Exception as e:
        logger.error(f"Error rendering media {media.id}: {str(e)}")
        st.warning(f"Could not display media: {media.filename}")


def get_popular_tags(limit: int = 10) -> List[str]:
    """
    Retrieve popular tags based on usage.
    Args:
        limit: Maximum number of tags to return.
    Returns:
        List[str]: List of tag names.
    """
    try:
        with Session() as session:
            tags = session.query(Tag).join(blog_tags).group_by(Tag.id).order_by(
                func.count(blog_tags.c.blog_id).desc()).limit(limit).all()
            tags += session.query(Tag).join(case_study_tags).group_by(Tag.id).order_by(
                func.count(case_study_tags.c.case_study_id).desc()).limit(limit).all()
            return list(set(tag.name for tag in tags))[:limit]
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving popular tags: {str(e)}")
        return []


if __name__ == "__main__":
    enhanced_main()
