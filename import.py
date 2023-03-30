import csv
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)

    for isbn, title , author, year in reader:
        query = text("INSERT INTO books (isbn, title , author, year) VALUES (:isbn, :title , :author, :year)")
        db.execute(query,{"isbn":isbn, "title":title , "author":author, "year":year})
    db.commit()

if __name__ == "__main__":
    main()