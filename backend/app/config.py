from __future__ import annotations

import os

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:change-me@localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "resume-ai")
