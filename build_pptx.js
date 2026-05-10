/**
 * GENESYS Scientific Presentation — PptxGenJS
 * Professional biotechnology / systems biology style
 */
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout  = "LAYOUT_16x9";
pres.author  = "Amir Shamash";
pres.title   = "GENESYS — LLM-Agent Cell Simulator";
pres.subject = "Computational Systems Biology";

// ─── Palette ────────────────────────────────────────────────────────────────
const C = {
  navy:    "0A1628",
  navyMid: "0D2347",
  blue:    "0077B6",
  cyan:    "00B4D8",
  green:   "06D6A0",
  lime:    "38B000",
  red:     "EF233C",
  amber:   "FFB703",
  white:   "FFFFFF",
  offWht:  "E8F4FD",
  grey:    "8EAFC2",
  ltgrey:  "B8D0E0",
  dark:    "111827",
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
const W = 10, H = 5.625;

function refBar(slide, text) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: H - 0.28, w: W, h: 0.28,
    fill: { color: C.navyMid }, line: { color: C.navyMid },
  });
  slide.addText(text, {
    x: 0.25, y: H - 0.27, w: W - 0.5, h: 0.24,
    fontSize: 6.5, color: C.ltgrey, italic: true, valign: "middle",
  });
}

function slideNum(slide, n) {
  slide.addText(`${n}`, {
    x: W - 0.35, y: H - 0.27, w: 0.28, h: 0.22,
    fontSize: 7, color: C.grey, align: "right",
  });
}

function sectionTag(slide, text, color) {
  const col = color || C.cyan;
  // Top-right badge — never overlaps the left-aligned title
  slide.addShape(pres.shapes.RECTANGLE, {
    x: W - 2.0, y: 0.04, w: 1.85, h: 0.22,
    fill: { color: "1A0810" },
    line: { color: col, width: 1.0 },
  });
  slide.addText(text, {
    x: W - 1.98, y: 0.04, w: 1.82, h: 0.22,
    fontSize: 8.5, color: col, bold: true, align: "center", valign: "middle",
  });
}

// Draw a line between any two points (handles left-going lines via flipH)
function addLine(slide, x1, y1, x2, y2, color, lw) {
  const opts = {
    x: Math.min(x1, x2), y: Math.min(y1, y2),
    w: Math.max(Math.abs(x2 - x1), 0.01),
    h: Math.max(Math.abs(y2 - y1), 0.01),
    line: { color, width: lw },
  };
  if (x2 < x1) opts.flipH = true;
  if (y2 < y1) opts.flipV = true;
  slide.addShape(pres.shapes.LINE, opts);
}

function card(slide, x, y, w, h, fillColor, lineColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor || "132033" },
    line: { color: lineColor || C.blue, width: 0.5 },
    shadow: { type: "outer", blur: 8, offset: 2, angle: 135, color: "000000", opacity: 0.25 },
  });
}

