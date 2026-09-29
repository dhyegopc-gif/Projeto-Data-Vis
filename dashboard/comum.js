// Funções comuns das telas R02 a R05 (o gerador injeta antes do código da tela).
// Todo texto que vem do dado entra por textContent, nunca por innerHTML.
const NS = "http://www.w3.org/2000/svg";
const $ = (id) => document.getElementById(id);

function el(tag, attrs, pai) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (pai) pai.appendChild(e);
  return e;
}
function h(tag, props, filhos) {
  const e = document.createElement(tag);
  if (props) for (const k in props) {
    if (k === "text") e.textContent = props[k];
    else if (k === "class") e.className = props[k];
    else e.setAttribute(k, props[k]);
  }
  if (filhos) for (const f of filhos) if (f !== null && f !== undefined && f !== false)
    e.appendChild(typeof f === "string" || typeof f === "number" ? document.createTextNode(String(f)) : f);
  return e;
}
function texto(svgPai, x, y, conteudo, attrs) {
  const t = el("text", Object.assign({ x, y }, attrs || {}), svgPai);
  t.textContent = conteudo;
  return t;
}

const num = (n, casas) => Number(n).toLocaleString("pt-BR", { maximumFractionDigits: casas ?? 0, minimumFractionDigits: casas ? 0 : 0 });
const num1 = (n) => Number(n).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const pct = (n) => num1(n) + "%";
const plural = (n, um, varios) => num(n) + " " + (n === 1 ? um : varios);
const fmt = (iso) => iso ? iso.slice(8, 10) + "/" + iso.slice(5, 7) + "/" + iso.slice(0, 4) : "–";
const fmtDH = (iso) => iso ? fmt(iso) + " " + iso.slice(11, 16) : "–";

// Duração em linguagem comum, a partir de dias (fração)
function duracao(dias) {
  const horas = dias * 24;
  if (horas < 1) return `${Math.max(1, Math.round(horas * 60))} min`;
  if (horas < 24) return `${num(horas, horas < 10 ? 1 : 0)} h`;
  return `${num(dias, dias < 10 ? 1 : 0)} ${dias < 1.95 ? "dia" : "dias"}`;
}

// Dica flutuante: um só elemento #tip para a página
const dica = {
  mostrar(linhas, x, y) {
    const t = $("tip");
    t.replaceChildren(...linhas.map(([cls, txt]) => h("div", { class: cls, text: txt })));
    t.hidden = false;
    const r = t.getBoundingClientRect();
    let px = x + 14, py = y + 14;
    if (px + r.width > innerWidth - 8) px = x - r.width - 14;
    if (py + r.height > innerHeight - 8) py = y - r.height - 14;
    t.style.left = Math.max(8, px) + "px";
    t.style.top = Math.max(8, py) + "px";
  },
  noElemento(linhas, alvo) {
    const r = alvo.getBoundingClientRect();
    this.mostrar(linhas, r.left + r.width / 2, r.top);
  },
  esconder() { $("tip").hidden = true; },
};
addEventListener("scroll", () => dica.esconder(), { passive: true });

// Redesenhar recria botões e SVG, e o foco do teclado se perderia. Quem tem
// data-foco recebe o foco de volta depois de fn(), pelo mesmo valor.
function comFoco(fn) {
  const a = document.activeElement;
  const k = a && a.getAttribute ? a.getAttribute("data-foco") : null;
  fn();
  if (k) {
    const e = document.querySelector(`[data-foco="${CSS.escape(k)}"]`);
    if (e) e.focus();
  }
}

// Botão "Ver como tabela" que alterna um contêiner
function alternarTabela(botaoId, caixaId) {
  const b = $(botaoId), c = $(caixaId);
  b.addEventListener("click", () => {
    const abrir = c.hidden;
    c.hidden = !abrir;
    b.setAttribute("aria-expanded", String(abrir));
    b.textContent = abrir ? "Ocultar tabela" : "Ver como tabela";
  });
}

// Tabela simples: colunas [{t: título, num: bool}], linhas de células (texto ou nó)
function tabela(colunas, linhas, legenda) {
  const tb = h("table", {}, [
    legenda ? h("caption", { class: "sr", text: legenda }) : null,
    h("thead", {}, [h("tr", {}, colunas.map((c) => h("th", { class: c.num ? "num" : "", scope: "col", text: c.t })))]),
    h("tbody", {}, linhas.map((l) => h("tr", l.classe ? { class: l.classe } : {},
      (l.celulas || l).map((v, i) => h("td", { class: colunas[i].num ? "num" : (colunas[i].classe || "") },
        [v instanceof Node ? v : String(v ?? "–")]))))),
  ]);
  return tb;
}

// Navegação entre as telas: arquivo local quando aberto do disco, URL publicada
// quando aberto na web (se já houver uma).
function montarTelas(atual) {
  const lista = $("telas");
  const local = location.protocol === "file:";
  for (const t of D.telas) {
    const href = local || !t.url ? t.arquivo : t.url;
    const a = h("a", { href, text: `${t.id} · ${t.nome}` });
    if (t.id === atual) a.setAttribute("aria-current", "page");
    lista.appendChild(h("li", {}, [a]));
  }
}
function linkTela(id) {
  const t = D.telas.find((x) => x.id === id);
  if (!t) return null;
  const local = location.protocol === "file:";
  return h("a", { href: local || !t.url ? t.arquivo : t.url, text: id });
}

// Marcas por forma (forma + cor: a identidade nunca depende só da cor)
function marca(pai, forma, x, y, r, attrs) {
  let e;
  if (forma === "triangulo") {
    const a = r * 1.25;
    e = el("path", Object.assign({ d: `M${x},${y - a} L${x + a * 0.95},${y + a * 0.62} L${x - a * 0.95},${y + a * 0.62} Z` }, attrs), pai);
  } else if (forma === "quadrado") {
    e = el("rect", Object.assign({ x: x - r * 0.9, y: y - r * 0.9, width: r * 1.8, height: r * 1.8, rx: 1 }, attrs), pai);
  } else {
    e = el("circle", Object.assign({ cx: x, cy: y, r }, attrs), pai);
  }
  return e;
}
function marcaLegenda(forma, cor) {
  const s = el("svg", { width: 14, height: 14, viewBox: "0 0 14 14", class: "marca-svg", "aria-hidden": "true" });
  marca(s, forma, 7, 7.5, 4.6, { fill: cor });
  return s;
}

// Bloco "Premissas desta tela": a mesma lista da linha "Premissas do grupo" do
// requisito (fonte única em comum.py, conferida pelo gerador).
const maiuscula = (t) => t[0].toUpperCase() + t.slice(1);
function montarPremissas() {
  $("premissas").replaceChildren(tabela(
    [{ t: "Premissa" }, { t: "Valor adotado" }, { t: "Por quê" }],
    D.premissas.map((p) => [h("strong", { text: p.nome }), maiuscula(p.valor), maiuscula(p.por_que)]),
    "Premissas desta tela"));
}
