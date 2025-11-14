import os
from datetime import datetime

import fitz
from sqlmodel import Session

from app.models.form_response import FormResponse
from app.utils.database import engine


def get_nivel(score: float) -> str:
    """
    Determina o nível baseado no score.

    Args:
        score: Score de 0 a 10

    Returns:
        String com o nível (BAIXO, MÉDIO, ALTO)
    """
    if score < 3.5:
        return "BAIXO"
    elif score < 7.0:
        return "MÉDIO"
    else:
        return "ALTO"


def get_descritivo(categoria: str, score: float) -> str:
    """
    Retorna texto descritivo baseado no score da categoria.

    Args:
        categoria: Nome da categoria
        score: Score de 0 a 10

    Returns:
        Texto descritivo personalizado
    """
    nivel = get_nivel(score)

    # Textos descritivos básicos (podem ser customizados depois)
    if nivel == "ALTO":
        return f"Você apresenta forte preferência por ambientes com alta {categoria.lower().replace('_', ' ')}."
    elif nivel == "MÉDIO":
        return f"Você apresenta preferência moderada por ambientes com {categoria.lower().replace('_', ' ')}."
    else:
        return f"Você apresenta baixa preferência por ambientes com {categoria.lower().replace('_', ' ')}."


def expand_rect(
    rect: fitz.Rect, expand_x: float = 50, expand_y: float = 20
) -> fitz.Rect:
    """
    Expande um retângulo para dar mais espaço ao texto.

    Args:
        rect: Retângulo original
        expand_x: Pixels para expandir horizontalmente (cada lado)
        expand_y: Pixels para expandir verticalmente (cada lado)

    Returns:
        Novo retângulo expandido
    """
    return fitz.Rect(
        rect.x0 - expand_x, rect.y0 - expand_y, rect.x1 + expand_x, rect.y1 + expand_y
    )


