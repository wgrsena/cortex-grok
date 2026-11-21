"""Como a Centauro fala da cobertura de lance: como sequência, nunca como número frio nem probabilidade.
A IA recebe só o W (assembleias seguidas, 1..6); grupo, mediana e embutido ficam no dossiê de handoff."""


def frase_sequencia(w):
    if not isinstance(w, int) or isinstance(w, bool) or not 0 <= w <= 6:
        raise ValueError("w deve ser inteiro entre 0 e 6")
    if w == 0:
        return "Nas últimas assembleias esse lance não teria sido suficiente, então vale a gente conversar sobre ajustar."
    if w == 1:
        return "Com esse lance você teria sido contemplado na última assembleia."
    return f"Com esse lance você teria sido contemplado nas últimas {w} assembleias seguidas."
