"""Partes comuns aos dois jeitos de cadastrar no Google Form ("sistema do cliente")."""

from collections.abc import Callable
from dataclasses import dataclass, field

from sessao_1.solucao import ResultadoDePara

FORM_URL: str = "https://docs.google.com/forms/d/e/1FAIpQLSciaeAzDZI8233vcPUgvPua1YcMQVCCdeLEppHsLq0-gs1uKA"
CAMPOS: dict[str, str] = {
    "cnj": "entry.1564099154",
    "estado": "entry.939829063",
    "tribunal": "entry.323214906",
    "comarca": "entry.1170186343",
    "foro": "entry.697666039",
}


@dataclass
class ResumoCadastro:
    """O que aconteceu com cada CNJ no cadastro."""

    enviados: list[str] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)
    pulados: list[ResultadoDePara] = field(default_factory=list)


def montar_payload(resultado: ResultadoDePara) -> dict[str, str]:
    """Monta os campos `entry.<id>` do form a partir de um de-para com sucesso.

    Args:
        resultado: De-para com localização completa.

    Returns:
        Payload do POST em /formResponse.
    """
    loc = resultado.localizacao
    assert loc is not None and loc.completa(), "Só cadastramos de-para com sucesso"
    return {
        CAMPOS["cnj"]: resultado.cnj,
        CAMPOS["estado"]: loc.estado or "",
        CAMPOS["tribunal"]: loc.tribunal or "",
        CAMPOS["comarca"]: loc.comarca or "",
        CAMPOS["foro"]: loc.foro or "",
    }


def executar_cadastro(
    resultados: list[ResultadoDePara],
    enviar_um: Callable[[ResultadoDePara], bool],
) -> ResumoCadastro:
    """Envia cada de-para com sucesso e pula os demais.

    Args:
        resultados: Saída do de-para.
        enviar_um: Envia um resultado e devolve True quando o form confirmou.

    Returns:
        Resumo com enviados, falhas e pulados (com motivo).
    """
    resumo = ResumoCadastro()
    for indice, resultado in enumerate(resultados, start=1):
        print(f"Progresso {indice}/{len(resultados)}: {resultado.cnj}")
        if not resultado.sucesso:
            resumo.pulados.append(resultado)
            continue
        if enviar_um(resultado):
            resumo.enviados.append(resultado.cnj)
            continue
        resumo.falhas.append(resultado.cnj)
    return resumo


def imprimir_resumo(resumo: ResumoCadastro) -> None:
    """Imprime o resumo do cadastro.

    Args:
        resumo: Resultado de executar_cadastro.
    """
    print(f"Enviados: {len(resumo.enviados)}")
    for cnj in resumo.falhas:
        print(f"FALHA no envio: {cnj}")
    for resultado in resumo.pulados:
        print(f"Pulado {resultado.cnj}: {resultado.motivo} (no fluxo real, iria para tratamento humano)")
