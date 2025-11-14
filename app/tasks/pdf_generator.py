import os
from datetime import datetime

from sqlmodel import Session

from app.models.form_response import FormResponse
from app.utils.database import engine

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


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
    if fitz is None:
        raise ImportError("PyMuPDF não está instalado. Execute: pip install PyMuPDF")

    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise Exception(f"Response {response_id} não encontrado")

        # Preparar substituições com informações de fonte por tipo
        data_atual = datetime.now().strftime("%d/%m/%Y")

        # Cinza escuro usado no template
        gray_color = (0.26, 0.26, 0.26)

        # Fontes Base14 do PDF - sempre disponíveis:
        # "helv" = Helvetica (normal)
        # "hebo" = Helvetica-Bold
        # "heit" = Helvetica-Oblique (itálico)

        replacements = {
            # Nome, email, data (fonte normal, tamanho 16, preto)
            "{{nome}}": {
                "text": response.name,
                "fontname": "helv",
                "fontsize": 16,
                "color": (0, 0, 0),
            },
            "{{email}}": {
                "text": response.email,
                "fontname": "helv",
                "fontsize": 16,
                "color": (0, 0, 0),
            },
            "{{data}}": {
                "text": data_atual,
                "fontname": "helv",
                "fontsize": 16,
                "color": (0, 0, 0),
            },
            # Scores numéricos (fonte bold, tamanho 38, cinza)
            "{1}": {
                "text": f"{response.score_agilidade:.1f}"
                if response.score_agilidade
                else "0.0",
                "fontname": "hebo",  # Helvetica Bold
                "fontsize": 38,
                "color": gray_color,
            },
            "{2}": {
                "text": f"{response.score_agressividade:.1f}"
                if response.score_agressividade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            "{3}": {
                "text": f"{response.score_atencao_detalhes:.1f}"
                if response.score_atencao_detalhes
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            "{4}": {
                "text": f"{response.score_enfase_recompensas:.1f}"
                if response.score_enfase_recompensas
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            "{5}": {
                "text": f"{response.score_estabilidade:.1f}"
                if response.score_estabilidade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            "{6}": {
                "text": f"{response.score_informalidade:.1f}"
                if response.score_informalidade
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            "{7}": {
                "text": f"{response.score_orientacao_resultados:.1f}"
                if response.score_orientacao_resultados
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            "{8}": {
                "text": f"{response.score_trabalho_equipe:.1f}"
                if response.score_trabalho_equipe
                else "0.0",
                "fontname": "hebo",
                "fontsize": 38,
                "color": gray_color,
            },
            # Níveis (fonte normal, tamanho 16, cinza)
            "{{nivel1}}": {
                "text": get_nivel(response.score_agilidade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel2}}": {
                "text": get_nivel(response.score_agressividade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel3}}": {
                "text": get_nivel(response.score_atencao_detalhes or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel4}}": {
                "text": get_nivel(response.score_enfase_recompensas or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel5}}": {
                "text": get_nivel(response.score_estabilidade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel6}}": {
                "text": get_nivel(response.score_informalidade or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel7}}": {
                "text": get_nivel(response.score_orientacao_resultados or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            "{{nivel8}}": {
                "text": get_nivel(response.score_trabalho_equipe or 0),
                "fontname": "helv",
                "fontsize": 16,
                "color": gray_color,
            },
            # Descritivos (fonte normal, tamanho 10, cinza)
            "{{DESCRITIVO-AGILIDADE}}": {
                "text": get_descritivo("AGILIDADE", response.score_agilidade or 0),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{DESCRITIVO-AGRESSIVIDADE}}": {
                "text": get_descritivo(
                    "AGRESSIVIDADE", response.score_agressividade or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{DESCRITIVO-ATENCAO-DETALHES}}": {
                "text": get_descritivo(
                    "ATENÇÃO A DETALHES", response.score_atencao_detalhes or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{DESCRITIVO-ENFASE-RECOMPENSA}}": {
                "text": get_descritivo(
                    "ÊNFASE EM RECOMPENSA", response.score_enfase_recompensas or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{DESCRITIVO-ESTABILIDADE}}": {
                "text": get_descritivo(
                    "ESTABILIDADE", response.score_estabilidade or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{DESCRITIVO-INFORMALIDADE}}": {
                "text": get_descritivo(
                    "INFORMALIDADE", response.score_informalidade or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{DESCRITIVO-ORIENTACAO-RESULTADO}}": {
                "text": get_descritivo(
                    "ORIENTAÇÃO A RESULTADOS", response.score_orientacao_resultados or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
            },
            "{{TRABALHO-EQUIPE}}": {
                "text": get_descritivo(
                    "TRABALHO EM EQUIPE", response.score_trabalho_equipe or 0
                ),
                "fontname": "helv",
                "fontsize": 10,
                "color": gray_color,
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
                    # Adicionar redação com fonte e cor especificadas
                    page.add_redact_annot(
                        inst,
                        text=replacement_info["text"],
                        fontname=replacement_info["fontname"],
                        fontsize=replacement_info["fontsize"],
                        text_color=replacement_info["color"],
                    )

            # Tratar o placeholder quebrado {{DESCRITIVO-ORIENTACAO-RESULTAD\nO}}
            part1_list = page.search_for("{{DESCRITIVO-ORIENTACAO-RESULTAD")
            part2_list = page.search_for("O}}")

            if part1_list and part2_list:
                # Criar retângulo combinado
                combined_rect = fitz.Rect(
                    part1_list[0].x0,
                    part1_list[0].y0,
                    part2_list[0].x1,
                    part2_list[0].y1,
                )

                # Pegar o texto de substituição
                replacement_info = replacements.get(
                    "{{DESCRITIVO-ORIENTACAO-RESULTADO}}", {}
                )

                page.add_redact_annot(
                    combined_rect,
                    text=replacement_info.get("text", ""),
                    fontname=replacement_info.get("fontname", "helv"),
                    fontsize=replacement_info.get("fontsize", 10),
                    text_color=replacement_info.get("color", gray_color),
                )

            # Aplicar todas as redações
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
