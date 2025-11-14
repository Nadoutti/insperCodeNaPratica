import os
from datetime import datetime
from typing import TypedDict

import fitz
from sqlmodel import Session

from app.models.form_response import FormResponse
from app.utils.database import engine


class ReplacementConfig(TypedDict):
    """Configuração de substituição de texto no PDF."""

    text: str
    fontname: str
    fontsize: int
    color: tuple[float, float, float]
    align: int


# Constantes
GRAY_COLOR = (0.26, 0.26, 0.26)
BLACK_COLOR = (0, 0, 0)

NIVEL_THRESHOLDS = {
    "BAIXO": (0, 3.5),
    "MÉDIO": (3.5, 7.0),
    "ALTO": (7.0, 10.0),
}

FONT_CONFIGS = {
    "titulo": {"fontname": "hebo", "fontsize": 20, "color": BLACK_COLOR},
    "subtitulo": {"fontname": "helv", "fontsize": 18, "color": BLACK_COLOR},
    "score": {"fontname": "hebo", "fontsize": 42, "color": GRAY_COLOR},
    "nivel": {"fontname": "helv", "fontsize": 16, "color": GRAY_COLOR},
    "descritivo": {"fontname": "helv", "fontsize": 12, "color": GRAY_COLOR},
}


def get_nivel(score: float) -> str:
    """Determina o nível baseado no score (0-10)."""
    for nivel, (min_val, max_val) in NIVEL_THRESHOLDS.items():
        if min_val <= score < max_val:
            return nivel
    return "ALTO"


def get_descritivo(categoria: str, score: float) -> str:
    """Retorna texto descritivo baseado no score da categoria."""
    nivel = get_nivel(score)
    categoria_formatada = categoria.lower()

    descritivos = {
        "ALTO": f"Você apresenta forte preferência por ambientes com alta {categoria_formatada}.",
        "MÉDIO": f"Você apresenta preferência moderada por ambientes com {categoria_formatada}.",
        "BAIXO": f"Você apresenta baixa preferência por ambientes com {categoria_formatada}.",
    }

    return descritivos[nivel]


def create_replacement(
    text: str, config_type: str, align: int = fitz.TEXT_ALIGN_LEFT
) -> ReplacementConfig:
    """Cria configuração de substituição baseada no tipo."""
    config = FONT_CONFIGS[config_type].copy()
    config["text"] = text
    config["align"] = align
    return config  # type: ignore


def build_replacements(response: FormResponse) -> dict[str, ReplacementConfig]:
    """Constrói dicionário de substituições a partir do FormResponse."""
    data_atual = datetime.now().strftime("%d/%m/%Y")

    # Mapeamento de scores
    scores = {
        "agilidade": response.score_agilidade or 0,
        "agressividade": response.score_agressividade or 0,
        "atencao_detalhes": response.score_atencao_detalhes or 0,
        "enfase_recompensas": response.score_enfase_recompensas or 0,
        "estabilidade": response.score_estabilidade or 0,
        "informalidade": response.score_informalidade or 0,
        "orientacao_resultados": response.score_orientacao_resultados or 0,
        "trabalho_equipe": response.score_trabalho_equipe or 0,
    }

    replacements = {
        # Cabeçalho
        "{{nome}}": create_replacement(response.name, "titulo"),
        "{{email}}": create_replacement(response.email, "subtitulo"),
        "{{data}}": create_replacement(data_atual, "subtitulo"),
    }

    # Configuração das categorias com placeholders corretos
    categorias = [
        ("agilidade", "AGILIDADE", "{{DESCRITIVO-AGILIDADE}}"),
        ("agressividade", "AGRESSIVIDADE", "{{DESCRITIVO-AGRESSIVIDADE}}"),
        ("atencao_detalhes", "ATENÇÃO A DETALHES", "{{DESCRITIVO-ATENCAO-DETALHES}}"),
        (
            "enfase_recompensas",
            "ÊNFASE EM RECOMPENSA",
            "{{DESCRITIVO-ENFASE-RECOMPENSA}}",
        ),
        ("estabilidade", "ESTABILIDADE", "{{DESCRITIVO-ESTABILIDADE}}"),
        ("informalidade", "INFORMALIDADE", "{{DESCRITIVO-INFORMALIDADE}}"),
        (
            "orientacao_resultados",
            "ORIENTAÇÃO PARA RESULTADO",
            "{{DESCRITIVO-ORIENTACAO-RESULTADO}}",
        ),
        ("trabalho_equipe", "TRABALHO EM EQUIPE", "{{TRABALHO-EQUIPE}}"),
    ]

    for idx, (key, nome_categoria, placeholder_descritivo) in enumerate(
        categorias, start=1
    ):
        score = scores[key]

        # Score numérico
        replacements[f"{{{idx}}}"] = create_replacement(
            f"{score:.1f}", "score", fitz.TEXT_ALIGN_CENTER
        )

        # Nível
        replacements[f"{{{{nivel{idx}}}}}"] = create_replacement(
            get_nivel(score), "nivel", fitz.TEXT_ALIGN_CENTER
        )

        # Descritivo
        replacements[placeholder_descritivo] = create_replacement(
            get_descritivo(nome_categoria, score), "descritivo"
        )

    return replacements


def apply_replacements(
    doc: fitz.Document, replacements: dict[str, ReplacementConfig]
) -> None:
    """Aplica substituições em todas as páginas do documento."""
    for page in doc:
        for placeholder, config in replacements.items():
            text_instances = page.search_for(placeholder)

            for inst in text_instances:
                # Usar o retângulo original sem expansão
                page.add_redact_annot(
                    inst,
                    text=config["text"],
                    fontname=config["fontname"],
                    fontsize=config["fontsize"],
                    text_color=config["color"],
                    align=config["align"],
                )

        page.apply_redactions()


def generate_pdf(response_id: int) -> str:
    """
    Gera PDF personalizado baseado no template.

    Args:
        response_id: ID do FormResponse no banco

    Returns:
        Caminho do arquivo PDF gerado
    """
    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise ValueError(f"Response {response_id} não encontrado")

        # Validar template
        template_path = os.path.join(os.getcwd(), "relatorio_template.pdf")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template não encontrado: {template_path}")

        # Processar PDF
        doc = fitz.open(template_path)
        replacements = build_replacements(response)
        apply_replacements(doc, replacements)

        # Salvar
        output_dir = "/tmp"
        os.makedirs(output_dir, exist_ok=True)
        output_filename = (
            f"relatorio_{response_id}_{response.email.replace('@', '_')}.pdf"
        )
        output_path = os.path.join(output_dir, output_filename)

        doc.save(output_path)
        doc.close()

        return output_path
