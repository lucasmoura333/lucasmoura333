"use strict";

// --- Paleta (espelha tools/profile/theme.py) -------------------------------
const C = {
  bg: "#0a0a0c", panel: "#121216", grid: "#1c1c24",
  gold: "#c8a15a", goldBright: "#f2d06b", goldDim: "#7a6234",
  grace: "#f2d06b", stamina: "#4e7a3a", mist: "#3a3a45",
  text: "#d8d2c4", textDim: "#8a8578",
};

// --- Geometria iso (espelha theme.py) --------------------------------------
const TW = 28, TH = 14, INSET = 0.06, ELEV_MAX = 16, SEED = 424242;
const VIEW_W = 1200, VIEW_H = 560;
const TOP_PAD = 90, BOT_PAD = 40;

// --- Helpers de cor --------------------------------------------------------
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const toHex = (rgb) => "#" + rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
function mix(a, b, t) {
  const [ra, ga, ba] = hex(a), [rb, gb, bb] = hex(b);
  return toHex([ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t]);
}
function shade(c, f) { return toHex(hex(c).map((v) => v * f)); }

// --- PRNG determinístico (mulberry32), espelha o seed do Python ------------
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// --- Grade: 53 semanas x 7 dias --------------------------------------------
function buildGrid(year, days, today) {
  const jan1 = new Date(Date.UTC(year, 0, 1));
  const start = new Date(jan1);
  start.setUTCDate(jan1.getUTCDate() - jan1.getUTCDay()); // domingo <= 1/jan
  const weeks = [];
  for (let w = 0; w < 53; w++) {
    const week = [];
    for (let d = 0; d < 7; d++) {
      const dt = new Date(start);
      dt.setUTCDate(start.getUTCDate() + w * 7 + d);
      const date = dt.toISOString().slice(0, 10);
      const inYear = dt.getUTCFullYear() === year;
      week.push({ date, count: inYear ? days[date] || 0 : 0, future: date > today, out: !inYear });
    }
    weeks.push(week);
  }
  return weeks;
}

const iso = (c, r, ox, oy) => [(c - r) * TW / 2 + ox, (c + r) * TH / 2 + oy];

function polys(px, py, elev) {
  const hw = TW / 2 * (1 - INSET), rt = TH / 2 * (1 - INSET);
  const top = [px, py - elev], right = [px + hw, py + rt - elev];
  const bottom = [px, py + 2 * rt - elev], left = [px - hw, py + rt - elev];
  return {
    top: [top, right, bottom, left],
    left: [left, bottom, [px, py + 2 * rt], [px - hw, py + rt]],
    right: [bottom, right, [px + hw, py + rt], [px, py + 2 * rt]],
  };
}
const pts = (p) => p.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
const poly = (p, fill, { stroke = "none", sw = 0, opacity = 1, dash = null } = {}) =>
  `<polygon points="${pts(p)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" opacity="${opacity}"${dash ? ` stroke-dasharray="${dash}"` : ""}/>`;