def generate_pdf(response_id: int) -> str:
    """
    Gera PDF personalizado baseado no template.

    Usa apenas fontes base do PDF (Base14) que funcionam em qualquer ambiente,
    incluindo Docker sem fontes instaladas.

    Args:
        response_id: ID do FormResponse no banco

    Returns:
        Caminho do arquivo PDF gerado
    """
    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise Exception(f"Response {response_id} não encontrado")

        # Preparar substituições com informações de fonte por tipo
        data_atual = datetime.now().strftime("%d/%m/%Y")

        # Cinza escuro usado no template
        gray_color = (0.26, 0.26, 0.26)

        replacements = {
            # Nome, email, data - expandir moderadamente
            "{{nome}}": {
                "text": response.name,
                "fontname": "hebo",  # Bold para destaque
                "fontsize": 20,
                "color": (0, 0, 0),
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (50, 5),  # Reduzido para não sair da página
            },
            "{{email}}": {
                "text": response.email,
                "fontname": "helv",
                "fontsize": 18,
                "color": (0, 0, 0),
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (50, 5),
            },
            "{{data}}": {
                "text": data_atual,
                "fontname": "helv",
                "fontsize": 18,
                "color": (0, 0, 0),
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (30, 5),
            },
            # Scores numéricos - expandir moderadamente
            "{1}": {
                "text": f"{response.score_agilidade:.1f}"
                if response.score_agilidade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),  # Reduzido
            },
            "{2}": {
                "text": f"{response.score_agressividade:.1f}"
                if response.score_agressividade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            "{3}": {
                "text": f"{response.score_atencao_detalhes:.1f}"
                if response.score_atencao_detalhes
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            "{4}": {
                "text": f"{response.score_enfase_recompensas:.1f}"
                if response.score_enfase_recompensas
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            "{5}": {
                "text": f"{response.score_estabilidade:.1f}"
                if response.score_estabilidade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            "{6}": {
                "text": f"{response.score_informalidade:.1f}"
                if response.score_informalidade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            "{7}": {
                "text": f"{response.score_orientacao_resultados:.1f}"
                if response.score_orientacao_resultados
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            "{8}": {
                "text": f"{response.score_trabalho_equipe:.1f}"
                if response.score_trabalho_equipe
                else "0.0",
                "fontname": "hebo",
                "fontsize": 42,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 10),
            },
            # Níveis - expandir moderadamente
            "{{nivel1}}": {
                "text": get_nivel(response.score_agilidade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),  # Reduzido
            },
            "{{nivel2}}": {
                "text": get_nivel(response.score_agressividade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            "{{nivel3}}": {
                "text": get_nivel(response.score_atencao_detalhes or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            "{{nivel4}}": {
                "text": get_nivel(response.score_enfase_recompensas or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            "{{nivel5}}": {
                "text": get_nivel(response.score_estabilidade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            "{{nivel6}}": {
                "text": get_nivel(response.score_informalidade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            "{{nivel7}}": {
                "text": get_nivel(response.score_orientacao_resultados or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            "{{nivel8}}": {
                "text": get_nivel(response.score_trabalho_equipe or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_CENTER,
                "expand": (20, 5),
            },
            # Descritivos - expandir horizontalmente mas com cuidado
            "{{DESCRITIVO-AGILIDADE}}": {
                "text": get_descritivo("AGILIDADE", response.score_agilidade or 0),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),  # Reduzido bastante
            },
            "{{DESCRITIVO-AGRESSIVIDADE}}": {
                "text": get_descritivo(
                    "AGRESSIVIDADE", response.score_agressividade or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
            "{{DESCRITIVO-ATENCAO-DETALHES}}": {
                "text": get_descritivo(
                    "ATENÇÃO A DETALHES", response.score_atencao_detalhes or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
            "{{DESCRITIVO-ENFASE-RECOMPENSA}}": {
                "text": get_descritivo(
                    "ÊNFASE EM RECOMPENSA", response.score_enfase_recompensas or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
            "{{DESCRITIVO-ESTABILIDADE}}": {
                "text": get_descritivo(
                    "ESTABILIDADE", response.score_estabilidade or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
            "{{DESCRITIVO-INFORMALIDADE}}": {
                "text": get_descritivo(
                    "INFORMALIDADE", response.score_informalidade or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
            "{{DESCRITIVO-ORIENTACAO-RESULTADO}}": {
                "text": get_descritivo(
                    "ORIENTAÇÃO A RESULTADOS", response.score_orientacao_resultados or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
            "{{TRABALHO-EQUIPE}}": {
                "text": get_descritivo(
                    "TRABALHO EM EQUIPE", response.score_trabalho_equipe or 0
                ),
                "fontname": "helv",
                "fontsize": 12,
                "color": gray_color,
                "align": fitz.TEXT_ALIGN_LEFT,
                "expand": (80, 15),
            },
        }

        # Abrir template PDF
        template_path = os.path.join(os.getcwd(), "relatorio_template.pdf")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template PDF não encontrado em: {template_path}")

        doc = fitz.open(template_path)

        # Substituir texto em todas as páginas
        for page in doc:
            for placeholder, replacement_info in replacements.items():
                # Buscar o placeholder
                text_instances = page.search_for(placeholder)

                for inst in text_instances:
                    # Expandir a área do retângulo
                    expand_x, expand_y = replacement_info.get("expand", (50, 20))
                    expanded_rect = expand_rect(inst, expand_x, expand_y)

                    # Adicionar redação com área expandida
                    page.add_redact_annot(
                        expanded_rect,
                        text=replacement_info["text"],
                        fontname=replacement_info["fontname"],
                        fontsize=replacement_info["fontsize"],
                        text_color=replacement_info["color"],
                        align=replacement_info.get("align", fitz.TEXT_ALIGN_LEFT),
                    )

            page.apply_redactions()

        # Salvar PDF gerado
        output_dir = "/tmp"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            f"relatorio_{response_id}_{response.email.replace('@', '_')}.pdf",
        )

        doc.save(output_path)
        doc.close()

        return output_path
