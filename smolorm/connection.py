from sqlalchemy import create_engine

SQLITE3 = "sqlite:///db.sqlite3"

engine = create_engine(SQLITE3)

