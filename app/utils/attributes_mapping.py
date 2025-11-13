# Categorias e seus respectivos atributos
CATEGORIES = {
    "ESTABILIDADE": [
        "Ser organizado",
        "Segurança",
        "Estabilidade",
        "Ser orientado para regras",
        "Tomar riscos",  # Invertido (10 -)
    ],
    "AGRESSIVIDADE": [
        "Ser competitivo",
        "Ser agressivo",
        "Ser socialmente responsável",  # Invertido (10 -)
    ],
    "ORIENTAÇÃO_A_RESULTADOS": [
        "Ser orientado para resultados",
        "Ser diferente dos outros",  # Invertido (10 -)
        "Ser inovativo",  # Invertido (10 -)
    ],
    "INFORMALIDADE": [
        "Informalidade",
        "Não ser restrito por regras",
        "Compartilhar informações livremente",
    ],
    "AGILIDADE": [
        "Ser rápido em aproveitar oportunidades",
        "Ser voltado para ação",
        "Ser calmo",  # Invertido (10 -)
    ],
    "ÊNFASE_EM_RECOMPENSAS": [
        "Oportunidades para crescimento profissional",
        "Alto pagamento por alta performance",
    ],
    "ATENÇÃO_A_DETALHES": [
        "Ênfase em qualidade",
        "Ser analítico",
        "Prestar atenção em detalhes",
    ],
    "TRABALHO_EM_EQUIPE": [
        "Oferecer elogios por alta performance",
        "Trabalhar em equipe",
        "Tomar responsabilidade individual",  # Invertido (10 -)
        "Autonomia",  # Invertido (10 -)
    ],
}

# Atributos que devem ser invertidos (10 - valor) para certas categorias
INVERTED_ATTRIBUTES = {
    "ESTABILIDADE": ["Tomar riscos"],
    "AGRESSIVIDADE": ["Ser socialmente responsável"],
    "ORIENTAÇÃO_A_RESULTADOS": ["Ser diferente dos outros", "Ser inovativo"],
    "AGILIDADE": ["Ser calmo"],
    "TRABALHO_EM_EQUIPE": ["Tomar responsabilidade individual", "Autonomia"],
}

# Normalização dos textos dos atributos (para lidar com variações)
ATTRIBUTE_NORMALIZE = {
    "ter princípios claros": "Ter princípios claros",
    "tomar responsabilidade individual": "Tomar responsabilidade individual",
    "ter entusiamo pelo trabalho": "Ter entusiamo pelo trabalho",
    "ter uma boa reputação": "Ter uma boa reputação",
    "informalidade": "Informalidade",
    "ser socialmente responsável": "Ser socialmente responsável",
    "autonomia": "Autonomia",
    "justiça": "Justiça",
    "segurança": "Segurança",
    "confrontar conflitos diretamente": "Confrontar conflitos diretamente",
    "adaptabilidade": "Adaptabilidade",
    "alto pagamento por alta performance": "Alto pagamento por alta performance",
    "não ser restrito por muitas regras": "Não ser restrito por regras",
    "ênfase em qualidade": "Ênfase em qualidade",
    "ser orientado para resultados": "Ser orientado para resultados",
    "ter expectativas de alta performance": "Ter expectativas de alta performance",
    "ser calmo": "Ser calmo",
    "ser rápido em aproveitar oportunidades": "Ser rápido em aproveitar oportunidades",
    "ser diferente dos outros": "Ser diferente dos outros",
    "ser competitivo": "Ser competitivo",
    "prestar atenção em detalhes": "Prestar atenção em detalhes",
    "tomar riscos": "Tomar riscos",
    "ser flexível": "Ser flexível",
    "criar amizades no trabalho": "Criar amizades no trabalho",
    "ser agressivo": "Ser agressivo",
    "compartilhar informação livremente": "Compartilhar informações livremente",
    "ser organizado": "Ser organizado",
    "ser analítico": "Ser analítico",
    "oportunidades para crescimento profissional": "Oportunidades para crescimento profissional",
    "oferecer elogios por alta performance": "Oferecer elogios por alta performance",
    "ser decidido": "Ser decidido",
    "trabalhar em equipe": "Trabalhar em equipe",
    "dar suporte para os outros": "Dar suporte para os outros",
    "ser orientado para pessoas": "Ser orientado para pessoas",
    "estabilidade": "Estabilidade",
    "ser inovativo": "Ser inovativo",
    "ser voltado para ação": "Ser voltado para ação",
    "ser orientado para regras": "Ser orientado para regras",
    "trabalhar muitas horas": "Trabalhar muitas horas",
}


def get_category_for_attribute(attribute: str) -> list[str]:
    """
    Retorna as categorias às quais um atributo pertence.

    Args:
        attribute: Nome do atributo

    Returns:
        Lista de categorias às quais o atributo pertence
    """
    # Normalizar o atributo
    normalized = ATTRIBUTE_NORMALIZE.get(attribute.lower(), attribute)

    categories = []
    for category, attributes in CATEGORIES.items():
        if normalized in attributes:
            categories.append(category)

    return categories


def is_inverted_attribute(category: str, attribute: str) -> bool:
    """
    Verifica se um atributo deve ser invertido (10 - valor) para uma categoria específica.

    Args:
        category: Nome da categoria
        attribute: Nome do atributo

    Returns:
        True se o atributo deve ser invertido, False caso contrário
    """
    normalized = ATTRIBUTE_NORMALIZE.get(attribute.lower(), attribute)
    return normalized in INVERTED_ATTRIBUTES.get(category, [])
