# -*- coding: utf-8 -*-
import os
from pathlib import Path

from config import ProductionConfig as BaseConfig


DATA_ROOT = Path(os.getenv('DATA_ROOT', '/data/var'))


class LocalConfig(BaseConfig):
    DEBUG = True
    REVERSE_PROXY_SETUP = True

    PROJECT_DATABASE_PATH = str(DATA_ROOT)
    SUBMISSIONS_DATABASE_PATH = str(DATA_ROOT / 'submissions')
    ASSET_DATABASE_PATH = str(DATA_ROOT / 'assets')
    UPLOADS_DATABASE_PATH = str(DATA_ROOT / 'uploads')
    # FIXME: There is code that won't allow for `SQLALCHEMY_DATABASE_PATH = None`
    #        File "/code/tasks/app/db.py", in upgrade: `if os.path.exists(_db_filepath):`
    # SQLALCHEMY_DATABASE_PATH = None
    SQLALCHEMY_DATABASE_PATH = str(DATA_ROOT / 'database.sqlite3')

    SECRET_KEY = 'seekret'
    SENTRY_DSN = None

    GITLAB_REMOTE_URI = os.getenv('GITLAB_REMOTE_URI')
    GITLAB_PUBLIC_NAME = os.getenv('GITLAB_PUBLIC_NAME')
    GITLAB_EMAIL = os.getenv('GITLAB_EMAIL')
    GITLAB_NAMESPACE = os.getenv('GITLAB_NAMESPACE')
    GITLAB_REMOTE_LOGIN_PAT = os.getenv('GITLAB_REMOTE_LOGIN_PAT')
