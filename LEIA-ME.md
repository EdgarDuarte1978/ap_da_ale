# Guia de hóspedes da Casa Terras Altas — do zero até o site no ar

Este guia explica, para quem **nunca programou**, como criar uma página igual a esta: um site de
hóspedes com **restaurantes**, **atrações** e **informações da casa**, com dados reais do Google e
fotos de cada lugar, publicado de graça na internet.

Tempo estimado na primeira vez: 2 a 4 horas (a maior parte é conferir as fotos e personalizar os textos).

> **Resultado final:** um endereço como `https://SEU-USUARIO.github.io/NOME-DO-SITE/`
> para mandar aos hóspedes. Exemplo real: https://edgarduarte1978.github.io/casa-terras-altas/

---

## Índice

1. [Como o projeto funciona (visão geral)](#1-como-o-projeto-funciona)
2. [O que você precisa ter](#2-o-que-você-precisa-ter)
3. [Instalar os programas](#3-instalar-os-programas)
4. [Pegar o projeto e personalizar para a sua casa](#4-pegar-o-projeto-e-personalizar-para-a-sua-casa)
5. [Criar a chave do Google (Places API)](#5-criar-a-chave-do-google-places-api)
6. [Gerar as listas de restaurantes e atrações](#6-gerar-as-listas-de-restaurantes-e-atrações)
7. [Baixar as fotos (regra: sem rostos identificáveis)](#7-baixar-as-fotos)
8. [Ver o site no seu computador](#8-ver-o-site-no-seu-computador)
9. [Publicar na internet (GitHub Pages)](#9-publicar-na-internet-github-pages)
10. [Atualizar o site depois](#10-atualizar-o-site-depois)
11. [Backup e restauração](#11-backup-e-restauração)
12. [Segurança (leia antes de publicar!)](#12-segurança)
13. [Problemas comuns](#13-problemas-comuns)
14. [Mapa de arquivos](#14-mapa-de-arquivos)

---

## 1. Como o projeto funciona

O site é **estático**: são só arquivos (páginas, listas e fotos). Não há servidor nem banco de dados.

```
Google Places  ──►  scripts Python  ──►  listas (restaurantes.json / atracoes.json) + fotos
                                                     │
                       páginas HTML + CSS + JS  ◄────┘      ──►  GitHub Pages  ──►  hóspedes
```

- **Páginas:** `index.html` (restaurantes), `o_que_fazer.html` (atrações), `sobre_a_casa.html` (casa).
- **Listas:** `restaurantes.json` e `atracoes.json` — cada item tem nome, nota, endereço, link do Google Maps, foto.
- **Scripts (Python):** buscam os lugares no Google, escolhem os mais famosos e baixam uma foto de cada.
- **Seleção "de fama":** nota × log10(nº de avaliações). Favorece lugares conhecidos e bem avaliados
  (não um 5,0 com 3 avaliações). Nada é inventado: tudo vem do Google.

Você vai usar principalmente o **Prompt de Comando** do Windows (a tela preta onde se digitam comandos).

---

## 2. O que você precisa ter

| Item | Para quê | Custo |
|---|---|---|
| Computador com Windows | Rodar os scripts | — |
| Conta Google | Criar a chave de acesso aos dados de lugares | Grátis (a API exige cartão no Google Cloud; veja a tabela de preços atual do Google — uma execução completa faz algumas centenas de consultas) |
| Conta no GitHub (github.com) | Hospedar o site | Grátis |
| Python 3 | Rodar os scripts | Grátis |
| Git | Enviar o site ao GitHub | Grátis |
| Fotos da sua casa (opcional, recomendado) | Página "Sobre a Casa" e topo do site | — |

---

## 3. Instalar os programas

### 3.1 Python
1. Acesse **python.org/downloads** e baixe o instalador para Windows.
2. No instalador, **marque "Add python.exe to PATH"** e clique em *Install Now*.
3. Teste: abra o **Prompt de Comando** (menu Iniciar → digite `cmd` → Enter) e rode:
   ```
   py -3 --version
   ```
   Deve aparecer algo como `Python 3.x.x`.

### 3.2 Git
1. Acesse **git-scm.com/download/win**, baixe e instale (pode aceitar todas as opções padrão).
2. Teste no Prompt de Comando: `git --version`

### 3.3 Bibliotecas do projeto
Dentro da pasta do projeto (veja o passo 4), rode:
```
py -3 -m pip install -r requirements.txt
```
> O `requirements.txt` fixa a versão `4.10.0.84` do OpenCV (detector de rosto). **Não troque por
> versão 5.x**: a 5.0.0 testada para Python 3.14 veio sem o detector e o script quebra.

---

## 4. Pegar o projeto e personalizar para a sua casa

### 4.1 Obter os arquivos
- **Se você tem o backup (.zip):** descompacte numa pasta, por exemplo `C:\Users\SEU-NOME\meu-site`.
- **Ou pelo GitHub:** `git clone https://github.com/edgarduarte1978/casa-terras-altas.git`

Abra o Prompt de Comando **dentro da pasta** (dica: na pasta, clique na barra de endereço, digite `cmd` e Enter).

### 4.2 O que trocar para o SEU imóvel
**Tudo o que é específico da cidade e do imóvel fica em UM arquivo: `config_imovel.json`.** Abra com o Bloco de Notas e preencha:

| Bloco do arquivo | O que colocar |
|---|---|
| `imovel` | Nome, anfitrião(ã), endereço público (**sem número do apartamento**), endereço de origem do botão "Como Chegar", `lat`/`lng` (veja abaixo), links do Airbnb/Instagram/Google, telefone |
| `cidade` | `nome`, `filtro_endereco` (texto que aparece no endereço do Google, ex.: `", santos - sp"`) e `raio_busca_m` |
| `excluir_nomes` | Lugares que você **não** quer ver nas listas (ex.: `"Mercado Municipal"`) |
| `restaurantes` / `atracoes` | Categorias de cada lista: `[consulta no Google, tipo, tag do filtro, quantidade opcional]`. Escolha categorias que façam sentido na sua região (praia, serra, campo…) |

Depois ajuste **à mão** (são textos, não dá para automatizar):
- `index.html`, `o_que_fazer.html`, `sobre_a_casa.html`: nome, links, textos, botões de filtro (a `tag` do botão = a `tag` do config), informações úteis (bombeiros, hospital, posto) e avaliações reais do anúncio.
- `script.js` e `script_atracoes.js`: a linha `ORIGEM_CASA = "..."` (endereço de origem do "Como Chegar") e o nome da cidade no destino.
- Fotos: `hero_*.jpg` (topo) e a pasta `avaliacoes/` (fotos do anúncio, **sem rostos de terceiros**).

> **Coordenadas:** no Google Maps, abra o imóvel/local e copie os dois números depois do `@` na barra de endereço (`@-23.96,-46.33`). Raio de 8 000–15 000 m costuma servir.

---|---|
| `index.html`, `o_que_fazer.html`, `sobre_a_casa.html` | Nome da casa (`Casa Terras Altas`), cidade, links do Airbnb/Instagram/Google, telefones, e-mail, textos |
| `sobre_a_casa.html` | Anfitriões, endereço de "Como Chegar", telefones de emergência/hospital/posto da sua cidade, lembretes da casa |
| `script.js` e `script_atracoes.js` | Linha `ORIGEM_CASA = "..."` → **endereço da sua casa** (usado no botão "Como Chegar") |
| `_places_utils.py` | `CAMPOS_DO_JORDAO_LAT`, `_LNG`, `_RAIO_M` → coordenadas e raio da **sua cidade**; e a função `endereco_em_campos_do_jordao` (o texto `"campos do jordao"` vira o nome da sua cidade) |
| `gerar_restaurantes_google.py` / `gerar_atracoes_google.py` | Nas listas `CATEGORIAS`, troque `Campos do Jordão` pela sua cidade e ajuste as categorias que quiser |
| `hero_casa_terras_altas.png` | Foto grande do topo (troque pelo arquivo da sua casa, **mantendo o nome** ou ajustando nas 3 páginas) |
| `avaliacoes/` | Fotos da seção "O que dizem os hóspedes" — use **suas** fotos e **avaliações reais** do seu anúncio |

> **Coordenadas da cidade:** no Google Maps, clique com o botão direito no centro da cidade — as
> coordenadas aparecem no topo do menu. Raio de 10 000–15 000 m costuma servir.

---

## 5. Criar a chave do Google (Places API)

A chave é uma "senha" que permite aos scripts consultar o Google. **Trate como senha.**

1. Acesse **console.cloud.google.com** e entre com sua conta Google.
2. Crie um **projeto** (botão no topo → *Novo projeto*).
3. Ative o **faturamento** (cartão) no projeto — o Google exige, mesmo dentro da cota gratuita.
4. Em *APIs e serviços* → *Biblioteca*, procure **"Places API (New)"** e clique em **Ativar**.
5. Em *APIs e serviços* → *Chaves e credenciais* → **Criar credenciais → Chave de API**.
6. **Restrinja a chave** a "Places API (New)" (em *Restrições de API*). Assim, se vazar, só serve para isso.
7. Copie a chave (começa com `AIzaSy...`, 39 caracteres).

### Como usar a chave nos scripts (importante!)
Use **um Prompt de Comando avulso** (menu Iniciar → `cmd`). **Não** use o terminal embutido de editores/IA,
que pode esconder a chave e quebrar o comando.

```
cd "C:\caminho\da\sua\pasta"
set GOOGLE_PLACES_API_KEY=cole_a_sua_chave_aqui
```

- Troque `cole_a_sua_chave_aqui` pela chave **de verdade**, sem aspas, sem espaço.
- A chave vale só **enquanto aquela janela estiver aberta**. Se fechar, defina de novo.
- **Nunca** cole a chave em e-mail, chat, print ou arquivo do projeto. Se vazar: apague e gere outra no Console.

---

## 6. Gerar as listas de restaurantes e atrações

Todos os comandos abaixo rodam no Prompt de Comando, na pasta do projeto, com a chave já definida (passo 5).
Cada script, **sem `--gravar`**, apenas **mostra** o que faria (modo de teste). Com `--gravar`, grava (e faz backup do arquivo anterior).

### 6.1 Restaurantes (5 categorias × 10)
```
py -3 gerar_restaurantes_google.py
py -3 gerar_restaurantes_google.py --gravar
```
Gera `restaurantes.json`. Se uma categoria não tiver 10 lugares famosos de verdade, o script **avisa** em vez de inventar.

### 6.2 Atrações (7 modalidades × 10)
```
py -3 gerar_atracoes_google.py
py -3 gerar_atracoes_google.py --gravar
```
Modalidades: Natureza, Passeios Clássicos, Cultura, Compras, Aventura, Mirantes e Supermercados.

### 6.3 Nomes "limpos" (nome fantasia)
O Google devolve nomes cheios de palavras-chave, tipo *"Restaurante Cacerola | Carnes Nobres | Campos do Jordão"*.
O script `limpar_nomes_fantasia.py` troca por *"Cacerola"* usando uma **tabela escrita à mão** dentro do arquivo
(arquivo `nomes_fantasia.json`). O nome da cidade no fim do nome ("... em Santos") é removido automaticamente. Para os demais:
1. Rode `py -3 limpar_nomes_fantasia.py` (teste) e veja quais nomes ficaram grandes.
2. Abra `nomes_fantasia.json` e adicione linhas no formato `"nome longo do Google": "Nome Curto",`.
3. Rode `py -3 limpar_nomes_fantasia.py --gravar` (restaurantes) e
   `py -3 limpar_nomes_fantasia.py --arquivo atracoes.json --gravar` (atrações).

O nome original é guardado no campo `nome_google`, então nada se perde.

### 6.4 Conferir se tudo existe (opcional)
```
py -3 verificar_restaurantes.py
```
Gera um relatório (MANTER / REVISAR / REMOVER) comparando cada item com o Google. Só altera o arquivo se você usar `--aplicar`.

### 6.5 Adicionar um lugar que ficou de fora (sem tirar os outros)
```
py -3 adicionar_lugar.py "Nome do lugar Cidade" --categoria Cervejaria --tag cervejaria
```
Mostra os resultados numerados. Escolha o certo:
```
py -3 adicionar_lugar.py "Nome do lugar Cidade" --categoria Cervejaria --tag cervejaria --escolher 1 --gravar
```
(`--tag` deve ser a mesma usada nos botões de filtro da página, ex.: `fondue`, `pizza`, `carnes`, `cervejaria`, `cafés`.)

> Para atrações, o `adicionar_lugar.py` grava em `restaurantes.json`. Para uma atração avulsa, adicione o item
> manualmente em `atracoes.json` copiando o formato de um item existente.

---

## 7. Baixar as fotos

### 7.1 Regra de ouro: sem rostos identificáveis
Foto de lugar público pode ter gente, **mas nenhum rosto pode ser reconhecível** (privacidade). Os scripts aplicam:

- Detector de rosto automático: aceita a foto se **nenhum rosto** for detectado; se só houver rostos
  **pequenos (menos de 5% da largura da foto)**, aceita com aviso "conferir visualmente".
- Rosto grande ou nítido → foto descartada, tenta a próxima (até **10 candidatas** por lugar — limite da API do Google).
- **Criança, close, funcionário/cliente em destaque: sempre fora**, mesmo que o detector deixe passar.
- Sem foto segura → o item fica **sem foto** (o site funciona normalmente, só sem imagem).

### 7.2 Comandos
```
py -3 baixar_fotos_restaurantes.py --gravar
py -3 baixar_fotos_atracoes.py --gravar
```
Salvam em `restaurantes_fotos/` e `atracoes_fotos/` e preenchem o campo `"foto"` de cada item.
Rodar de novo só tenta os itens **sem foto**. Para reexaminar também as já baixadas: acrescente `--revisar`.

### 7.3 Conferência visual (não pule!)
O detector erra nos dois sentidos (acha rosto em prato de comida e deixa passar gente de longe).
Abra as pastas de fotos no Windows (modo "ícones grandes") e olhe **uma por uma**. Se uma tiver rosto
identificável, **apague o arquivo** e remova a linha `"foto": "..."` desse item no `.json` (ou rode o passo 7.4).

### 7.4 Itens que ficaram sem foto
Opção A — ver todas as candidatas do Google:
```
py -3 baixar_candidatas_sem_foto.py
```
Salva as fotos em `_candidatas/` e mostra o tamanho do maior rosto de cada uma. Escolha uma sem gente.

Opção B — **à mão, pelo Google Maps** (a API só entrega 10 fotos; o Maps mostra mais):
1. Abra o lugar no Google Maps → **Fotos** → escolha uma foto sem pessoas.
2. Clique com o botão direito na foto → *Salvar imagem como…*
3. Salve com o nome do arquivo esperado: `restaurantes_fotos/nome-do-lugar.jpg` (ou `atracoes_fotos/...`).
   Nome = minúsculo, sem acento, espaços viram hífen (ex.: *Café Terraço* → `cafe-terraco.jpg`).
4. No `.json`, no item do lugar, acrescente `"foto": "restaurantes_fotos/cafe-terraco.jpg"`.

> Fotos tiradas pelo Google/Maps pertencem a terceiros. Para um guia de hóspedes é uso comum, mas se quiser
> evitar qualquer questão, substitua por fotos suas (mesmo nome de arquivo).

### 7.5 Peso das fotos
Fotos muito grandes deixam o site lento no celular. Se algum arquivo passar de ~1 MB, reduza-o
(ex.: abra no Paint → Redimensionar → largura 1200 px → salvar como JPG).

---

## 8. Ver o site no seu computador

As páginas carregam as listas por `fetch()`, então **não abra o .html com duplo clique** (a tela fica vazia). Rode:
```
py -3 -m http.server 8000
```
e abra no navegador: **http://localhost:8000**. Para parar: `Ctrl + C` na janela preta.

Confira nas **3 páginas** (e no celular, se possível):
- cards com foto; botões de filtro funcionando;
- "Como Chegar" abrindo o Maps a partir da sua casa;
- textos, telefones e links corretos;
- **nenhuma senha/código de acesso** em lugar nenhum (veja o passo 12).

---

## 9. Publicar na internet (GitHub Pages)

### 9.1 Criar o repositório (uma vez só)
1. Entre em **github.com** → botão **New** (novo repositório).
2. Nome: algo simples, sem espaço/acento (ex.: `casa-minha-casa`). Deixe **Public**. Não marque README. Clique **Create**.

### 9.2 Enviar os arquivos (primeira vez)
No Prompt de Comando, dentro da pasta do projeto:
```
git init
git branch -M main
git add .
git commit -m "Primeira versao do site"
git remote add origin https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
git push -u origin main
```
- Na primeira vez o Git abre o **navegador para você fazer login** no GitHub — autorize.
- Antes do `git add .`, **confira o `.gitignore`**: ele impede o envio de arquivos sensíveis (veja o passo 12).
- Se aparecer erro "rejected / fetch first", o repositório já tinha arquivos: rode `git pull origin main --allow-unrelated-histories`
  e tente o push de novo.

### 9.3 Ligar o site
1. No repositório: **Settings → Pages**.
2. Em *Source*: **Deploy from a branch**; Branch: **main**; pasta: **/ (root)**; **Save**.
3. Espere 1–2 minutos. O endereço aparece no topo da mesma tela:
   `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/`

### 9.4 Conferir
Abra o endereço (use `Ctrl + F5` para ignorar cache) e teste as 3 páginas.

---

## 10. Atualizar o site depois

Qualquer mudança (texto, lista, foto) segue o mesmo ciclo:

1. Edite / rode o script.
2. Teste local (passo 8).
3. Envie:
   ```
   git add .
   git commit -m "Descreva a mudanca em poucas palavras"
   git push origin main
   ```
4. Espere 1–2 minutos e confira o endereço público.

Exemplos:
- **Trocar nota/lista de um restaurante:** `py -3 gerar_restaurantes_google.py --gravar` e refaça os passos 6.3 e 7 (isso **substitui** a lista; faça backup antes).
- **Incluir um restaurante:** passo 6.5.
- **Mudar telefone/horário:** edite o `.html` direto.

---

## 11. Backup e restauração

### Fazer o backup
```
py -3 fazer_backup.py
```
Cria `backup/backup_casa_terras_altas_AAAAMMDD_HHMM.zip` com **tudo** que é necessário (páginas, estilos, scripts, listas,
fotos, imagens do guia, leia-me, requirements) e um `MANIFESTO.txt`. **Ficam de fora**, de propósito: as imagens
com senhas (`4.png`, `8.png`), qualquer arquivo com chave de API e arquivos temporários. A pasta `backup/` não vai para o GitHub.

> Guarde uma cópia do .zip **fora do computador** (nuvem, pen drive).

### Restaurar
1. Descompacte o `.zip` numa pasta nova.
2. Siga este guia a partir do **passo 3.3** (instalar bibliotecas) e, para publicar, o **passo 9**.
3. A chave do Google **não** está no backup — gere/defina de novo (passo 5).

---

## 12. Segurança

Este site é **público**. Quem tiver o link vê tudo o que estiver nos arquivos.

- ❌ **Nunca publique:** senha do Wi-Fi, código do cofre de chaves, código do alarme, endereço de câmeras, documentos.
  → Envie por mensagem ao hóspede **perto do check-in**. Neste projeto, `4.png` e `8.png` (slides com essas senhas)
  estão no `.gitignore` e **nunca** devem ser enviados. Se você tiver arquivos parecidos, **adicione-os ao `.gitignore`**
  (uma linha por arquivo) **antes** do `git add .`.
- ❌ **Nunca coloque a chave do Google** em arquivo do projeto, e-mail, chat ou print. Use só o `set` do passo 5.
  Se vazou: Console do Google → Chaves e credenciais → excluir e criar outra.
- ❌ **Rostos identificáveis:** veja o passo 7. Fotos dos anfitriões, só com a autorização deles.
- ⚠️ **Se um arquivo sensível já foi enviado ao GitHub**, apagá-lo depois **não basta** (o histórico guarda). Troque a senha/código
  e refaça o repositório sem esse arquivo.
- ✅ Antes de publicar: abra o site e use `Ctrl + F` procurando por "senha", "código", "wifi".

---

## 13. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ERRO: defina GOOGLE_PLACES_API_KEY` | A chave não está definida **nesta janela** | Rode o `set GOOGLE_PLACES_API_KEY=...` (passo 5) na mesma janela |
| `API key not valid` (400) | Chave com texto errado (ex.: ficou `sua_chave_aqui`), com traço "esperto" (–) ou bolinhas (•) | Digite a chave de novo, no `cmd` avulso; confira o tamanho (39 caracteres) |
| `UnicodeEncodeError` | Caractere especial colado junto da chave | Mesmo conserto acima |
| `py` não é reconhecido | Python sem "Add to PATH" | Reinstale o Python marcando a opção |
| `can't open file '...py'` | Está na pasta errada | `cd` para a pasta do projeto antes |
| Página abre vazia | Abriu o `.html` com duplo clique | Use `py -3 -m http.server 8000` (passo 8) |
| Letras estranhas (`Jord�o`) no terminal | O terminal do Windows exibe acentos errado | É só na tela; o arquivo está correto |
| `module 'cv2' has no attribute 'CascadeClassifier'` | OpenCV 5.x instalado | `py -3 -m pip install opencv-python-headless==4.10.0.84` |
| `git push` rejeitado (fetch first) | O GitHub tem arquivos que você não tem | `git pull origin main --allow-unrelated-histories` e push de novo |
| Foto aparece quebrada no site | Arquivo não foi enviado ou nome diferente | Confira o nome/pasta no `.json` e rode `git add .`, `commit`, `push` |
| Site não mudou depois do push | Cache do navegador / deploy em andamento | Espere 2 min e `Ctrl + F5` |
| Lista com menos de 10 itens | Poucos lugares "famosos" na cidade | Normal: o script não inventa; aceite ou use `adicionar_lugar.py` |

---

## 14. Mapa de arquivos

| Arquivo / pasta | O que é |
|---|---|
| `index.html`, `o_que_fazer.html`, `sobre_a_casa.html` | As 3 páginas |
| `style.css` | Visual (cores, cartões, celular) |
| `script.js` / `script_atracoes.js` | Desenham os cartões e os filtros |
| `restaurantes.json` / `atracoes.json` | As listas (dados + caminho da foto) |
| `restaurantes_fotos/`, `atracoes_fotos/` | Uma foto por lugar |
| `avaliacoes/` | Fotos da seção "O que dizem os hóspedes" e dos anfitriões (manuais) |
| `hero_casa_terras_altas.png`, `airbnb-icon.png` | Imagem do topo e ícone do Airbnb |
| `1.png`…`9.png` | Slides do guia antigo (fonte dos recortes de `avaliacoes/`; **`4.png` e `8.png` nunca no GitHub**) |
| `_places_utils.py` | Funções compartilhadas (busca no Google, fama, detector de rosto) |
| `gerar_restaurantes_google.py`, `gerar_atracoes_google.py` | Criam as listas |
| `limpar_nomes_fantasia.py` | Encurta nomes (tabela manual) |
| `verificar_restaurantes.py` | Relatório de conferência com o Google |
| `adicionar_lugar.py` | Adiciona um lugar sem mexer nos outros |
| `baixar_fotos_restaurantes.py`, `baixar_fotos_atracoes.py` | Baixam as fotos (com regra de rosto) |
| `baixar_candidatas_sem_foto.py` | Mostra todas as candidatas dos itens sem foto |
| `fazer_backup.py` | Gera o .zip de backup |
| `requirements.txt` | Bibliotecas Python necessárias |
| `.gitignore` | Lista do que **não** vai para o GitHub (senhas, temporários) |
| `legado/` | Scripts da 1ª versão (dados não verificados). **Não use**: sobrescrevem as listas reais |
| `backup/` | Backups gerados (não vai para o GitHub) |

---

### Resumo em 12 linhas
```
1. Instale Python e Git                      (passo 3)
2. py -3 -m pip install -r requirements.txt
3. Troque textos, endereço, cidade e fotos  (passo 4)
4. Crie a chave do Google; no cmd: set GOOGLE_PLACES_API_KEY=...   (passo 5)
5. py -3 gerar_restaurantes_google.py --gravar
6. py -3 gerar_atracoes_google.py --gravar
7. Ajuste nomes: limpar_nomes_fantasia.py --gravar                  (passo 6.3)
8. py -3 baixar_fotos_restaurantes.py --gravar ; py -3 baixar_fotos_atracoes.py --gravar
9. Confira as fotos uma a uma (sem rostos)   (passo 7.3)
10. py -3 -m http.server 8000  → http://localhost:8000              (passo 8)
11. git init / add / commit / push; ligar o Pages                   (passo 9)
12. py -3 fazer_backup.py                                           (passo 11)
```
