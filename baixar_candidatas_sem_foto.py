#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Para cada item de restaurantes.json / atracoes.json que ficou SEM foto (e tem place_id),
baixa TODAS as fotos candidatas do Google para a pasta _candidatas/ e mostra, por foto,
se o detector de rosto marcou (e por isso foi descartada). Serve para escolher a foto
na mao (olhando) quando o detector automatico foi conservador demais.

Uso:
    py -3 baixar_candidatas_sem_foto.py
"""
import json
import re
import time
import unicodedata
from pathlib import Path

from _places_utils import baixar_bytes_da_foto, listar_fotos_do_lugar, maior_rosto_pct, obter_api_key_validada

ROOT = Path(__file__).resolve().parent
SAIDA = ROOT / "_candidatas"


def slugificar(nome):
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower() or "sem-nome"


def main():
    api_key = obter_api_key_validada()
    for arquivo, prefixo in (("restaurantes.json", "restaurantes"), ("atracoes.json", "atracoes")):
        itens = json.loads((ROOT / arquivo).read_text(encoding="utf-8"))
        for it in itens:
            if it.get("foto"):
                continue
            if not it.get("place_id"):
                print(f"[{prefixo}] {it['nome']}: sem place_id - sem como buscar (baixar manualmente)")
                continue
            slug = slugificar(it["nome"])
            pasta = SAIDA / f"{prefixo}__{slug}"
            pasta.mkdir(parents=True, exist_ok=True)
            nomes = listar_fotos_do_lugar(it["place_id"], api_key, maximo=10)
            print(f"[{prefixo}] {it['nome']}: {len(nomes)} fotos candidatas")
            for i, nome_foto in enumerate(nomes, 1):
                dados = baixar_bytes_da_foto(nome_foto, api_key)
                (pasta / f"{i:02d}.jpg").write_bytes(dados)
                print(f"    {i:02d}.jpg  maior rosto: {maior_rosto_pct(dados):.1%} da largura")
                time.sleep(0.1)
    print(f"\nPronto. Fotos em: {SAIDA}")


if __name__ == "__main__":
    main()
