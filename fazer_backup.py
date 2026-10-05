#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um backup (.zip) com TUDO que e preciso para regerar, atualizar ou republicar o site:
paginas, estilos, scripts, listas (json), fotos, imagens do guia usadas nos recortes,
requirements.txt e os leia-mes.

NUNCA entram no backup:
  - 4.png e 8.png (slides com codigo do cofre/alarme e senha do Wi-Fi) e os .zip do guia
  - qualquer arquivo de texto que contenha uma chave de API do Google (padrao AIza...)
  - lixo temporario: __pycache__, _candidatas, backups *.json, planilhas de fonte, .git

Uso:
    py -3 fazer_backup.py

O arquivo sai em backup/backup_casa_terras_altas_AAAAMMDD_HHMM.zip
Para restaurar: descompacte o zip numa pasta nova e siga o LEIA-ME.md (a partir do passo 2).
"""
import hashlib
import re
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DESTINO = ROOT / "backup"

NUNCA = {"4.png", "8.png"}
PASTAS_IGNORADAS = {"__pycache__", "_candidatas", "backup", "publicar", ".git", ".venv", "venv", ".vscode"}
PADROES_IGNORADOS = ("*_backup_*.json", "*_google_fontes.csv", "restaurantes_relatorio.csv", "*.zip", "*.pyc", "resultado_*.txt")
EXTENSOES_TEXTO = {".py", ".json", ".md", ".txt", ".html", ".css", ".js", ".csv", ".code-workspace"}
PADRAO_CHAVE = re.compile(r"AIza[0-9A-Za-z_\-]{30,}")


def deve_ignorar(caminho: Path) -> bool:
    rel = caminho.relative_to(ROOT)
    if caminho.name in NUNCA:
        return True
    if any(parte in PASTAS_IGNORADAS for parte in rel.parts):
        return True
    return any(caminho.match(p) for p in PADROES_IGNORADOS)


def main():
    arquivos, suspeitos = [], []
    for caminho in sorted(ROOT.rglob("*")):
        if not caminho.is_file() or deve_ignorar(caminho):
            continue
        if caminho.suffix.lower() in EXTENSOES_TEXTO:
            try:
                if PADRAO_CHAVE.search(caminho.read_text(encoding="utf-8", errors="ignore")):
                    suspeitos.append(caminho)
                    continue
            except OSError:
                pass
        arquivos.append(caminho)

    if suspeitos:
        print("ATENCAO: estes arquivos parecem conter uma chave de API do Google e FICARAM DE FORA do backup:")
        for s in suspeitos:
            print("  -", s.relative_to(ROOT))
        print("Remova a chave do arquivo e rode o backup de novo.\n")

    DESTINO.mkdir(exist_ok=True)
    nome = f"backup_casa_terras_altas_{datetime.now():%Y%m%d_%H%M}.zip"
    saida = DESTINO / nome

    manifesto = ["Backup do guia Casa Terras Altas", f"Gerado em: {datetime.now():%d/%m/%Y %H:%M}",
                 "Para restaurar, veja LEIA-ME.md (passo 2 em diante).", "", "arquivo | bytes | sha256 (inicio)"]
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        for a in arquivos:
            rel = a.relative_to(ROOT).as_posix()
            z.write(a, rel)
            manifesto.append(f"{rel} | {a.stat().st_size} | {hashlib.sha256(a.read_bytes()).hexdigest()[:12]}")
        z.writestr("MANIFESTO.txt", "\n".join(manifesto) + "\n")

    mb = saida.stat().st_size / 1_048_576
    print(f"Backup criado: {saida}")
    print(f"{len(arquivos)} arquivos, {mb:.1f} MB")


if __name__ == "__main__":
    main()
