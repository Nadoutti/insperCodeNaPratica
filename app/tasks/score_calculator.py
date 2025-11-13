from dataclasses import dataclass

from app.utils.attributes_mapping import (
    ATTRIBUTE_NORMALIZE,
    CATEGORIES,
    INVERTED_ATTRIBUTES,
)


@dataclass
class UserResponse:
    name: str
    email: str
    attribute_values: dict[str, float]  # atributo -> valor (0, 1, ou ranking 1-9)


def parse_webhook(payload: dict) -> UserResponse:
    """
    Extrai informações do payload do webhook do Tally.

    Args:
        payload: Payload JSON do webhook

    Returns:
        UserResponse com nome, email e valores dos atributos
    """
    fields = payload["data"]["fields"]
    name = email = ""
    attr_values = {}

    # Mapear IDs para textos
    id_to_text = {}

    for f in fields:
        label = f.get("label", "")
        value = f.get("value")

        if "nome" in label.lower():
            name = value or ""
        elif "e-mail" in label.lower():
            email = value or ""
        elif "MAIS importantes" in label and f.get("type") == "CHECKBOXES":
            # Selecionar 16 MAIS importantes -> valor = 1
            for opt in f.get("options", []):
                id_to_text[opt["id"]] = opt["text"]
            selected = value if isinstance(value, list) else []
            for attr_id in selected:
                if attr_id in id_to_text:
                    attr_values[id_to_text[attr_id]] = 1.0
        elif "MENOS importantes" in label and f.get("type") == "CHECKBOXES":
            # Checkbox individual MENOS importante -> valor = 0
            if "(" in label and ")" in label:
                attr_text = label.split("(")[1].split(")")[0]
                if value is True:
                    attr_values[attr_text] = 0.0
        elif "ranqueie" in label.lower() and f.get("type") == "RANKING":
            # Mapear ranking - a ordem na lista É o ranking
            # Posição 0 = rank 1 (MAIS importante), posição 8 = rank 9 (MENOS importante)
            for opt in f.get("options", []):
                id_to_text[opt["id"]] = opt["text"]

            if value and isinstance(value, list):
                for rank, opt_id in enumerate(value, 1):  # 1-based
                    if opt_id in id_to_text:
                        attr_values[id_to_text[opt_id]] = float(rank)

    # Normalizar nomes
    normalized_values = {}
    for attr, val in attr_values.items():
        normalized = ATTRIBUTE_NORMALIZE.get(attr.lower(), attr)
        normalized_values[normalized] = val

    return UserResponse(name, email, normalized_values)


def calculate_scores(response: UserResponse) -> dict[str, float]:
    """
    Calcula os scores para cada categoria baseado nos valores dos atributos.

    Args:
        response: UserResponse com os valores dos atributos

    Returns:
        Dicionário com nome da categoria -> score (0-10)
    """
    scores = {}

    for category, attrs in CATEGORIES.items():
        inverted = INVERTED_ATTRIBUTES.get(category, [])

        # Somar valores dos atributos
        soma = 0.0
        count = 0
        for attr in attrs:
            if attr in response.attribute_values:
                val = response.attribute_values[attr]
                # Se invertido, fazer 10 - val
                if attr in inverted:
                    val = 10.0 - val
                soma += val
                count += 1

        # Fórmula: ((soma/n) - 1) * 1.25
        if count > 0:
            score = ((soma / count) - 1) * 1.25
        else:
            score = 0.0

        scores[category] = round(score, 2)

    return scores


def process_webhook(payload: dict) -> dict:
    """
    Processa o payload do webhook e retorna os scores calculados.

    Args:
        payload: Payload JSON do webhook do Tally

    Returns:
        Dicionário com informações do usuário, scores e valores dos atributos
    """
    response = parse_webhook(payload)
    scores = calculate_scores(response)

    return {
        "user": {"name": response.name, "email": response.email},
        "scores": scores,
        "attribute_values": response.attribute_values,
    }
