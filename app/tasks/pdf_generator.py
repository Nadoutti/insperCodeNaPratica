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
    Gera PDF personalizado baseado no template, preservando formatação original.

    Esta versão:
    - Preserva fontes, tamanhos e cores do template original
    - Lida com placeholders quebrados em múltiplas linhas
    - Usa insert_textbox para melhor controle de layout

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

        # Processar cada página
        for page in doc:
            replacements_to_apply = []

            # Buscar cada placeholder no PDF
            for placeholder, replacement_text in replacements.items():
                # Buscar o placeholder completo
                areas = page.search_for(placeholder)

                if areas:
                    # Placeholder encontrado normalmente
                    for area in areas:
                        replacements_to_apply.append(
                            (area, placeholder, replacement_text)
                        )
                else:
                    # Tentar encontrar placeholder quebrado em duas linhas
                    # Exemplo: "{{DESCRITIVO-ORIENTACAO-RESULTAD" na linha 1 e "O}}" na linha 2
                    placeholder_clean = placeholder.replace("{{", "").replace("}}", "")
                    parts = placeholder_clean.split("-")

                    if len(parts) > 1:
                        last_part = parts[-1]
                        # Tentar diferentes pontos de quebra na última parte
                        for break_point in range(1, len(last_part)):
                            # Primeira parte do placeholder quebrado
                            first_half = (
                                "{{"
                                + "-".join(parts[:-1])
                                + "-"
                                + last_part[:break_point]
                            )
                            # Segunda parte
                            second_half = last_part[break_point:] + "}}"

                            areas1 = page.search_for(first_half)
                            areas2 = page.search_for(second_half)

                            if areas1 and areas2:
                                # Combinar as duas áreas
                                combined_area = fitz.Rect(
                                    min(areas1[0].x0, areas2[0].x0),
                                    min(areas1[0].y0, areas2[0].y0),
                                    max(areas1[0].x1, areas2[0].x1),
                                    max(areas1[0].y1, areas2[0].y1),
                                )
                                replacements_to_apply.append(
                                    (combined_area, placeholder, replacement_text)
                                )
                                break

            # Aplicar todas as substituições encontradas
            for area, original_text, new_text in replacements_to_apply:
                # Extrair propriedades de fonte da área
                text_dict = page.get_text("dict", clip=area)

                font_name = "helv"  # fonte padrão
                font_size = 10  # tamanho padrão
                color = (0, 0, 0)  # preto padrão

                # Tentar extrair informações de fonte do texto original
                for block in text_dict.get("blocks", []):  # type: ignore
                    if block.get("type") == 0:  # text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                # Pegar a primeira fonte encontrada
                                font_name = span.get("font", font_name)
                                font_size = span.get("size", font_size)
                                # Converter cor de int para RGB normalizado
                                color_int = span.get("color", 0)
                                r = ((color_int >> 16) & 0xFF) / 255.0
                                g = ((color_int >> 8) & 0xFF) / 255.0
                                b = (color_int & 0xFF) / 255.0
                                color = (r, g, b)
                                break
                            break
                        break

                # Limpar a área (colocar retângulo branco)
                page.draw_rect(area, color=(1, 1, 1), fill=(1, 1, 1))

                # Inserir novo texto na mesma área
                try:
                    rc = page.insert_textbox(
                        area,
                        new_text,
                        fontname=font_name,
                        fontsize=font_size,
                        color=color,
                        align=fitz.TEXT_ALIGN_LEFT,
                    )

                    # Se o texto não couber, tentar com fonte menor
                    if rc < 0:
                        font_size = font_size * 0.9
                        page.draw_rect(area, color=(1, 1, 1), fill=(1, 1, 1))
                        page.insert_textbox(
                            area,
                            new_text,
                            fontname=font_name,
                            fontsize=font_size,
                            color=color,
                            align=fitz.TEXT_ALIGN_LEFT,
                        )
                except Exception as e:
                    # Fallback: usar fonte padrão sem especificar fontname
                    print(
                        f"Aviso: não foi possível usar fonte '{font_name}', usando padrão. Erro: {e}"
                    )
                    page.draw_rect(area, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_textbox(
                        area,
                        new_text,
                        fontsize=font_size,
                        color=color,
                        align=fitz.TEXT_ALIGN_LEFT,
                    )

        # Salvar PDF gerado com compressão
        output_dir = "/tmp"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            f"relatorio_{response_id}_{response.email.replace('@', '_')}.pdf",
        )

        # Salvar com otimizações
        doc.save(
            output_path,
            garbage=4,  # remove objetos não usados
            deflate=True,  # comprimir
            clean=True,  # limpar estrutura
        )
        doc.close()

        return output_path
