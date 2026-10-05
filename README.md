# Guia Ap da Alê — Santos

Site estático (guia de hóspedes) do **Ap da Alê**, em frente à praia do Gonzaga, Santos/SP: restaurantes,
atrações e informações do apartamento, com dados e fotos reais de cada lugar.

**Passo a passo completo (para leigos): [LEIA-ME.md](LEIA-ME.md)** · Configuração do imóvel: `config_imovel.json`

| Página | Conteúdo |
|---|---|
| `index.html` | Restaurantes (filtro por categoria) |
| `o_que_fazer.html` | Atrações, serviços e passeios de Santos |
| `sobre_a_casa.html` | Anfitriã, apartamento, avaliações dos hóspedes, como chegar, informações úteis |

Rodar localmente: `py -3 -m http.server 8000` e abrir http://localhost:8000
Backup do projeto: `py -3 fazer_backup.py`
