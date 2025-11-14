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

        # Preparar substituições
        data_atual = datetime.now().strftime("%d/%m/%Y")

        replacements = {
            "{{nome}}": response.name,
            "{{email}}": response.email,
            "{{data}}": data_atual,
            # Scores numéricos
            "{1}": f"{response.score_agilidade:.1f}"
            if response.score_agilidade
            else "0.0",
            "{2}": f"{response.score_agressividade:.1f}"
            if response.score_agressividade
            else "0.0",
            "{3}": f"{response.score_atencao_detalhes:.1f}"
            if response.score_atencao_detalhes
            else "0.0",
            "{4}": f"{response.score_enfase_recompensas:.1f}"
            if response.score_enfase_recompensas
            else "0.0",
            "{5}": f"{response.score_estabilidade:.1f}"
            if response.score_estabilidade
            else "0.0",
            "{6}": f"{response.score_informalidade:.1f}"
            if response.score_informalidade
            else "0.0",
            "{7}": f"{response.score_orientacao_resultados:.1f}"
            if response.score_orientacao_resultados
            else "0.0",
            "{8}": f"{response.score_trabalho_equipe:.1f}"
            if response.score_trabalho_equipe
            else "0.0",
            # Níveis
            "{{nivel1}}": get_nivel(response.score_agilidade or 0),
            "{{nivel2}}": get_nivel(response.score_agressividade or 0),
            "{{nivel3}}": get_nivel(response.score_atencao_detalhes or 0),
            "{{nivel4}}": get_nivel(response.score_enfase_recompensas or 0),
            "{{nivel5}}": get_nivel(response.score_estabilidade or 0),
            "{{nivel6}}": get_nivel(response.score_informalidade or 0),
            "{{nivel7}}": get_nivel(response.score_orientacao_resultados or 0),
            "{{nivel8}}": get_nivel(response.score_trabalho_equipe or 0),
            # Descritivos
            "{{DESCRITIVO-AGILIDADE}}": get_descritivo(
                "AGILIDADE", response.score_agilidade or 0
            ),
            "{{DESCRITIVO-AGRESSIVIDADE}}": get_descritivo(
                "AGRESSIVIDADE", response.score_agressividade or 0
            ),
            "{{DESCRITIVO-ATENCAO-DETALHES}}": get_descritivo(
                "ATENÇÃO A DETALHES", response.score_atencao_detalhes or 0
            ),
            "{{DESCRITIVO-ENFASE-RECOMPENSA}}": get_descritivo(
                "ÊNFASE EM RECOMPENSA", response.score_enfase_recompensas or 0
            ),
            "{{DESCRITIVO-ESTABILIDADE}}": get_descritivo(
                "ESTABILIDADE", response.score_estabilidade or 0
            ),
            "{{DESCRITIVO-INFORMALIDADE}}": get_descritivo(
                "INFORMALIDADE", response.score_informalidade or 0
            ),
            "{{DESCRITIVO-ORIENTACAO-RESULTADO}}": get_descritivo(
                "ORIENTAÇÃO A RESULTADOS", response.score_orientacao_resultados or 0
            ),
            "{{TRABALHO-EQUIPE}}": get_descritivo(
                "TRABALHO EM EQUIPE", response.score_trabalho_equipe or 0
            ),
        }

        # Abrir template PDF
        template_path = os.path.join(os.getcwd(), "relatorio_template.pdf")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template PDF não encontrado em: {template_path}")

        doc = fitz.open(template_path)

        # Substituir texto em todas as páginas
        for page in doc:
            # Aplicar substituições normais
            for old_text, new_text in replacements.items():
                # Buscar todas as instâncias do texto
                text_instances = page.search_for(old_text)

                for inst in text_instances:
                    # Adicionar anotação de redação
                    page.add_redact_annot(inst, new_text)

            # Tratar especialmente o placeholder quebrado
            # {{DESCRITIVO-ORIENTACAO-RESULTAD\nO}}
            part1_list = page.search_for("{{DESCRITIVO-ORIENTACAO-RESULTAD")
            part2_list = page.search_for("O}}")

            if part1_list and part2_list:
                # Encontrou o placeholder quebrado
                # Pegar as coordenadas e fazer uma área grande o suficiente
                part1 = part1_list[0]
                part2 = part2_list[0]

                # Criar retângulo que engloba as duas partes
                combined_rect = fitz.Rect(
                    part1.x0,  # x inicial da primeira parte
                    part1.y0,  # y inicial da primeira parte
                    part2.x1,  # x final da segunda parte
                    part2.y1,  # y final da segunda parte
                )

                # Substituir com o texto correto
                replacement_text = replacements.get(
                    "{{DESCRITIVO-ORIENTACAO-RESULTADO}}", ""
                )
                page.add_redact_annot(combined_rect, replacement_text)

            # Aplicar redações
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
