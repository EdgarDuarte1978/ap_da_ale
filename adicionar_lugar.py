#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona UM lugar real (buscado no Google Places) a restaurantes.json, sem mexer nos
existentes. Nome, endereco, nota, avaliacoes, preco e link do Maps vem da API; a foto
e a primeira candidata sem rosto detectado.

Uso:
    py -3 adicionar_lugar.py "Fauno cervejaria" --categoria Cervejaria --tag cervejaria
        -> lista os resultados encontrados (nada e gravado)
    py -3 adicionar_lugar.py "Fauno cervejaria" --categoria Cervejaria --tag cervejaria --escolher 1 --gravar
        -> adiciona o resultado numero 1
"""
import argparse
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from _places_utils import (buscar_texto, endereco_na_cidade, escolher_foto_sem_rosto,
                           montar_item_comum, obter_api_key_validada)

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "restaurantes.json"
PASTA_FOTOS = ROOT / "restaurantes_fotos"


def slugificar(nome):
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower() or "sem-nome"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("consulta")
    ap.add_argument("--categoria", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--escolher", type=int, help="numero do resultado a adicionar")
    ap.add_argument("--gravar", action="store_true")
    args = ap.parse_args()

    api_key = obter_api_key_validada()
    achados = [l for l in buscar_texto(args.consulta, api_key) if endereco_na_cidade(l)][:6]
    if not achados:
        print("Nada encontrado na cidade configurada para essa busca.")
        return

    for i, l in enumerate(achados, 1):
        print(f"{i}. {l['displayName']['text']} | {l.get('rating', '-')} estrelas, "
              f"{l.get('userRatingCount', 0)} aval. | {l.get('formattedAddress', '')} | {l.get('businessStatus', '')}")

    if not args.escolher:
        print("\nRode de novo com --escolher N --gravar para adicionar.")
        return

    lugar = achados[args.escolher - 1]
    itens = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if any(it.get("place_id") == lugar["id"] for it in itens):
        print("Esse lugar ja esta na lista.")
        return

    item = montar_item_comum(lugar)
    item["tags"] = [args.tag]
    item["categoria"] = args.categoria
    item["subcategoria"] = args.categoria

    dados, motivo = escolher_foto_sem_rosto(lugar["id"], api_key)
    if dados:
        PASTA_FOTOS.mkdir(exist_ok=True)
        slug = slugificar(item["nome"])
        (PASTA_FOTOS / f"{slug}.jpg").write_bytes(dados)
        item["foto"] = f"restaurantes_fotos/{slug}.jpg"
    else:
        print(f"Sem foto automatica: {motivo}")

    print("\nItem:", json.dumps(item, ensure_ascii=False, indent=1))
    if not args.gravar:
        print("\n(dry-run - falta --gravar)")
        return

    backup = ROOT / f"restaurantes_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    backup.write_text(JSON_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    itens.append(item)
    JSON_PATH.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nAdicionado. restaurantes.json agora tem {len(itens)} itens. Backup: {backup.name}")


if __name__ == "__main__":
    main()
