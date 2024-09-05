from langchain_community.llms import OpenAI
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
import os
import openai
from dotenv import load_dotenv, find_dotenv
import pandas as pd
from sqlalchemy import create_engine

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Set OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Get database connection parameters
db_type = os.getenv('DB_TYPE')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
hostname = os.getenv('DB_HOSTNAME')
port = os.getenv('DB_PORT')
database = os.getenv('DB_NAME')

# Construct the database URI
uri = f"{db_type}://{username}:{password}@{hostname}:{port}/{database}"

# 1. Connect to PostgreSQL
engine = create_engine(uri)

# 2. Create a table from Appro limited in time
select_query = """
SELECT cetab, ltie, qterec1, daterec
FROM dafacd
WHERE daterec >= '2024-01-02' 
AND daterec <= '2024-06-30';
"""

# Execute the query and store the result in a DataFrame
df = pd.read_sql_query(select_query, engine)
print("Data from dafacd:")
print(df)

# Create an in-memory SQLite database and write the DataFrame to it
sqlite_engine = create_engine(r'sqlite:///C:/Users/bob/PycharmProjects/QA Tool/sqlitedb/temp.db', echo=False)
df.to_sql('Appro', sqlite_engine, index=False, if_exists='replace')

# 3. Create a 2nd table with the names of the Group suppliers
select_query = """
SELECT DISTINCT lvniv1
FROM dhierfou
WHERE ltypehier = 'GROUPE INDUSTRIEL/PRODUCTEURS';
"""

# Execute the query and store the result in a DataFrame
df = pd.read_sql_query(select_query, engine)
print("Group suppliers from dhierfou:")
print(df)
df.to_sql('Groupe', sqlite_engine, index=False, if_exists='replace')

# 4. Create a 3rd table with the Appro table filtered by Group suppliers
select_query = """
SELECT Appro.cetab, Appro.ltie, Appro.qterec1, Appro.daterec
FROM Appro
INNER JOIN Groupe
ON Appro.ltie LIKE Groupe.lvniv1 || '%';
"""

"""
#This is to combine the whole thing into one sql commande block
SELECT t1.ltie, t1.qterec1, t1.daterec
FROM dafacd t1
INNER JOIN dhierfou t2
ON t1.ltie LIKE t2.lvniv1 || '%'
WHERE t1.cetab = '13'
AND t1.daterec >= '2024-01-02'
AND t1.daterec <= '2024-06-30'
AND t2.ltypehier = 'GROUPE INDUSTRIEL/PRODUCTEURS';
"""

# Execute the query and store the result in a DataFrame using the SQLite engine
df = pd.read_sql_query(select_query, sqlite_engine)
print("Filtered Appro data based on Group suppliers:")
print(df)
df.to_sql('ApproGroupe', sqlite_engine, index=False, if_exists='replace')


db = SQLDatabase(sqlite_engine)
llm = OpenAI(verbose = True, api_key=OPENAI_API_KEY)

def database_response(query_text, llm = llm, db=db):
    db_chain = SQLDatabaseChain.from_llm(llm, db, verbose = True)
    # use the following for very large DB
    #db_chain = SQLDatabaseSequentialChain.from_llm(llm=llm, db=db, verbose=True, use_query_checker=True, top_k=1)
    res = db_chain.invoke(query_text)
    return res

database_response("Quels sont les 5 fournisseurs avec le plus de poids en mars 2024?")
#database_response("Montrer les poids mensuels par fournisseur en 6 colonnes, de janvier à juin")
