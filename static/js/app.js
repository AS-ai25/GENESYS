/* ═══════════════════════════════════════════════════════════════
   GENESYS — app.js
   E. coli K-12 Virtual Cell · Cytoscape.js network dashboard
═══════════════════════════════════════════════════════════════ */

'use strict';

// ── Type colour map ───────────────────────────────────────────
const TYPE_COLOR = {
  CDS:            '#4fc3f7',
  tRNA:           '#a5d6a7',
  rRNA:           '#ef9a9a',
  ncRNA:          '#ffcc80',
  mobile_element: '#f48fb1',
  gene:           '#80deea',
  misc_feature:   '#bcaaa4',
  rep_origin:     '#ffe082',
};
const DEFAULT_COLOR = '#90a4ae';

// Operon palette: up to 40 distinct family colours
const OPERON_PALETTE = [
  '#b39ddb','#f48fb1','#ffe082','#80cbc4','#ff8a65','#ce93d8',
  '#80deea','#a5d6a7','#fff59d','#ffab91','#bcaaa4','#b0bec5',
  '#c5e1a5','#e6ee9c','#ffccbc','#cfd8dc','#d7ccc8','#dcedc8',
  '#f0f4c3','#b2dfdb','#b3e5fc','#e1bee7','#fce4ec','#fff3e0',
  '#e8f5e9','#e3f2fd','#ede7f6','#fbe9e7','#efebe9','#eceff1',
  '#f3e5f5','#e8eaf6','#e0f2f1','#f9fbe7','#fff8e1','#fff3e0',
  '#e8f5e9','#e3f2fd','#ede7f6','#fbe9e7',
];

// ── State ─────────────────────────────────────────────────────
let cy = null;
let allNodes = [];      // raw gene objects from /api/genes
let allEdges = [];      // raw edges from /api/network
let operonColorMap = {};
let selectedGene = null;
let activeFilters = { types: new Set(['CDS','tRNA','rRNA','ncRNA','mobile_element','gene','misc_feature','rep_origin']), ppiOnly: true };
let showEdges = { ppi: true, operon: true, llm: true };

// ── DOM references ────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initCytoscape();
  bindControls();
  loadDashboard();
});

async function loadDashboard() {
  setLoaderSub('Fetching genome stats…');
  const stats = await fetchJSON('/api/stats');
  renderStats(stats);

  setLoaderSub('Loading 4 700+ gene agents…');
  allNodes = await fetchJSON('/api/genes');

  // Build operon colour map
  const operons = [...new Set(allNodes.map(g => g.operon).filter(Boolean))];
  operons.forEach((op, i) => {
    operonColorMap[op] = OPERON_PALETTE[i % OPERON_PALETTE.length];
  });

  setLoaderSub('Building protein interaction network…');
  allEdges = await fetchJSON('/api/network');

  setLoaderSub('Rendering virtual cell…');
  $('headerGeneCount').textContent = `${allNodes.length.toLocaleString()} gene agents`;

  renderNetwork();
  $('loadingOverlay').style.display = 'none';
}

// ── Stats ─────────────────────────────────────────────────────
function renderStats(s) {
  $('statTotalVal').textContent = (s.total_genes || 0).toLocaleString();
  $('statCDSVal').textContent   = (s.by_type?.CDS || 0).toLocaleString();
  const rna = (s.by_type?.tRNA||0) + (s.by_type?.rRNA||0) + (s.by_type?.ncRNA||0);
  $('statRNAVal').textContent   = rna.toLocaleString();
  $('statOperonsVal').textContent = (s.total_operons || 0).toLocaleString();
  $('statPPIVal').textContent   = (s.total_ppi || 0).toLocaleString();
  $('statPersonalitiesVal').textContent = (s.cached_personalities || 0).toLocaleString();
}

