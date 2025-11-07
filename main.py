from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, time
from db import filiais_col, arquivos_col, excecutar_col
import json, os

app = FastAPI(title="Monitoramento API")

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
    """Recebe logs e atualiza ou cria um novo log para a filial e terminal"""
    try:
        dados = await request.json()

        # Verifica se já existe um log para a mesma filial e terminal
        filtro = {"filial": dados["filial"], "terminal": dados["terminal"]}

        # Atualiza o log se a combinação de filial e terminal já existir
        resultado = filiais_col.update_one(
            filtro,
            {"$set": {
                "filial": dados["filial"],
                "terminal": dados["terminal"],
                "versao": dados.get("versao", "1.0.0"),
                "status": dados.get("status", "OK"),
                "detalhe": dados.get("detalhe", ""),
                "ultima_execucao": dados.get("data")
            }},
            upsert=False  # Não cria novo registro se não encontrar um existente
        )

        # Se nenhum documento foi atualizado, significa que a combinação filial + terminal não existe, então cria um novo
        if resultado.matched_count == 0:
            # Inserir um novo log se não encontrou o existente
            filiais_col.insert_one({
                "filial": dados["filial"],
                "terminal": dados["terminal"],
                "versao": dados.get("versao", "1.0.0"),
                "status": dados.get("status", "OK"),
                "detalhe": dados.get("detalhe", ""),
                "ultima_execucao": dados.get("data")
            })

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
    try:
        dados = await request.json()  # Recebe os dados do corpo da requisição
        # Verificação simples para garantir que os dados não estejam vazios
        if not dados:
            raise HTTPException(status_code=400, detail="Dados inválidos ou vazios.")

        # Salvar no arquivo config.json
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return {"msg": "Configuração atualizada com sucesso!"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Erro ao processar os dados enviados.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a configuração: {str(e)}")


# Endpoint para listar arquivos
@app.get("/api/arquivos")
def listar_arquivos():
    """Lista todos os arquivos cadastrados no banco"""
    try:
        # Aqui você retorna os arquivos, incluindo o _id explicitamente
        arquivos = list(arquivos_col.find({}, {}))  # Sem restrição de campos
        return JSONResponse(arquivos)
    except Exception as e:
        # Captura qualquer erro que aconteça e imprime no log
        print(f"Erro ao buscar arquivos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar arquivos")



# Endpoint para adicionar arquivo
@app.post("/api/arquivos")
async def adicionar_arquivo(request: Request):
    """Adiciona um novo arquivo ao banco"""
    try:
        dados = await request.json()

        # Imprime os dados recebidos para depuração
        print(f"Dados recebidos: {dados}")

        # Verifica se todos os campos estão presentes
        if not all(key in dados for key in ["nome", "url", "descricao", "destino", "versao"]):
            raise HTTPException(status_code=400, detail="Campos incompletos.")

        # Adiciona o arquivo à coleção
        arquivos_col.insert_one(dados)

        return {"msg": "✅ Arquivo adicionado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar arquivo: {str(e)}")
    
    
    
@app.get("/api/arquivos/{arquivo_id}")
async def obter_arquivo(arquivo_id: str):
    try:
        # Verifique se o ID está sendo recebido corretamente como string
        arquivo = arquivos_col.find_one({"_id": ObjectId(arquivo_id)})

        if not arquivo:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        # Certifique-se de que o MongoDB retorna os dados sem o _id
        arquivo["_id"] = str(arquivo["_id"])  # Convertendo ObjectId para string
        return arquivo

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar arquivo: {str(e)}")
    
    



# Endpoint para editar arquivo usando o ID ao invés do nome
@app.put("/api/arquivos/{id}")
async def editar_arquivo(id: str, request: Request):
    """Edita as informações de um arquivo no banco"""
    try:
        dados = await request.json()

        # Verifica se os campos necessários estão presentes
        if not all(key in dados for key in ["url", "descricao", "destino", "versao"]):
            raise HTTPException(status_code=400, detail="Campos incompletos.")

        # Atualiza o arquivo no banco de dados
        resultado = arquivos_col.update_one(
            {"_id": id},  # Agora usando o id para localizar o arquivo
            {"$set": dados}
        )

        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

        return {"msg": "✅ Arquivo atualizado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao editar arquivo: {str(e)}")



# =====================================
# 🖥️ EXECUÇÃO DE ARQUIVOS PROGRAMADOS
# =====================================

# Endpoint para listar os arquivos programados para execução
@app.get("/api/execucao")
def listar_execucoes():
    """Lista todos os arquivos agendados para execução"""
    execucoes = list(excecutar_col.find({"ativo": True}, {"_id": 0}))
    return JSONResponse(execucoes)


# Endpoint para agendar um arquivo para execução
@app.post("/api/execucao")
async def agendar_execucao(request: Request):
    """Agendar um novo arquivo para execução em horários ou intervalos específicos"""
    try:
        dados = await request.json()

        # Validação de campos obrigatórios
        if not all(key in dados for key in ["nome", "ativo", "horario", "local"]):
            raise HTTPException(status_code=400, detail="Campos obrigatórios ausentes.")

        # Adiciona o agendamento de execução no banco de dados
        excecutar_col.insert_one(dados)

        return {"msg": "✅ Arquivo agendado para execução com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao agendar execução: {str(e)}")


# Endpoint para disparar a execução de arquivos com base na programação
@app.post("/api/executar")
async def executar_arquivos_programados():
    """Executa arquivos com base nos agendamentos, filiais, e terminais definidos"""
    try:
        # Pega o horário atual
        agora = datetime.now()

        # Filtra arquivos com execução programada para o horário atual
        arquivos_agendados = list(excecutar_col.find({
            "ativo": True,
            "horario": {"$in": [agora.strftime("%H:%M")]},  # Verifica o horário atual
        }, {"_id": 0}))

        # Se não houver arquivos para execução, retorna uma mensagem
        if not arquivos_agendados:
            return JSONResponse({"msg": "Nenhum arquivo agendado para este horário."}, status_code=404)

        for arquivo in arquivos_agendados:
            # Aqui você pode adicionar a lógica de execução do arquivo
            # Por exemplo, você pode enviar comandos via SSH ou outro protocolo para os terminais ou filiais
            for terminal in arquivo.get("terminal", []):
                for filial in arquivo.get("filial", []):
                    # Simulação de comando de execução:
                    print(f"Executando {arquivo['nome']} na filial {filial} e terminal {terminal}")
                    # Aqui você pode chamar uma função que manda o comando real para o terminal/filial

        return JSONResponse({"msg": "Comandos executados com sucesso!"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar arquivos: {str(e)}")