// --- Render ----------------------------------------------------------------
function render(weeks, state) {
  const cols = weeks.length, rows = 7;
  let maxc = 1;
  for (const w of weeks) for (const d of w) if (!d.out && !d.future) maxc = Math.max(maxc, d.count);

  const minX = iso(0, rows - 1, 0, 0)[0], maxX = iso(cols - 1, 0, 0, 0)[0];
  const ox = VIEW_W / 2 - (minX + maxX) / 2;
  const fieldH = (cols - 1 + rows - 1) * TH / 2 + TH;
  const oy = TOP_PAD + Math.max(0, (VIEW_H - TOP_PAD - BOT_PAD - fieldH) / 2);

  const fogTop = mix(C.bg, C.mist, 0.24);
  const r = rng(SEED);
  const decor = new Map();
  for (let i = 0; i < 130; i++) {
    const c = Math.floor(r() * cols), row = Math.floor(r() * rows), d = weeks[c][row];
    if (d.out || d.future || d.count === 0) continue;
    const k = c + "," + row;
    if (!decor.has(k)) decor.set(k, []);
    decor.get(k).push([r() * 0.64 - 0.32, r() * 0.64 + 0.18]);
  }

  const cells = [];
  for (let c = 0; c < cols; c++) for (let row = 0; row < rows; row++) cells.push([c, row, weeks[c][row]]);
  cells.sort((a, b) => (a[0] + a[1]) - (b[0] + b[1]) || a[0] - b[0]);

  const out = [];
  for (const [c, row, d] of cells) {
    const [px, py] = iso(c, row, ox, oy);
    if (d.out) {
      const t = polys(px, py, 0);
      out.push(poly(t.top, mix(C.bg, C.mist, 0.05), { stroke: C.grid, sw: 0.6, opacity: 0.35, dash: "2 4" }));
      continue;
    }
    const heat = d.future ? 0 : d.count / maxc;
    const elev = d.future ? 0 : Math.round(ELEV_MAX * Math.pow(heat, 0.62));
    if (d.future) {
      const t = polys(px, py, 0);
      out.push(poly(t.top, mix(C.bg, C.mist, 0.07), { stroke: C.mist, sw: 0.6, opacity: 0.5, dash: "3 4" }));
      continue;
    }
    const topCol = d.count === 0
      ? fogTop
      : mix(mix(C.bg, C.stamina, 0.5), C.goldBright, Math.min(1, 0.22 + 0.85 * Math.sqrt(heat)));
    const t = polys(px, py, elev);
    const edge = shade(topCol, 0.5);
    const attrs = `data-date="${d.date}" data-count="${d.count}" class="tile${d.count ? "" : " fog"}"`;
    if (elev > 0) {
      out.push(`<g ${attrs}>`);
      out.push(poly(t.left, shade(topCol, 0.42), { stroke: edge, sw: 0.6 }));
      out.push(poly(t.right, shade(topCol, 0.62), { stroke: edge, sw: 0.6 }));
      out.push(poly(t.top, topCol, { stroke: d.count === 0 ? C.mist : edge, sw: 0.7, opacity: 0.96, dash: d.count === 0 ? "3 3" : null }));
      out.push("</g>");
    } else {
      out.push(`<g ${attrs}>`);
      out.push(poly(t.top, topCol, { stroke: d.count === 0 ? C.mist : edge, sw: 0.7, opacity: 0.96, dash: d.count === 0 ? "3 3" : null }));
      out.push("</g>");
    }
    if (d.count > 0) {
      const cx = px, cy = py + TH / 2 - elev - TH * 0.10;
      const beam = 5 + 10 * Math.min(1, heat * 1.6);
      out.push(`<line x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy - beam}" stroke="${C.grace}" stroke-width="1.2" opacity="0.6"/>`);
      out.push(`<circle cx="${cx}" cy="${cy - beam}" r="${(1.6 + 2.4 * heat).toFixed(1)}" fill="${C.grace}" opacity="0.8"/>`);
      for (const [fx, fy] of decor.get(c + "," + row) || []) {
        out.push(`<circle cx="${(cx + fx * TW * 0.5).toFixed(1)}" cy="${(cy + (fy - 0.5) * TH * 0.6).toFixed(1)}" r="0.9" fill="${C.goldBright}" opacity="0.7"/>`);
      }
    }
  }

  const svg = document.getElementById("map");
  svg.innerHTML = out.join("");
  state.maxc = maxc;
}

// --- Tooltip ---------------------------------------------------------------
const WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
function attachTip(state) {
  const svg = document.getElementById("map");
  const tip = document.getElementById("tip");
  let pinned = null;

  const show = (g, ev) => {
    const date = g.dataset.date, count = +g.dataset.count;
    const wd = WD[new Date(date + "T00:00:00Z").getUTCDay()];
    tip.innerHTML = `<b>${date}</b> · ${wd}<br><span class="cnt">${count}</span> contribution${count === 1 ? "" : "s"}`;
    tip.hidden = false;
    move(ev);
  };
  const move = (ev) => {
    const box = svg.getBoundingClientRect();
    const x = ev.clientX - box.left, y = ev.clientY - box.top;
    tip.style.left = Math.min(x + 14, box.width - 150) + "px";
    tip.style.top = Math.max(y - 10, 4) + "px";
  };

  svg.addEventListener("pointermove", (ev) => {
    const g = ev.target.closest(".tile");
    if (!g) { if (!pinned) tip.hidden = true; return; }
    if (!pinned) show(g, ev); else move(ev);
  });
  svg.addEventListener("pointerleave", () => { if (!pinned) tip.hidden = true; });
  svg.addEventListener("click", (ev) => {
    const g = ev.target.closest(".tile");
    if (!g) return;
    if (pinned) pinned.classList.remove("pinned");
    if (pinned === g) { pinned = null; tip.hidden = true; return; }
    pinned = g; g.classList.add("pinned"); show(g, ev);
  });
}

// --- Boot ------------------------------------------------------------------
async function boot() {
  const data = await fetch("./data.json").then((r) => r.json());
  const today = data.today || new Date().toISOString().slice(0, 10);
  const years = [...new Set(Object.keys(data.days).map((d) => d.slice(0, 4)))].sort();
  const sel = document.getElementById("year");
  sel.innerHTML = years.map((y) => `<option value="${y}">${y}</option>`).join("");
  const curYear = today.slice(0, 4);
  sel.value = years.includes(curYear) ? curYear : years[years.length - 1];

  const state = {};
  const statsEl = document.getElementById("stats");
  const draw = () => {
    const year = sel.value;
    const weeks = buildGrid(+year, data.days, today);
    render(weeks, state);
    attachTip(state);
    const total = weeks.flat().filter((d) => !d.out).reduce((s, d) => s + d.count, 0);
    const active = weeks.flat().filter((d) => !d.out && d.count > 0).length;
    statsEl.innerHTML =
      `<span class="big">${total.toLocaleString("pt-BR")}</span> contributions in ${year}` +
      `<span class="dim"> · ${active} active days · streak ${data.stats.current_streak}d (record ${data.stats.longest_streak}d)</span>`;
  };
  sel.addEventListener("change", draw);
  draw();
}

boot().catch((e) => {
  document.getElementById("stats").textContent = "erro ao carregar dados: " + e.message;
});