// ── Cytoscape init ────────────────────────────────────────────
function initCytoscape() {
  cy = cytoscape({
    container: $('cy'),
    style: buildCyStyle(),
    elements: [],
    minZoom: 0.05,
    maxZoom: 8,
    wheelSensitivity: 0.3,
  });

  // Hover tooltip
  const tooltip = $('tooltip');
  cy.on('mouseover', 'node', evt => {
    const d = evt.target.data();
    const pos = evt.renderedPosition;
    tooltip.innerHTML = `
      <strong style="color:${TYPE_COLOR[d.type]||DEFAULT_COLOR}">${d.id}</strong>
      <div style="color:#8aa8c8;font-size:0.72rem;margin-top:3px">${d.type} · ${d.locus}</div>
      <div style="font-size:0.72rem;margin-top:4px;max-width:220px">${d.product||''}</div>
      ${d.operon ? `<div style="font-size:0.68rem;color:#b39ddb;margin-top:3px">Operon: ${d.operon}</div>` : ''}
      ${d.ppi_count > 0 ? `<div style="font-size:0.68rem;color:#ffcc80;margin-top:2px">PPI partners: ${d.ppi_count}</div>` : ''}
    `;
    tooltip.style.left = (pos.x + 14) + 'px';
    tooltip.style.top  = (pos.y - 10) + 'px';
    tooltip.classList.remove('d-none');
  });
  cy.on('mouseout', 'node', () => tooltip.classList.add('d-none'));
  cy.on('mousedown', () => tooltip.classList.add('d-none'));

  // Node click → detail panel
  cy.on('tap', 'node', evt => {
    const name = evt.target.data('id');
    openGeneDetail(name);
    highlightNode(name);
  });

  cy.on('tap', evt => {
    if (evt.target === cy) clearHighlight();
  });
}

// ── Build Cytoscape style ─────────────────────────────────────
function buildCyStyle() {
  return [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'border-width': 2,
        'border-color': 'data(borderColor)',
        'border-opacity': 0.7,
        'label': 'data(label)',
        'font-size': 8,
        'font-family': 'JetBrains Mono, monospace',
        'color': '#c8daf0',
        'text-valign': 'bottom',
        'text-margin-y': 3,
        'min-zoomed-font-size': 10,
        'width': 'data(size)',
        'height': 'data(size)',
        'shadow-blur': 12,
        'shadow-color': 'data(color)',
        'shadow-opacity': 0.5,
        'shadow-offset-x': 0,
        'shadow-offset-y': 0,
      }
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': '#00e5ff',
        'border-opacity': 1,
        'shadow-blur': 24,
        'shadow-color': '#00e5ff',
        'shadow-opacity': 0.9,
      }
    },
    {
      selector: 'node.dimmed',
      style: { 'opacity': 0.15 }
    },
    {
      selector: 'node.highlighted',
      style: {
        'border-width': 3,
        'border-color': '#00e5ff',
        'border-opacity': 1,
        'opacity': 1,
      }
    },
    {
      selector: 'edge[type="ppi"]',
      style: {
        'width': 'mapData(score, 0.5, 1.0, 0.8, 2.5)',
        'line-color': '#37474f',
        'opacity': 0.55,
        'curve-style': 'bezier',
        'display': 'data(showPpi)',
      }
    },
    {
      selector: 'edge[type="operon"]',
      style: {
        'width': 2.5,
        'line-color': 'data(operonColor)',
        'line-style': 'dashed',
        'line-dash-pattern': [6, 3],
        'opacity': 0.75,
        'curve-style': 'bezier',
        'display': 'data(showOperon)',
      }
    },
    {
      selector: 'edge[type="llm"]',
      style: {
        'width': 2,
        'line-color': '#80cbc4',
        'line-style': 'dotted',
        'opacity': 0.8,
        'curve-style': 'bezier',
        'display': 'data(showLlm)',
      }
    },
    {
      selector: 'edge.dimmed',
      style: { 'opacity': 0.05 }
    }
  ];
}

