#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstroi atracoes.json buscando no Google Places API (New): 10 itens por
modalidade, escolhidos pelo critério de fama (nota * log10(avaliações + 1)).

Modalidades: Natureza, Passeios Clássicos, Cultura, Compras, Aventura,
Mirantes e Supermercados (pedido do usuário, para quem vai cozinhar na casa).

Requer GOOGLE_PLACES_API_KEY no ambiente.

Uso:
    py -3 gerar_atracoes_google.py                  -> dry-run
    py -3 gerar_atracoes_google.py --gravar          -> grava (com backup)
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from _places_utils import CONFIG, buscar_categoria_ampla, excluir_da_categoria, filtrar_por_distancia, montar_item_comum, obter_api_key_validada, selecionar_top_n

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "atracoes.json"

# categoria -> (consulta, tipo Places, tag)
CATEGORIAS = {k: tuple(v[:3]) for k, v in CONFIG["atracoes"].items()}
QUANTIDADE_ESPECIAL = {k: v[3] for k, v in CONFIG["atracoes"].items() if len(v) > 3 and v[3]}
RAIO_ESPECIAL = {k: v[4] for k, v in CONFIG["atracoes"].items() if len(v) > 4 and v[4]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--por-categoria", type=int, default=10)
    args = ap.parse_args()

    api_key = obter_api_key_validada()

    usados = {}
    resultado = []
    linhas_fonte = []
    avisos = []

    for categoria, (query, tipo, tag) in CATEGORIAS.items():
        print(f"\n=== {categoria} ===  \"{query}\"")
        candidatos = buscar_categoria_ampla(query, tipo, api_key, RAIO_ESPECIAL.get(categoria))
        candidatos = excluir_da_categoria(candidatos, categoria)
        if categoria in RAIO_ESPECIAL:
            candidatos = filtrar_por_distancia(candidatos, RAIO_ESPECIAL[categoria])
        print(f"  {len(candidatos)} candidatos {'a ate ' + str(RAIO_ESPECIAL[categoria]) + ' m do imovel' if categoria in RAIO_ESPECIAL else 'brutos'} encontrados")

        # supermercado/compras nao precisam do mesmo piso de fama de um point turistico
        meta = QUANTIDADE_ESPECIAL.get(categoria, args.por_categoria)
        escolhidos, piso = selecionar_top_n(candidatos, meta, usados)
        if piso != 100:
            avisos.append(f"{categoria}: precisei aceitar avaliações >= {piso} para completar.")
        if len(escolhidos) < meta:
            avisos.append(f"{categoria}: só {len(escolhidos)} lugares reais elegíveis (meta {meta}).")

        for lugar in escolhidos:
            item = montar_item_comum(lugar)
            item.pop("preco", None)  # atracoes.json nao usa "preco"
            item["tags"] = [tag]
            item["categoria"] = categoria
            usados[lugar["id"]] = categoria
            resultado.append(item)
            linhas_fonte.append({
                "categoria": categoria, "nome": item["nome"], "nota": item["nota"],
                "avaliacoes": item["avaliacoes"], "endereco": item["endereco"], "maps": item["maps"],
            })
            print(f"  + {item['nome']}  ({item['nota']}★, {item['avaliacoes']} aval.)")

    print("\n=== RESUMO ===")
    for categoria in CATEGORIAS:
        n = sum(1 for i in resultado if i["categoria"] == categoria)
        print(f"  {categoria}: {n}/{QUANTIDADE_ESPECIAL.get(categoria, args.por_categoria)}")
    print(f"  TOTAL: {len(resultado)}")

    if avisos:
        print("\n=== AVISOS ===")
        for a in avisos:
            print(f"  - {a}")

    fonte_csv = ROOT / "atracoes_google_fontes.csv"
    with open(fonte_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["categoria", "nome", "nota", "avaliacoes", "endereco", "maps"])
        w.writeheader()
        w.writerows(linhas_fonte)
    print(f"\nFonte de cada item: {fonte_csv}")

    if not args.gravar:
        print("\n(dry-run - rode com --gravar para substituir atracoes.json)")
        return

    if JSON_PATH.exists():
        backup = ROOT / f"atracoes_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
        backup.write_text(JSON_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backup salvo em: {backup}")

    # preserva as fotos ja baixadas (casando pelo place_id) - regerar a lista nao pode apagar fotos
    if JSON_PATH.exists():
        antigas = {i.get("place_id"): i["foto"] for i in json.loads(JSON_PATH.read_text(encoding="utf-8")) if i.get("foto")}
        mantidas = 0
        for item in resultado:
            foto = antigas.get(item.get("place_id"))
            if foto and (ROOT / foto).exists():
                item["foto"] = foto
                mantidas += 1
        print(f"Fotos ja baixadas preservadas: {mantidas}")

    JSON_PATH.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\natracoes.json gravado com {len(resultado)} itens.")


if __name__ == "__main__":
    main()
