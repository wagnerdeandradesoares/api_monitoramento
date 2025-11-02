from pydantic import BaseModel
from typing import Optional

class Log(BaseModel):
    filial: str
    terminal: Optional[str] = "DESCONHECIDO"
    status: str
    detalhe: str
    versao: Optional[str] = "1.0.0"

class Filial(BaseModel):
    filial: str
    terminal: str
    versao: str
    status: str
    detalhe: str
    ultima_execucao: str
