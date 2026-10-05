#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa 1 foto real (do proprio Google Places) para cada restaurante de restaurantes.json
e grava o caminho no campo "foto" de cada item.

Nao inventa nada: a foto vem do "Place Details" do Google para o place_id
ja salvo em cada item (o mesmo place_id usado pra gerar nome/endereco/nota).
Itens sem place_id ficam sem foto e sao avisados no final.

Seguranca: nunca usa foto com rosto de pessoa reconhecivel. Para cada lugar, olha
varias fotos candidatas (na ordem de relevancia do Google) e usa a PRIMEIRA sem
rosto detectado. Se todas as candidatas tiverem gente, o item fica sem foto.

Uso:
    py -3 baixar_fotos_restaurantes.py                 -> dry-run (mostra o que faria)
    py -3 baixar_fotos_restaurantes.py --gravar         -> baixa as fotos e grava restaurantes.json
    py -3 baixar_fotos_restaurantes.py --revisar --gravar
                                                        -> reexamina as fotos JA baixadas
                                                           e troca qualquer uma com rosto
"""
import argparse
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

from _places_utils import obter_api_key_validada, escolher_foto_sem_rosto, rosto_identificavel

ROOT = Path(__file__).resolve().parent
PASTA_FOTOS = ROOT / "restaurantes_fotos"


def slugificar(nome):
    texto = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto or "sem-nome"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help="Baixa as fotos de verdade e grava restaurantes.json")
    ap.add_argument("--revisar", action="store_true",
                     help="Tambem reexamina as fotos ja baixadas antes, trocando as que tiverem rosto")
    args = ap.parse_args()

    api_key = obter_api_key_validada()
    itens = json.loads((ROOT / "restaurantes.json").read_text(encoding="utf-8"))

    sem_place_id = [it["nome"] for it in itens if not it.get("place_id")]
    ja_tem_foto = sum(1 for it in itens if it.get("foto"))

    print(f"Total de restaurantes: {len(itens)}")
    print(f"Ja tem foto: {ja_tem_foto}")
    print(f"Sem place_id (nao da pra buscar foto): {len(sem_place_id)}")
    for n in sem_place_id:
        print(f"  - {n}")
    print()

    if not args.gravar:
        print("(dry-run - nada baixado/gravado. Rode com --gravar para aplicar.)")
        return

    PASTA_FOTOS.mkdir(exist_ok=True)
    baixadas = 0
    trocadas = 0
    falhas = []

    for it in itens:
        if not it.get("place_id"):
            continue

        se_ja_tem_e_nao_e_revisao = it.get("foto") and not args.revisar
        if se_ja_tem_e_nao_e_revisao:
            continue

        nome = it["nome"]
        slug = slugificar(nome)
        destino = PASTA_FOTOS / f"{slug}.jpg"

        try:
            if it.get("foto") and args.revisar:
                if destino.exists() and not rosto_identificavel(destino.read_bytes()):
                    continue
                print(f"  REVISAR  {nome}: foto atual tem rosto (ou sumiu) - buscando outra...")

            dados, motivo = escolher_foto_sem_rosto(it["place_id"], api_key)
            if dados is None:
                if it.get("foto"):  # a foto antiga tem rosto: melhor sem foto do que com ela
                    destino.unlink(missing_ok=True)
                    del it["foto"]
                    motivo += " (foto removida)"
                falhas.append((nome, motivo))
                continue
            destino.write_bytes(dados)
            era_nova = not it.get("foto")
            it["foto"] = f"restaurantes_fotos/{slug}.jpg"
            if era_nova:
                baixadas += 1
                print(f"  OK  {nome} -> {destino.name}")
            else:
                trocadas += 1
                print(f"  TROCADA  {nome} -> {destino.name}")
        except requests.HTTPError as e:
            falhas.append((nome, str(e)))
        except Exception as e:
            falhas.append((nome, str(e)))
        time.sleep(0.15)

    print(f"\nFotos novas: {baixadas} | Fotos trocadas (tinham rosto): {trocadas}")
    if falhas:
        print(f"Sem foto segura disponivel ({len(falhas)}):")
        for nome, erro in falhas:
            print(f"  - {nome}: {erro}")

    backup = ROOT / f"restaurantes_backup_fotos_{datetime.now():%Y%m%d_%H%M%S}.json"
    backup.write_text((ROOT / "restaurantes.json").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Backup salvo em: {backup}")

    (ROOT / "restaurantes.json").write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("restaurantes.json atualizado.")


if __name__ == "__main__":
    main()
