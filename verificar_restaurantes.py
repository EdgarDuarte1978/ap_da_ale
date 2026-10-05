#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica cada item de restaurantes.json (ou atracoes.json) contra o
Google Places API (New) e gera um relatorio automatico com recomendacao:
    MANTER   -> encontrado, nome bate, aberto
    REVISAR  -> encontrado mas nome/endereco nao batem bem (pode ser outro lugar)
    REMOVER  -> nao encontrado OU fechado permanentemente (provavel dado inventado)

Nao decide nada sozinho por padrao: so LE a API e escreve um relatorio.
Use as flags --aplicar / --remover para de fato alterar o JSON.

Requer uma chave de API do Google Cloud com "Places API (New)" habilitada:
    1. https://console.cloud.google.com/ -> criar projeto (ou usar um existente)
    2. Ativar a API "Places API (New)"
    3. Criar uma API key em "Credenciais"
    4. (opcional, recomendado) restringir a key so para Places API
    A cota gratis mensal do Google cobre folgadamente ~35-100 buscas.

Uso:
    set GOOGLE_PLACES_API_KEY=xxxxxxxx                 (PowerShell: $env:GOOGLE_PLACES_API_KEY="xxxx")
    py -3 verificar_restaurantes.py                    -> so gera o relatorio (CSV + JSON)
    py -3 verificar_restaurantes.py --aplicar           -> alem do relatorio, corrige
                                                            endereco/nota/maps dos itens MANTER
    py -3 verificar_restaurantes.py --aplicar --remover -> tambem apaga do JSON os itens REMOVER
