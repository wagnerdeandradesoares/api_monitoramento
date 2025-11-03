from pydantic import BaseModel
from typing import List, Optional
class Filial(BaseModel):
    filial: str
    terminal: str
    versao: str
    status: str
    detalhe: str
    ultima_execucao: str
class ArquivoExecucao(BaseModel):
    nome: str
    ativo: bool
    horario: List[str]
    intervalo: int = 0
    local: str
    terminal: Optional[List[str]] = []
    dia: Optional[List[int]] = []
    mes: Optional[List[int]] = []
    intervalo_dias: Optional[int] = 0

# Modelo de resposta para listar os arquivos programados
class ArquivoExecucaoResponse(BaseModel):
    nome: str
    ativo: bool
    horario: List[str]
    intervalo: int
    local: str
    terminal: Optional[List[str]] = []
    dia: Optional[List[int]] = []
    mes: Optional[List[int]] = []
    intervalo_dias: Optional[int] = 0