// ── Render network ────────────────────────────────────────────
function renderNetwork() {
  const ppiOnly = activeFilters.ppiOnly;
  const activeTypes = activeFilters.types;
  const sizeBy = $('nodeSizeSelect').value;

  // Filter nodes
  const visibleNodes = allNodes.filter(g =>
    activeTypes.has(g.type) && (!ppiOnly || g.ppi_count > 0)
  );
  const visibleSet = new Set(visibleNodes.map(g => g.id));

  // Compute size
  const maxPPI  = Math.max(...visibleNodes.map(g => g.ppi_count || 0), 1);
  const maxMW   = Math.max(...visibleNodes.map(g => parseFloat(g.mw) || 0), 1);
  const maxLen  = Math.max(...visibleNodes.map(g => parseInt(g.length) || 0), 1);

  function nodeSize(g) {
    if (sizeBy === 'ppi')     return 12 + ((g.ppi_count||0) / maxPPI) * 28;
    if (sizeBy === 'mw')      return 12 + ((parseFloat(g.mw)||0) / maxMW) * 28;
    if (sizeBy === 'length')  return 12 + ((parseInt(g.length)||0) / maxLen) * 28;
    return 16;
  }

  const cyNodes = visibleNodes.map(g => {
    const col = TYPE_COLOR[g.type] || DEFAULT_COLOR;
    const opCol = g.operon ? operonColorMap[g.operon] : col;
    return {
      data: {
        id: g.id,
        label: g.id,
        type: g.type,
        locus: g.locus,
        operon: g.operon || '',
        ppi_count: g.ppi_count,
        product: g.product,
        color: col,
        borderColor: opCol,
        size: nodeSize(g),
        showPpi: showEdges.ppi ? 'element' : 'none',
        showOperon: showEdges.operon ? 'element' : 'none',
        showLlm: showEdges.llm ? 'element' : 'none',
      }
    };
  });

  const cyEdges = allEdges
    .filter(e => visibleSet.has(e.source) && visibleSet.has(e.target))
    .map((e, i) => ({
      data: {
        id: `e${i}`,
        source: e.source,
        target: e.target,
        type: e.type,
        score: e.score || 1,
        operonColor: e.operon ? operonColorMap[e.operon] || '#b39ddb' : '#b39ddb',
        showPpi: showEdges.ppi ? 'element' : 'none',
        showOperon: showEdges.operon ? 'element' : 'none',
        showLlm: showEdges.llm ? 'element' : 'none',
      }
    }));

  cy.elements().remove();
  cy.add([...cyNodes, ...cyEdges]);
  runLayout();
}

function runLayout() {
  const name = $('layoutSelect').value;
  const layouts = {
    fcose: {
      name: 'fcose',
      quality: 'default',
      randomize: true,
      animate: true,
      animationDuration: 800,
      nodeSeparation: 75,
      idealEdgeLength: edge => edge.data('type') === 'operon' ? 60 : 120,
      numIter: 2500,
    },
    circle: { name: 'circle', animate: true, animationDuration: 600 },
    grid:   { name: 'grid',   animate: true, animationDuration: 600 },
    breadthfirst: { name: 'breadthfirst', animate: true, animationDuration: 600, spacingFactor: 1.3 },
  };
  cy.layout(layouts[name] || layouts.fcose).run();
}

// ── Highlight helpers ─────────────────────────────────────────
function highlightNode(name) {
  cy.elements().addClass('dimmed');
  cy.elements().removeClass('highlighted');
  const node = cy.$(`node[id="${name}"]`);
  node.removeClass('dimmed').addClass('highlighted');
  node.neighborhood().removeClass('dimmed').addClass('highlighted');
}

function clearHighlight() {
  cy.elements().removeClass('dimmed highlighted');
}

// ── Gene Detail Panel ─────────────────────────────────────────
async function openGeneDetail(name) {
  selectedGene = name;

  // Switch to detail view
  $('welcomeMsg').classList.add('d-none');
  $('geneDetail').classList.remove('d-none');

  // Reset tabs
  switchTab('identity');

  // Show loading placeholders
  $('detailGeneName').textContent = name;
  $('detailLocus').textContent = '…';
  $('identityGrid').innerHTML = '<div class="ig-key">Loading…</div><div></div>';
  clearPersonalityUI();
  clearConnectionsUI();

  const g = await fetchJSON(`/api/gene/${name}`);

  // Header
  $('detailGeneName').textContent = g.Gene_Name;
  $('detailLocus').textContent = `${g.Locus_Tag} · ${g.Start}–${g.End} (${g.Strand === '1' ? '+' : '−'})`;

  const badge = $('geneBadgeType');
  badge.textContent = g.Type;
  badge.className = `gene-badge badge-${g.Type} badge-${g.Type in TYPE_COLOR ? g.Type : 'default'}`;

  // Identity tab
  renderIdentity(g);

  // Personality
  if (g.personality) {
    showPersonality(g.personality);
  } else {
    clearPersonalityUI();
  }

  // Connections
  renderConnections(g);

  // LLM connections (cached)
  if (g.llm_connections && g.llm_connections.length > 0) {
    renderLLMConnections(g.llm_connections);
  }
}

