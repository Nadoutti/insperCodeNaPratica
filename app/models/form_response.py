from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class FormResponse(SQLModel, table=True):
    """Modelo para armazenar respostas do formulário Tally"""

    # Campos principais
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # Email único por participante
    name: str

    # Metadados da submissão
    tally_response_id: str = Field(unique=True, index=True)  # ID único do Tally
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # Payload completo do webhook (JSON)
    raw_payload: str  # Armazenar como string JSON

    # Scores calculados (0-10)
    score_agilidade: Optional[float] = None
    score_agressividade: Optional[float] = None
    score_atencao_detalhes: Optional[float] = None
    score_enfase_recompensas: Optional[float] = None
    score_estabilidade: Optional[float] = None
    score_informalidade: Optional[float] = None
    score_orientacao_resultados: Optional[float] = None
    score_trabalho_equipe: Optional[float] = None

    # Status do processamento
    processed: bool = Field(default=False)
    pdf_generated: bool = Field(default=False)
    email_sent: bool = Field(default=False)

    # Controle de erros
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
