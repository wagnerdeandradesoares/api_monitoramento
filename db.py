from pymongo import MongoClient
import os

# URL do MongoDB local ou remoto
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://wagnergw770_db_user:pBEa1npG18EbmhZf@monitoramento-cluster.bdozvv6.mongodb.net/?appName=monitoramento-cluster")
DB_NAME = "monitoramento"

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Coleções
filiais_col = db["filiais"]
# Coleção de arquivos
arquivos_col = db["arquivos"]