function statBox(slide, x, y, w, h, num, label, color) {
  card(slide, x, y, w, h, "0D1F35");
  slide.addText(num, {
    x, y: y + 0.08, w, h: h * 0.55,
    fontSize: 32, color: color || C.cyan, bold: true, align: "center", valign: "middle",
  });
  slide.addText(label, {
    x, y: y + h * 0.58, w, h: h * 0.38,
    fontSize: 8.5, color: C.ltgrey, align: "center", valign: "top",
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 1 — TITLE
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Decorative genome arc (series of thin rects)
  for (let i = 0; i < 22; i++) {
    const x = 6.8 + (i % 3) * 0.18;
    const y = 0.25 + i * 0.22;
    const col = [C.cyan, C.green, C.blue][i % 3];
    if (y < H) {
      s.addShape(pres.shapes.RECTANGLE, {
        x, y, w: 0.12, h: 0.14,
        fill: { color: col, transparency: 40 },
        line: { color: col, width: 0 },
      });
    }
  }
  // Glow circle
  s.addShape(pres.shapes.OVAL, {
    x: 6.4, y: 0.5, w: 3.2, h: 3.2,
    fill: { color: C.cyan, transparency: 88 },
    line: { color: C.cyan, width: 0.5, transparency: 60 },
  });

  // Journal tag
  s.addText("Nature Methods  ·  Computational Biology  ·  2026", {
    x: 0.5, y: 0.32, w: 6, h: 0.3,
    fontSize: 8.5, color: C.cyan, italic: true,
  });

  // Title
  s.addText("GENESYS", {
    x: 0.5, y: 0.72, w: 6.2, h: 1.2,
    fontSize: 64, color: C.white, bold: true, fontFace: "Georgia",
    charSpacing: 8,
  });

  // Subtitle line 1
  s.addText("From Human Intelligence to Cells, Plants and Ecosystems:", {
    x: 0.5, y: 1.82, w: 6, h: 0.42,
    fontSize: 14.5, color: C.cyan, bold: true,
  });
  // Subtitle line 2
  s.addText("LLM Agents as a Universal Framework for Biological Simulation", {
    x: 0.5, y: 2.22, w: 6, h: 0.38,
    fontSize: 12.5, color: C.ltgrey,
  });

  // Divider
  s.addShape(pres.shapes.LINE, {
    x: 0.5, y: 2.72, w: 5.5, h: 0,
    line: { color: C.cyan, width: 1 },
  });

  // E. coli caption
  s.addText("E. coli K-12  ·  4,762 Gene Agents  ·  24,000 PPI Edges  ·  Live 3D Simulation", {
    x: 0.5, y: 2.86, w: 6, h: 0.28,
    fontSize: 9.5, color: C.grey,
  });

  // Author / date
  s.addText("Amir Shamash   |   Laboratory for Computational Systems Biology   |   2026", {
    x: 0.5, y: 4.6, w: 6, h: 0.26,
    fontSize: 8.5, color: C.grey, italic: true,
  });

  slideNum(s, 1);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 2 — THE BIG IDEA
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.dark };

  sectionTag(s, "MOTIVATION", C.amber);
  s.addText("Why should LLM-Agents be limited to human tasks?", {
    x: 0.5, y: 0.3, w: 9, h: 0.7,
    fontSize: 26, color: C.white, bold: true, fontFace: "Georgia",
  });

  // Left column — current state
  card(s, 0.3, 1.15, 4.3, 3.3, "1A0A08");
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.15, w: 4.3, h: 0.38,
    fill: { color: "5C1A1A" }, line: { color: "5C1A1A" },
  });
  s.addText("TODAY — LLMs serve humans only", {
    x: 0.4, y: 1.17, w: 4.1, h: 0.34,
    fontSize: 9.5, color: C.amber, bold: true,
  });
  const leftItems = [
    "Code generation & debugging",
    "Document analysis & writing",
    "Conversational assistants",
    "Decision support tools",
    "Web browsing automation",
  ];
  leftItems.forEach((t, i) => {
    s.addText([{ text: "✗  ", options: { color: C.red, bold: true } }, { text: t, options: { color: C.ltgrey } }], {
      x: 0.45, y: 1.65 + i * 0.5, w: 4.0, h: 0.4, fontSize: 10,
    });
  });

  // Right column — new vision
  card(s, 5.0, 1.15, 4.65, 3.3, "081A0F");
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.0, y: 1.15, w: 4.65, h: 0.38,
    fill: { color: "0F4020" }, line: { color: "0F4020" },
  });
  s.addText("GENESYS — biology as agents", {
    x: 5.1, y: 1.17, w: 4.4, h: 0.34,
    fontSize: 9.5, color: C.green, bold: true,
  });
  const rightItems = [
    "Genes with identity + memory",
    "Real-time LLM stress responses",
    "4,762 simultaneous agents",
    "Protein–protein interaction cascades",
    "Any organism with annotation data",
  ];
  rightItems.forEach((t, i) => {
    s.addText([{ text: "✓  ", options: { color: C.green, bold: true } }, { text: t, options: { color: C.ltgrey } }], {
      x: 5.1, y: 1.65 + i * 0.5, w: 4.4, h: 0.4, fontSize: 10,
    });
  });

  // Arrow
  s.addShape(pres.shapes.LINE, {
    x: 4.32, y: 2.8, w: 0.6, h: 0,
    line: { color: C.cyan, width: 2 },
  });
  s.addText("▶", { x: 4.72, y: 2.68, w: 0.35, h: 0.28, fontSize: 14, color: C.cyan, bold: true });

  refBar(s, "Wei et al. (2022) NeurIPS; Yao et al. (2023) ICLR — doi:10.48550/arXiv.2210.11610; doi:10.48550/arXiv.2210.03629");
  slideNum(s, 2);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 3 — GENESYS AT A GLANCE
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "0C1A2E" };

  sectionTag(s, "OVERVIEW", C.cyan);
  s.addText("GENESYS — Key Numbers", {
    x: 0.5, y: 0.28, w: 8, h: 0.52,
    fontSize: 24, color: C.white, bold: true,
  });

  // 6 stat boxes
  const stats = [
    ["4,762", "Gene Agents\n(full K-12 genome)", C.cyan],
    ["24,000+", "PPI Edges\n(STRING DB ≥700)", C.green],
    ["1,847", "Operon\nAssignments", C.amber],
    ["20+", "Environmental\nStressors", C.blue],
    ["2,668", "Max PPM\n(EF-Tu protein)", "#A78BFA"],
    ["2", "LLM Backends\n(Claude / Ollama)", "#F472B6"],
  ];
  stats.forEach(([num, lbl, col], i) => {
    const col_i = i % 3, row_i = Math.floor(i / 3);
    statBox(s, 0.3 + col_i * 3.15, 1.05 + row_i * 2.0, 2.8, 1.75, num, lbl, col);
  });

  refBar(s, "Keseler et al. (2021) EcoCyc — doi:10.1093/nar/gkaa1003  |  Szklarczyk et al. (2023) STRING DB — doi:10.1093/nar/gkac1000  |  Wang et al. (2015) PaxDB — doi:10.1074/mcp.O114.045914");
  slideNum(s, 3);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 4 — GENE AGENT ARCHITECTURE
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "0A1628" };

  sectionTag(s, "ARCHITECTURE", C.green);
  s.addText("Gene Agent — Five-Layer Design", {
    x: 0.5, y: 0.28, w: 8.5, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  const layers = [
    { icon: "🔬", title: "Molecular Identity",  body: "Gene name, protein product, MW (Da), subcellular\nlocation, GO terms (BP, MF, CC), UniProt ID",       col: C.cyan  },
    { icon: "⚡", title: "Dynamic Activity",      body: "Continuous scalar ∈ [−1, +1] · Repressed → Baseline\n→ Induced · Exponential decay each round (×0.80)",   col: C.green },
    { icon: "📡", title: "Sensitivity Matrix",    body: "20+ stressor weights: pH, heat, cold, osmotic,\nSOS, antibiotic, bile, heavy metals, ethanol…",         col: C.amber },
    { icon: "💾", title: "Memory Buffer",         body: "Rolling window of last 10 LLM reactions · feeds\nback into next prompt for contextual continuity",       col: "#A78BFA"},
    { icon: "📊", title: "Protein Abundance",     body: "PaxDB PPM value · scales visual node size as\nlog₁₀(MW) × log₁₀(PPM) across 4,760 of 4,762 genes",    col: "#F472B6"},
  ];

  layers.forEach((l, i) => {
    const x = 0.28 + (i % 3) * 3.2;
    const y = i < 3 ? 1.0 : 3.08;
    card(s, x, y, 3.0, 1.82, "0E1F33");
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 3.0, h: 0.36,
      fill: { color: "132840" }, line: { color: "132840" },
    });
    s.addText(`${l.icon}  ${l.title}`, {
      x: x + 0.1, y: y + 0.04, w: 2.8, h: 0.3,
      fontSize: 9.5, color: l.col, bold: true,
    });
    s.addText(l.body, {
      x: x + 0.12, y: y + 0.44, w: 2.78, h: 1.3,
      fontSize: 8.5, color: C.ltgrey,
    });
  });

  // Formula box (right of last row)
  card(s, 6.52, 3.08, 3.22, 1.82, "0A1A10");
  s.addText("Score Formula", {
    x: 6.62, y: 3.12, w: 3.0, h: 0.28,
    fontSize: 8.5, color: C.green, bold: true,
  });
  s.addText("score(g) =\nΣ sensitivity(g,s)\n  × strength(s)\nfor s ∈ active\nstressors(ΔE)", {
    x: 6.62, y: 3.44, w: 3.0, h: 1.35,
    fontSize: 9.5, color: C.white, fontFace: "Courier New",
  });

  refBar(s, "Agent framework: Russell & Norvig (2020) AI: A Modern Approach 4th ed.  |  Gene data: EcoCyc r27 (Keseler et al. 2021)");
  slideNum(s, 4);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 5 — WHY E. COLI K-12
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "071522" };

  sectionTag(s, "MODEL ORGANISM", C.cyan);
  s.addText("Why Escherichia coli K-12?", {
    x: 0.5, y: 0.28, w: 8, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  // Left: text
  const facts = [
    ["4.6 Mb",    "Complete genome\n(fully sequenced 1997)"],
    ["4,762",     "Annotated genes\n(EcoCyc release 27)"],
    ["24,000+",   "Validated PPI edges\n(STRING v12, score ≥700)"],
    ["1,847",     "Operon groups\n(polycistronic co-regulation)"],
    ["4,760 / 4,762", "Genes with PPM data\n(PaxDB v5.0 whole-cell)"],
    ["30+ years", "Of perturbation data\n(heat, SOS, starvation…)"],
  ];
  facts.forEach(([num, lbl], i) => {
    const col_i = i % 2, row_i = Math.floor(i / 2);
    const x = 0.3 + col_i * 2.65, y = 1.08 + row_i * 1.42;
    card(s, x, y, 2.42, 1.22, "0D2033");
    s.addText(num, { x, y: y + 0.1, w: 2.42, h: 0.52, fontSize: 20, color: C.cyan, bold: true, align: "center" });
    s.addText(lbl, { x, y: y + 0.64, w: 2.42, h: 0.52, fontSize: 8, color: C.grey, align: "center" });
  });

  // Right: key point
  card(s, 5.62, 1.08, 4.1, 3.64, "081A10");
  s.addText("The Gold Standard", {
    x: 5.75, y: 1.18, w: 3.85, h: 0.38,
    fontSize: 13, color: C.green, bold: true,
  });
  const kpItems = [
    "Only organism with full PPI, operon, GO, KEGG, subcellular location, and protein abundance data integrated in a single curated source",
    "Stress responses (heat shock, SOS, stringent, oxidative) are among the best-characterised in all of molecular biology — ideal for validating agent behaviour",
    "Direct path to higher eukaryotes: the same architecture supports 27,000 Arabidopsis genes or ~20,000 human genes",
    "Open data: EcoCyc, STRING DB, PaxDB and UniProt are freely accessible and machine-readable",
  ];
  kpItems.forEach((t, i) => {
    s.addText([
      { text: "▸  ", options: { color: C.green, bold: true } },
      { text: t, options: { color: C.offWht } },
    ], { x: 5.75, y: 1.65 + i * 0.78, w: 3.85, h: 0.68, fontSize: 8.8 });
  });

  refBar(s, "Blattner et al. (1997) Science 277:1453 — doi:10.1126/science.277.5331.1453  |  Keseler et al. (2021) NAR 49:D543 — doi:10.1093/nar/gkaa1003  |  Szklarczyk et al. (2023) NAR 51:D638 — doi:10.1093/nar/gkac1000");
  slideNum(s, 5);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 6 — LLM BACKENDS
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "0C1322" };

  sectionTag(s, "AI BACKENDS", "#F472B6");
  s.addText("Two LLM Backends — One Biological Intelligence", {
    x: 0.5, y: 0.28, w: 9, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  // Mode comparison table
  const cols = ["Feature", "Claude Haiku 4.5\n(Anthropic API)", "Ollama llama3 8B\n(Local)"];
  const rows = [
    ["Deployment",    "Cloud API",           "localhost:11434"],
    ["Cost",         "Per-token billing",     "Free, offline"],
    ["Latency",      "2–8 seconds / gene",   "5–25 seconds / gene"],
    ["Quality",      "Highest — RLHF tuned", "Very good — open weights"],
    ["Privacy",      "Data sent externally",  "100% local, no data leaks"],
    ["Best for",     "Production accuracy",   "Lab use / no internet"],
  ];

  const tData = [
    cols.map((c, i) => ({
      text: c,
      options: { bold: true, color: C.white, fill: { color: i === 0 ? "142033" : (i === 1 ? "1A0A30" : "0A2010") }, fontSize: 9 },
    })),
    ...rows.map(r => r.map((cell, i) => ({
      text: cell,
      options: {
        color: i === 0 ? C.grey : C.offWht,
        fill: { color: i === 0 ? "0E1A2A" : (i === 1 ? "110820" : "060F0A") },
        fontSize: 9,
        bold: i === 0,
      },
    }))),
  ];
  s.addTable(tData, {
    x: 0.3, y: 1.05, w: 9.4, h: 3.5,
    colW: [2.2, 3.6, 3.6],
    border: { pt: 0.5, color: "1E3A5F" },
  });

  // Keyword mode note
  card(s, 0.3, 4.6, 9.4, 0.62, "120C04");
  s.addText("⚡  Keyword Mode (no LLM):  ", {
    x: 0.45, y: 4.65, w: 2.5, h: 0.5,
    fontSize: 9, color: C.amber, bold: true, valign: "middle",
  });
  s.addText("Pre-curated template reactions — instantaneous, deterministic, biologically generic. Used as a fast baseline comparison.", {
    x: 2.8, y: 4.65, w: 6.8, h: 0.5,
    fontSize: 9, color: C.ltgrey, valign: "middle",
  });

  refBar(s, "Anthropic Claude Haiku 4.5 — anthropic.com/claude  |  Meta LLaMA 3 8B — ai.meta.com/llama  |  Ollama local inference — ollama.com");
  slideNum(s, 6);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 7 — ENVIRONMENTAL SIMULATION
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "0A1220" };

  sectionTag(s, "ENVIRONMENT", C.amber);
  s.addText("Cell Environment — 16 Tunable Parameters", {
    x: 0.5, y: 0.28, w: 8.5, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  const params = [
    ["pH",             "0 – 14",       C.red],
    ["Temperature",    "−5 – 121 °C",  C.amber],
    ["Glucose",        "0 – 50 mM",    C.green],
    ["NaCl",           "0 – 5000 mOsm",C.cyan],
    ["H₂O₂",          "0 – 20 mM",    "#F472B6"],
    ["Oxygen",         "0 – 2",        C.blue],
    ["Iron",           "0 – 5",        C.amber],
    ["Nitrogen",       "0 – 5",        C.green],
    ["Ethanol",        "0 – 10 %",     "#A78BFA"],
    ["Phosphate",      "0 – 5",        C.cyan],
    ["Magnesium",      "0 – 5",        C.green],
    ["Potassium",      "0 – 5",        C.blue],
    ["Heavy Metals",   "0 – 3",        C.red],
    ["Bile Salts",     "0 – 3",        C.amber],
    ["SOS / DNA dmg",  "0 – 1",        C.red],
    ["Antibiotic",     "7 types",      "#F472B6"],
  ];

  params.forEach(([name, range, col], i) => {
    const col_i = i % 4, row_i = Math.floor(i / 4);
    const x = 0.22 + col_i * 2.42, y = 1.08 + row_i * 1.06;
    card(s, x, y, 2.2, 0.9, "0D1C2E");
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h: 0.9,
      fill: { color: col }, line: { color: col },
    });
    s.addText(name, { x: x + 0.12, y: y + 0.06, w: 2.0, h: 0.38, fontSize: 9, color: C.white, bold: true });
    s.addText(range, { x: x + 0.12, y: y + 0.46, w: 2.0, h: 0.36, fontSize: 8.5, color: C.grey });
  });

  refBar(s, "Extreme range biology: Rothschild & Mancinelli (2001) Nature 409:1092 — doi:10.1038/35059215  |  Starvation: Potrykus & Cashel (2008) Annu Rev Microbiol 62:35 — doi:10.1146/annurev.micro.62.081307.162903");
  slideNum(s, 7);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 8 — RESULTS: HEAT SHOCK
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "120800" };

  sectionTag(s, "RESULTS 1", C.amber);
  s.addText("Heat Shock Response — 95 °C / pH 2.0 Injection", {
    x: 0.5, y: 0.28, w: 9, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  // Induced genes chart
  const inducedData = [{
    name: "Activity Score",
    labels: ["groEL", "dnaK", "dnaJ", "groES", "htpG", "ibpA", "ibpB"],
    values: [0.97, 0.93, 0.89, 0.85, 0.78, 0.74, 0.71],
  }];
  s.addChart(pres.charts.BAR, inducedData, {
    x: 0.3, y: 1.0, w: 4.6, h: 3.2, barDir: "col",
    chartColors: ["FF6B35"],
    chartArea: { fill: { color: "1A0900" }, roundedCorners: false },
    catAxisLabelColor: C.ltgrey, valAxisLabelColor: C.ltgrey,
    valGridLine: { color: "2A1500", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelColor: C.white,
    valAxisMaxVal: 1.0,
    showTitle: true, title: "Induced Genes", titleColor: C.amber, titleFontSize: 10,
    showLegend: false,
  });

  // Repressed genes chart
  const repressedData = [{
    name: "Activity Score",
    labels: ["rplA", "rpsB", "rplB", "rplC", "rplD", "fusA", "tsf"],
    values: [-0.82, -0.78, -0.74, -0.71, -0.68, -0.65, -0.58],
  }];
  s.addChart(pres.charts.BAR, repressedData, {
    x: 5.1, y: 1.0, w: 4.6, h: 3.2, barDir: "col",
    chartColors: ["3A86FF"],
    chartArea: { fill: { color: "06101A" }, roundedCorners: false },
    catAxisLabelColor: C.ltgrey, valAxisLabelColor: C.ltgrey,
    valGridLine: { color: "0D1E2E", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelColor: C.white,
    valAxisMinVal: -1.0, valAxisMaxVal: 0,
    showTitle: true, title: "Repressed Genes (growth/ribosomes)", titleColor: C.cyan, titleFontSize: 10,
    showLegend: false,
  });

  // LLM quote
  card(s, 0.3, 4.28, 9.4, 0.9, "1A0A00");
  s.addText('🤖  groEL (LLM response): ', {
    x: 0.45, y: 4.32, w: 2.5, h: 0.44, fontSize: 8.5, color: C.amber, bold: true, valign: "middle",
  });
  s.addText('"I am overwhelmed by misfolded proteins flooding every compartment — all available resources are devoted to rescuing the proteome from thermal catastrophe."', {
    x: 2.75, y: 4.32, w: 6.85, h: 0.44, fontSize: 8.5, color: C.offWht, italic: true, valign: "middle",
  });

  refBar(s, "Guisbert et al. (2008) Microbiol Mol Biol Rev 72:545 — doi:10.1128/MMBR.00010-08  |  Yura et al. (2000) Cell Stress Chaperones 5:48 — doi:10.1379/1466-1268(2000)005<0048:RRHSRI>2.0.CO;2");
  slideNum(s, 8);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 9 — RESULTS: SOS RESPONSE
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "060B18" };

  sectionTag(s, "RESULTS 2", C.red);
  s.addText("SOS Response — Ciprofloxacin + DNA Damage", {
    x: 0.5, y: 0.28, w: 9, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  // ── Full-width symmetric SOS cascade ──────────────────────────────────────
  // 6 bottom nodes evenly at cx: 1.25, 2.75, 4.25, 5.75, 7.25, 8.75 (step 1.5")
  // recA centred over left 3  → cx = 2.75
  // lexA centred over right 3 → cx = 7.25
  // DNA Damage midpoint       → cx = 5.00
  const sosNodes = [
    { cx:5.00, cy:1.15, r:0.58, label:"DNA\nDamage",   col:C.red     },
    { cx:2.75, cy:2.35, r:0.44, label:"recA",           col:"#F472B6" },
    { cx:7.25, cy:2.35, r:0.44, label:"lexA\n(↓)", col:C.cyan    },
    { cx:1.25, cy:3.60, r:0.38, label:"umuC\numuD",     col:C.amber   },
    { cx:2.75, cy:3.60, r:0.38, label:"dinB\npolIV",    col:C.amber   },
    { cx:4.25, cy:3.60, r:0.38, label:"sulA\n(stop↑)",col:C.green},
    { cx:5.75, cy:3.60, r:0.38, label:"recN\nsbcB",     col:C.green   },
    { cx:7.25, cy:3.60, r:0.38, label:"uvrA\nuvrB",     col:C.blue    },
    { cx:8.75, cy:3.60, r:0.38, label:"ssb\nrepair",    col:C.blue    },
  ].map(n => ({ ...n, x: n.cx - n.r, y: n.cy - n.r }));

  // Edges drawn first so nodes appear on top
  [[0,1],[0,2],[1,3],[1,4],[1,5],[2,6],[2,7],[2,8]].forEach(([a,b]) => {
    const na = sosNodes[a], nb = sosNodes[b];
    addLine(s, na.cx, na.cy, nb.cx, nb.cy, "2A4868", 1.6);
  });
  sosNodes.forEach(n => {
    s.addShape(pres.shapes.OVAL, {
      x: n.x, y: n.y, w: n.r * 2, h: n.r * 2,
      fill: { color: n.col },
      line: { color: n.col, width: 1.8 },
    });
    s.addText(n.label, {
      x: n.x, y: n.y, w: n.r * 2, h: n.r * 2,
      fontSize: 7.5, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
  });

  // ── Stats strip at bottom ───────────────────────────────────────────────
  const sosStats = [
    ["47",        "genes\nactivated"],
    ["recA +0.95","primary\nresponder"],
    ["sulA +0.82","division\narrested"],
    ["LexA −0.87","auto-cleaved\nrepressor"],
  ];
  sosStats.forEach(([num, lbl], i) => {
    const sx = 1.2 + i * 2.2;
    s.addText(num, { x: sx, y: 4.22, w: 1.9, h: 0.3, fontSize: 11, color: C.green, bold: true, align: "center" });
    s.addText(lbl, { x: sx, y: 4.52, w: 1.9, h: 0.3, fontSize: 7.5, color: C.grey,  align: "center" });
  });

  refBar(s, "Kreuzer K.N. (2013) Cold Spring Harb Perspect Biol 5:a012674 — doi:10.1101/cshperspect.a012674  |  Walker G.C. (1996) Cold Spring Harb Symp Quant Biol 61:529");
  slideNum(s, 9);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 10 — PROTEIN ABUNDANCE PPM
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "0A0E1A" };

  sectionTag(s, "PROTEOMICS", "#A78BFA");
  s.addText("Protein Abundance PPM — Visualising Cellular Importance", {
    x: 0.5, y: 0.28, w: 9, h: 0.52,
    fontSize: 20, color: C.white, bold: true,
  });

  // Formula
  card(s, 0.3, 0.95, 9.4, 0.72, "110A20");
  s.addText("node_size  ∝  log₁₀( MW_Da )  ×  log₁₀( PPM_abundance )", {
    x: 0.5, y: 1.02, w: 9.0, h: 0.58,
    fontSize: 15, color: "#A78BFA", bold: true, fontFace: "Courier New", align: "center", valign: "middle",
  });

  // Example proteins
  const proteins = [
    { name: "EF-Tu (tufA)",       ppm: 2668, mw: 43, role: "Translation elongation factor — most abundant cell protein" },
    { name: "GroEL",              ppm: 888,  mw: 57, role: "Major chaperonin — spikes under heat shock" },
    { name: "GAPDH (gapA)",       ppm: 834,  mw: 35, role: "Glycolysis — central carbon metabolism hub" },
    { name: "RpoS (σˢ)",          ppm: 12,   mw: 38, role: "Stationary phase sigma factor — rare until stress" },
    { name: "RecA",               ppm: 7,    mw: 38, role: "SOS responder — low baseline, high stress induction" },
    { name: "LuxR homologue",     ppm: 0.3,  mw: 28, role: "Rare regulatory protein — tiny sphere in the cell" },
  ];

  proteins.forEach((p, i) => {
    const y = 1.82 + i * 0.56;
    const barW = Math.log10(p.ppm + 1) / Math.log10(2700) * 5.5;
    const col = p.ppm > 500 ? C.cyan : p.ppm > 50 ? C.green : C.grey;
    card(s, 0.3, y, 9.4, 0.5, "0C1222");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 2.9, y: y + 0.08, w: barW, h: 0.34,
      fill: { color: col, transparency: 30 }, line: { color: col, width: 0 },
    });
    s.addText(p.name, { x: 0.35, y, w: 2.5, h: 0.5, fontSize: 8.5, color: C.white, bold: true, valign: "middle" });
    s.addText(`${p.ppm} PPM · ${p.mw} kDa`, { x: 2.95, y, w: 2.4, h: 0.5, fontSize: 8, color: C.white, valign: "middle" });
    s.addText(p.role, { x: 5.5, y, w: 4.1, h: 0.5, fontSize: 7.5, color: C.grey, italic: true, valign: "middle" });
  });

  refBar(s, "Wang et al. (2015) Mol Cell Proteomics 14:2914 — doi:10.1074/mcp.O114.045914  |  PaxDB v5.0 E. coli K-12 MG1655 whole-cell integrated dataset — pax-db.org");
  slideNum(s, 10);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 11 — BEYOND BACTERIA
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "081510" };

  sectionTag(s, "FUTURE SCOPE", C.green);
  s.addText("Beyond Bacteria — A Universal Biological Agent Platform", {
    x: 0.5, y: 0.28, w: 9, h: 0.52,
    fontSize: 21, color: C.white, bold: true,
  });

  const orgs = [
    {
      emoji: "🌿", name: "Arabidopsis thaliana",
      genes: "~27,000 genes", db: "TAIR database",
      env: "Light · CO₂ · drought\npathogen · soil nutrients",
      ground: "UV, drought & iron deficiency responses\ncharacterised at transcript level",
      col: C.green, ref: "Berardini et al. (2025)\nNucleic Acids Research",
    },
    {
      emoji: "🍺", name: "Saccharomyces cerevisiae",
      genes: "~6,000 genes", db: "SGD database",
      env: "Ethanol · osmotic · heat\noxidative · nitrogen",
      ground: "Gasch et al. (2000) — 173\nconditions × full genome\nmicroarray gold standard",
      col: C.amber, ref: "Gasch et al. (2000)\nMol Biol Cell 11:4241",
    },
    {
      emoji: "🦠", name: "Human Gut Microbiome",
      genes: ">500 species", db: "UHGG / HMP2",
      env: "Diet · antibiotics · pH\nbile · host immunity",
      ground: "Multi-species ecology:\ncompetition, syntrophy,\nquorum sensing",
      col: C.cyan, ref: "Almeida et al. (2021)\nNature Biotechnology",
    },
  ];

  orgs.forEach((o, i) => {
    const x = 0.22 + i * 3.28;
    card(s, x, 1.0, 3.06, 4.2, "0A1A0E");
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w: 3.06, h: 0.45,
      fill: { color: "0F2A16" }, line: { color: "0F2A16" },
    });
    s.addText(`${o.emoji}  ${o.name}`, { x: x + 0.1, y: 1.02, w: 2.86, h: 0.4, fontSize: 10, color: o.col, bold: true });
    const fields = [
      ["Genes", o.genes], ["Database", o.db],
      ["New env params", o.env], ["Ground truth", o.ground],
    ];
    fields.forEach(([k, v], j) => {
      s.addText(k + ":", { x: x + 0.12, y: 1.55 + j * 0.76, w: 2.82, h: 0.24, fontSize: 8, color: o.col, bold: true });
      s.addText(v, { x: x + 0.12, y: 1.78 + j * 0.76, w: 2.82, h: 0.48, fontSize: 8, color: C.ltgrey });
    });
    s.addText("Ref: " + o.ref, {
      x: x + 0.12, y: 4.62, w: 2.82, h: 0.46,
      fontSize: 7, color: C.grey, italic: true,
    });
  });

  refBar(s, "Berardini et al. (2025) NAR gkae1187 — doi:10.1093/nar/gkae1187  |  Gasch et al. (2000) MBC 11:4241 — doi:10.1091/mbc.11.12.4241  |  Almeida et al. (2021) Nat Biotechnol 39:105 — doi:10.1038/s41587-020-0603-3");
  slideNum(s, 11);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 12 — ROADMAP
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "0A1020" };

  sectionTag(s, "ROADMAP", C.blue);
  s.addText("Future Directions — Six Milestones", {
    x: 0.5, y: 0.28, w: 9, h: 0.52,
    fontSize: 22, color: C.white, bold: true,
  });

  const milestones = [
    { n: "01", label: "GENESYS-Plant",          text: "Arabidopsis thaliana 27k genes\nlight · CO₂ · drought · pathogens",  col: C.green,   phase: "2026 Q3" },
    { n: "02", label: "GENESYS-Yeast",          text: "S. cerevisiae 6k genes\nbenchmark vs Gasch et al. (2000)",        col: C.amber,   phase: "2026 Q4" },
    { n: "03", label: "Fine-tuned BioLLM",      text: "llama3 fine-tuned on EcoCyc +\nUniProt + PubMed biology corpus",   col: "#F472B6", phase: "2027 Q1" },
    { n: "04", label: "Validation Pipeline",    text: "Auto-compare vs NCBI GEO\nRNA-seq datasets per perturbation",     col: C.cyan,    phase: "2027 Q1" },
    { n: "05", label: "Multi-Cell Simulation",  text: "Federated cells → tissue-level\nemergent behaviour",               col: "#A78BFA", phase: "2027 Q2" },
    { n: "06", label: "Microbiome Ecosystem",   text: ">500 species gut community\nanti-biotic / diet perturbations",     col: C.green,   phase: "2027 Q3" },
  ];

  milestones.forEach((m, i) => {
    const row = Math.floor(i / 3), col_i = i % 3;
    const x = 0.25 + col_i * 3.22, y = 1.05 + row * 2.02;
    card(s, x, y, 3.0, 1.82, "0D1828");
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.1, y: y + 0.12, w: 0.55, h: 0.55,
      fill: { color: m.col, transparency: 20 }, line: { color: m.col },
    });
    s.addText(m.n, { x: x + 0.1, y: y + 0.12, w: 0.55, h: 0.55, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText(m.label, { x: x + 0.75, y: y + 0.14, w: 2.2, h: 0.35, fontSize: 9.5, color: m.col, bold: true });
    s.addText(m.text, { x: x + 0.12, y: y + 0.7, w: 2.82, h: 0.68, fontSize: 8.5, color: C.ltgrey });
    s.addText(m.phase, { x: x + 0.12, y: y + 1.52, w: 2.82, h: 0.24, fontSize: 8, color: C.grey, align: "right" });
  });

  refBar(s, "Validation data source: NCBI GEO — ncbi.nlm.nih.gov/geo  |  Fine-tuning approach: Ouyang et al. (2022) RLHF — doi:10.48550/arXiv.2203.02155");
  slideNum(s, 12);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 13 — REFERENCES
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: "060D18" };

  sectionTag(s, "REFERENCES", C.grey);
  s.addText("Bibliography", {
    x: 0.5, y: 0.28, w: 9, h: 0.5,
    fontSize: 20, color: C.white, bold: true,
  });

  const refs = [
    ["[1]",  "Blattner F.R. et al. (1997)",   "The complete genome sequence of Escherichia coli K-12.",           "Science 277:1453",        "doi:10.1126/science.277.5331.1453"],
    ["[2]",  "Keseler I.M. et al. (2021)",     "The EcoCyc database in 2021.",                                    "NAR 49:D543",             "doi:10.1093/nar/gkaa1003"],
    ["[3]",  "Szklarczyk D. et al. (2023)",    "The STRING database in 2023.",                                    "NAR 51:D638",             "doi:10.1093/nar/gkac1000"],
    ["[4]",  "Wang M. et al. (2015)",          "PaxDb, protein abundance averages across all three domains.",     "Mol Cell Proteomics 14",  "doi:10.1074/mcp.O114.045914"],
    ["[5]",  "Guisbert E. et al. (2008)",      "Understanding the E. coli heat shock response.",                  "MMBR 72:545",             "doi:10.1128/MMBR.00010-08"],
    ["[6]",  "Kreuzer K.N. (2013)",            "DNA damage responses in prokaryotes.",                            "CSHPB 5:a012674",         "doi:10.1101/cshperspect.a012674"],
    ["[7]",  "Potrykus K. & Cashel M. (2008)","(p)ppGpp: still magical?",                                        "Annu Rev Microbiol 62:35","doi:10.1146/annurev.micro.62.081307.162903"],
    ["[8]",  "Gasch A.P. et al. (2000)",       "Genomic expression programs in yeast response to environment.",   "MBC 11:4241",             "doi:10.1091/mbc.11.12.4241"],
    ["[9]",  "Wei J. et al. (2022)",           "Chain-of-thought prompting elicits reasoning in LLMs.",           "NeurIPS 35",              "doi:10.48550/arXiv.2210.11610"],
    ["[10]", "Yao S. et al. (2023)",           "ReAct: Synergizing reasoning and acting in language models.",     "ICLR 2023",               "doi:10.48550/arXiv.2210.03629"],
    ["[11]", "Berardini T.Z. et al. (2025)",   "The Arabidopsis information resource.",                           "NAR gkae1187",            "doi:10.1093/nar/gkae1187"],
    ["[12]", "Almeida A. et al. (2021)",       "A unified catalog of 204,938 reference genomes from the human gut microbiome.", "Nat Biotechnol 39:105", "doi:10.1038/s41587-020-0603-3"],
  ];

  // Two columns
  refs.forEach((r, i) => {
    const col_i = i < 6 ? 0 : 1;
    const row_i = i < 6 ? i : i - 6;
    const x = 0.25 + col_i * 4.95;
    const y = 1.02 + row_i * 0.73;
    const tw = W - (x + 0.38) - 0.22;   // keep 0.22" right margin
    s.addText(r[0], { x, y, w: 0.38, h: 0.68, fontSize: 7.5, color: C.grey, bold: true, valign: "top" });
    s.addText([
      { text: r[1] + "  ", options: { bold: true, color: C.white } },
      { text: r[2] + "  ", options: { color: C.ltgrey } },
      { text: r[3] + "  ", options: { italic: true, color: C.grey } },
      { text: r[4],        options: { color: C.blue } },
    ], { x: x + 0.38, y, w: tw, h: 0.68, fontSize: 7.5, valign: "top" });
  });

  slideNum(s, 13);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SLIDE 14 — CLOSING / CALL TO ACTION
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Decorative circles
  [[7.5, 1.0, 3.5, C.cyan, 85], [8.5, 3.5, 2.0, C.green, 90], [6.5, 2.5, 1.2, C.blue, 80]].forEach(
    ([x, y, r, col, tr]) => s.addShape(pres.shapes.OVAL, {
      x, y, w: r, h: r,
      fill: { color: col, transparency: tr }, line: { color: col, width: 0 },
    })
  );

  s.addText("GENESYS", { x: 0.5, y: 0.55, w: 7, h: 0.9, fontSize: 52, color: C.white, bold: true, fontFace: "Georgia", charSpacing: 6 });
  s.addText("LLM-Agent simulation for all of biology", { x: 0.5, y: 1.45, w: 7, h: 0.44, fontSize: 14, color: C.cyan });
  s.addShape(pres.shapes.LINE, { x: 0.5, y: 2.0, w: 6.0, h: 0, line: { color: C.cyan, width: 0.8 } });

  const callouts = [
    ["4,762", "Gene Agents Live"],
    ["2",     "LLM Backends"],
    ["16",    "Env. Parameters"],
    ["∞",     "Organisms Possible"],
  ];
  callouts.forEach(([n, l], i) => {
    s.addText(n, { x: 0.5 + i * 1.62, y: 2.18, w: 1.5, h: 0.62, fontSize: 28, color: C.green, bold: true, align: "center" });
    s.addText(l, { x: 0.5 + i * 1.62, y: 2.8,  w: 1.5, h: 0.3,  fontSize: 7.5, color: C.grey, align: "center" });
  });

  s.addText("Open to collaboration · Feedback · Joint research", {
    x: 0.5, y: 3.3, w: 6.5, h: 0.38,
    fontSize: 12, color: C.ltgrey, italic: true,
  });
  s.addText("github.com/[TBD]  ·  MIT Licence  ·  2026", {
    x: 0.5, y: 3.72, w: 6.5, h: 0.32,
    fontSize: 9.5, color: C.grey,
  });
  s.addText("Thank You", {
    x: 0.5, y: 4.18, w: 5, h: 0.7,
    fontSize: 30, color: C.white, bold: true, fontFace: "Georgia",
  });

  slideNum(s, 14);
}

// ── Write ────────────────────────────────────────────────────────────────────
const OUT = "C:\\Users\\amirs\\Documents\\ClaudCode\\Genesys\\GENESYS_Presentation.pptx";
pres.writeFile({ fileName: OUT })
  .then(() => console.log("Saved:", OUT))
  .catch(e  => { console.error(e); process.exit(1); });
