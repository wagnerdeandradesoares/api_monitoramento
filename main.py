from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from db import filiais_col, logs_col
from models import Log
import json, os

app = FastAPI(title="Monitoramento Filiais API")

# 🔓 CORS — permite que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_FILE = "config.json"

# =====================================
# 📡 STATUS E LOGS
# =====================================

@app.get("/api/status")
def listar_filiais():
    """Lista todas as filiais registradas"""
    filiais = list(filiais_col.find({}, {"_id": 0}))
    return JSONResponse(filiais)


# =====================================
# 📤 RECEBIMENTO DE LOGS (valida_bkp e launcher)
# =====================================

@app.post("/api/logs")
async def receber_log(request: Request):
    """Recebe logs e atualiza a filial"""
    try:
        dados = await request.json()
        dados["data_execucao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Atualiza ou cria filial
        filiais_col.update_one(
            {"filial": dados["filial"]},
            {"$set": {
                "filial": dados["filial"],
                "terminal": dados.get("terminal", "DESCONHECIDO"),
                "versao": dados.get("versao", "1.0.0"),
                "status": dados.get("status", "OK"),
                "detalhe": dados.get("detalhe", ""),
                "ultima_execucao": dados["data_execucao"]
            }},
            upsert=True
        )

        return {"msg": "✅ Dados da filial atualizados com sucesso"}

    except Exception as e:
        raise HTTPException(400, detail=f"Erro ao salvar dados da filial: {e}")



# =====================================
# ⚙️ CONFIGURAÇÃO GLOBAL
# =====================================

@app.get("/api/config")
def get_config():
    """Lê o arquivo config.json"""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/config")
async def save_config(request: Request):
    """Atualiza o config.json"""
    dados = await request.json()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    return {"msg": "Configuração atualizada"}


# =====================================
# 🧪 TESTE RÁPIDO
# =====================================

@app.get("/api/test")
def test():
    return {"status": "ok", "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
