# -*- coding: utf-8 -*-
"""
NoBakwaas - shared config & env vars. Same pattern as FakiraMusafir/config.py.
"""
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
# Business-specific page ID (not the shared NOTION_PAGE_ID name) so
# NoBakwaas and ELYNE can't accidentally write into the same page.
NOTION_PAGE_ID = os.getenv("NOBAKWAAS_NOTION_PAGE_ID", "")
