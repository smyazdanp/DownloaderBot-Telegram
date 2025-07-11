#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات دانلودر فوق حرفه‌ای تلگرام
نسخه: 3.0 - Enterprise Edition
توسعه‌دهنده: Professional Bot Developer
"""

import os
import sys
import asyncio
import aiohttp
import sqlite3
import logging
import zipfile
import hashlib
import json
import time
import io
import tempfile
import shutil
import mimetypes
import traceback
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote, quote
from typing import Optional, List, Tuple, Dict, Union, Any
from functools import wraps
from pathlib import Path
from contextlib import asynccontextmanager
import re

# بررسی کتابخانه‌ها
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, StateFilter, CommandStart
    from aiogram.types import (
        Message, FSInputFile, InlineKeyboardMarkup, 
        InlineKeyboardButton, CallbackQuery, BufferedInputFile,
        InputFile, URLInputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
    import aiofiles
    import magic
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import font_manager
    import numpy as np
except ImportError as e:
    print(f"❌ خطا: کتابخانه‌های مورد نیاز نصب نشده‌اند!")
    print(f"خطا: {e}")
    print("\n📦 برای نصب:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# ===== تنظیمات اصلی =====
BOT_TOKEN = "8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw"
ADMIN_IDS = [111111111]

# محدودیت‌ها
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2000MB (کمی کمتر از 2GB برای اطمینان)
CHUNK_SIZE = 1900 * 1024 * 1024  # 1900MB برای هر بخش
DEFAULT_DAILY_LIMIT = 10
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks
MAX_CONCURRENT_DOWNLOADS = 3
DOWNLOAD_TIMEOUT = 3600  # 1 ساعت

# Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ایجاد پوشه‌ها
for folder in ['downloads', 'uploads', 'temp', 'logs', 'backups']:
    os.makedirs(folder, exist_ok=True)

# ===== ایجاد ربات =====
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ===== States =====
class DownloadStates(StatesGroup):
    choosing_format = State()
    waiting_for_url = State()

class AdminStates(StatesGroup):
    setting_global_limit = State()
    setting_user_limit = State()
    uploading_file = State()
    waiting_user_id = State()
    broadcast_message = State()
    waiting_vip_user_id = State()
    waiting_ban_user_id = State()

# ===== دیتابیس پیشرفته =====
class Database:
    """سیستم دیتابیس پیشرفته با قابلیت transaction و error handling"""
    
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self):
        """ایجاد connection جدید با تنظیمات بهینه"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager برای transaction"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """ایجاد و تنظیم جداول دیتابیس"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # جدول کاربران با فیلدهای کامل
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'fa',
                    is_vip INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    daily_limit INTEGER,
                    total_downloads INTEGER DEFAULT 0,
                    total_size INTEGER DEFAULT 0,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # جدول دانلودها با اطلاعات کامل
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_url TEXT NOT NULL,
                    file_name TEXT,
                    file_size INTEGER,
                    file_type TEXT,
                    mime_type TEXT,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT,
                    download_time REAL,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول آپلودها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT UNIQUE NOT NULL,
                    admin_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    file_path TEXT NOT NULL,
                    mime_type TEXT,
                    download_count INTEGER DEFAULT 0,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expire_date TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (admin_id) REFERENCES users (user_id)
                )
            ''')
            
            # جدول تنظیمات با نوع داده
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    value_type TEXT DEFAULT 'string',
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                )
            ''')
            
            # جدول لاگ با جزئیات بیشتر
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # جدول آمار روزانه
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    total_downloads INTEGER DEFAULT 0,
                    total_size INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ایندکس‌ها برای performance
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_downloads_user_date ON downloads(user_id, download_date)",
                "CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)",
                "CREATE INDEX IF NOT EXISTS idx_uploads_hash ON uploads(file_hash)",
                "CREATE INDEX IF NOT EXISTS idx_uploads_active ON uploads(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_logs_user_time ON activity_logs(user_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)"
            ]
            
            for index in indices:
                cursor.execute(index)
            
            # تنظیمات پیش‌فرض با نوع صحیح
            default_settings = [
                ('global_daily_limit', str(DEFAULT_DAILY_LIMIT), 'integer', 'محدودیت روزانه عمومی'),
                ('download_enabled', '1', 'boolean', 'وضعیت فعال بودن دانلود'),
                ('maintenance_mode', '0', 'boolean', 'حالت تعمیر و نگهداری'),
                ('welcome_message', 'به ربات دانلودر خوش آمدید!', 'string', 'پیام خوش‌آمدگویی'),
                ('max_file_size', str(MAX_FILE_SIZE), 'integer', 'حداکثر حجم فایل'),
                ('vip_unlimited', '1', 'boolean', 'دانلود نامحدود برای VIP'),
                ('auto_cleanup_days', '7', 'integer', 'روزهای نگهداری فایل‌های موقت'),
                ('enable_stats', '1', 'boolean', 'فعال بودن آمارگیری'),
                ('flood_limit', '5', 'integer', 'حد flood در دقیقه'),
                ('compression_enabled', '1', 'boolean', 'فشرده‌سازی فایل‌های بزرگ')
            ]
            
            for key, value, value_type, description in default_settings:
                cursor.execute('''
                    INSERT OR IGNORE INTO settings (key, value, value_type, description)
                    VALUES (?, ?, ?, ?)
                ''', (key, value, value_type, description))
            
            conn.commit()
            logger.info("✅ دیتابیس با موفقیت راه‌اندازی شد")
            
        except Exception as e:
            logger.error(f"خطا در راه‌اندازی دیتابیس: {e}")
            raise
        finally:
            conn.close()
    
    def add_user(self, user_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None,
                 language_code: str = 'fa') -> bool:
        """ثبت یا به‌روزرسانی کاربر"""
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, language_code)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        last_activity = CURRENT_TIMESTAMP
                ''', (user_id, username, first_name, last_name, language_code))
                conn.commit()
                
                # آمار کاربر جدید
                if cursor.lastrowid:
                    self._update_daily_stats('new_users', 1)
                
                return True
            except Exception as e:
                logger.error(f"Error adding user {user_id}: {e}")
                return False
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """دریافت اطلاعات کامل کاربر"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                user_dict = dict(row)
                # Parse settings JSON
                try:
                    user_dict['settings'] = json.loads(user_dict.get('settings', '{}'))
                except:
                    user_dict['settings'] = {}
                return user_dict
            return None
    
    def is_user_banned(self, user_id: int) -> bool:
        """بررسی وضعیت بن کاربر"""
        user = self.get_user(user_id)
        return bool(user and user['is_banned'])
    
    def set_user_status(self, user_id: int, is_vip: bool = None, is_banned: bool = None):
        """تنظیم وضعیت کاربر"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if is_vip is not None:
                updates.append("is_vip = ?")
                params.append(int(is_vip))
                
            if is_banned is not None:
                updates.append("is_banned = ?")
                params.append(int(is_banned))
            
            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                # لاگ
                action = []
                if is_vip is not None:
                    action.append(f"VIP={'ON' if is_vip else 'OFF'}")
                if is_banned is not None:
                    action.append(f"Ban={'ON' if is_banned else 'OFF'}")
                
                self.log_activity(user_id, 'status_change', ' | '.join(action))
    
    def add_download(self, user_id: int, file_url: str, file_name: str, 
                    file_size: int, file_type: str = 'document', 
                    mime_type: str = None, status: str = 'completed',
                    download_time: float = 0, error_message: str = None) -> int:
        """ثبت دانلود با اطلاعات کامل"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # ثبت دانلود
            cursor.execute('''
                INSERT INTO downloads 
                (user_id, file_url, file_name, file_size, file_type, 
                 mime_type, status, download_time, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, file_url, file_name, file_size, file_type, 
                  mime_type, status, download_time, error_message))
            
            download_id = cursor.lastrowid
            
            # به‌روزرسانی آمار کاربر
            if status == 'completed':
                cursor.execute('''
                    UPDATE users 
                    SET total_downloads = total_downloads + 1,
                        total_size = total_size + ?,
                        last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (file_size, user_id))
                
                # آمار روزانه
                self._update_daily_stats('total_downloads', 1)
                self._update_daily_stats('total_size', file_size)
            
            conn.commit()
            
            # لاگ
            self.log_activity(user_id, 'download', 
                            f'{file_name} ({format_size(file_size)}) - {status}')
            
            return download_id
    
    def get_daily_downloads(self, user_id: int) -> Tuple[int, int]:
        """تعداد و حجم دانلودهای امروز"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(file_size), 0)
                FROM downloads 
                WHERE user_id = ? 
                AND DATE(download_date) = DATE('now', 'localtime')
                AND status = 'completed'
            ''', (user_id,))
            count, size = cursor.fetchone()
            return count or 0, size or 0
    
    def get_user_limit(self, user_id: int) -> int:
        """محاسبه محدودیت کاربر"""
        user = self.get_user(user_id)
        if not user:
            return self.get_setting('global_daily_limit', DEFAULT_DAILY_LIMIT)
        
        # VIP check
        if user['is_vip'] and self.get_setting('vip_unlimited', True):
            return 999999
        
        # محدودیت شخصی
        if user['daily_limit'] is not None:
            return user['daily_limit']
        
        # محدودیت عمومی
        return self.get_setting('global_daily_limit', DEFAULT_DAILY_LIMIT)
    
    def set_user_limit(self, user_id: int, limit: Optional[int]):
        """تنظیم محدودیت شخصی"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET daily_limit = ? WHERE user_id = ?',
                (limit, user_id)
            )
            conn.commit()
            self.log_activity(user_id, 'limit_change', f'Set to {limit}')
    
    def get_setting(self, key: str, default=None):
        """دریافت تنظیمات با type conversion"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT value, value_type FROM settings WHERE key = ?', 
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return default
            
            value, value_type = row
            
            # تبدیل نوع
            try:
                if value_type == 'integer':
                    return int(value)
                elif value_type == 'boolean':
                    return value in ('1', 'true', 'True', 'yes')
                elif value_type == 'float':
                    return float(value)
                elif value_type == 'json':
                    return json.loads(value)
                else:
                    return value
            except:
                return default
    
    def set_setting(self, key: str, value: Any, value_type: str = None, 
                   updated_by: int = None):
        """ذخیره تنظیمات با type safety"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # تشخیص نوع
            if value_type is None:
                if isinstance(value, bool):
                    value_type = 'boolean'
                    value = '1' if value else '0'
                elif isinstance(value, int):
                    value_type = 'integer'
                    value = str(value)
                elif isinstance(value, float):
                    value_type = 'float'
                    value = str(value)
                elif isinstance(value, (dict, list)):
                    value_type = 'json'
                    value = json.dumps(value)
                else:
                    value_type = 'string'
                    value = str(value)
            
            cursor.execute('''
                INSERT INTO settings (key, value, value_type, updated_at, updated_by)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    value_type = excluded.value_type,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = excluded.updated_by
            ''', (key, str(value), value_type, updated_by))
            
            conn.commit()
            logger.info(f"Setting updated: {key} = {value} ({value_type})")
    
    def get_all_users(self, limit: int = 50, offset: int = 0, 
                     filter_vip: bool = None, filter_banned: bool = None,
                     search: str = None) -> Tuple[List[dict], int]:
        """دریافت لیست کاربران با فیلتر و جستجو"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Query اصلی
            where_clauses = []
            params = []
            
            if filter_vip is not None:
                where_clauses.append("is_vip = ?")
                params.append(int(filter_vip))
                
            if filter_banned is not None:
                where_clauses.append("is_banned = ?")
                params.append(int(filter_banned))
                
            if search:
                where_clauses.append(
                    "(username LIKE ? OR first_name LIKE ? OR user_id LIKE ?)"
                )
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # شمارش کل
            cursor.execute(f"SELECT COUNT(*) FROM users {where_sql}", params)
            total_count = cursor.fetchone()[0]
            
            # دریافت داده‌ها
            params.extend([limit, offset])
            cursor.execute(f'''
                SELECT * FROM users 
                {where_sql}
                ORDER BY last_activity DESC 
                LIMIT ? OFFSET ?
            ''', params)
            
            users = [dict(row) for row in cursor.fetchall()]
            return users, total_count
    
    def get_statistics(self) -> dict:
        """آمار جامع سیستم"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # آمار کاربران
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_vip = 1 THEN 1 ELSE 0 END) as vip,
                    SUM(CASE WHEN is_banned = 1 THEN 1 ELSE 0 END) as banned,
                    SUM(CASE WHEN DATE(last_activity) = DATE('now', 'localtime') THEN 1 ELSE 0 END) as active_today
                FROM users
            ''')
            user_stats = cursor.fetchone()
            stats['users'] = dict(user_stats)
            
            # آمار دانلودها
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(file_size) as total_size,
                    AVG(file_size) as avg_size,
                    AVG(download_time) as avg_time,
                    SUM(CASE WHEN DATE(download_date) = DATE('now', 'localtime') THEN 1 ELSE 0 END) as today_count,
                    SUM(CASE WHEN DATE(download_date) = DATE('now', 'localtime') THEN file_size ELSE 0 END) as today_size,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM downloads
            ''')
            download_stats = cursor.fetchone()
            stats['downloads'] = dict(download_stats)
            
            # آمار آپلودها
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(file_size) as total_size,
                    SUM(download_count) as total_downloads
                FROM uploads
                WHERE is_active = 1
            ''')
            upload_stats = cursor.fetchone()
            stats['uploads'] = dict(upload_stats)
            
            # آمار فایل‌ها بر اساس نوع
            cursor.execute('''
                SELECT file_type, COUNT(*) as count, SUM(file_size) as size
                FROM downloads
                GROUP BY file_type
                ORDER BY count DESC
            ''')
            stats['file_types'] = {row[0]: {'count': row[1], 'size': row[2]} 
                                  for row in cursor.fetchall()}
            
            # کاربران برتر
            cursor.execute('''
                SELECT user_id, username, first_name, total_downloads, total_size
                FROM users
                ORDER BY total_downloads DESC
                LIMIT 5
            ''')
            stats['top_users'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def get_daily_stats(self, days: int = 7) -> List[dict]:
        """آمار روزانه تفصیلی"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # آمار از جدول downloads
            cursor.execute('''
                WITH RECURSIVE dates(date) AS (
                    SELECT DATE('now', 'localtime', '-{} days')
                    UNION ALL
                    SELECT DATE(date, '+1 day')
                    FROM dates
                    WHERE date < DATE('now', 'localtime')
                )
                SELECT 
                    d.date,
                    COALESCE(COUNT(dl.id), 0) as downloads,
                    COALESCE(SUM(dl.file_size), 0) as size,
                    COALESCE(COUNT(DISTINCT dl.user_id), 0) as unique_users,
                    COALESCE(ds.new_users, 0) as new_users,
                    COALESCE(ds.total_errors, 0) as errors
                FROM dates d
                LEFT JOIN downloads dl ON DATE(dl.download_date) = d.date
                LEFT JOIN daily_stats ds ON ds.date = d.date
                GROUP BY d.date
                ORDER BY d.date
            '''.format(days - 1))
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'date': row[0],
                    'downloads': row[1],
                    'size': row[2],
                    'unique_users': row[3],
                    'new_users': row[4],
                    'errors': row[5]
                })
            
            return stats
    
    def _update_daily_stats(self, field: str, increment: int = 1):
        """به‌روزرسانی آمار روزانه"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                today = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute(f'''
                    INSERT INTO daily_stats (date, {field})
                    VALUES (?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        {field} = {field} + ?
                ''', (today, increment, increment))
                
                # به‌روزرسانی unique users
                if field == 'total_downloads':
                    cursor.execute('''
                        UPDATE daily_stats 
                        SET unique_users = (
                            SELECT COUNT(DISTINCT user_id) 
                            FROM downloads 
                            WHERE DATE(download_date) = ?
                        )
                        WHERE date = ?
                    ''', (today, today))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
    
    def log_activity(self, user_id: int, action: str, details: str = None,
                    ip_address: str = None, user_agent: str = None):
        """ثبت لاگ فعالیت"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_logs 
                    (user_id, action, details, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, action, details, ip_address, user_agent))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def save_upload(self, admin_id: int, file_hash: str, file_name: str,
                   file_size: int, file_path: str, mime_type: str = None,
                   expire_days: int = 7) -> Tuple[bool, str]:
        """ذخیره اطلاعات آپلود"""
        try:
            expire_date = datetime.now() + timedelta(days=expire_days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO uploads 
                    (file_hash, admin_id, file_name, file_size, file_path, 
                     mime_type, expire_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (file_hash, admin_id, file_name, file_size, file_path,
                      mime_type, expire_date))
                conn.commit()
                
                self.log_activity(admin_id, 'upload', 
                                f'{file_name} ({format_size(file_size)})')
                return True, "Success"
                
        except sqlite3.IntegrityError:
            return False, "این فایل قبلاً آپلود شده است"
        except Exception as e:
            logger.error(f"Error saving upload: {e}")
            return False, str(e)
    
    def get_upload(self, file_hash: str) -> Optional[dict]:
        """دریافت اطلاعات آپلود"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM uploads 
                WHERE file_hash = ? 
                AND expire_date > CURRENT_TIMESTAMP 
                AND is_active = 1
            ''', (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def increment_download_count(self, file_hash: str):
        """افزایش شمارنده دانلود"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE uploads 
                SET download_count = download_count + 1 
                WHERE file_hash = ?
            ''', (file_hash,))
            conn.commit()
    
    def cleanup_expired(self) -> Tuple[int, int]:
        """پاکسازی فایل‌های منقضی"""
        files_deleted = 0
        space_freed = 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # فایل‌های منقضی
            cursor.execute('''
                SELECT file_path, file_size FROM uploads 
                WHERE expire_date < CURRENT_TIMESTAMP OR is_active = 0
            ''')
            
            for row in cursor.fetchall():
                try:
                    if os.path.exists(row[0]):
                        os.remove(row[0])
                        files_deleted += 1
                        space_freed += row[1] or 0
                except Exception as e:
                    logger.error(f"Error deleting file {row[0]}: {e}")
            
            # به‌روزرسانی دیتابیس
            cursor.execute('''
                UPDATE uploads 
                SET is_active = 0 
                WHERE expire_date < CURRENT_TIMESTAMP
            ''')
            
            # پاکسازی لاگ‌های قدیمی
            cursor.execute('''
                DELETE FROM activity_logs 
                WHERE timestamp < datetime('now', '-30 days')
            ''')
            
            conn.commit()
            
        return files_deleted, space_freed
    
    def get_user_statistics(self, user_id: int) -> dict:
        """آمار کامل یک کاربر"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # اطلاعات پایه
            user = self.get_user(user_id)
            if not user:
                return {}
            
            stats = {'user': user}
            
            # آمار دانلودها
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_count,
                    SUM(file_size) as total_size,
                    AVG(file_size) as avg_size,
                    MAX(file_size) as max_size,
                    COUNT(DISTINCT DATE(download_date)) as active_days,
                    MIN(download_date) as first_download,
                    MAX(download_date) as last_download
                FROM downloads
                WHERE user_id = ? AND status = 'completed'
            ''', (user_id,))
            
            download_stats = cursor.fetchone()
            stats['downloads'] = dict(download_stats) if download_stats else {}
            
            # توزیع بر اساس نوع فایل
            cursor.execute('''
                SELECT file_type, COUNT(*) as count, SUM(file_size) as size
                FROM downloads
                WHERE user_id = ? AND status = 'completed'
                GROUP BY file_type
            ''', (user_id,))
            
            stats['file_types'] = {row[0]: {'count': row[1], 'size': row[2]} 
                                  for row in cursor.fetchall()}
            
            # آمار 30 روز اخیر
            cursor.execute('''
                SELECT DATE(download_date) as date, COUNT(*) as count, SUM(file_size) as size
                FROM downloads
                WHERE user_id = ? AND download_date >= datetime('now', '-30 days')
                GROUP BY DATE(download_date)
                ORDER BY date
            ''', (user_id,))
            
            stats['recent_activity'] = [dict(row) for row in cursor.fetchall()]
            
            return stats

# ایجاد نمونه دیتابیس
db = Database()

# ===== توابع کمکی پیشرفته =====
def admin_required(show_alert: bool = True):
    """دکوریتور پیشرفته برای بررسی ادمین"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = update.from_user.id
            
            if user_id not in ADMIN_IDS:
                if isinstance(update, CallbackQuery):
                    await update.answer(
                        "⛔ شما اجازه دسترسی به این بخش را ندارید!",
                        show_alert=show_alert
                    )
                else:
                    await update.reply(
                        "⛔ این دستور فقط برای ادمین‌ها قابل استفاده است."
                    )
                return
            
            return await func(update, *args, **kwargs)
        return wrapper
    return decorator

def format_size(size_bytes: int) -> str:
    """تبدیل بایت به واحد خوانا"""
    if size_bytes == 0:
        return "0B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.2f} {units[i]}"

def format_time(seconds: float) -> str:
    """تبدیل ثانیه به فرمت خوانا"""
    if seconds < 60:
        return f"{seconds:.1f} ثانیه"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{int(minutes)} دقیقه و {int(secs)} ثانیه"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)} ساعت و {int(minutes)} دقیقه"

def is_valid_url(url: str) -> bool:
    """بررسی اعتبار URL با regex"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return url_pattern.match(url) is not None

def extract_filename_from_url(url: str) -> str:
    """استخراج نام فایل از URL"""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    
    # اگر نام فایل معتبر نیست
    if not filename or '.' not in filename:
        # تلاش برای استخراج از query string
        if parsed.query:
            import urllib.parse
            params = urllib.parse.parse_qs(parsed.query)
            for key in ['filename', 'name', 'file', 'download']:
                if key in params:
                    filename = params[key][0]
                    break
    
    return filename if filename and '.' in filename else None

def sanitize_filename(filename: str) -> str:
    """پاکسازی نام فایل از کاراکترهای غیرمجاز"""
    # حذف کاراکترهای غیرمجاز
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # محدود کردن طول
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext

# ===== کلاس مدیریت دانلود حرفه‌ای =====
class AdvancedDownloadManager:
    """سیستم دانلود پیشرفته با قابلیت‌های حرفه‌ای"""
    
    def __init__(self):
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_queue: asyncio.Queue = asyncio.Queue()
        self.progress_trackers: Dict[int, dict] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """راه‌اندازی session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(
                total=DOWNLOAD_TIMEOUT,
                connect=30,
                sock_connect=30,
                sock_read=300
            )
            
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                force_close=True
            )
            
            self.session = aiohttp.ClientSession(
                headers=HEADERS,
                timeout=timeout,
                connector=connector,
                trust_env=True
            )
    
    async def close(self):
        """بستن session"""
        if self.session:
            await self.session.close()
    
    async def download_file(self, url: str, user_id: int, 
                          progress_callback=None) -> Tuple[Optional[str], Optional[str], int, dict]:
        """دانلود فایل با قابلیت‌های پیشرفته"""
        await self.initialize()
        
        temp_dir = tempfile.mkdtemp(dir="temp", prefix=f"user_{user_id}_")
        download_info = {
            'start_time': time.time(),
            'temp_dir': temp_dir,
            'error': None,
            'attempts': 0,
            'headers': {}
        }
        
        try:
            # حداکثر 3 تلاش
            for attempt in range(3):
                download_info['attempts'] = attempt + 1
                
                try:
                    result = await self._download_with_resume(
                        url, temp_dir, user_id, progress_callback, attempt
                    )
                    
                    if result:
                        download_info['end_time'] = time.time()
                        download_info['success'] = True
                        return result + (download_info,)
                        
                except asyncio.TimeoutError:
                    download_info['error'] = "Timeout"
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise
                    
                except aiohttp.ClientError as e:
                    download_info['error'] = str(e)
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise
            
        except Exception as e:
            logger.error(f"Download error for user {user_id}: {e}", exc_info=True)
            download_info['error'] = str(e)
            download_info['traceback'] = traceback.format_exc()
            
            # پاکسازی
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
            return None, None, 0, download_info
    
    async def _download_with_resume(self, url: str, temp_dir: str, 
                                  user_id: int, progress_callback, 
                                  attempt: int) -> Optional[Tuple[str, str, int]]:
        """دانلود با قابلیت resume"""
        headers = HEADERS.copy()
        temp_file = None
        downloaded_size = 0
        
        # بررسی فایل ناتمام
        partial_files = [f for f in os.listdir(temp_dir) if f.endswith('.partial')]
        if partial_files:
            temp_file = os.path.join(temp_dir, partial_files[0])
            downloaded_size = os.path.getsize(temp_file)
            headers['Range'] = f'bytes={downloaded_size}-'
            logger.info(f"Resuming download from {format_size(downloaded_size)}")
        
        async with self.session.get(url, headers=headers, allow_redirects=True) as response:
            # بررسی status
            if response.status == 416:  # Range Not Satisfiable
                # فایل کامل دانلود شده
                if temp_file:
                    final_name = temp_file[:-8]  # حذف .partial
                    os.rename(temp_file, final_name)
                    return final_name, os.path.basename(final_name), os.path.getsize(final_name)
            
            if response.status not in (200, 206):
                raise aiohttp.ClientError(f"HTTP {response.status}: {response.reason}")
            
            # اطلاعات فایل
            total_size = int(response.headers.get('Content-Length', 0))
            if response.status == 206:  # Partial Content
                content_range = response.headers.get('Content-Range', '')
                if '/' in content_range:
                    total_size = int(content_range.split('/')[-1])
            else:
                downloaded_size = 0  # شروع از ابتدا
            
            # نام فایل
            filename = await self._extract_filename(response, url)
            filename = sanitize_filename(filename)
            
            if not temp_file:
                temp_file = os.path.join(temp_dir, f"{filename}.partial")
            
            # ذخیره progress
            self.progress_trackers[user_id] = {
                'filename': filename,
                'total_size': total_size,
                'downloaded': downloaded_size,
                'start_time': time.time(),
                'speed': 0,
                'eta': 0
            }
            
            # دانلود
            mode = 'ab' if downloaded_size > 0 else 'wb'
            async with aiofiles.open(temp_file, mode) as file:
                async for chunk in response.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                    await file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # آپدیت progress
                    if user_id in self.progress_trackers:
                        tracker = self.progress_trackers[user_id]
                        tracker['downloaded'] = downloaded_size
                        
                        # محاسبه سرعت
                        elapsed = time.time() - tracker['start_time']
                        if elapsed > 0:
                            tracker['speed'] = downloaded_size / elapsed
                            
                            # ETA
                            if tracker['speed'] > 0 and total_size > 0:
                                remaining = total_size - downloaded_size
                                tracker['eta'] = remaining / tracker['speed']
                        
                        # callback
                        if progress_callback:
                            await progress_callback(user_id, tracker)
            
            # تغییر نام نهایی
            final_path = os.path.join(temp_dir, filename)
            os.rename(temp_file, final_path)
            
            # پاکسازی progress
            if user_id in self.progress_trackers:
                del self.progress_trackers[user_id]
            
            return final_path, filename, os.path.getsize(final_path)
    
    async def _extract_filename(self, response: aiohttp.ClientResponse, 
                               url: str) -> str:
        """استخراج نام فایل از response"""
        filename = None
        
        # از Content-Disposition
        cd = response.headers.get('Content-Disposition', '')
        if cd:
            # استخراج با regex
            filename_match = re.findall(
                r'filename\*?=(["\']?)(.+?)\1(?:;|$)', cd, re.IGNORECASE
            )
            if filename_match:
                _, filename = filename_match[0]
                
                # Decode RFC 5987
                if filename.startswith("UTF-8''"):
                    filename = unquote(filename[7:])
                elif filename.startswith("utf-8''"):
                    filename = unquote(filename[7:])
        
        # از URL
        if not filename:
            filename = extract_filename_from_url(url)
        
        # نام پیش‌فرض
        if not filename:
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.bin'
            filename = f"download_{int(time.time())}{ext}"
        
        return filename
    
    def get_progress(self, user_id: int) -> Optional[dict]:
        """دریافت وضعیت دانلود"""
        return self.progress_trackers.get(user_id)
    
    def cancel_download(self, user_id: int) -> bool:
        """لغو دانلود"""
        if user_id in self.active_downloads:
            self.active_downloads[user_id].cancel()
            del self.active_downloads[user_id]
            
            if user_id in self.progress_trackers:
                del self.progress_trackers[user_id]
            
            return True
        return False

# ایجاد نمونه
download_manager = AdvancedDownloadManager()

# ===== تابع اصلی ارسال فایل =====
async def send_file_to_user(message: Message, file_path: str, filename: str, 
                          file_size: int, send_as: str = 'auto',
                          mime_type: str = None) -> bool:
    """ارسال فایل به کاربر با مدیریت خطا"""
    try:
        if not os.path.exists(file_path):
            await message.reply("❌ فایل یافت نشد! لطفاً دوباره تلاش کنید.")
            return False
        
        # تعیین نوع ارسال
        if send_as == 'auto':
            if not mime_type:
                try:
                    mime = magic.Magic(mime=True)
                    mime_type = mime.from_file(file_path)
                except:
                    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # تعیین بر اساس mime type
            if mime_type.startswith('image/') and file_size < 10 * 1024 * 1024:
                send_as = 'photo'
            elif mime_type.startswith('video/'):
                send_as = 'video'
            elif mime_type.startswith('audio/'):
                send_as = 'audio'
            else:
                send_as = 'document'
        
        # ایجاد input file
        input_file = FSInputFile(file_path, filename=filename)
        caption = f"📁 {filename}\n📊 حجم: {format_size(file_size)}"
        
        # ارسال بر اساس نوع
        if send_as == 'photo':
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=input_file,
                caption=caption
            )
        elif send_as == 'video':
            await bot.send_video(
                chat_id=message.chat.id,
                video=input_file,
                caption=caption,
                supports_streaming=True
            )
        elif send_as == 'audio':
            await bot.send_audio(
                chat_id=message.chat.id,
                audio=input_file,
                caption=caption
            )
        else:  # document
            await bot.send_document(
                chat_id=message.chat.id,
                document=input_file,
                caption=caption
            )
        
        return True
        
    except TelegramAPIError as e:
        if "File too large" in str(e):
            await message.reply(
                f"❌ فایل بزرگتر از حد مجاز تلگرام است!\n"
                f"حجم فایل: {format_size(file_size)}"
            )
        else:
            logger.error(f"Telegram API error: {e}")
            await message.reply(f"❌ خطا در ارسال: {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending file: {e}", exc_info=True)
        await message.reply(
            f"❌ خطای غیرمنتظره در ارسال فایل:\n"
            f"<code>{str(e)}</code>",
            parse_mode=ParseMode.HTML
        )
        return False

# ===== دستورات اصلی =====
@dp.message(CommandStart())
async def start_command(message: Message):
    """دستور شروع"""
    user = message.from_user
    
    # ثبت کاربر
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code
    )
    
    # بررسی بن
    if db.is_user_banned(user.id):
        await message.reply("⛔ شما از استفاده از ربات محروم شده‌اید.")
        return
    
    # بررسی حالت تعمیر
    if db.get_setting('maintenance_mode', False) and user.id not in ADMIN_IDS:
        await message.reply(
            "🔧 ربات در حال تعمیر و نگهداری است.\n"
            "لطفاً کمی بعد مراجعه کنید."
        )
        return
    
    # اطلاعات کاربر
    user_info = db.get_user(user.id)
    daily_limit = db.get_user_limit(user.id)
    downloads_today, size_today = db.get_daily_downloads(user.id)
    
    # پیام خوش‌آمدگویی
    welcome_text = f"""
👋 سلام <b>{user.first_name}</b> عزیز!

🤖 <b>{db.get_setting('welcome_message')}</b>

📊 <b>وضعیت حساب شما:</b>
├ نوع: {'⭐ VIP' if user_info['is_vip'] else '👤 عادی'}
├ محدودیت روزانه: {daily_limit if daily_limit < 999999 else '♾ نامحدود'}
├ دانلود امروز: {downloads_today} فایل
└ حجم امروز: {format_size(size_today)}

📝 برای دانلود کافیست لینک مستقیم فایل را ارسال کنید.
    """
    
    # کیبورد
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 آمار من", callback_data="my_stats")
    keyboard.button(text="❓ راهنما", callback_data="help")
    
    if user.id in ADMIN_IDS:
        keyboard.button(text="🔧 پنل ادمین", callback_data="admin_panel")
    
    keyboard.button(text="💬 پشتیبانی", url="https://t.me/your_support")
    keyboard.adjust(2, 1, 1)
    
    await message.reply(
        welcome_text,
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    """راهنمای کامل"""
    help_text = """
📚 <b>راهنمای کامل ربات دانلودر</b>

🔹 <b>نحوه استفاده:</b>
1️⃣ لینک مستقیم فایل را ارسال کنید
2️⃣ صبر کنید تا فایل دانلود شود
3️⃣ نوع ارسال را انتخاب کنید
4️⃣ فایل را دریافت کنید

🔹 <b>ویژگی‌ها:</b>
✅ دانلود از همه سایت‌ها
✅ پشتیبانی از فایل تا 2GB
✅ تقسیم خودکار فایل‌های بزرگ
✅ رزومه دانلود در صورت قطعی
✅ انتخاب فرمت ارسال
✅ آمار کامل دانلودها

🔹 <b>دستورات:</b>
/start - شروع و منوی اصلی
/help - این راهنما
/mystats - آمار کامل شما
/dl [code] - دانلود با کد

🔹 <b>محدودیت‌ها:</b>
• کاربران عادی: {db.get_setting('global_daily_limit')} فایل در روز
• کاربران VIP: نامحدود
• حداکثر حجم: 2GB (محدودیت تلگرام)

💡 <b>نکات:</b>
• از لینک‌های مستقیم استفاده کنید
• لینک‌های کوتاه‌شده پشتیبانی نمی‌شوند
• برای فایل‌های بزرگ صبور باشید
    """
    
    await message.reply(help_text.strip(), parse_mode=ParseMode.HTML)

@dp.message(Command("mystats"))
async def my_stats_command(message: Message):
    """آمار کامل کاربر"""
    user_id = message.from_user.id
    stats = db.get_user_statistics(user_id)
    
    if not stats:
        await message.reply("❌ اطلاعاتی یافت نشد!")
        return
    
    user = stats['user']
    downloads = stats.get('downloads', {})
    file_types = stats.get('file_types', {})
    
    # متن آمار
    stats_text = f"""
📊 <b>آمار کامل شما</b>

👤 <b>اطلاعات حساب:</b>
├ آیدی: <code>{user_id}</code>
├ نام: {user['first_name']}
├ نوع: {'⭐ VIP' if user['is_vip'] else '👤 عادی'}
└ عضویت: {user['join_date'][:10]}

📥 <b>آمار دانلود:</b>
├ تعداد کل: {downloads.get('total_count', 0):,} فایل
├ حجم کل: {format_size(downloads.get('total_size', 0))}
├ میانگین حجم: {format_size(downloads.get('avg_size', 0))}
├ بزرگترین فایل: {format_size(downloads.get('max_size', 0))}
└ روزهای فعال: {downloads.get('active_days', 0)} روز
    """
    
    # توزیع فایل‌ها
    if file_types:
        stats_text += "\n📎 <b>توزیع فایل‌ها:</b>\n"
        for ftype, fdata in sorted(file_types.items(), 
                                  key=lambda x: x[1]['count'], 
                                  reverse=True)[:5]:
            stats_text += f"├ {ftype}: {fdata['count']} فایل ({format_size(fdata['size'])})\n"
    
    # دکمه نمودار
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📈 نمودار فعالیت", callback_data=f"user_chart_{user_id}")
    
    await message.reply(
        stats_text.strip(),
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("dl"))
async def download_by_code(message: Message):
    """دانلود با کد"""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "❌ لطفاً کد فایل را وارد کنید!\n"
            "مثال: <code>/dl ABC123</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    file_hash = parts[1].strip()
    upload_info = db.get_upload(file_hash)
    
    if not upload_info:
        await message.reply("❌ کد نامعتبر یا منقضی شده است!")
        return
    
    # بررسی فایل
    if not os.path.exists(upload_info['file_path']):
        await message.reply("❌ فایل یافت نشد! ممکن است حذف شده باشد.")
        return
    
    # ارسال
    try:
        await message.reply("📤 در حال ارسال فایل...")
        
        success = await send_file_to_user(
            message,
            upload_info['file_path'],
            upload_info['file_name'],
            upload_info['file_size'],
            mime_type=upload_info.get('mime_type')
        )
        
        if success:
            # آپدیت آمار
            db.increment_download_count(file_hash)
            
            await message.reply(
                f"✅ فایل ارسال شد!\n"
                f"📥 تعداد دانلود: {upload_info['download_count'] + 1}"
            )
            
    except Exception as e:
        logger.error(f"Error in download by code: {e}", exc_info=True)
        await message.reply(f"❌ خطا: {str(e)}")

# ===== پنل ادمین =====
@dp.message(Command("admin"))
@admin_required()
async def admin_command(message: Message):
    """ورود به پنل ادمین"""
    await show_admin_panel(message)

async def show_admin_panel(message: Message):
    """نمایش پنل ادمین"""
    stats = db.get_statistics()
    
    admin_text = f"""
🔧 <b>پنل مدیریت ربات</b>

👥 کاربران: {stats['users']['total']:,} (امروز: {stats['users']['active_today']})
📥 دانلودها: {stats['downloads']['total']:,} (امروز: {stats['downloads']['today_count']})
💾 حجم کل: {format_size(stats['downloads']['total_size'] or 0)}

🕒 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    keyboard = InlineKeyboardBuilder()
    
    # ردیف اول
    keyboard.button(text="📊 آمار تفصیلی", callback_data="admin_detailed_stats")
    keyboard.button(text="📈 نمودارها", callback_data="admin_charts")
    
    # ردیف دوم
    keyboard.button(text="👥 مدیریت کاربران", callback_data="admin_users")
    keyboard.button(text="⚙️ تنظیمات", callback_data="admin_settings")
    
    # ردیف سوم
    keyboard.button(text="📤 آپلود فایل", callback_data="admin_upload")
    keyboard.button(text="📢 پیام همگانی", callback_data="admin_broadcast")
    
    # ردیف چهارم
    keyboard.button(text="🗑 پاکسازی", callback_data="admin_cleanup")
    keyboard.button(text="📜 لاگ فعالیت", callback_data="admin_logs")
    
    # ردیف پنجم
    keyboard.button(text="🔄 رفرش", callback_data="admin_refresh")
    
    keyboard.adjust(2, 2, 2, 2, 1)
    
    await message.reply(
        admin_text.strip(),
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == "admin_panel")
@admin_required()
async def admin_panel_callback(callback: CallbackQuery):
    """بازگشت به پنل"""
    await show_admin_panel(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "admin_refresh")
@admin_required()
async def admin_refresh_callback(callback: CallbackQuery):
    """رفرش پنل"""
    await callback.answer("در حال به‌روزرسانی...")
    await show_admin_panel(callback.message)

@dp.callback_query(F.data == "admin_settings")
@admin_required()
async def admin_settings_callback(callback: CallbackQuery):
    """تنظیمات ربات"""
    # دریافت تنظیمات
    settings = {
        'download_enabled': db.get_setting('download_enabled', True),
        'maintenance_mode': db.get_setting('maintenance_mode', False),
        'global_limit': db.get_setting('global_daily_limit', DEFAULT_DAILY_LIMIT),
        'vip_unlimited': db.get_setting('vip_unlimited', True),
        'compression': db.get_setting('compression_enabled', True)
    }
    
    settings_text = f"""
⚙️ <b>تنظیمات ربات</b>

📥 دانلود: {'✅ فعال' if settings['download_enabled'] else '❌ غیرفعال'}
🔧 حالت تعمیر: {'🔴 فعال' if settings['maintenance_mode'] else '🟢 غیرفعال'}
🌐 محدودیت عمومی: {settings['global_limit']} فایل
⭐ VIP نامحدود: {'✅ بله' if settings['vip_unlimited'] else '❌ خیر'}
📦 فشرده‌سازی: {'✅ فعال' if settings['compression'] else '❌ غیرفعال'}
    """
    
    keyboard = InlineKeyboardBuilder()
    
    # تنظیمات
    keyboard.button(
        text=f"{'🔴' if settings['download_enabled'] else '🟢'} دانلود",
        callback_data="admin_toggle_download"
    )
    keyboard.button(
        text=f"{'🔴' if not settings['maintenance_mode'] else '🟢'} تعمیرات",
        callback_data="admin_toggle_maintenance"
    )
    
    keyboard.button(
        text="🔢 محدودیت عمومی",
        callback_data="admin_set_global_limit"
    )
    keyboard.button(
        text=f"{'🔴' if settings['vip_unlimited'] else '🟢'} VIP نامحدود",
        callback_data="admin_toggle_vip_unlimited"
    )
    
    keyboard.button(text="🔙 بازگشت", callback_data="admin_panel")
    
    keyboard.adjust(2, 2, 1)
    
    await callback.message.edit_text(
        settings_text.strip(),
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_toggle_download")
@admin_required()
async def toggle_download_callback(callback: CallbackQuery):
    """تغییر وضعیت دانلود"""
    current = db.get_setting('download_enabled', True)
    new_value = not current
    
    db.set_setting('download_enabled', new_value, updated_by=callback.from_user.id)
    
    await callback.answer(
        f"✅ دانلود {'فعال' if new_value else 'غیرفعال'} شد!",
        show_alert=True
    )
    
    # رفرش صفحه
    await admin_settings_callback(callback)

@dp.callback_query(F.data == "admin_toggle_maintenance")
@admin_required()
async def toggle_maintenance_callback(callback: CallbackQuery):
    """تغییر حالت تعمیر"""
    current = db.get_setting('maintenance_mode', False)
    new_value = not current
    
    db.set_setting('maintenance_mode', new_value, updated_by=callback.from_user.id)
    
    await callback.answer(
        f"✅ حالت تعمیر {'فعال' if new_value else 'غیرفعال'} شد!",
        show_alert=True
    )
    
    await admin_settings_callback(callback)

@dp.callback_query(F.data == "admin_users")
@admin_required()
async def admin_users_menu(callback: CallbackQuery):
    """منوی مدیریت کاربران"""
    total_users = db.get_statistics()['users']['total']
    
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="📋 لیست کاربران", callback_data="admin_users_list")
    keyboard.button(text="🔍 جستجوی کاربر", callback_data="admin_search_user")
    
    keyboard.button(text="⭐ مدیریت VIP", callback_data="admin_vip_menu")
    keyboard.button(text="🚫 مدیریت بن", callback_data="admin_ban_menu")
    
    keyboard.button(text="📊 آمار کاربر", callback_data="admin_user_stats")
    keyboard.button(text="🔙 بازگشت", callback_data="admin_panel")
    
    keyboard.adjust(2, 2, 1, 1)
    
    await callback.message.edit_text(
        f"👥 <b>مدیریت کاربران</b>\n\n"
        f"تعداد کل: {total_users:,} کاربر",
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_vip_menu")
@admin_required()
async def admin_vip_menu(callback: CallbackQuery):
    """منوی VIP"""
    vip_count = db.get_statistics()['users']['vip']
    
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="➕ افزودن VIP", callback_data="admin_add_vip")
    keyboard.button(text="➖ حذف VIP", callback_data="admin_remove_vip")
    keyboard.button(text="📋 لیست VIP ها", callback_data="admin_vip_list")
    keyboard.button(text="🔙 بازگشت", callback_data="admin_users")
    
    keyboard.adjust(2, 1, 1)
    
    await callback.message.edit_text(
        f"⭐ <b>مدیریت VIP</b>\n\n"
        f"تعداد VIP ها: {vip_count:,} کاربر",
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_add_vip")
@admin_required()
async def admin_add_vip(callback: CallbackQuery, state: FSMContext):
    """افزودن VIP"""
    await callback.message.edit_text(
        "🆔 آیدی عددی کاربر را ارسال کنید:\n\n"
        "برای لغو: /cancel"
    )
    await state.set_state(AdminStates.waiting_vip_user_id)
    await state.update_data(action="add_vip")
    await callback.answer()

# ===== مدیریت دانلود =====
@dp.message(F.text)
async def handle_message(message: Message, state: FSMContext):
    """مدیریت پیام‌های متنی"""
    # بررسی state
    current_state = await state.get_state()
    if current_state:
        return  # در حال انجام عملیات دیگر
    
    text = message.text.strip()
    
    # بررسی URL
    if not is_valid_url(text):
        return
    
    # بررسی کاربر
    user_id = message.from_user.id
    
    # بررسی بن
    if db.is_user_banned(user_id):
        await message.reply("⛔ شما از استفاده از ربات محروم شده‌اید.")
        return
    
    # بررسی وضعیت دانلود
    if not db.get_setting('download_enabled', True) and user_id not in ADMIN_IDS:
        await message.reply(
            "⚠️ دانلود موقتاً غیرفعال است.\n"
            "لطفاً بعداً مراجعه کنید."
        )
        return
    
    # بررسی محدودیت
    downloads_today, size_today = db.get_daily_downloads(user_id)
    limit = db.get_user_limit(user_id)
    
    if downloads_today >= limit:
        user_info = db.get_user(user_id)
        await message.reply(
            f"⛔ <b>محدودیت روزانه!</b>\n\n"
            f"شما به حد مجاز ({limit} فایل) رسیده‌اید.\n"
            f"دانلود امروز: {downloads_today} فایل ({format_size(size_today)})\n\n"
            f"{'⭐ برای اکانت VIP با ادمین تماس بگیرید.' if not user_info['is_vip'] else ''}",
            parse_mode=ParseMode.HTML
        )
        return
    
    # شروع دانلود
    await handle_download(message, text, state)

async def handle_download(message: Message, url: str, state: FSMContext):
    """مدیریت فرآیند دانلود"""
    start_msg = await message.reply(
        "🔍 در حال بررسی لینک...\n"
        "⏳ لطفاً صبر کنید..."
    )
    
    start_time = time.time()
    
    # پروگرس callback
    async def progress_callback(user_id: int, progress: dict):
        try:
            if time.time() - progress.get('last_update', 0) < 1:
                return
            
            progress['last_update'] = time.time()
            
            # محاسبات
            percent = 0
            if progress['total_size'] > 0:
                percent = (progress['downloaded'] / progress['total_size']) * 100
            
            speed = progress.get('speed', 0)
            eta = progress.get('eta', 0)
            
            # نوار پیشرفت
            bar_length = 20
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            text = f"""
📥 <b>در حال دانلود...</b>

📁 {progress['filename']}
▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️
[{bar}] {percent:.1f}%
▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️
📊 {format_size(progress['downloaded'])} / {format_size(progress['total_size'])}
⚡ سرعت: {format_size(int(speed))}/s
⏱ زمان باقی: {format_time(eta)}
            """
            
            await start_msg.edit_text(text.strip(), parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logger.error(f"Progress update error: {e}")
    
    # دانلود
    try:
        result = await download_manager.download_file(
            url, 
            message.from_user.id,
            progress_callback
        )
        
        if not result or not result[0]:
            download_info = result[3] if result else {}
            error_msg = download_info.get('error', 'Unknown error')
            
            await start_msg.edit_text(
                f"❌ <b>خطا در دانلود!</b>\n\n"
                f"🔗 لینک: <code>{url}</code>\n"
                f"⚠️ خطا: {error_msg}\n"
                f"🔄 تلاش‌ها: {download_info.get('attempts', 1)}",
                parse_mode=ParseMode.HTML
            )
            
            # ثبت در دیتابیس
            db.add_download(
                message.from_user.id,
                url,
                "Unknown",
                0,
                status='failed',
                error_message=error_msg
            )
            return
        
        file_path, filename, file_size, download_info = result
        download_time = download_info.get('end_time', time.time()) - start_time
        
        # ثبت موفق
        download_id = db.add_download(
            message.from_user.id,
            url,
            filename,
            file_size,
            status='completed',
            download_time=download_time
        )
        
        # بررسی حجم برای فایل‌های بزرگ
        if file_size > MAX_FILE_SIZE:
            await start_msg.edit_text("📦 فایل بزرگ است. در حال پردازش...")
            await handle_large_file(message, file_path, filename, file_size, state)
            return
        
        # ذخیره در state
        await state.update_data(
            file_path=file_path,
            filename=filename,
            file_size=file_size,
            url=url,
            download_id=download_id,
            temp_dir=download_info.get('temp_dir')
        )
        
        # گزینه‌های ارسال
        await show_send_options(message, start_msg, filename, file_size, state)
        
    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        await start_msg.edit_text(
            f"❌ خطای غیرمنتظره:\n"
            f"<code>{str(e)}</code>",
            parse_mode=ParseMode.HTML
        )

async def show_send_options(message: Message, edit_message: Message,
                          filename: str, file_size: int, state: FSMContext):
    """نمایش گزینه‌های ارسال"""
    # تشخیص نوع با magic
    data = await state.get_data()
    file_path = data['file_path']
    
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
    except:
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    # ذخیره mime type
    await state.update_data(mime_type=mime_type)
    
    # ایجاد کیبورد
    keyboard = InlineKeyboardBuilder()
    
    if mime_type.startswith('video/'):
        keyboard.button(text="🎬 ویدیو (استریم)", callback_data="send_as_video")
        keyboard.button(text="📄 فایل ویدیو", callback_data="send_as_document")
    elif mime_type.startswith('image/') and file_size < 10 * 1024 * 1024:
        keyboard.button(text="🖼 عکس", callback_data="send_as_photo")
        keyboard.button(text="📄 فایل عکس", callback_data="send_as_document")
    elif mime_type.startswith('audio/'):
        keyboard.button(text="🎵 موسیقی", callback_data="send_as_audio")
        keyboard.button(text="📄 فایل صوتی", callback_data="send_as_document")
    else:
        keyboard.button(text="📄 ارسال فایل", callback_data="send_as_document")
    
    keyboard.button(text="❌ لغو", callback_data="cancel_send")
    keyboard.adjust(2, 1)
    
    info_text = f"""
✅ <b>دانلود کامل شد!</b>

📁 نام: {filename}
📊 حجم: {format_size(file_size)}
📎 نوع: {mime_type}

نحوه ارسال را انتخاب کنید:
    """
    
    await edit_message.edit_text(
        info_text.strip(),
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )
    
    await state.set_state(DownloadStates.choosing_format)

async def handle_large_file(message: Message, file_path: str, 
                          filename: str, file_size: int, state: FSMContext):
    """مدیریت فایل‌های بزرگ"""
    await message.reply(
        f"📦 <b>فایل بزرگ!</b>\n\n"
        f"حجم: {format_size(file_size)}\n"
        f"در حال تقسیم به بخش‌های {format_size(CHUNK_SIZE)}...",
        parse_mode=ParseMode.HTML
    )
    
    try:
        parts_dir = tempfile.mkdtemp(dir="temp", prefix="parts_")
        parts = []
        
        # تقسیم فایل
        with open(file_path, 'rb') as infile:
            part_num = 1
            
            while True:
                # خواندن بخش
                chunk = infile.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # ایجاد zip
                part_name = f"{os.path.splitext(filename)[0]}_part{part_num:03d}.zip"
                part_path = os.path.join(parts_dir, part_name)
                
                with zipfile.ZipFile(part_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # نام فایل داخل zip
                    inner_name = f"part{part_num:03d}_{filename}"
                    zf.writestr(inner_name, chunk)
                
                parts.append((part_path, part_name, len(chunk)))
                part_num += 1
                
                # پیام وضعیت
                if part_num % 5 == 0:
                    await message.reply(f"⏳ {part_num - 1} بخش آماده شد...")
        
        # ارسال بخش‌ها
        await message.reply(
            f"📤 شروع ارسال {len(parts)} بخش...\n"
            f"⏱ این عملیات ممکن است چند دقیقه طول بکشد."
        )
        
        for i, (part_path, part_name, part_size) in enumerate(parts, 1):
            try:
                caption = (
                    f"📦 بخش {i} از {len(parts)}\n"
                    f"📊 حجم: {format_size(part_size)}\n"
                    f"📁 {part_name}\n\n"
                )
                
                if i == 1:
                    caption += "💡 برای ادغام فایل‌ها از نرم‌افزار مناسب استفاده کنید."
                
                await bot.send_document(
                    chat_id=message.chat.id,
                    document=FSInputFile(part_path),
                    caption=caption
                )
                
                # تاخیر برای جلوگیری از flood
                if i < len(parts):
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error sending part {i}: {e}")
                await message.reply(f"❌ خطا در ارسال بخش {i}: {str(e)}")
        
        # دستورالعمل
        instruction = f"""
✅ <b>ارسال کامل شد!</b>

📦 تعداد: {len(parts)} بخش
📊 حجم کل: {format_size(file_size)}

📝 <b>راهنمای ادغام:</b>
1️⃣ همه فایل‌های ZIP را دانلود کنید
2️⃣ آنها را Extract کنید
3️⃣ فایل‌های part را به ترتیب ادغام کنید

💻 <b>Windows:</b>
<code>copy /b part001_* + part002_* + ... output{os.path.splitext(filename)[1]}</code>

🐧 <b>Linux/Mac:</b>
<code>cat part* > output{os.path.splitext(filename)[1]}</code>
        """
        
        await message.reply(instruction.strip(), parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Large file error: {e}", exc_info=True)
        await message.reply(
            f"❌ خطا در پردازش فایل بزرگ:\n"
            f"<code>{str(e)}</code>",
            parse_mode=ParseMode.HTML
        )
    
    finally:
        # پاکسازی
        try:
            if 'parts_dir' in locals():
                shutil.rmtree(parts_dir)
            os.remove(file_path)
        except:
            pass
        
        await state.clear()

# ===== کالبک‌های ارسال =====
@dp.callback_query(StateFilter(DownloadStates.choosing_format))
async def handle_send_callback(callback: CallbackQuery, state: FSMContext):
    """مدیریت انتخاب نوع ارسال"""
    if callback.data == "cancel_send":
        await callback.message.edit_text("❌ ارسال لغو شد.")
        
        # پاکسازی
        data = await state.get_data()
        if data.get('temp_dir'):
            try:
                shutil.rmtree(data['temp_dir'])
            except:
                pass
        
        await state.clear()
        await callback.answer()
        return
    
    # دریافت اطلاعات
    data = await state.get_data()
    file_path = data.get('file_path')
    filename = data.get('filename')
    file_size = data.get('file_size')
    
    if not file_path or not os.path.exists(file_path):
        await callback.answer("❌ فایل یافت نشد!", show_alert=True)
        await state.clear()
        return
    
    # تعیین نوع ارسال
    send_as = callback.data.replace("send_as_", "")
    
    await callback.answer("در حال ارسال...")
    await callback.message.edit_text(
        f"📤 در حال ارسال فایل...\n"
        f"📁 {filename}\n"
        f"📊 {format_size(file_size)}"
    )
    
    # ارسال
    try:
        success = await send_file_to_user(
            callback.message,
            file_path,
            filename,
            file_size,
            send_as=send_as,
            mime_type=data.get('mime_type')
        )
        
        if success:
            # پیام موفقیت
            downloads_today, size_today = db.get_daily_downloads(callback.from_user.id)
            limit = db.get_user_limit(callback.from_user.id)
            
            await callback.message.edit_text(
                f"✅ <b>ارسال کامل شد!</b>\n\n"
                f"📥 دانلود امروز: {downloads_today}/{limit if limit < 999999 else '♾'}\n"
                f"💾 حجم امروز: {format_size(size_today)}",
                parse_mode=ParseMode.HTML
            )
        
    except Exception as e:
        logger.error(f"Send error: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ خطا در ارسال:\n{str(e)}"
        )
    
    finally:
        # پاکسازی
        try:
            if data.get('temp_dir'):
                shutil.rmtree(data['temp_dir'])
        except:
            pass
        
        await state.clear()

# ===== مدیریت States ادمین =====
@dp.message(AdminStates.waiting_vip_user_id)
@admin_required()
async def handle_vip_user_id(message: Message, state: FSMContext):
    """دریافت آیدی برای VIP"""
    try:
        user_id = int(message.text.strip())
        data = await state.get_data()
        action = data.get('action')
        
        # بررسی کاربر
        user = db.get_user(user_id)
        if not user:
            # ایجاد کاربر
            db.add_user(user_id)
            user = db.get_user(user_id)
        
        if action == "add_vip":
            if user['is_vip']:
                await message.reply("⚠️ این کاربر از قبل VIP است!")
            else:
                db.set_user_status(user_id, is_vip=True)
                await message.reply(
                    f"✅ کاربر {user_id} به لیست VIP اضافه شد!\n"
                    f"نام: {user['first_name'] or 'ناشناس'}"
                )
                
                # ارسال پیام به کاربر
                try:
                    await bot.send_message(
                        user_id,
                        "🎉 تبریک! شما به عضویت VIP ارتقا یافتید!\n"
                        "اکنون می‌توانید بدون محدودیت دانلود کنید."
                    )
                except:
                    pass
        
        elif action == "remove_vip":
            if not user['is_vip']:
                await message.reply("⚠️ این کاربر VIP نیست!")
            else:
                db.set_user_status(user_id, is_vip=False)
                await message.reply(f"✅ VIP کاربر {user_id} لغو شد!")
        
        await state.clear()
        
    except ValueError:
        await message.reply("❌ آیدی نامعتبر! لطفاً عدد وارد کنید.")
    except Exception as e:
        await message.reply(f"❌ خطا: {str(e)}")

@dp.message(AdminStates.setting_global_limit)
@admin_required()
async def handle_global_limit(message: Message, state: FSMContext):
    """تنظیم محدودیت عمومی"""
    try:
        limit = int(message.text.strip())
        
        if limit < 1:
            await message.reply("❌ محدودیت باید حداقل 1 باشد!")
            return
        
        db.set_setting('global_daily_limit', limit, updated_by=message.from_user.id)
        
        await message.reply(
            f"✅ محدودیت عمومی به {limit} فایل در روز تغییر کرد!"
        )
        await state.clear()
        
    except ValueError:
        await message.reply("❌ لطفاً یک عدد معتبر وارد کنید!")

@dp.message(AdminStates.uploading_file)
@admin_required()
async def handle_upload(message: Message, state: FSMContext):
    """دریافت فایل آپلود"""
    if not (message.document or message.video or message.photo or message.audio):
        await message.reply("❌ لطفاً یک فایل ارسال کنید!")
        return
    
    processing_msg = await message.reply("⏳ در حال پردازش فایل...")
    
    try:
        # تشخیص نوع فایل
        if message.document:
            file = message.document
            file_name = file.file_name or f"document_{int(time.time())}"
        elif message.video:
            file = message.video
            file_name = f"video_{int(time.time())}.mp4"
        elif message.audio:
            file = message.audio
            file_name = file.file_name or f"audio_{int(time.time())}.mp3"
        else:  # photo
            file = message.photo[-1]
            file_name = f"photo_{int(time.time())}.jpg"
        
        # دانلود فایل
        file_info = await bot.get_file(file.file_id)
        
        # تولید هش یونیک
        file_hash = hashlib.md5(
            f"{file.file_id}{time.time()}{message.from_user.id}".encode()
        ).hexdigest()[:10].upper()
        
        # مسیر ذخیره
        safe_filename = sanitize_filename(file_name)
        saved_path = os.path.join("uploads", f"{file_hash}_{safe_filename}")
        
        # دانلود
        await bot.download_file(file_info.file_path, saved_path)
        file_size = os.path.getsize(saved_path)
        
        # تشخیص MIME type
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(saved_path)
        except:
            mime_type = mimetypes.guess_type(saved_path)[0]
        
        # ذخیره در دیتابیس
        success, msg = db.save_upload(
            admin_id=message.from_user.id,
            file_hash=file_hash,
            file_name=safe_filename,
            file_size=file_size,
            file_path=saved_path,
            mime_type=mime_type,
            expire_days=30  # 30 روز اعتبار
        )
        
        if success:
            await processing_msg.edit_text(
                f"✅ <b>فایل با موفقیت آپلود شد!</b>\n\n"
                f"📁 نام: {safe_filename}\n"
                f"📊 حجم: {format_size(file_size)}\n"
                f"📎 نوع: {mime_type}\n"
                f"🔑 کد دانلود: <code>{file_hash}</code>\n"
                f"⏱ اعتبار: 30 روز\n\n"
                f"🔗 لینک دانلود:\n"
                f"<code>https://t.me/{(await bot.get_me()).username}?start={file_hash}</code>\n\n"
                f"💡 کاربران می‌توانند با دستور زیر دانلود کنند:\n"
                f"<code>/dl {file_hash}</code>",
                parse_mode=ParseMode.HTML
            )
        else:
            await processing_msg.edit_text(f"❌ خطا: {msg}")
            # حذف فایل
            try:
                os.remove(saved_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ خطا در آپلود:\n<code>{str(e)}</code>",
            parse_mode=ParseMode.HTML
        )
    
    await state.clear()

# ===== کالبک‌های دیگر ادمین =====
@dp.callback_query(F.data == "admin_set_global_limit")
@admin_required()
async def set_global_limit_callback(callback: CallbackQuery, state: FSMContext):
    """تنظیم محدودیت عمومی"""
    current = db.get_setting('global_daily_limit', DEFAULT_DAILY_LIMIT)
    
    await callback.message.edit_text(
        f"🔢 <b>تنظیم محدودیت عمومی</b>\n\n"
        f"محدودیت فعلی: {current} فایل در روز\n\n"
        f"محدودیت جدید را وارد کنید:\n"
        f"(برای لغو: /cancel)"
    )
    await state.set_state(AdminStates.setting_global_limit)
    await callback.answer()

@dp.callback_query(F.data == "admin_upload")
@admin_required()
async def upload_file_callback(callback: CallbackQuery, state: FSMContext):
    """آپلود فایل"""
    await callback.message.edit_text(
        "📤 <b>آپلود فایل</b>\n\n"
        "فایل مورد نظر را ارسال کنید:\n"
        "• حداکثر حجم: 2GB\n"
        "• همه انواع فایل پشتیبانی می‌شود\n"
        "• کد یونیک برای دانلود تولید می‌شود\n\n"
        "برای لغو: /cancel"
    )
    await state.set_state(AdminStates.uploading_file)
    await callback.answer()

@dp.callback_query(F.data == "admin_cleanup")
@admin_required()
async def cleanup_callback(callback: CallbackQuery):
    """پاکسازی سیستم"""
    await callback.answer("🗑 در حال پاکسازی...")
    
    cleanup_msg = await callback.message.edit_text("⏳ در حال پاکسازی سیستم...")
    
    try:
        # پاکسازی فایل‌های منقضی
        files_deleted, space_freed = db.cleanup_expired()
        
        # پاکسازی temp
        temp_deleted = 0
        temp_size = 0
        
        for root, dirs, files in os.walk("temp"):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # فایل‌های قدیمی‌تر از 24 ساعت
                    if time.time() - os.path.getmtime(file_path) > 86400:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        temp_deleted += 1
                        temp_size += size
                except:
                    pass
        
        # حذف پوشه‌های خالی
        for root, dirs, files in os.walk("temp", topdown=False):
            try:
                if not os.listdir(root):
                    os.rmdir(root)
            except:
                pass
        
        cleanup_text = f"""
🗑 <b>پاکسازی کامل شد!</b>

📤 <b>فایل‌های آپلود:</b>
├ تعداد حذف شده: {files_deleted}
└ فضای آزاد شده: {format_size(space_freed)}

📁 <b>فایل‌های موقت:</b>
├ تعداد حذف شده: {temp_deleted}
└ فضای آزاد شده: {format_size(temp_size)}

💾 <b>مجموع فضای آزاد شده:</b>
{format_size(space_freed + temp_size)}
        """
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 بازگشت", callback_data="admin_panel")
        
        await cleanup_msg.edit_text(
            cleanup_text.strip(),
            reply_markup=keyboard.as_markup(),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        await cleanup_msg.edit_text(f"❌ خطا در پاکسازی: {str(e)}")

@dp.callback_query(F.data == "admin_detailed_stats")
@admin_required()
async def detailed_stats_callback(callback: CallbackQuery):
    """آمار تفصیلی"""
    await callback.answer("در حال بارگذاری...")
    
    stats = db.get_statistics()
    
    detailed_text = f"""
📊 <b>آمار تفصیلی سیستم</b>

👥 <b>کاربران:</b>
├ کل: {stats['users']['total']:,}
├ فعال امروز: {stats['users']['active_today']:,}
├ VIP: {stats['users']['vip']:,}
└ بن شده: {stats['users']['banned']:,}

📥 <b>دانلودها:</b>
├ کل: {stats['downloads']['total']:,}
├ امروز: {stats['downloads']['today_count']:,}
├ ناموفق: {stats['downloads']['failed']:,}
└ میانگین زمان: {format_time(stats['downloads']['avg_time'] or 0)}

💾 <b>حجم مصرفی:</b>
├ کل: {format_size(stats['downloads']['total_size'] or 0)}
├ امروز: {format_size(stats['downloads']['today_size'] or 0)}
└ میانگین: {format_size(stats['downloads']['avg_size'] or 0)}

📤 <b>آپلودها:</b>
├ تعداد: {stats['uploads']['total']:,}
├ حجم: {format_size(stats['uploads']['total_size'] or 0)}
└ دانلود شده: {stats['uploads']['total_downloads']:,} بار
    """
    
    # توزیع فایل‌ها
    if stats['file_types']:
        detailed_text += "\n\n📎 <b>توزیع انواع فایل:</b>\n"
        for ftype, data in sorted(stats['file_types'].items(), 
                                 key=lambda x: x[1]['count'], 
                                 reverse=True)[:5]:
            percent = (data['count'] / stats['downloads']['total']) * 100
            detailed_text += f"├ {ftype}: {data['count']:,} ({percent:.1f}%)\n"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📈 نمودار", callback_data="admin_charts")
    keyboard.button(text="🔙 بازگشت", callback_data="admin_panel")
    keyboard.adjust(2)
    
    await callback.message.edit_text(
        detailed_text.strip(),
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == "admin_charts")
@admin_required()
async def show_charts_callback(callback: CallbackQuery):
    """نمایش نمودارها"""
    await callback.answer("در حال تولید نمودار...")
    
    processing_msg = await callback.message.edit_text("⏳ در حال تولید نمودارها...")
    
    try:
        # دریافت آمار
        daily_stats = db.get_daily_stats(14)  # 14 روز
        
        # آماده‌سازی داده‌ها
        dates = []
        downloads = []
        sizes = []
        users = []
        
        for stat in daily_stats:
            dates.append(datetime.strptime(stat['date'], '%Y-%m-%d'))
            downloads.append(stat['downloads'])
            sizes.append(stat['size'] / (1024**3))  # GB
            users.append(stat['unique_users'])
        
        # ایجاد نمودار
        plt.style.use('seaborn-v0_8-darkgrid')
        fig = plt.figure(figsize=(14, 10))
        
        # Layout
        gs = fig.add_gridspec(3, 2, height_ratios=[2, 2, 1], hspace=0.3, wspace=0.3)
        
        # نمودار دانلودها
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(dates, downloads, marker='o', linewidth=2.5, 
                markersize=8, color='#2196F3', label='دانلودها')
        ax1.fill_between(dates, downloads, alpha=0.3, color='#2196F3')
        ax1.set_title('تعداد دانلودها در 14 روز گذشته', fontsize=16, fontweight='bold')
        ax1.set_ylabel('تعداد', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # نمودار حجم
        ax2 = fig.add_subplot(gs[1, 0])
        bars = ax2.bar(dates, sizes, color='#4CAF50', alpha=0.8, edgecolor='black')
        ax2.set_title('حجم دانلود (GB)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('گیگابایت', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # رنگ‌بندی میله‌ها
        for i, bar in enumerate(bars):
            if sizes[i] > 50:
                bar.set_color('#FF5722')
            elif sizes[i] > 20:
                bar.set_color('#FF9800')
        
        # نمودار کاربران
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.plot(dates, users, marker='s', linewidth=2, markersize=8, 
                color='#FF9800', label='کاربران فعال')
        ax3.fill_between(dates, users, alpha=0.3, color='#FF9800')
        ax3.set_title('کاربران فعال روزانه', fontsize=14, fontweight='bold')
        ax3.set_ylabel('تعداد', fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # آمار خلاصه
        ax4 = fig.add_subplot(gs[2, :])
        ax4.axis('off')
        
        stats = db.get_statistics()
        summary_text = (
            f"📊 خلاصه آمار: "
            f"کل کاربران: {stats['users']['total']:,} | "
            f"کل دانلودها: {stats['downloads']['total']:,} | "
            f"حجم کل: {format_size(stats['downloads']['total_size'] or 0)} | "
            f"میانگین روزانه: {sum(downloads)/len(downloads):.0f} دانلود"
        )
        ax4.text(0.5, 0.5, summary_text, ha='center', va='center', 
                fontsize=12, bbox=dict(boxstyle="round,pad=0.5", 
                facecolor="lightgray", alpha=0.5))
        
        # تنظیم تاریخ
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.suptitle('گزارش آماری ربات دانلودر', fontsize=18, fontweight='bold')
        
        # ذخیره
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        plt.close()
        
        # ارسال
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=BufferedInputFile(buffer.read(), filename="stats.png"),
            caption="📈 نمودار آماری 14 روز گذشته"
        )
        
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Chart error: {e}", exc_info=True)
        await processing_msg.edit_text(f"❌ خطا در تولید نمودار: {str(e)}")

# ===== کالبک‌های عمومی =====
@dp.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: CallbackQuery):
    """آمار کاربر"""
    await my_stats_command(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """راهنما"""
    await help_command(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("user_chart_"))
async def user_chart_callback(callback: CallbackQuery):
    """نمودار فعالیت کاربر"""
    user_id = int(callback.data.split("_")[2])
    
    if callback.from_user.id != user_id and callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ شما اجازه مشاهده این نمودار را ندارید!", show_alert=True)
        return
    
    await callback.answer("در حال تولید نمودار...")
    
    try:
        stats = db.get_user_statistics(user_id)
        if not stats or not stats.get('recent_activity'):
            await callback.answer("داده‌ای برای نمایش وجود ندارد!", show_alert=True)
            return
        
        # آماده‌سازی داده‌ها
        activity = stats['recent_activity']
        dates = [datetime.strptime(a['date'], '%Y-%m-%d') for a in activity]
        counts = [a['count'] for a in activity]
        sizes = [a['size'] / (1024**3) for a in activity]  # GB
        
        # نمودار
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # دانلودها
        ax1.bar(dates, counts, color='skyblue', edgecolor='navy', alpha=0.8)
        ax1.set_title('تعداد دانلودها در 30 روز گذشته', fontsize=14)
        ax1.set_ylabel('تعداد')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # حجم
        ax2.plot(dates, sizes, marker='o', color='green', linewidth=2)
        ax2.fill_between(dates, sizes, alpha=0.3, color='lightgreen')
        ax2.set_title('حجم دانلود (GB)', fontsize=14)
        ax2.set_ylabel('گیگابایت')
        ax2.grid(True, alpha=0.3)
        
        # فرمت تاریخ
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # ذخیره و ارسال
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        user = stats['user']
        await callback.message.reply_photo(
            photo=BufferedInputFile(buffer.read(), filename="user_stats.png"),
            caption=f"📈 نمودار فعالیت {user['first_name'] or 'کاربر'}"
        )
        
    except Exception as e:
        logger.error(f"User chart error: {e}", exc_info=True)
        await callback.answer(f"خطا: {str(e)}", show_alert=True)

# ===== دستور Cancel =====
@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """لغو عملیات جاری"""
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await message.reply("❌ عملیات لغو شد.")
    else:
        await message.reply("هیچ عملیاتی در حال انجام نیست.")

# ===== مدیریت خطاها =====
@dp.error()
async def error_handler(event, exception):
    """مدیریت خطاهای عمومی"""
    logger.error(f"Error: {exception}", exc_info=True)

# ===== توابع startup و shutdown =====
async def on_startup():
    """عملیات راه‌اندازی"""
    logger.info("🚀 Starting bot...")
    
    # بررسی پوشه‌ها
    for folder in ['downloads', 'uploads', 'temp', 'logs', 'backups']:
        os.makedirs(folder, exist_ok=True)
    
    # پاکسازی اولیه
    try:
        files_deleted, space_freed = db.cleanup_expired()
        logger.info(f"Cleanup: {files_deleted} files, {format_size(space_freed)} freed")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    
    # اطلاعات ربات
    bot_info = await bot.get_me()
    logger.info(f"✅ Bot started: @{bot_info.username}")
    
    # پیام به ادمین‌ها
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🚀 ربات راه‌اندازی شد!\n"
                f"🤖 @{bot_info.username}\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except:
            pass

async def on_shutdown():
    """عملیات خاموش شدن"""
    logger.info("🔴 Shutting down...")
    
    # بستن download manager
    await download_manager.close()
    
    # ذخیره آمار
    stats = db.get_statistics()
    logger.info(f"Final stats: Users={stats['users']['total']}, Downloads={stats['downloads']['total']}")
    
    await bot.session.close()

async def main():
    """تابع اصلی"""
    # تنظیم handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # حذف webhook
    await bot.delete_webhook(drop_pending_updates=True)
    
    # شروع
    logger.info("🤖 Bot is ready!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)