"""
import argparse
import csv
import difflib
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
API_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.googleMapsUri",
    "places.businessStatus",
    "places.id",
])

# abaixo desse grau de parecenca entre o nome do JSON e o nome achado no Google,
# tratamos como "pode ser outro lugar" em vez de confirmar automaticamente
SIMILARIDADE_MINIMA = 0.55

# Campos do Jordao - usado pra enviesar a busca e pra rejeitar resultado em outra cidade
from _places_utils import CONFIG, endereco_na_cidade
CAMPOS_DO_JORDAO_LAT = CONFIG["imovel"]["lat"]
CAMPOS_DO_JORDAO_LNG = CONFIG["imovel"]["lng"]
CAMPOS_DO_JORDAO_RAIO_M = float(CONFIG["cidade"]["raio_busca_m"])

# palavras genericas demais para contar como "nome batendo" (aparecem em varios
# estabelecimentos diferentes e inflam a parecenca sem significar nada)
PALAVRAS_GENERICAS = {
    "restaurante", "restaurant", "pizzaria", "pizza", "cafe", "bar", "choperia",
    "cervejaria", "emporio", "casa", "do", "da", "de", "dos", "das", "e", "a", "o",
    "bistro", "confeitaria", "padaria", "grill", "club", "lanchonete",
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return texto.lower().strip()


def nucleo(texto):
    """Remove palavras genericas, deixando so as palavras que de fato identificam o lugar."""
    palavras = [p for p in normalizar(texto).split() if p not in PALAVRAS_GENERICAS]
    return " ".join(palavras) if palavras else normalizar(texto)


def parecenca(a, b):
    """Maior valor entre: parecenca da string inteira, parecenca so do 'nucleo'
    (sem palavras genericas) e contencao de um nome dentro do outro. Isso evita
    dois erros opostos: marcar como diferente um nome que so tem palavras extras
    (ex. 'Matterhorn' vs 'Matterhorn - Emporio e Restaurante') e marcar como igual
    um nome que so compartilha uma palavra generica (ex. 'Le Bon Cafe' vs 'Bam Bam Cafe')."""
    na, nb = normalizar(a), normalizar(b)
    ratio_completo = difflib.SequenceMatcher(None, na, nb).ratio()

    ca, cb = nucleo(a), nucleo(b)
    ratio_nucleo = difflib.SequenceMatcher(None, ca, cb).ratio() if ca and cb else 0.0

    contido = 1.0 if (ca and ca in cb) or (cb and cb in ca) else 0.0

    return max(ratio_completo, ratio_nucleo, contido)


def buscar_no_google(nome, api_key, cidade=CONFIG["cidade"]["nome"] + ", SP"):
    payload = {
        "textQuery": f"{nome} {cidade}",
        "languageCode": "pt-BR",
        "maxResultCount": 1,
        "locationBias": {
            "circle": {
                "center": {"latitude": CAMPOS_DO_JORDAO_LAT, "longitude": CAMPOS_DO_JORDAO_LNG},
                "radius": CAMPOS_DO_JORDAO_RAIO_M,
            }
        },
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    dados = resp.json()
    lugares = dados.get("places", [])
    return lugares[0] if lugares else None


def fora_de_campos_do_jordao(endereco):
    e = normalizar(endereco)
    return CONFIG["cidade"]["filtro_endereco"] not in e


def avaliar_item(item, api_key):
    nome = item["nome"]
    lugar = buscar_no_google(nome, api_key)

    if lugar is None:
        return {
            "nome_json": nome,
            "encontrado": False,
            "nome_google": "",
            "endereco_google": "",
            "nota_google": "",
            "avaliacoes_google": "",
            "status_google": "",
            "similaridade": 0.0,
            "maps_url": "",
            "place_id": "",
            "recomendacao": "REMOVER",
            "motivo": "Nao encontrado no Google (provavel dado inventado)",
        }

    nome_google = lugar.get("displayName", {}).get("text", "")
    endereco_google = lugar.get("formattedAddress", "")
    status = lugar.get("businessStatus", "")
    sim = round(parecenca(nome, nome_google), 2)

    if status == "CLOSED_PERMANENTLY":
        recomendacao, motivo = "REMOVER", "Encontrado, mas fechado permanentemente"
    elif fora_de_campos_do_jordao(endereco_google):
        recomendacao, motivo = "REMOVER", f"Resultado fica fora da cidade configurada ({endereco_google})"
    elif sim < SIMILARIDADE_MINIMA:
        recomendacao, motivo = "REVISAR", "Nome no Google bate pouco - pode ser outro estabelecimento"
    else:
        recomendacao, motivo = "MANTER", "Encontrado e nome confere"

    return {
        "nome_json": nome,
        "encontrado": True,
        "nome_google": nome_google,
        "endereco_google": endereco_google,
        "nota_google": lugar.get("rating", ""),
        "avaliacoes_google": lugar.get("userRatingCount", ""),
        "status_google": status,
        "similaridade": sim,
        "maps_url": lugar.get("googleMapsUri", ""),
        "place_id": lugar.get("id", ""),
        "recomendacao": recomendacao,
        "motivo": motivo,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", default="restaurantes.json", help="JSON a verificar (default: restaurantes.json)")
    ap.add_argument("--aplicar", action="store_true", help="Atualiza endereco/nota/maps dos itens MANTER no JSON")
    ap.add_argument("--remover", action="store_true", help="Junto com --aplicar, remove do JSON os itens REMOVER")
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("ERRO: defina a variavel de ambiente GOOGLE_PLACES_API_KEY com sua chave do Google Places API.")
        print('PowerShell:  $env:GOOGLE_PLACES_API_KEY = "sua_chave_aqui"')
        sys.exit(1)

    caminho = ROOT / args.arquivo
    itens = json.loads(caminho.read_text(encoding="utf-8"))

    resultados = []
    for i, item in enumerate(itens, 1):
        print(f"[{i}/{len(itens)}] verificando: {item['nome']}")
        try:
            r = avaliar_item(item, api_key)
        except requests.HTTPError as e:
            r = {"nome_json": item["nome"], "encontrado": False, "recomendacao": "ERRO",
                 "motivo": f"Erro na API: {e}", "nome_google": "", "endereco_google": "",
                 "nota_google": "", "avaliacoes_google": "", "status_google": "",
                 "similaridade": 0.0, "maps_url": ""}
        resultados.append(r)
        time.sleep(0.15)  # nao martelar a API

    # --- duplicatas: dois itens do JSON resolvendo pro mesmo lugar no Google ---
    vistos = {}
    for r in resultados:
        pid = r.get("place_id")
        if not pid or r["recomendacao"] == "REMOVER":
            continue
        if pid in vistos:
            r["recomendacao"] = "REMOVER"
            r["motivo"] = f"Duplicata - mesmo local que \"{vistos[pid]}\" no Google"
        else:
            vistos[pid] = r["nome_json"]

    # --- relatorio ---
    relatorio_csv = ROOT / f"{caminho.stem}_relatorio.csv"
    with open(relatorio_csv, "w", newline="", encoding="utf-8-sig") as f:
        campos = ["nome_json", "recomendacao", "motivo", "encontrado", "similaridade",
                  "nome_google", "endereco_google", "nota_google", "avaliacoes_google",
                  "status_google", "maps_url", "place_id"]
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(resultados)

    resumo = {"MANTER": 0, "REVISAR": 0, "REMOVER": 0, "ERRO": 0}
    for r in resultados:
        resumo[r["recomendacao"]] = resumo.get(r["recomendacao"], 0) + 1

    print("\n=== RESUMO ===")
    for k, v in resumo.items():
        print(f"  {k}: {v}")
    print(f"\nRelatorio completo: {relatorio_csv}")

    if not args.aplicar:
        print("\n(rode novamente com --aplicar para corrigir os itens MANTER no JSON)")
        return

    # --- aplicar correcoes ---
    por_nome = {r["nome_json"]: r for r in resultados}
    novos_itens = []
    for item in itens:
        r = por_nome.get(item["nome"])
        if r is None:
            novos_itens.append(item)
            continue

        if r["recomendacao"] == "REMOVER" and args.remover:
            continue  # descarta do JSON

        if r["recomendacao"] == "MANTER":
            if r["endereco_google"]:
                item["endereco"] = r["endereco_google"]
            if r["nota_google"] != "":
                item["nota"] = r["nota_google"]
            if r["maps_url"]:
                item["maps"] = r["maps_url"]

        novos_itens.append(item)

    caminho.write_text(json.dumps(novos_itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{caminho.name} atualizado: {len(novos_itens)} itens "
          f"({len(itens) - len(novos_itens)} removidos)." if args.remover
          else f"\n{caminho.name} atualizado (enderecos/notas corrigidos para os itens MANTER).")


if __name__ == "__main__":
    main()