function renderIdentity(g) {
  const fields = [
    ['— Identity —', null],
    ['Gene Name', g.Gene_Name],
    ['Locus Tag', g.Locus_Tag],
    ['Type', g.Type],
    ['Strand', g.Strand === '1' ? '(+) forward' : '(−) reverse'],
    ['Start', Number(g.Start).toLocaleString() + ' bp'],
    ['End', Number(g.End).toLocaleString() + ' bp'],
    ['Length', `${g.Length} ${g.Unit}`],

    ['— Product & Function —', null],
    ['Product', g.Product],
    ['Function', g.Function || '—'],
    ['Subcellular Location', g.Subcellular_Location || '—'],
    ['Mini Review', g.Mini_Review_Summary || '—'],

    ['— GO Annotation —', null],
    ['Biological Process', g.GO_Biological_Process || '—'],
    ['Molecular Function', g.GO_Molecular_Function || '—'],
    ['Cellular Component', g.GO_Cellular_Component || '—'],

    ['— Biophysics —', null],
    ['Molecular Weight', g.Molecular_Weight_Da ? Number(g.Molecular_Weight_Da).toLocaleString() + ' Da' : '—'],
    ['Max Size', g.Max_Size_A ? g.Max_Size_A + ' Å' : '—'],
    ['Dimensions (XYZ)', g.Dimensions_XYZ_A || '—'],
    ['Radius of Gyration', g.Radius_of_Gyration_A ? g.Radius_of_Gyration_A + ' Å' : '—'],

    ['— Database IDs —', null],
    ['UniProt', g.UniProt_ID || '—'],
    ['GeneID', g.GeneID || '—'],
    ['Protein ID', g.Protein_ID || '—'],

    ['— KEGG —', null],
    ['KEGG Definition', g.KEGG_Definition || '—'],
    ['KEGG KO', g.KEGG_KO_Meaning || '—'],
    ['KEGG BRITE', g.KEGG_BRITE_Meaning || '—'],
    ['Pathways', g.KEGG_Pathways || '—'],

    ['— Operon / Family —', null],
    ['Operon', g.operon || '(none)'],
    ['Family Members', g.operon_members?.join(', ') || '—'],

    ['— STRING Network —', null],
    ['Gene Symbol', g.Gene_Symbol_STRING || '—'],
    ['PPI Partners', g.PPI_Partners || '—'],
    ['PPI Count', g.PPI_Count || '0'],
  ];

  let html = '';
  for (const [key, val] of fields) {
    if (val === null) {
      html += `<div class="ig-section">${key}</div>`;
    } else {
      html += `<div class="ig-key">${key}</div><div class="ig-val">${val}</div>`;
    }
  }
  $('identityGrid').innerHTML = html;
}

// ── Personality tab ───────────────────────────────────────────
function showPersonality(text) {
  $('personalityText').textContent = text;
  $('personalityText').style.display = 'block';
  $('personalityPlaceholder').style.display = 'none';
}

function clearPersonalityUI() {
  $('personalityText').textContent = '';
  $('personalityText').style.display = 'none';
  $('personalityPlaceholder').style.display = 'flex';
  $('personalityStatus').textContent = '';
}

// ── Connections tab ───────────────────────────────────────────
function renderConnections(g) {
  // PPI
  const ppiList = $('ppiList');
  ppiList.innerHTML = '';
  if (g.ppi_parsed && g.ppi_parsed.length > 0) {
    g.ppi_parsed.sort((a, b) => b.score - a.score).forEach(p => {
      const item = connItem(p.name, '', p.score, () => openGeneDetail(p.name));
      ppiList.appendChild(item);
    });
  } else {
    ppiList.innerHTML = '<div style="font-size:0.75rem;color:var(--text-lo);padding:4px 0">No PPI partners recorded</div>';
  }

  // Operon
  const opList = $('operonList');
  opList.innerHTML = '';
  if (g.operon_members && g.operon_members.length > 1) {
    g.operon_members.filter(n => n !== g.Gene_Name).forEach(n => {
      const item = connItem(n, `Same operon: ${g.operon}`, null, () => openGeneDetail(n));
      opList.appendChild(item);
    });
  } else {
    opList.innerHTML = '<div style="font-size:0.75rem;color:var(--text-lo);padding:4px 0">Not part of a named operon family</div>';
  }
}

