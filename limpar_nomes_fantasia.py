#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Troca o "nome" de cada item de restaurantes.json/atracoes.json (hoje o texto completo do
anuncio no Google, cheio de palavra-chave de SEO) pelo nome fantasia - o nome pelo qual o
cliente realmente conhece o lugar.

Duas camadas:
  1. AUTOMATICA: tira o nome da cidade no fim ("... em Santos", "- Santos", "| Santos - SP").
  2. MANUAL: tabela nomes_fantasia.json  {"nome longo do Google": "Nome Curto"}  (voce edita).

Nao inventa nada: o nome curto e sempre um recorte literal do nome que veio do Google.
O nome original fica preservado no campo "nome_google".

Uso:
    py -3 limpar_nomes_fantasia.py                        -> restaurantes.json, dry-run
    py -3 limpar_nomes_fantasia.py --gravar                -> grava
    py -3 limpar_nomes_fantasia.py --arquivo atracoes.json --gravar
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from _places_utils import CONFIG

ROOT = Path(__file__).resolve().parent
TABELA = ROOT / "nomes_fantasia.json"


def limpar_automatico(nome):
    cidade = re.escape(CONFIG["cidade"]["nome"])
    novo = re.sub(rf"\s*(?:[-–|,]|\bem\b)\s*{cidade}(?:\s*[-–,]\s*SP)?\s*$", "", nome, flags=re.I)
    return novo.strip() or nome


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", default="restaurantes.json", help="JSON a limpar (default: restaurantes.json)")
    ap.add_argument("--gravar", action="store_true", help="Faz backup e grava o arquivo")
    args = ap.parse_args()

    manual = json.loads(TABELA.read_text(encoding="utf-8")) if TABELA.exists() else {}
    manual = {k: v for k, v in manual.items() if not k.startswith("_")}

    json_path = ROOT / args.arquivo
    itens = json.loads(json_path.read_text(encoding="utf-8"))

    trocados = 0
    for item in itens:
        atual = item["nome"]
        original = item.get("nome_google", atual)
        novo = manual.get(original) or manual.get(atual) or limpar_automatico(original)
        if novo != atual:
            print(f'  "{atual}"\n   -> "{novo}"\n')
            item.setdefault("nome_google", original)
            item["nome"] = novo
            trocados += 1

    longos = [i["nome"] for i in itens if len(i["nome"]) > 32]
    print(f"Total de nomes simplificados: {trocados} de {len(itens)}")
    if longos:
        print("\nAinda longos (considere adicionar em nomes_fantasia.json):")
        for n in longos:
            print("  -", n)

    if not args.gravar:
        print("\n(dry-run - nada gravado. Rode com --gravar para aplicar.)")
        return

    backup = ROOT / f"{json_path.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    backup.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Backup salvo em: {backup}")
    json_path.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{json_path.name} atualizado.")


if __name__ == "__main__":
    main()
