// =====================================================
// script_atracoes.js (v2) — atrações turísticas
// Correções:
//  - fim da renderização dupla (onclick inline + listener)
//  - filtro "Passeios Clássicos" volta a funcionar
//  - corrige typo atracoesFiltrados / atracoesFiltradas
//  - template com classes explícitas (.card-meta / .card-desc)
// =====================================================

const ORIGEM_CASA = "Av. Presidente Wilson, 26 - José Menino, Santos, SP"; // endereço confirmado no Google Business da casa

let atracoes = [];

async function carregarAtracoes() {
    try {
        const resposta = await fetch("atracoes.json");
        atracoes = await resposta.json();
        renderizar(atracoes);
    } catch (erro) {
        console.error("Erro ao carregar atrações:", erro);
        document.getElementById("attractionGrid").innerHTML = `
            <p style="text-align:center;padding:40px;">
                Não foi possível carregar as atrações.
            </p>`;
    }
}

function renderizar(lista) {
    const grid = document.getElementById("attractionGrid");
    grid.innerHTML = "";

    if (!lista.length) {
        grid.innerHTML = `
            <p style="text-align:center;padding:40px;">
                Nenhuma atração encontrada.
            </p>`;
        return;
    }

    lista.forEach(a => {
        const card = document.createElement("article");
        card.className = "restaurant-card";

        const directionsUrl =
            `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(ORIGEM_CASA)}` +
            `&destination=${encodeURIComponent(a.nome + " Santos")}`+
            (a.place_id ? `&destination_place_id=${a.place_id}` : "");

        const visitLink = a.maps ||
            `https://www.google.com/maps/search/${encodeURIComponent(a.nome + " Santos")}`;

        const foto = a.foto
            ? `<a href="${a.foto}" target="_blank" rel="noopener noreferrer" title="Ver foto em tamanho maior">
                   <img src="${a.foto}" alt="Foto real de ${a.nome}" loading="lazy">
               </a>`
            : "";

        card.innerHTML = `
            ${foto}
            <div class="restaurant-content${a.foto ? "" : " no-image"}">
                <h3>${a.nome}</h3>
                <p class="card-meta">⭐ ${a.nota} • ${a.categoria}</p>
                ${a.valor_entrada ? `<p class="price-info">💰 ${a.valor_entrada}</p>` : ""}
                <p class="card-desc">${a.descricao || ""}</p>
                ${a.endereco ? `<p class="endereco-info">📍 ${a.endereco}</p>` : ""}
                <div class="card-actions">
                    <a href="${visitLink}" target="_blank" rel="noopener noreferrer" class="visit-button">Visitar</a>
                    <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" class="map-button">Como Chegar</a>
                </div>
            </div>`;

        grid.appendChild(card);
    });
}

function filtrarPorExperiencia(tag) {
    if (tag === "Todos" || !tag) {
        renderizar(atracoes);
        return;
    }
    const alvo = tag.toLowerCase();
    renderizar(atracoes.filter(a =>
        (a.tags || []).some(t => t.toLowerCase() === alvo) ||
        (a.categoria || "").toLowerCase() === alvo
    ));
}

document.addEventListener("DOMContentLoaded", () => {
    carregarAtracoes();

    // apenas o destaque visual — o filtro roda pelo onclick inline dos botões
    const botoes = document.querySelectorAll(".experience-grid button, .intro-features button");
    botoes.forEach(botao => {
        botao.addEventListener("click", () => {
            botoes.forEach(b => b.classList.remove("active"));
            botao.classList.add("active");
        });
    });
});
