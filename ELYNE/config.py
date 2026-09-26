# -*- coding: utf-8 -*-
"""
ELYNE System - shared config & env vars. Same pattern as
FakiraMusafir/config.py and NoBakwaas/config.py.
"""
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")
