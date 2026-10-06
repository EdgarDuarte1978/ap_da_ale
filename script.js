// =====================================================
// Guia Gastronômico Casa Terras Altas — script.js (v2)
// Correções:
//  - remove dependência de #searchInput / .categories (erro no console)
//  - destaque do filtro ativo agora funciona
//  - "Como Chegar" parte de um endereço válido da casa
//  - template do card usa classes explícitas (.card-meta / .card-desc)
// =====================================================

const ORIGEM_CASA = "Av. Presidente Wilson, 26 - José Menino, Santos, SP"; // endereço confirmado no Google Business da casa

let restaurantes = [];
let restaurantesFiltrados = [];

// ------------------------------------------------------
// CARREGAR JSON
// ------------------------------------------------------
async function carregarRestaurantes() {
    try {
        const resposta = await fetch("restaurantes.json");
        restaurantes = await resposta.json();
        // bares tradicionais (guardados em atracoes.json) tambem aparecem aqui
        try {
            const rb = await fetch("atracoes.json");
            const bares = (await rb.json()).filter(a => (a.tags || []).includes("bares"));
            restaurantes = restaurantes.concat(bares);
        } catch (e) { console.warn("Bares nao carregados:", e); }
        restaurantesFiltrados = [...restaurantes];
        renderizar(restaurantesFiltrados);
    } catch (erro) {
        console.error("Erro ao carregar restaurantes:", erro);
        document.getElementById("restaurantGrid").innerHTML = `
            <p style="text-align:center;padding:40px;">
                Não foi possível carregar os restaurantes.
            </p>`;
    }
}

// ------------------------------------------------------
// RENDERIZAR CARDS
// ------------------------------------------------------
function renderizar(lista) {
    const grid = document.getElementById("restaurantGrid");
    grid.innerHTML = "";

    if (!lista.length) {
        grid.innerHTML = `
            <p style="text-align:center;padding:40px;">
                Nenhum restaurante encontrado.
            </p>`;
        return;
    }

    lista.forEach(r => {
        const card = document.createElement("article");
        card.className = "restaurant-card";

        const destino = `${r.nome} ${r.bairro || ""} Santos`
            .replace(/\s+/g, " ")
            .trim();

        const directionsUrl =
            `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(ORIGEM_CASA)}` +
            `&destination=${encodeURIComponent(destino)}`+
            (r.place_id ? `&destination_place_id=${r.place_id}` : "");

        // link de visita: site > instagram > maps
        const visitLink = r.site || r.instagram || r.maps || null;
        const visitButton = visitLink
            ? `<a href="${visitLink}" target="_blank" rel="noopener noreferrer" class="visit-button">Visitar</a>`
            : `<button class="visit-button disabled" disabled>Visitar</button>`;

        const foto = r.foto
            ? `<a href="${r.foto}" target="_blank" rel="noopener noreferrer" title="Ver foto em tamanho maior">
                   <img src="${r.foto}" alt="Foto real de ${r.nome}" loading="lazy">
               </a>`
            : "";

        card.innerHTML = `
            ${foto}
            <div class="restaurant-content${r.foto ? "" : " no-image"}">
                <h3>${r.nome}</h3>
                <p class="card-meta">⭐ ${r.nota} • ${r.categoria}${r.preco ? " • " + r.preco : ""}</p>
                ${r.valor_medio ? `<p class="price-info">💰 ${r.valor_medio}</p>` : ""}
                <p class="card-desc">${r.descricao || ""}</p>
                ${r.endereco ? `<p class="endereco-info">📍 ${r.endereco}</p>` : ""}
                <div class="card-actions">
                    ${visitButton}
                    <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" class="map-button">Como Chegar</a>
                </div>
            </div>`;

        grid.appendChild(card);
    });
}

// ------------------------------------------------------
// PESQUISA (ativa apenas se existir um campo #searchInput)
// ------------------------------------------------------
function pesquisar(texto) {
    texto = (texto || "").toLowerCase();
    restaurantesFiltrados = restaurantes.filter(r =>
        (r.nome || "").toLowerCase().includes(texto) ||
        (r.categoria || "").toLowerCase().includes(texto) ||
        (r.bairro || "").toLowerCase().includes(texto) ||
        (r.tags || []).some(t => t.toLowerCase().includes(texto))
    );
    renderizar(restaurantesFiltrados);
}

// ------------------------------------------------------
// FILTRO POR EXPERIÊNCIA / CATEGORIA
// ------------------------------------------------------
const NOTA_BARES = "Santos tem uma tradição de bares: mesas na calçada, chope gelado, petiscos e conversa até tarde, espalhados pelos bairros da cidade. Uma seleção dos mais queridos pelos santistas.";

function filtrarPorExperiencia(tag) {
    const nota = document.getElementById("nota-categoria");
    if (nota) {
        nota.textContent = tag === "bares" ? NOTA_BARES : "";
        nota.hidden = tag !== "bares";
    }
    if (tag === "Todos" || !tag) {
        restaurantesFiltrados = [...restaurantes];
    } else {
        const alvo = tag.toLowerCase();
        restaurantesFiltrados = restaurantes.filter(r =>
            (r.tags || []).some(t => t.toLowerCase() === alvo) ||
            (r.categoria || "").toLowerCase() === alvo
        );
    }
    renderizar(restaurantesFiltrados);
}

// ------------------------------------------------------
// EVENTOS
// ------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    carregarRestaurantes();

    // destaque visual do filtro ativo (o filtro roda pelo onclick inline)
    const botoes = document.querySelectorAll(".experience-grid button, .intro-features button");
    botoes.forEach(botao => {
        botao.addEventListener("click", () => {
            botoes.forEach(b => b.classList.remove("active"));
            botao.classList.add("active");
        });
    });

    // busca opcional
    const pesquisa = document.getElementById("searchInput");
    if (pesquisa) {
        pesquisa.addEventListener("keyup", e => pesquisar(e.target.value));
    }
});
