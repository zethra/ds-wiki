"""
Database setup for the webapp.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

"""
Where the Sqlite database can be found.
"""
SQLALCHEMY_DATABASE_URL = f"sqlite:///./sql_app_{os.path.basename(sys.argv[1])}.db"
# SQLALCHEMY_DATABASE_URL = f"sqlite://"

"""
The db engine.
"""
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

"""
A value to use for the local session
"""
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

"""
Base class to inherit from for an object in the db.
"""
Base = declarative_base()