function renderLLMConnections(connections) {
  const list = $('llmConnList');
  list.innerHTML = '';
  connections.forEach(c => {
    const item = connItem(c.name, c.reason, null, () => openGeneDetail(c.name));
    list.appendChild(item);

    // Add LLM edge to graph if not already present
    addLLMEdge(selectedGene, c.name);
  });
}

function clearConnectionsUI() {
  $('ppiList').innerHTML = '';
  $('operonList').innerHTML = '';
  $('llmConnList').innerHTML = '';
  $('connStatus').textContent = '';
}

function connItem(name, detail, score, onClick) {
  const div = document.createElement('div');
  div.className = 'conn-item';
  div.innerHTML = `
    <span class="conn-item-name">${name}</span>
    ${detail ? `<span class="conn-item-detail">${detail}</span>` : ''}
    ${score !== null ? `<span class="conn-score">${score.toFixed(3)}</span>` : ''}
  `;
  div.addEventListener('click', onClick);
  return div;
}

function addLLMEdge(source, target) {
  if (!cy) return;
  const eid = `llm-${source}-${target}`;
  if (cy.$(`#${eid}`).length > 0) return;
  if (!cy.$(`node[id="${target}"]`).length) return;
  cy.add({
    data: {
      id: eid,
      source, target,
      type: 'llm',
      score: 1,
      showLlm: showEdges.llm ? 'element' : 'none',
    }
  });
}

// ── Tab switching ─────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.gs-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === `tab-${name}`));
}

// ── Controls binding ──────────────────────────────────────────
function bindControls() {
  // Tab clicks
  document.querySelectorAll('.gs-tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Close detail
  $('closeDetail').addEventListener('click', () => {
    $('geneDetail').classList.add('d-none');
    $('welcomeMsg').classList.remove('d-none');
    selectedGene = null;
    clearHighlight();
  });

  // Type checkboxes
  document.querySelectorAll('.type-cb').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) activeFilters.types.add(cb.value);
      else activeFilters.types.delete(cb.value);
      renderNetwork();
    });
  });

  // Edge visibility
  $('showPPI').addEventListener('change', e => {
    showEdges.ppi = e.target.checked;
    cy.edges('[type="ppi"]').style('display', showEdges.ppi ? 'element' : 'none');
  });
  $('showOperon').addEventListener('change', e => {
    showEdges.operon = e.target.checked;
    cy.edges('[type="operon"]').style('display', showEdges.operon ? 'element' : 'none');
  });
  $('showLLM').addEventListener('change', e => {
    showEdges.llm = e.target.checked;
    cy.edges('[type="llm"]').style('display', showEdges.llm ? 'element' : 'none');
  });

  // PPI only toggle
  $('ppiOnlyToggle').addEventListener('change', e => {
    activeFilters.ppiOnly = e.target.checked;
    renderNetwork();
  });

  // Layout + size
  $('layoutSelect').addEventListener('change', renderNetwork);
  $('nodeSizeSelect').addEventListener('change', () => {
    // Just re-render nodes without rebuilding edges
    renderNetwork();
  });

  // Zoom buttons
  $('zoomIn').addEventListener('click', () => cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width()/2, y: cy.height()/2 } }));
  $('zoomOut').addEventListener('click', () => cy.zoom({ level: cy.zoom() * 0.77, renderedPosition: { x: cy.width()/2, y: cy.height()/2 } }));
  $('centerBtn').addEventListener('click', () => cy.fit(cy.elements(), 40));
  $('fitBtn').addEventListener('click', () => cy.fit(cy.elements(), 40));
  $('resetBtn').addEventListener('click', renderNetwork);

  // Generate personality
  $('genPersonalityBtn').addEventListener('click', async () => {
    if (!selectedGene) return;
    const btn = $('genPersonalityBtn');
    const status = $('personalityStatus');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner spin me-2"></i>Generating…';
    status.textContent = '';
    try {
      const res = await postJSON(`/api/personality/${selectedGene}`);
      showPersonality(res.personality);
      status.textContent = res.cached ? '⚡ Loaded from cache' : '✨ Generated by Claude';
      status.style.color = res.cached ? '#80deea' : '#a5d6a7';
      refreshStatBadge();
    } catch (err) {
      status.textContent = '❌ Error: ' + err.message;
      status.style.color = '#ef9a9a';
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles me-2"></i>Regenerate Personality';
    }
  });

  // Generate AI connections
  $('genConnectionsBtn').addEventListener('click', async () => {
    if (!selectedGene) return;
    const btn = $('genConnectionsBtn');
    const status = $('connStatus');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner spin me-2"></i>Evaluating connections…';
    status.textContent = '';
    try {
      const res = await postJSON(`/api/connections/${selectedGene}`);
      renderLLMConnections(res.connections || []);
      status.textContent = res.cached ? `⚡ Loaded from cache (${res.connections?.length} links)` : `✨ ${res.connections?.length} AI connections generated`;
      status.style.color = res.cached ? '#80deea' : '#a5d6a7';
    } catch (err) {
      status.textContent = '❌ Error: ' + err.message;
      status.style.color = '#ef9a9a';
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles me-2"></i>Regenerate AI Connections';
    }
  });

  // Load sequences
  $('loadSeqBtn').addEventListener('click', async () => {
    if (!selectedGene) return;
    const btn = $('loadSeqBtn');
    const loading = $('seqLoading');
    btn.style.display = 'none';
    loading.classList.remove('d-none');
    try {
      const seq = await fetchJSON(`/api/gene/${selectedGene}/sequence`);
      if (seq.dna) {
        $('seqDNAText').value = seq.dna;
        $('seqDNA').classList.remove('d-none');
      }
      if (seq.protein) {
        $('seqProtText').value = seq.protein;
        $('seqProt').classList.remove('d-none');
      }
    } finally {
      loading.classList.add('d-none');
    }
  });

  // Search
  initSearch();
}

