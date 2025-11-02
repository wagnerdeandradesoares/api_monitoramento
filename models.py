from pydantic import BaseModel
class Filial(BaseModel):
    filial: str
    terminal: str
    versao: str
    status: str
    detalhe: str
    ultima_execucao: str
