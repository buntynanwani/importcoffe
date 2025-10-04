#!/usr/bin/env python3
import sqlite3
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'code' / 'db.sqlite3'
if not p.exists():
    conn = sqlite3.connect(p)
    conn.execute('PRAGMA user_version = 1;')
    conn.commit()
    conn.close()
    print('Created', p)
else:
    print('Already exists', p)