// ── Search ────────────────────────────────────────────────────
function initSearch() {
  const input = $('searchInput');
  const dropdown = $('searchDropdown');

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    if (q.length < 1) { dropdown.classList.add('d-none'); return; }

    const matches = allNodes
      .filter(g => g.id.toLowerCase().includes(q) || g.locus.toLowerCase().includes(q) || g.product.toLowerCase().includes(q))
      .slice(0, 20);

    if (!matches.length) { dropdown.classList.add('d-none'); return; }

    dropdown.innerHTML = matches.map(g => `
      <div class="search-item" data-name="${g.id}">
        <span class="si-type ${g.type}">${g.type}</span>
        <strong>${g.id}</strong>
        <span style="color:#8aa8c8;font-size:0.72rem;flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">${g.product}</span>
      </div>
    `).join('');

    dropdown.classList.remove('d-none');
    dropdown.querySelectorAll('.search-item').forEach(item => {
      item.addEventListener('click', () => {
        const name = item.dataset.name;
        dropdown.classList.add('d-none');
        input.value = name;
        focusGene(name);
      });
    });
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) dropdown.classList.add('d-none');
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { dropdown.classList.add('d-none'); input.blur(); }
  });
}

function focusGene(name) {
  const node = cy.$(`node[id="${name}"]`);
  if (!node.length) {
    // Gene not in current view — might be filtered out
    alert(`Gene ${name} is not currently visible. Check your type filters.`);
    return;
  }
  cy.animate({ center: { eles: node }, zoom: 2 }, { duration: 500 });
  highlightNode(name);
  openGeneDetail(name);
}

// ── Refresh stats badge ───────────────────────────────────────
async function refreshStatBadge() {
  try {
    const s = await fetchJSON('/api/stats');
    $('statPersonalitiesVal').textContent = s.cached_personalities;
  } catch (_) {}
}

// ── Helpers ───────────────────────────────────────────────────
function setLoaderSub(msg) {
  const el = $('loaderSub');
  if (el) el.textContent = msg;
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function postJSON(url, body = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
