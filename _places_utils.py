#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funções compartilhadas pelos geradores gerar_restaurantes_google.py e
gerar_atracoes_google.py. Não é executado sozinho.

Critério de seleção ("padrão de fama/custo-benefício" pedido pelo usuário):
    fama = nota * log10(avaliacoes + 1)
Isso favorece lugares FAMOSOS e bem avaliados (nota alta E muita gente avaliou),
em vez de um 5.0 com 3 avaliações. Como o público é de alto poder aquisitivo,
não penalizamos preço alto - só usamos nota + volume de avaliações.
"""
import math
import sys
import time
import unicodedata

import requests


def obter_api_key_validada():
    """Le GOOGLE_PLACES_API_KEY do ambiente e valida que e' um valor limpo
    (so ASCII, sem espacos/traços "espertos" que copiar-colar as vezes introduz).
    Isso evita o erro 'UnicodeEncodeError: latin-1 codec...' ao montar o header HTTP."""
    import os
    bruta = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not bruta:
        print("ERRO: defina GOOGLE_PLACES_API_KEY antes de rodar.")
        print('No cmd:        set GOOGLE_PLACES_API_KEY=sua_chave_aqui')
        print('No PowerShell: $env:GOOGLE_PLACES_API_KEY = "sua_chave_aqui"')
        sys.exit(1)

    chave = bruta.strip()
    suspeitos = [(i, c, hex(ord(c))) for i, c in enumerate(chave) if ord(c) > 126]
    if suspeitos:
        print("ERRO: a GOOGLE_PLACES_API_KEY tem caractere(s) fora do padrao (provavelmente")
        print("de copiar/colar - um traço \"esperto\" (–) no lugar do hifen (-), ou espaço invisivel).")
        print("Caracteres suspeitos encontrados:")
        for i, c, code in suspeitos:
            print(f"  posicao {i}: {c!r} (codigo {code})")
        print("\nDigite a chave manualmente no terminal (sem copiar/colar) ou copie de novo")
        print("direto da tela 'Chaves e credenciais' do Google Cloud Console.")
        sys.exit(1)

    if chave != bruta:
        print("Aviso: havia espaço(s) sobrando no começo/fim da chave - removido automaticamente.")

    return chave

API_URL = "https://places.googleapis.com/v1/places:searchText"


def carregar_config():
    """Le config_imovel.json (a unica coisa a editar para trocar de imovel/cidade)."""
    import json
    from pathlib import Path
    return json.loads((Path(__file__).resolve().parent / "config_imovel.json").read_text(encoding="utf-8"))


CONFIG = carregar_config()
CENTRO_LAT = CONFIG["imovel"]["lat"]
CENTRO_LNG = CONFIG["imovel"]["lng"]
RAIO_BUSCA_M = float(CONFIG["cidade"]["raio_busca_m"])

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.googleMapsUri",
    "places.businessStatus",
    "places.priceLevel",
    "places.editorialSummary",
])

PRICE_LEVEL_MAP = {
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}

# tenta primeiro com este piso de avaliações; se a categoria nao atingir a meta,
# relaxa a etapas (nunca inventa dado pra completar, so aceita lugares "menos famosos")
FAIXAS_MIN_AVALIACOES = [100, 50, 20, 5]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return texto.lower().strip()


def fama_score(lugar):
    nota = lugar.get("rating") or 0
    avaliacoes = lugar.get("userRatingCount") or 0
    return nota * math.log10(avaliacoes + 1)


def buscar_texto(query, api_key, tipo=None):
    payload = {
        "textQuery": query,
        "languageCode": "pt-BR",
        "maxResultCount": 20,
        "locationBias": {
            "circle": {
                "center": {"latitude": CENTRO_LAT, "longitude": CENTRO_LNG},
                "radius": RAIO_BUSCA_M,
            }
        },
    }
    if tipo:
        payload["includedType"] = tipo

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json().get("places", [])


def buscar_categoria_ampla(query, tipo, api_key):
    """Busca com o tipo (mais preciso) E sem tipo (mais amplo), mescla por place_id.
    Isso evita perder lugares famosos que o Google classifica num tipo diferente
    do esperado (ex.: um café que a API não marca como 'cafe')."""
    vistos = {}
    for t in (tipo, None):
        try:
            lugares = buscar_texto(query, api_key, tipo=t)
        except requests.HTTPError:
            lugares = []
        for l in lugares:
            pid = l.get("id")
            if pid and pid not in vistos:
                vistos[pid] = l
        time.sleep(0.15)
    return list(vistos.values())


def endereco_na_cidade(lugar):
    """True se o endereco do Google contem o filtro da cidade (config_imovel.json)."""
    return CONFIG["cidade"]["filtro_endereco"] in normalizar(lugar.get("formattedAddress", ""))


def nome_excluido(lugar):
    """True se o nome contem algum item de 'excluir_nomes' do config (ex.: lugares que o dono nao quer)."""
    nome = normalizar((lugar.get("displayName") or {}).get("text", ""))
    return any(normalizar(x) in nome for x in CONFIG.get("excluir_nomes", []))


def operacional(lugar):
    return lugar.get("businessStatus") == "OPERATIONAL"


def selecionar_top_n(candidatos, n, usados_globalmente):
    """Filtra por cidade+operacional, tenta as faixas de MIN_AVALIACOES em ordem
    (mais exigente primeiro) e devolve os N mais 'famosos' (nota * log(avaliações)).
    Retorna (selecionados, faixa_usada)."""
    base = [
        l for l in candidatos
        if operacional(l) and endereco_na_cidade(l) and not nome_excluido(l) and l.get("id") not in usados_globalmente
    ]
    for piso in FAIXAS_MIN_AVALIACOES:
        elegiveis = [l for l in base if (l.get("userRatingCount") or 0) >= piso]
        if len(elegiveis) >= n:
            elegiveis.sort(key=fama_score, reverse=True)
            return elegiveis[:n], piso
    # nem no piso mais baixo deu a meta - devolve o que tiver (sem inventar)
    base.sort(key=fama_score, reverse=True)
    return base[:n], FAIXAS_MIN_AVALIACOES[-1]


DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
PHOTO_MEDIA_URL = "https://places.googleapis.com/v1/{photo_name}/media"

_detectores = None


def _carregar_detectores():
    global _detectores
    if _detectores is None:
        import cv2
        base = cv2.data.haarcascades
        nomes = ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml", "haarcascade_profileface.xml")
        _detectores = [cv2.CascadeClassifier(base + n) for n in nomes]
    return _detectores


# Regra do projeto: pode aparecer gente na foto, desde que NENHUM rosto seja identificavel.
# Na pratica: rosto detectado com largura >= 5% da largura da foto e considerado identificavel
# (grande/nitido o bastante). Pessoa de costas, de longe ou minuscula passa. Crianca fora
# nunca e decidido aqui - o detector nao sabe; por isso toda foto aprovada passa por
# conferencia visual antes de ir ao ar.
LIMITE_ROSTO_PCT = 0.05


def maior_rosto_pct(dados_da_imagem):
    """Largura do MAIOR rosto detectado, como fracao da largura da foto (0 = nenhum).
    Usa 3 detectores (frente x2 e perfil, nos dois lados) com sensibilidade alta, entao
    superestima: prato/textura podem virar 'rosto' pequeno. Se a imagem nao decodificar,
    devolve 1.0 (assume o pior)."""
    import cv2
    import numpy as np
    img = cv2.imdecode(np.frombuffer(dados_da_imagem, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 1.0
    largura = img.shape[1]
    maior = 0
    for det in _carregar_detectores():
        for versao in (img, cv2.flip(img, 1)):
            for (_, _, w, _) in det.detectMultiScale(versao, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)):
                maior = max(maior, w)
    return maior / largura


def tem_rosto(dados_da_imagem):
    """Qualquer rosto detectado, de qualquer tamanho (criterio antigo, mais rigido)."""
    return maior_rosto_pct(dados_da_imagem) > 0


def rosto_identificavel(dados_da_imagem):
    """True se algum rosto e grande o bastante para identificar a pessoa."""
    return maior_rosto_pct(dados_da_imagem) >= LIMITE_ROSTO_PCT


def listar_fotos_do_lugar(place_id, api_key, maximo=10):
    """Devolve os 'names' das fotos cadastradas pelo Google para esse place_id
    (mais famosas/relevantes primeiro, na ordem que o proprio Google devolve)."""
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": "photos"}
    resp = requests.get(DETAILS_URL.format(place_id=place_id), headers=headers, timeout=20)
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} {resp.reason}: {resp.text}")
    fotos = resp.json().get("photos", [])
    return [f["name"] for f in fotos[:maximo]]


def baixar_bytes_da_foto(photo_name, api_key, largura_max_px=1000):
    params = {"key": api_key, "maxWidthPx": largura_max_px, "skipHttpRedirect": "false"}
    resp = requests.get(PHOTO_MEDIA_URL.format(photo_name=photo_name), params=params, timeout=30)
    resp.raise_for_status()
    return resp.content


def escolher_foto_sem_rosto(place_id, api_key, tentativas=10):
    """Percorre as fotos do lugar (na ordem de relevancia do Google). Prefere a primeira
    sem NENHUM rosto detectado; se nao houver, aceita a primeira cujo maior rosto seja
    pequeno demais para identificar (< LIMITE_ROSTO_PCT) e avisa para conferir visualmente.
    Nunca inventa foto. Devolve (bytes, motivo_se_nao_achou)."""
    nomes = listar_fotos_do_lugar(place_id, api_key, maximo=tentativas)
    if not nomes:
        return None, "Google nao tem foto cadastrada para este lugar"
    aceitavel = None
    for nome_da_foto in nomes:
        dados = baixar_bytes_da_foto(nome_da_foto, api_key)
        pct = maior_rosto_pct(dados)
        if pct == 0:
            return dados, None
        if pct < LIMITE_ROSTO_PCT and aceitavel is None:
            aceitavel = (dados, pct)
    if aceitavel:
        print(f"    aviso: foto escolhida tem rosto pequeno ({aceitavel[1]:.1%} da largura) - conferir visualmente")
        return aceitavel[0], None
    return None, f"todas as {len(nomes)} fotos candidatas tinham rosto identificavel"


def montar_item_comum(lugar):
    preco = PRICE_LEVEL_MAP.get(lugar.get("priceLevel"), "")
    descricao = (lugar.get("editorialSummary") or {}).get("text", "")
    item = {
        "nome": lugar["displayName"]["text"],
        "nota": lugar.get("rating", ""),
        "avaliacoes": lugar.get("userRatingCount", 0),
        "endereco": lugar.get("formattedAddress", ""),
        "descricao": descricao,
        "maps": lugar.get("googleMapsUri", ""),
        "place_id": lugar.get("id", ""),
    }
    if preco:
        item["preco"] = preco
    return item
