#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║          🧬  GENESYS  v2.0                               ║
║  E. coli K-12 · Virtual Cell Simulation                  ║
║  ALL 4761 Gene Agents · Circular Chromosome Layout       ║
║  Cell Environment · Claude Personality · PPI Cascade     ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, random, time, math, csv, os, re, json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict

import anthropic
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d import Axes3D, proj3d
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np
from dotenv import load_dotenv

load_dotenv()

FONT_SCALE = 2.0
def fs(base: int) -> int:
    return max(6, int(base * FONT_SCALE))

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_FILE       = os.path.join(BASE_DIR, "k12info.csv")
PERS_CACHE_FILE = os.path.join(BASE_DIR, "personality_cache.json")

# ── Theme ─────────────────────────────────────────────────
BG_DARK   = "#060a14"
BG_CARD   = "#0c1220"
BG_INPUT  = "#141e2e"
BG_BORDER = "#1e2d44"
FG_TEXT   = "#e8f4fd"
FG_DIM    = "#8aa8c8"
ACCENT    = "#00e5ff"
SUCCESS   = "#00e676"
WARNING   = "#ffd740"
DANGER    = "#ff5252"
PURPLE    = "#b39ddb"

# ── Gene type config ──────────────────────────────────────
TYPE_CONFIG = {
    "CDS":            {"color": "#4fc3f7", "marker": "o",  "label": "Protein (CDS)"},
    "tRNA":           {"color": "#a5d6a7", "marker": "^",  "label": "tRNA"},
    "rRNA":           {"color": "#ef9a9a", "marker": "s",  "label": "rRNA"},
    "ncRNA":          {"color": "#ffcc80", "marker": "D",  "label": "ncRNA"},
    "mobile_element": {"color": "#f48fb1", "marker": "*",  "label": "Mobile Element"},
    "gene":           {"color": "#80deea", "marker": "h",  "label": "Gene/Pseudo"},
    "misc_feature":   {"color": "#bcaaa4", "marker": "p",  "label": "Misc Feature"},
    "rep_origin":     {"color": "#ffe082", "marker": "8",  "label": "Rep. Origin"},
}

OPERON_PALETTE = [
    "#b39ddb","#f48fb1","#ffe082","#80cbc4","#ff8a65","#ce93d8","#80deea",
    "#a5d6a7","#fff59d","#ffab91","#b2dfdb","#b3e5fc","#e1bee7","#fce4ec",
    "#dcedc8","#f0f4c3","#e8f5e9","#e3f2fd","#ede7f6","#fbe9e7",
]

# ── Environment baseline ──────────────────────────────────
ENV_BASELINE = {
    "pH":          7.0,
    "temperature": 37.0,
    "glucose":     1.0,
    "nacl":        300.0,
    "h2o2":        0.0,
    "oxygen":      1.0,   # 0=anaerobic, 1=aerobic
    "iron":        1.0,   # 0=depleted, 1=normal, 2=excess
    "nitrogen":    1.0,   # 0=starved, 1=normal
    "antibiotic":  0,     # 0=none … see ANTIBIOTIC_NAMES
    "sos":         0.0,   # DNA damage level 0-1
    "ethanol":     0.0,   # 0-2
    "phosphate":   1.0,   # 0=depleted, 1=normal
    # ── new parameters ──────────────────────────────────────
    "magnesium":   1.0,   # 0=depleted, 1=normal, 2=excess
    "potassium":   1.0,   # 0=low, 1=normal
    "heavy_metal": 0.0,   # 0=none, 1=toxic (Hg, Cd, As…)
    "bile":        0.0,   # 0=none, 1=gut-level bile salts
}

ANTIBIOTIC_NAMES = {0: "None", 1: "Ampicillin", 2: "Tetracycline",
                    3: "Chloramphenicol", 4: "Ciprofloxacin",
                    5: "Kanamycin", 6: "Rifampicin", 7: "Trimethoprim"}

# ── Stress keywords → GO/function text ───────────────────
STRESS_KEYWORDS: Dict[str, List[str]] = {
    "pH_acid":       ["acid", "glutamate decarboxylase", "acid resistance", "proton", "low ph", "gad"],
    "pH_base":       ["alkalin", "base stress", "high ph", "alkaline"],
    "heat":          ["heat shock", "chaperone", "protein folding", "hsp", "dnak", "groel", "groes",
                      "dnaj", "htpg", "thermal stress"],
    "cold":          ["cold shock", "cold stress", "csp", "cold-inducible"],
    "osmotic":       ["osmotic", "osmoprotect", "betaine", "trehalose", "osmo", "salt stress",
                      "kdp", "proU", "otsA", "otsB"],
    "glucose_up":    ["glucose", "glycolysis", "pts", "sugar transport", "carbon catabolite",
                      "phosphotransferase"],
    "glucose_dn":    ["carbon starvation", "gluconeogenesis", "alternative carbon", "camp",
                      "crp", "catabolite activator"],
    "anaerobic":     ["anaerob", "fermentation", "nitrate reductase", "fumarate", "fnr",
                      "arc", "electron acceptor", "anaerobic respiration", "nitrate"],
    "aerobic":       ["aerob", "cytochrome", "oxidative phosphorylation", "electron transport",
                      "respiration", "oxygen"],
    "oxidative":     ["oxidative", "peroxide", "catalase", "superoxide", "reactive oxygen",
                      "h2o2", "alkyl hydroperoxide", "oxyR", "soxRS", "katE", "katG"],
    "iron_low":      ["iron", "fur", "siderophore", "enterobactin", "iron acquisition",
                      "iron transport", "iron-sulfur", "feo"],
    "nitrogen_low":  ["nitrogen", "amino acid biosynthesis", "ammonia", "ntr", "glutamine",
                      "glnA", "nitrogen starvation", "nac"],
    "amp":           ["beta-lactam", "cell wall", "peptidoglycan", "murA", "ampC",
                      "penicillin", "beta-lactamase", "cell wall synthesis"],
    "tet":           ["ribosome", "30s", "50s", "translation", "tetracycline",
                      "drug resistance", "efflux"],
    "cam":           ["50s ribosomal", "peptidyl transfer", "chloramphenicol",
                      "ribosome", "translation", "elongation factor"],
    "cipro":         ["dna gyrase", "topoisomerase", "dna replication", "gyrA", "gyrB",
                      "parC", "dna damage", "sos"],
    "sos":           ["sos response", "dna repair", "recA", "lexA", "sulA", "recN",
                      "umuC", "umuD", "dna damage", "mutagenesis"],
    "ethanol":       ["ethanol", "alcohol", "membrane stress", "fatty acid",
                      "membrane fluidity"],
    "phosphate_low": ["phosphate", "pho regulon", "phoB", "phoR", "phosphate starvation",
                      "alkaline phosphatase"],
    "magnesium_low": ["magnesium", "mg2+", "phop", "phoq", "mgt", "magnesium transport",
                      "two-component", "antimicrobial peptide resistance"],
    "potassium_low": ["potassium", "kdp", "trk", "k+", "turgor", "osmosensing",
                      "potassium transport"],
    "heavy_metal":   ["heavy metal", "mercury", "cadmium", "arsenic", "zinc",
                      "metal resistance", "mer operon", "ars operon", "czc",
                      "metal efflux", "metallothionein", "copper"],
    "bile":          ["bile", "bile salt", "outer membrane", "efflux pump", "tolC",
                      "acrAB", "marA", "detergent", "amphipathic", "membrane integrity",
                      "lipopolysaccharide", "lps"],
    "kan":           ["aminoglycoside", "30s ribosome", "mistranslation", "membrane",
                      "aminoglycoside resistance", "aac", "ant", "aph"],
    "rif":           ["rna polymerase", "rpoB", "transcription", "rifampicin",
                      "rna synthesis"],
    "tmp":           ["dihydrofolate", "folate", "thymine", "purines", "thyA",
                      "one-carbon", "tetrahydrofolate"],
    "general":       ["stress", "response", "sigma", "stationary phase", "rpoS",
                      "general stress", "sigma s"],
}

MOCK_REACTIONS: Dict[str, List[str]] = {
    "activated":  [
        "Transcription rate surges — mobilising cellular machinery.",
        "Expression level elevated: responding to environmental signal.",
        "Gene induced — producing protein at accelerated rate.",
        "Regulatory cascade activates this locus.",
        "Upregulated to restore cell homeostasis.",
        "mRNA synthesis increased in response to stressor.",
    ],
    "repressed":  [
        "Transcription suppressed — energy conservation mode.",
        "Expression silenced by regulatory repressor.",
        "Gene downregulated: non-essential under current conditions.",
        "Repressor binding blocks promoter — gene silenced.",
        "Resource allocation shifts away from this gene.",
        "Feedback inhibition reduces expression level.",
    ],
    "neutral":    [
        "Maintaining baseline expression — not a primary responder.",
        "Stable transcription: gene unaffected by this stressor.",
        "No significant change in activity detected.",
        "Homeostatic regulation keeps expression constant.",
    ],
    "propagated": [
        "Activity shifted via PPI cascade from direct responder.",
        "Co-regulated with primary response partner.",
        "Operon-level co-expression change propagated.",
        "Indirect regulatory signal received through network.",
        "Secondary response: PPI partner transmitted signal.",
    ],
}

SIM_INTERVAL = 4.0
GENOME_SIZE  = 4_639_675   # E. coli K-12 MG1655 genome size (bp)

# ──────────────────────────────────────────────────────────
#  DATA LOADING
# ──────────────────────────────────────────────────────────
def load_genes() -> List[Dict]:
    with open(DATA_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def detect_operons(genes: List[Dict]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for g in genes:
        name = g["Gene_Name"]
        if len(name) > 1:
            groups[name[:-1]].append(name)
    return {k: v for k, v in groups.items() if len(v) >= 2}

def parse_ppi(ppi_str: str) -> List[Dict]:
    result = []
    if not ppi_str:
        return result
    for part in ppi_str.split(","):
        m = re.match(r"(\S+)\s*\(([0-9.]+)\)", part.strip())
        if m:
            result.append({"name": m.group(1), "score": float(m.group(2))})
    return result

def load_personality_cache() -> Dict:
    if os.path.exists(PERS_CACHE_FILE):
        with open(PERS_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_personality_cache(cache: Dict):
    with open(PERS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

# ──────────────────────────────────────────────────────────
#  GENE AGENT
# ──────────────────────────────────────────────────────────
@dataclass
class GeneAgent:
    gene_name:    str
    locus_tag:    str
    gene_type:    str
    strand:       str
    start:        int
    end:          int
    length:       int
    unit:         str
    product:      str
    function:     str
    subcell:      str
    mini_review:  str
    go_bp:        str
    go_mf:        str
    go_cc:        str
    mw_da:                float
    protein_abundance_ppm:float
    max_size_a:           float
    radius_gyr:   float
    dimensions:   str
    uniprot_id:   str
    gene_id:      str
    protein_id:   str
    kegg_def:     str
    kegg_pathways:str
    kegg_ko:      str
    kegg_brite:   str
    ppi_partners: List[Dict] = field(default_factory=list)
    ppi_count:    int        = 0
    operon:       str        = ""
    # Simulation state
    activity:     float      = 0.0   # -1 repressed → 0 baseline → +1 induced
    prev_activity:float      = 0.0   # for delta detection
    last_reaction:str        = ""
    memory:       List[str]  = field(default_factory=list)
    rounds_active:int        = 0
    personality:  str        = ""
    sensitivity:  Dict[str, float] = field(default_factory=dict)
    # Precomputed 3D position (set by engine)
    cx: float = 0.0
    cy: float = 0.0
    cz: float = 0.0

    @property
    def mid_pos(self) -> int:
        return (self.start + self.end) // 2

    @property
    def activity_label(self) -> str:
        if self.activity > 0.6:  return "Highly Induced ▲▲"
        if self.activity > 0.2:  return "Induced ▲"
        if self.activity < -0.6: return "Highly Repressed ▼▼"
        if self.activity < -0.2: return "Repressed ▼"
        return "Baseline ─"

    @property
    def type_cfg(self) -> Dict:
        return TYPE_CONFIG.get(self.gene_type, {"color": "#90a4ae", "marker": "o", "label": "?"})

    def compute_sensitivity(self):
        text = " ".join([
            self.function.lower(),
            self.go_bp.lower(),
            self.go_mf.lower(),
            self.mini_review.lower(),
            self.product.lower(),
            self.kegg_ko.lower(),
        ])
        for stressor, keywords in STRESS_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text)
            self.sensitivity[stressor] = min(1.0, hits * 0.30)

    def record(self, msg: str):
        self.last_reaction = msg
        self.memory.append(msg)
        if len(self.memory) > 10:
            self.memory.pop(0)


# ──────────────────────────────────────────────────────────
#  CLAUDE CLIENT
# ──────────────────────────────────────────────────────────
class ClaudeClient:
    def __init__(self):
        self._client = None

    def _get(self):
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def generate_reaction(self, agent: GeneAgent, env_change: str) -> str:
        pers = agent.personality or f"Gene {agent.gene_name}: {agent.product}. Function: {agent.function or agent.go_bp or 'Unknown'}"
        prompt = (
            f"You are gene {agent.gene_name} in E. coli K-12 — a molecular citizen in the cell.\n"
            f"Your identity: {pers}\n"
            f"Your current activity: {agent.activity:+.2f} ({agent.activity_label})\n"
            f"Cell environment changed: {env_change}\n\n"
            f"Respond in 1-2 sentences from the gene's perspective. Be scientifically accurate."
        )
        try:
            msg = self._get().messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=100,
                messages=[{"role": "user", "content": prompt}])
            return msg.content[0].text.strip()
        except Exception:
            return ClaudeClient._mock(agent)

    def generate_personality(self, agent: GeneAgent) -> str:
        prompt = (
            f"Create a 3-sentence personality for gene {agent.gene_name} in E. coli K-12 "
            f"as a citizen in a living cell-city.\n"
            f"Product: {agent.product}\nFunction: {agent.function or 'Unknown'}\n"
            f"GO BP: {agent.go_bp or 'Unknown'}\nGO MF: {agent.go_mf or 'Unknown'}\n"
            f"Mini Review: {agent.mini_review or 'Unknown'}\n\n"
            "1) their job/role, 2) personality traits, 3) how they work with others. "
            "No headers, just 3 sentences."
        )
        try:
            msg = self._get().messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=250,
                messages=[{"role": "user", "content": prompt}])
            return msg.content[0].text.strip()
        except Exception:
            return f"{agent.gene_name} works as a molecular specialist in the E. coli cell."

    def generate_environment(self, prompt: str) -> str:
        try:
            msg = self._get().messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=512,
                messages=[{"role": "user", "content": prompt}])
            return msg.content[0].text.strip()
        except Exception as ex:
            raise RuntimeError(f"Claude API error: {ex}") from ex

    @staticmethod
    def _mock(agent: GeneAgent) -> str:
        if agent.activity > 0.2:  return random.choice(MOCK_REACTIONS["activated"])
        if agent.activity < -0.2: return random.choice(MOCK_REACTIONS["repressed"])
        return random.choice(MOCK_REACTIONS["neutral"])


# ──────────────────────────────────────────────────────────
#  OLLAMA CLIENT  (local LLM — llama3 or any pulled model)
# ──────────────────────────────────────────────────────────
class OllamaClient:
    """Talks to a local Ollama server at http://localhost:11434."""

    def __init__(self, model: str = "llama3"):
        self.model = model

    # ── low-level HTTP helper ──────────────────────────────
    def _chat(self, prompt: str) -> str:
        import urllib.request as _urllib
        import json as _json
        payload = _json.dumps({
            "model":    self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream":   False,
        }).encode()
        req = _urllib.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with _urllib.urlopen(req, timeout=90) as r:
            data = _json.loads(r.read())
        return data["message"]["content"].strip()

    # ── public interface (mirrors ClaudeClient) ────────────
    def generate_reaction(self, agent: "GeneAgent", env_change: str) -> str:
        pers = agent.personality or f"Gene {agent.gene_name}: {agent.product}. Function: {agent.function or 'Unknown'}"
        prompt = (
            f"You are gene {agent.gene_name} in E. coli K-12 — a molecular citizen in the cell.\n"
            f"Your identity: {pers}\n"
            f"Your current activity: {agent.activity:+.2f} ({agent.activity_label})\n"
            f"Cell environment changed: {env_change}\n\n"
            "Respond in 1-2 sentences from the gene's perspective. Be scientifically accurate."
        )
        try:
            return self._chat(prompt)
        except Exception:
            return ClaudeClient._mock(agent)

    def generate_personality(self, agent: "GeneAgent") -> str:
        prompt = (
            f"Create a 3-sentence personality for gene {agent.gene_name} in E. coli K-12 "
            f"as a citizen in a living cell-city.\n"
            f"Product: {agent.product}\nFunction: {agent.function or 'Unknown'}\n"
            f"GO BP: {agent.go_bp or 'Unknown'}\nGO MF: {agent.go_mf or 'Unknown'}\n"
            f"Mini Review: {agent.mini_review or 'Unknown'}\n\n"
            "1) their job/role, 2) personality traits, 3) how they work with others. "
            "No headers, just 3 sentences."
        )
        try:
            return self._chat(prompt)
        except Exception:
            return f"{agent.gene_name} works as a molecular specialist in the E. coli cell."

    def generate_environment(self, prompt: str) -> str:
        try:
            return self._chat(prompt)
        except Exception as ex:
            raise RuntimeError(f"Ollama error (is Ollama running?): {ex}") from ex


# ──────────────────────────────────────────────────────────
#  SIMULATION ENGINE
# ──────────────────────────────────────────────────────────
class SimulationEngine:
    def __init__(self, update_cb, feed_cb):
        self.all_genes:    List[GeneAgent] = []
        self.gene_map:     Dict[str, GeneAgent] = {}
        self.operons:      Dict[str, List[str]] = {}
        self.operon_colors:Dict[str, str] = {}
        self.graph:        nx.Graph = nx.Graph()
        self.round:        int = 0
        self.running:      bool = False
        self.interval:     float = SIM_INTERVAL
        self.cell_env:     Dict = dict(ENV_BASELINE)
        self.last_env:     Dict = dict(ENV_BASELINE)
        self.env_changed:  str = ""
        self.use_llm:      bool = False
        self.llm_backend:  str  = "claude"   # "claude" | "ollama"
        self.claude        = ClaudeClient()
        self.ollama_client: Optional[OllamaClient] = None
        self._update_cb    = update_cb
        self._feed_cb      = feed_cb
        self._thread:      Optional[threading.Thread] = None
        self.pers_cache:   Dict = load_personality_cache()
        self.last_active:  Set[str] = set()   # gene names that just changed
        self.last_edges:   List[Tuple] = []   # edges to draw this round

    @property
    def active_llm(self):
        """Return the currently selected LLM client."""
        if self.llm_backend == "ollama":
            if self.ollama_client is None:
                self.ollama_client = OllamaClient("llama3")
            return self.ollama_client
        return self.claude

    # ── Build ──────────────────────────────────────────────
    def build(self):
        self.all_genes.clear()
        self.gene_map.clear()
        self.graph.clear()
        self.round = 0
        self.cell_env = dict(ENV_BASELINE)
        self.last_env = dict(ENV_BASELINE)
        self.last_active.clear()
        self.last_edges.clear()

        raw = load_genes()
        operons = detect_operons(raw)
        self.operons = operons

        op_list = sorted(operons.keys())
        self.operon_colors = {
            op: OPERON_PALETTE[i % len(OPERON_PALETTE)]
            for i, op in enumerate(op_list)
        }
        gene_to_operon: Dict[str, str] = {}
        for op, members in operons.items():
            for m in members:
                gene_to_operon[m] = op

        for row in raw:
            ppi = parse_ppi(row.get("PPI_Partners", ""))
            try:
                start = int(row.get("Start") or 0)
                end   = int(row.get("End") or 0)
            except (ValueError, TypeError):
                start = end = 0
            agent = GeneAgent(
                gene_name    = row["Gene_Name"],
                locus_tag    = row["Locus_Tag"],
                gene_type    = row["Type"],
                strand       = row.get("Strand", "1"),
                start        = start,
                end          = end,
                length       = int(row.get("Length") or 0),
                unit         = row.get("Unit", ""),
                product      = row.get("Product", ""),
                function     = row.get("Function", ""),
                subcell      = row.get("Subcellular_Location", ""),
                mini_review  = row.get("Mini_Review_Summary", ""),
                go_bp        = row.get("GO_Biological_Process", ""),
                go_mf        = row.get("GO_Molecular_Function", ""),
                go_cc        = row.get("GO_Cellular_Component", ""),
                mw_da                = float(row.get("Molecular_Weight_Da") or 0),
                protein_abundance_ppm= float(row.get("Protein_Abundance_PPM") or 0),
                max_size_a           = float(row.get("Max_Size_A") or 0),
                radius_gyr   = float(row.get("Radius_of_Gyration_A") or 0),
                dimensions   = row.get("Dimensions_XYZ_A", ""),
                uniprot_id   = row.get("UniProt_ID", ""),
                gene_id      = row.get("GeneID", ""),
                protein_id   = row.get("Protein_ID", ""),
                kegg_def     = row.get("KEGG_Definition", ""),
                kegg_pathways= row.get("KEGG_Pathways", ""),
                kegg_ko      = row.get("KEGG_KO_Meaning", ""),
                kegg_brite   = row.get("KEGG_BRITE_Meaning", ""),
                ppi_partners = ppi,
                ppi_count    = int(row.get("PPI_Count") or 0),
                operon       = gene_to_operon.get(row["Gene_Name"], ""),
                personality  = self.pers_cache.get(row["Gene_Name"], ""),
            )
            agent.compute_sensitivity()
            self.all_genes.append(agent)
            self.gene_map[agent.gene_name] = agent

        # Build full PPI graph
        for g in self.all_genes:
            self.graph.add_node(g.gene_name)
        for g in self.all_genes:
            for p in g.ppi_partners:
                if p["name"] in self.gene_map:
                    self.graph.add_edge(g.gene_name, p["name"],
                                        etype="ppi", score=p["score"])
            if g.operon:
                for other in self.operons.get(g.operon, []):
                    if other != g.gene_name and other in self.gene_map:
                        if not self.graph.has_edge(g.gene_name, other):
                            self.graph.add_edge(g.gene_name, other,
                                                etype="operon", score=1.0)

        # Compute 2D cell positions + pre-compute edge arrays
        self._compute_cell_positions()
        self._precompute_edges()

    # ── Cell-interior layout ──────────────────────────────
    def _compute_cell_positions(self):
        """
        Place every gene inside the cell based on subcellular location.
        Zones (radius):  outer membrane 0.82-0.93 | periplasm 0.63-0.78
                         inner membrane 0.48-0.62  | cytoplasm 0.06-0.44
        Operon members are pulled toward each other after initial placement.
        """
        ZONES = {
            "outer membrane":       (0.83, 0.93),
            "cell outer membrane":  (0.83, 0.93),
            "outer":                (0.80, 0.93),
            "periplasm":            (0.64, 0.78),
            "plasma membrane":      (0.49, 0.62),
            "inner membrane":       (0.49, 0.62),
            "membrane":             (0.46, 0.65),
            "ribosome":             (0.12, 0.38),
            "cytosol":              (0.07, 0.43),
            "cytoplasm":            (0.07, 0.43),
            "nucleoid":             (0.04, 0.22),
        }
        rng = random.Random(42)

        for g in self.all_genes:
            loc = g.subcell.lower()
            r_min, r_max = 0.18, 0.52  # default (unknown)
            for key, (r1, r2) in ZONES.items():
                if key in loc:
                    r_min, r_max = r1, r2
                    break
            r     = rng.uniform(r_min, r_max)
            theta = rng.uniform(0, 2 * math.pi)   # azimuthal
            phi   = rng.uniform(0, math.pi)         # polar
            # E. coli rod shape: stretch along x axis
            g.cx = r * math.sin(phi) * math.cos(theta) * 1.25
            g.cy = r * math.sin(phi) * math.sin(theta)
            g.cz = r * math.cos(phi)

        # Pull operon family members toward their cluster centroid (4 passes)
        for _ in range(4):
            for op, members in self.operons.items():
                op_genes = [self.gene_map[m] for m in members if m in self.gene_map]
                if len(op_genes) < 2:
                    continue
                cx_c = sum(g.cx for g in op_genes) / len(op_genes)
                cy_c = sum(g.cy for g in op_genes) / len(op_genes)
                cz_c = sum(g.cz for g in op_genes) / len(op_genes)
                for g in op_genes:
                    g.cx = g.cx * 0.55 + cx_c * 0.45
                    g.cy = g.cy * 0.55 + cy_c * 0.45
                    g.cz = g.cz * 0.55 + cz_c * 0.45
                    # Clamp inside cell ellipsoid
                    r = math.sqrt((g.cx / 1.25) ** 2 + g.cy ** 2 + g.cz ** 2)
                    if r > 0.96:
                        scale = 0.93 / r
                        g.cx *= scale
                        g.cy *= scale
                        g.cz *= scale

    def _precompute_edges(self):
        """Build LineCollection-ready segment arrays once after build."""
        # PPI edges (all, for dim background layer)
        seen = set()
        ppi_segs, ppi_alphas = [], []
        for g in self.all_genes:
            for p in g.ppi_partners:
                partner = self.gene_map.get(p["name"])
                if partner:
                    key = tuple(sorted([g.gene_name, partner.gene_name]))
                    if key not in seen:
                        seen.add(key)
                        ppi_segs.append([(g.cx, g.cy, g.cz), (partner.cx, partner.cy, partner.cz)])
                        ppi_alphas.append(min(1.0, p["score"]))
        self._ppi_segs   = ppi_segs
        self._ppi_alphas = ppi_alphas

        # Operon edges grouped by colour
        op_by_col: Dict[str, List] = defaultdict(list)
        for op, members in self.operons.items():
            col      = self.operon_colors.get(op, PURPLE)
            op_genes = [self.gene_map[m] for m in members if m in self.gene_map]
            for i, a in enumerate(op_genes):
                for b in op_genes[i + 1:]:
                    op_by_col[col].append([(a.cx, a.cy, a.cz), (b.cx, b.cy, b.cz)])
        self._op_by_col = dict(op_by_col)

    # ── Environment injection ─────────────────────────────
    def inject_environment(self, new_env: Dict, description: str):
        self.last_env  = dict(self.cell_env)
        self.cell_env  = dict(new_env)
        self.env_changed = description
        sep = "═" * 58
        self._feed_cb(f"\n{sep}\n🌡  ENV CHANGE:  {description}\n{sep}\n", "env")
        threading.Thread(target=self._react_to_environment, daemon=True).start()

    def _react_to_environment(self):
        delta = {k: self.cell_env.get(k, 0) - self.last_env.get(k, 0)
                 for k in ENV_BASELINE}

        # Determine active stressors with strength
        stressors: Dict[str, float] = {}
        ph = self.cell_env["pH"]
        if ph < 6.5:   stressors["pH_acid"]      = min(1.0, (6.5  - ph)   / 6.5)
        if ph > 7.5:   stressors["pH_base"]      = min(1.0, (ph   - 7.5)  / 6.5)
        temp = self.cell_env["temperature"]
        dt   = delta["temperature"]
        if temp > 42:  stressors["heat"]         = min(1.0, (temp - 42)   / 79.0)
        elif dt > 1.5: stressors["heat"]         = min(1.0, dt            / 20.0)
        if temp < 10:  stressors["cold"]         = min(1.0, (10   - temp) / 15.0)
        elif dt < -1.5:stressors["cold"]         = min(1.0, abs(dt)       / 20.0)
        nacl = self.cell_env["nacl"]
        if nacl > 350: stressors["osmotic"]      = min(1.0, (nacl - 350)  / 4650.0)
        dg = delta["glucose"]
        if dg > 0.3:   stressors["glucose_up"]   = min(1.0, dg            / 10.0)
        if dg < -0.3:  stressors["glucose_dn"]   = min(1.0, abs(dg)       / 5.0)
        h2o2 = self.cell_env["h2o2"]
        if h2o2 > 0.05:stressors["oxidative"]    = min(1.0, h2o2          / 20.0)
        oxy = self.cell_env["oxygen"]
        if oxy < 0.3:  stressors["anaerobic"]    = min(1.0, (0.3 - oxy)   / 0.3)
        if oxy > 0.7:  stressors["aerobic"]      = min(1.0, oxy           / 2.0)
        iron = self.cell_env["iron"]
        if iron < 0.5: stressors["iron_low"]     = min(1.0, (0.5 - iron)  / 0.5)
        nit = self.cell_env["nitrogen"]
        if nit < 0.5:  stressors["nitrogen_low"] = min(1.0, (0.5 - nit)   / 0.5)
        ab = self.cell_env["antibiotic"]
        if ab == 1:    stressors["amp"]          = 1.0
        if ab == 2:    stressors["tet"]          = 1.0
        if ab == 3:    stressors["cam"]          = 1.0
        if ab == 4:    stressors["cipro"]        = 1.0
        sos = self.cell_env["sos"]
        if sos > 0.1:  stressors["sos"]          = sos
        eth = self.cell_env["ethanol"]
        if eth > 0.05: stressors["ethanol"]      = min(1.0, eth            / 10.0)
        phos = self.cell_env["phosphate"]
        if phos < 0.5: stressors["phosphate_low"]= min(1.0, (0.5 - phos)  / 0.5)
        mg = self.cell_env.get("magnesium", 1.0)
        if mg < 0.5:   stressors["magnesium_low"]= min(1.0, (0.5 - mg)    / 0.5)
        k  = self.cell_env.get("potassium", 1.0)
        if k  < 0.5:   stressors["potassium_low"]= min(1.0, (0.5 - k)     / 0.5)
        hm = self.cell_env.get("heavy_metal", 0.0)
        if hm > 0.1:   stressors["heavy_metal"]  = min(1.0, hm            / 3.0)
        bl = self.cell_env.get("bile", 0.0)
        if bl > 0.1:   stressors["bile"]         = min(1.0, bl            / 3.0)
        if ab == 5:    stressors["kan"]           = 1.0
        if ab == 6:    stressors["rif"]           = 1.0
        if ab == 7:    stressors["tmp"]           = 1.0
        if stressors:  stressors["general"]       = 0.25

        if not stressors:
            self._feed_cb("  (No significant stressor — slow decay to baseline)\n", "neutral")
            for g in self.all_genes:
                g.prev_activity = g.activity
                g.activity *= 0.6
            self.last_active.clear()
            self.last_edges.clear()
            self._update_cb()
            return

        # Score each gene
        gene_scores: List[Tuple[float, GeneAgent]] = []
        for g in self.all_genes:
            score = sum(g.sensitivity.get(s, 0) * strength
                        for s, strength in stressors.items())
            gene_scores.append((score, g))

        gene_scores.sort(key=lambda x: -x[0])

        # Top responders react directly
        n_direct = max(5, min(60, len(gene_scores) // 12))
        top_genes = [g for score, g in gene_scores if score > 0.08][:n_direct]
        # Also add a few random ones with tiny scores (biological noise)
        noise_pool = [g for score, g in gene_scores if 0 < score <= 0.08]
        top_genes += random.sample(noise_pool, min(10, len(noise_pool)))

        primary_set = set(g.gene_name for g in top_genes)
        self.last_active = set()
        self.last_edges = []

        threads = []
        for score, g in [(s, g) for s, g in gene_scores if g in top_genes]:
            # Direction: most genes activated by their specific stressor
            # A few housekeeping / growth genes get repressed during stress
            if any(kw in g.function.lower() + g.go_bp.lower()
                   for kw in ["biosynthesis", "growth", "cell division", "proliferat"]):
                direction = -0.5 * score
            else:
                direction = score
            t = threading.Thread(target=self._gene_react,
                                 args=(g, direction), daemon=True)
            threads.append(t); t.start()

        for t in threads:
            t.join(timeout=25)

        # PPI cascade — propagate to neighbors
        self._propagate_ppi(primary_set)

        # Collect active edges for drawing
        active_genes_for_edges = [g for g in self.all_genes
                                   if g.gene_name in self.last_active][:30]
        edges_set = set()
        for g in active_genes_for_edges:
            for p in g.ppi_partners[:5]:
                pname = p["name"]
                if pname in self.gene_map:
                    key = tuple(sorted([g.gene_name, pname]))
                    if key not in edges_set:
                        edges_set.add(key)
                        self.last_edges.append((g.gene_name, pname,
                                                "ppi", p["score"]))
            if g.operon:
                for oname in self.operons.get(g.operon, [])[:3]:
                    if oname != g.gene_name and oname in self.gene_map:
                        key = tuple(sorted([g.gene_name, oname]))
                        if key not in edges_set:
                            edges_set.add(key)
                            self.last_edges.append((g.gene_name, oname, "operon", 1.0))

        n_ind = sum(1 for g in self.all_genes if g.activity > 0.2)
        n_rep = sum(1 for g in self.all_genes if g.activity < -0.2)
        self._feed_cb(
            f"  ▶ {len(self.last_active)} genes reacted  |  "
            f"{n_ind} induced  |  {n_rep} repressed  |  "
            f"{len(self.last_edges)} connections shown\n\n", "round")
        self._update_cb()

    def _gene_react(self, g: GeneAgent, direction: float):
        g.prev_activity = g.activity
        delta = direction * 0.75 + random.gauss(0, 0.05)
        g.activity = max(-1.0, min(1.0, g.activity + delta))
        g.rounds_active += 1
        self.last_active.add(g.gene_name)

        if self.use_llm:
            reaction = self.active_llm.generate_reaction(g, self.env_changed)
        else:
            if g.activity > 0.2:   reaction = random.choice(MOCK_REACTIONS["activated"])
            elif g.activity < -0.2: reaction = random.choice(MOCK_REACTIONS["repressed"])
            else:                   reaction = random.choice(MOCK_REACTIONS["neutral"])
        g.record(reaction)

        tag = "positive" if g.activity > 0.15 else "negative" if g.activity < -0.15 else "neutral"
        self._feed_cb(
            f"  [{g.gene_type:4s}] {g.gene_name:10s}  "
            f"{g.prev_activity:+.2f} → {g.activity:+.2f}  "
            f"({g.activity_label.split()[0]})\n"
            f"    ↳ {reaction}\n",
            tag,
        )

    def _propagate_ppi(self, primary: Set[str]):
        """Second-degree propagation through PPI & operon connections."""
        secondary = []
        for g in self.all_genes:
            if g.gene_name in primary:
                continue
            signal = 0.0
            for p in g.ppi_partners:
                partner = self.gene_map.get(p["name"])
                if partner and partner.gene_name in primary:
                    signal += partner.activity * p["score"] * 0.35
            if abs(signal) > 0.04:
                secondary.append((g, signal))

        for g, signal in secondary:
            g.prev_activity = g.activity
            g.activity = max(-1.0, min(1.0, g.activity + signal))
            self.last_active.add(g.gene_name)
            g.record(random.choice(MOCK_REACTIONS["propagated"]))
            if abs(signal) > 0.12:
                tag = "positive" if g.activity > 0 else "negative"
                self._feed_cb(
                    f"  [PPI↗] {g.gene_name:10s}  {g.prev_activity:+.2f} → {g.activity:+.2f}\n",
                    tag,
                )

        # Operon co-regulation
        for op, members in self.operons.items():
            op_agents = [self.gene_map[m] for m in members if m in self.gene_map]
            primary_in_op = [g for g in op_agents if g.gene_name in primary]
            if primary_in_op:
                avg = float(np.mean([g.activity for g in primary_in_op]))
                for g in op_agents:
                    if g.gene_name not in primary:
                        g.prev_activity = g.activity
                        g.activity = max(-1.0, min(1.0,
                            g.activity + (avg - g.activity) * 0.35))
                        if abs(g.activity - g.prev_activity) > 0.1:
                            self.last_active.add(g.gene_name)

    # ── Simulation loop ────────────────────────────────────
    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            self._run_round()
            elapsed = 0.0
            while self.running and elapsed < self.interval:
                time.sleep(0.25); elapsed += 0.25

    def _run_round(self):
        self.round += 1
        ts = datetime.now().strftime("%H:%M:%S")
        self._feed_cb(f"\n── Round {self.round}  {ts} ──\n", "round")
        # Slow decay toward baseline + noise
        for g in self.all_genes:
            g.prev_activity = g.activity
            g.activity *= 0.80
            noise = random.gauss(0, 0.02)
            g.activity = max(-1.0, min(1.0, g.activity + noise))
        # Fade last_active so only truly changed genes remain highlighted
        self.last_active = {n for n in self.last_active
                            if abs(self.gene_map[n].activity) > 0.15}
        # Rebuild active edges from current last_active
        self.last_edges = []
        for name in list(self.last_active)[:20]:
            g = self.gene_map.get(name)
            if not g:
                continue
            for p in g.ppi_partners[:3]:
                if p["name"] in self.gene_map:
                    self.last_edges.append((name, p["name"], "ppi", p["score"]))
        self._update_cb()

    def ensure_personality(self, agent: GeneAgent):
        if agent.personality:
            return
        if agent.gene_name in self.pers_cache:
            agent.personality = self.pers_cache[agent.gene_name]
            return
        p = self.active_llm.generate_personality(agent)
        agent.personality = p
        self.pers_cache[agent.gene_name] = p
        save_personality_cache(self.pers_cache)

    def stats(self) -> Dict:
        if not self.all_genes:
            return {}
        acts = [g.activity for g in self.all_genes]
        ab_name = ANTIBIOTIC_NAMES.get(int(self.cell_env.get("antibiotic", 0)), "None")
        oxy_label = "Aerobic" if self.cell_env["oxygen"] > 0.5 else "Anaerobic"
        return {
            "Total Genes":   len(self.all_genes),
            "Round":         self.round,
            "Induced":       sum(1 for a in acts if a > 0.2),
            "Repressed":     sum(1 for a in acts if a < -0.2),
            "Highly Active": sum(1 for a in acts if abs(a) > 0.6),
            "Baseline":      sum(1 for a in acts if -0.2 <= a <= 0.2),
            "Operons":       len(self.operons),
            "pH":            f"{self.cell_env['pH']:.1f}",
            "Temp °C":       f"{self.cell_env['temperature']:.1f}",
            "Glucose mM":    f"{self.cell_env['glucose']:.2f}",
            "NaCl mOsm":     f"{self.cell_env['nacl']:.0f}",
            "H₂O₂":         f"{self.cell_env['h2o2']:.2f}",
            "Oxygen":        oxy_label,
            "Iron":          f"{self.cell_env['iron']:.1f}",
            "Antibiotic":    ab_name,
            "SOS level":     f"{self.cell_env['sos']:.2f}",
        }


# ──────────────────────────────────────────────────────────
#  APPLICATION
# ──────────────────────────────────────────────────────────
class GenesysApp(tk.Tk):
    COLOR_MODES = ["Activity", "Gene Type", "Operon Family", "Subcell. Location"]

    def __init__(self):
        super().__init__()
        self.title("GENESYS v2.0  |  E. coli K-12 — All 4761 Gene Agents")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.state("zoomed")          # maximize on Windows

        self._selected:   Optional[GeneAgent] = None
        self._node_pos:   Dict[str, Tuple[float, float]] = {}
        self._zoom_level:  float = 1.0
        self._node_scale:  float = 1.0
        self._view_center: list  = [0.0, 0.0, 0.0]
        self._ax_dist:     float = 10.0   # camera distance (scroll zoom)

        self._speed_var      = tk.DoubleVar(value=SIM_INTERVAL)
        self._llm_var        = tk.BooleanVar(value=False)
        self._llm_backend_var= tk.StringVar(value="claude")   # "claude" | "ollama"
        self._ollama_model_var = tk.StringVar(value="llama3")
        self._color_mode = tk.StringVar(value="Activity")
        self._show_ppi   = tk.BooleanVar(value=True)
        self._show_op    = tk.BooleanVar(value=True)
        self._show_labels= tk.BooleanVar(value=True)

        # Environment sliders
        self._ph_var    = tk.DoubleVar(value=7.0)
        self._temp_var  = tk.DoubleVar(value=37.0)
        self._glc_var   = tk.DoubleVar(value=1.0)
        self._nacl_var  = tk.DoubleVar(value=300.0)
        self._h2o2_var  = tk.DoubleVar(value=0.0)
        self._oxy_var   = tk.DoubleVar(value=1.0)
        self._iron_var  = tk.DoubleVar(value=1.0)
        self._nit_var   = tk.DoubleVar(value=1.0)
        self._sos_var   = tk.DoubleVar(value=0.0)
        self._eth_var   = tk.DoubleVar(value=0.0)
        self._phos_var  = tk.DoubleVar(value=1.0)
        self._mg_var    = tk.DoubleVar(value=1.0)
        self._k_var     = tk.DoubleVar(value=1.0)
        self._hm_var    = tk.DoubleVar(value=0.0)
        self._bile_var  = tk.DoubleVar(value=0.0)
        self._ab_var    = tk.IntVar(value=0)

        self._build_ui()
        self.engine = SimulationEngine(
            update_cb=lambda: self.after(0, self._refresh),
            feed_cb=self._append_feed,
        )
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._status("GENESYS v2 ready — click  Build Cell  to load all 4761 gene agents")

    # ══════════════════════════════════════════
    #  UI LAYOUT
    # ══════════════════════════════════════════
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_DARK)
        hdr.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(hdr, text="🧬 GENESYS", bg=BG_DARK, fg=ACCENT,
                 font=("Courier", fs(19), "bold")).pack(side="left")
        tk.Label(hdr, text="  E. coli K-12 Virtual Cell  ·  4761 Gene Agents  ·  Circular Chromosome",
                 bg=BG_DARK, fg=FG_DIM, font=("Courier", fs(8))).pack(side="left", padx=8)
        self._status_lbl = tk.Label(hdr, text="", bg=BG_DARK, fg=WARNING,
                                     font=("Courier", fs(8)))
        self._status_lbl.pack(side="right")

        tk.Frame(self, bg=BG_BORDER, height=1).pack(fill="x", padx=8, pady=3)

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        left = tk.Frame(body, bg=BG_CARD, width=340)
        left.pack(side="left", fill="y", padx=(0, 4))
        left.pack_propagate(False)
        self._build_left(left)

        center = tk.Frame(body, bg=BG_CARD)
        center.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self._build_center(center)

        right = tk.Frame(body, bg=BG_DARK, width=600)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)
        self._build_right(right)

    # ── LEFT PANEL ──────────────────────────────────────────
    def _build_left(self, p):
        def sec(title):
            tk.Label(p, text=title, bg=BG_CARD, fg=ACCENT,
                     font=("Courier", fs(10), "bold")).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Frame(p, bg=BG_BORDER, height=1).pack(fill="x", padx=8, pady=(2, 4))

        tk.Label(p, text="CELL CONTROL", bg=BG_CARD, fg=FG_TEXT,
                 font=("Courier", fs(16), "bold")).pack(pady=(12, 4))

        sec("SIMULATION SPEED")
        r2 = tk.Frame(p, bg=BG_CARD); r2.pack(fill="x", padx=8, pady=2)
        self._spd_lbl = tk.Label(r2, text="4s", bg=BG_CARD, fg=ACCENT,
                                  font=("Courier", fs(13), "bold"), width=4)
        self._spd_lbl.pack(side="right")
        ttk.Scale(r2, from_=1, to=20, variable=self._speed_var, orient="horizontal",
                  command=self._on_speed).pack(side="left", fill="x", expand=True)

        _ck = dict(bg=BG_CARD, fg=FG_TEXT, selectcolor=BG_CARD,
                   activebackground=BG_CARD, activeforeground=ACCENT,
                   font=("Courier", fs(9)))
        _rb = dict(bg=BG_CARD, fg=FG_TEXT, selectcolor=BG_CARD,
                   activebackground=BG_CARD, activeforeground=ACCENT,
                   font=("Courier", fs(9)))

        sec("LLM REACTIONS")
        tk.Checkbutton(p, text="Enable LLM (slower)",
                       variable=self._llm_var,
                       command=self._on_llm, **_ck).pack(anchor="w", padx=10)
        tk.Label(p, text="  Off = fast keyword mode",
                 bg=BG_CARD, fg=FG_DIM, font=("Courier", fs(9))).pack(anchor="w", padx=10)

        # Backend selector
        _llm_row = tk.Frame(p, bg=BG_CARD); _llm_row.pack(fill="x", padx=10, pady=2)
        tk.Radiobutton(_llm_row, text="Claude API",
                       variable=self._llm_backend_var, value="claude",
                       command=self._on_llm_backend, **_rb).pack(side="left")
        tk.Radiobutton(_llm_row, text="Ollama",
                       variable=self._llm_backend_var, value="ollama",
                       command=self._on_llm_backend, **_rb).pack(side="left", padx=(8, 0))

        # Ollama model name row (shown only when Ollama selected)
        self._ollama_row = tk.Frame(p, bg=BG_CARD)
        self._ollama_row.pack(fill="x", padx=10, pady=1)
        tk.Label(self._ollama_row, text="Model:", bg=BG_CARD, fg=FG_DIM,
                 font=("Courier", fs(9))).pack(side="left")
        tk.Entry(self._ollama_row, textvariable=self._ollama_model_var,
                 bg="#0d1a2a", fg=ACCENT, insertbackground=ACCENT,
                 font=("Courier", fs(10)), width=12,
                 relief="flat", bd=1).pack(side="left", padx=4)
        tk.Button(self._ollama_row, text="✓", bg="#1a3a1a", fg="#4dff88",
                  font=("Courier", fs(9)), relief="flat", cursor="hand2",
                  command=self._on_ollama_model_apply).pack(side="left")
        tk.Label(p, text="  llama3 / mistral / gemma2 …",
                 bg=BG_CARD, fg=FG_DIM, font=("Courier", fs(9))).pack(anchor="w", padx=10)

        # Test connection button + status label
        self._ollama_test_row = tk.Frame(p, bg=BG_CARD)
        self._ollama_test_row.pack(fill="x", padx=10, pady=2)
        tk.Button(self._ollama_test_row, text="🔌 Test Connection",
                  bg="#0d1a2a", fg=ACCENT, font=("Courier", fs(9)),
                  relief="flat", cursor="hand2",
                  command=self._on_ollama_test).pack(side="left")
        self._ollama_status_lbl = tk.Label(self._ollama_test_row,
                  text="●  not tested", bg=BG_CARD, fg=FG_DIM,
                  font=("Courier", fs(9)))
        self._ollama_status_lbl.pack(side="left", padx=8)

        self._refresh_ollama_row()

        sec("NODE SIZE")
        r_ns = tk.Frame(p, bg=BG_CARD); r_ns.pack(fill="x", padx=8, pady=2)
        self._ns_lbl = tk.Label(r_ns, text="1x", bg=BG_CARD, fg=ACCENT,
                                font=("Courier", fs(13), "bold"), width=4)
        self._ns_lbl.pack(side="right")
        self._ns_var = tk.DoubleVar(value=1.0)
        ttk.Scale(r_ns, from_=0.5, to=30.0, variable=self._ns_var, orient="horizontal",
                  command=self._on_node_scale).pack(side="left", fill="x", expand=True)

        sec("GRAPH VIEW")
        for mode in self.COLOR_MODES:
            tk.Radiobutton(p, text=mode, variable=self._color_mode,
                           value=mode, command=self._redraw_graph, **_rb).pack(
                anchor="w", padx=16, pady=1)
        tk.Checkbutton(p, text="Show PPI edges (active genes)",
                       variable=self._show_ppi,
                       command=self._redraw_graph, **_ck).pack(anchor="w", padx=10, pady=1)
        tk.Checkbutton(p, text="Show Operon edges",
                       variable=self._show_op,
                       command=self._redraw_graph, **_ck).pack(anchor="w", padx=10, pady=1)
        tk.Checkbutton(p, text="Show gene labels",
                       variable=self._show_labels,
                       command=self._redraw_graph, **_ck).pack(anchor="w", padx=10, pady=1)

        sec("ACTIONS")
        bcfg = dict(font=("Courier", fs(11), "bold"), relief="flat", cursor="hand2", pady=6)
        self._btn_build = tk.Button(p, text="⬡  Build Cell  (all 4761)",
                                     bg=BG_INPUT, fg=FG_TEXT,
                                     command=self._do_build, **bcfg)
        self._btn_build.pack(fill="x", padx=8, pady=2)
        self._btn_start = tk.Button(p, text="▶  Start Auto-Rounds",
                                     bg=SUCCESS, fg=BG_DARK,
                                     command=self._do_start, state="disabled", **bcfg)
        self._btn_start.pack(fill="x", padx=8, pady=2)
        self._btn_stop  = tk.Button(p, text="⏸  Pause",
                                     bg=DANGER, fg=FG_TEXT,
                                     command=self._do_stop, state="disabled", **bcfg)
        self._btn_stop.pack(fill="x", padx=8, pady=2)
        self._btn_reset = tk.Button(p, text="↺  Reset",
                                     bg=BG_INPUT, fg=FG_DIM,
                                     command=self._do_reset, **bcfg)
        self._btn_reset.pack(fill="x", padx=8, pady=2)

        sec("LIVE STATS")
        self._stat_vars: Dict[str, tk.StringVar] = {}
        for key in ["Total Genes","Round","Induced","Repressed","Highly Active","Baseline",
                    "pH","Temp °C","Glucose mM","NaCl mOsm","H₂O₂",
                    "Oxygen","Iron","Antibiotic","SOS level"]:
            row = tk.Frame(p, bg=BG_CARD); row.pack(fill="x", padx=10, pady=0)
            tk.Label(row, text=f"{key}:", bg=BG_CARD, fg=FG_DIM,
                     font=("Courier", fs(9)), width=13, anchor="w").pack(side="left")
            sv = tk.StringVar(value="—")
            self._stat_vars[key] = sv
            tk.Label(row, textvariable=sv, bg=BG_CARD, fg=FG_TEXT,
                     font=("Courier", fs(9), "bold")).pack(side="left")

    # ── CENTER PANEL ─────────────────────────────────────────
    def _build_center(self, p):
        hrow = tk.Frame(p, bg=BG_CARD)
        hrow.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(hrow, text="🧬 E. COLI K-12 CHROMOSOME  (ALL GENES)",
                 bg=BG_CARD, fg=ACCENT,
                 font=("Courier", fs(11), "bold")).pack(side="left")
        tk.Label(hrow, text="outer=forward strand  inner=reverse  click=inspect  color=activity",
                 bg=BG_CARD, fg=FG_DIM, font=("Courier", fs(7))).pack(side="right")

        self._fig = plt.figure(figsize=(7, 8), facecolor=BG_CARD)
        self._ax = self._fig.add_subplot(111, projection='3d')
        self._ax.set_facecolor(BG_DARK)
        plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.04)
        self._canvas = FigureCanvasTkAgg(self._fig, master=p)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        toolbar = NavigationToolbar2Tk(self._canvas, p, pack_toolbar=False)
        toolbar.config(background=BG_CARD)
        toolbar.pack(side="bottom", fill="x", padx=4)
        toolbar.update()
        self._canvas.mpl_connect("button_press_event", self._on_graph_click)
        self._canvas.mpl_connect("scroll_event", self._on_scroll)
        self._draw_empty_graph()

        # Zoom buttons
        zrow = tk.Frame(p, bg=BG_CARD)
        zrow.pack(fill="x", padx=4, pady=(0, 2))
        for txt, delta in [("🔍 +", -3.0), ("🔎 −", 3.0), ("⟳ Reset", 0)]:
            tk.Button(zrow, text=txt, bg=BG_INPUT, fg=FG_TEXT,
                      font=("Courier", fs(8)), relief="flat", cursor="hand2",
                      command=lambda d=delta: self._zoom(d)).pack(side="left", padx=3)
        self._btn_zoom_gene = tk.Button(zrow, text="📍 Zoom→Gene",
                      bg=ACCENT, fg=BG_DARK,
                      font=("Courier", fs(8), "bold"), relief="flat", cursor="hand2",
                      command=self._zoom_to_selected, state="disabled")
        self._btn_zoom_gene.pack(side="left", padx=3)
        tk.Label(zrow, text="  drag=rotate  scroll=zoom",
                 bg=BG_CARD, fg=FG_DIM, font=("Courier", fs(7))).pack(side="left")

        self._graph_status = tk.StringVar(value="")
        tk.Label(p, textvariable=self._graph_status, bg=BG_DARK, fg=FG_DIM,
                 font=("Courier", fs(7))).pack(fill="x", padx=4, pady=(0, 2))

    # ── RIGHT PANEL ──────────────────────────────────────────
    def _build_right(self, p):
        # Environment control — scrollable
        env_outer = tk.Frame(p, bg=BG_CARD)
        env_outer.pack(fill="x", pady=(0, 3))

        tk.Label(env_outer, text="🌡  CELL ENVIRONMENT CONTROL",
                 bg=BG_CARD, fg=ACCENT,
                 font=("Courier", fs(12), "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        ec = env_outer  # shorthand

        def env_slider(lbl, var, from_, to, fmt, row_frame=None):
            rf = row_frame or tk.Frame(ec, bg=BG_CARD)
            rf.pack(fill="x", padx=10, pady=2)
            tk.Label(rf, text=f"{lbl}:", bg=BG_CARD, fg=FG_DIM,
                     font=("Courier", fs(9)), width=18, anchor="w").pack(side="left")
            val_lbl = tk.Label(rf, text=fmt.format(var.get()), bg=BG_CARD, fg=WARNING,
                                font=("Courier", fs(9), "bold"), width=8)
            val_lbl.pack(side="right")
            ttk.Scale(rf, from_=from_, to=to, variable=var, orient="horizontal",
                      command=lambda v, l=val_lbl, f=fmt: l.config(text=f.format(float(v)))
                      ).pack(side="left", fill="x", expand=True)

        # ── Sliders — extreme ranges ──────────────────────────────────
        env_slider("pH",              self._ph_var,    0.0,  14.0, "{:.1f}")
        env_slider("Temperature °C",  self._temp_var, -5.0, 121.0, "{:.1f}")
        env_slider("Glucose mM",      self._glc_var,   0.0,  50.0, "{:.1f}")
        env_slider("NaCl mOsm",       self._nacl_var,  0.0,5000.0, "{:.0f}")
        env_slider("H₂O₂ mM",         self._h2o2_var,  0.0,  20.0, "{:.2f}")
        env_slider("Oxygen (0=anaer)", self._oxy_var,   0.0,   2.0, "{:.2f}")
        env_slider("Iron (0=poor)",    self._iron_var,  0.0,   5.0, "{:.2f}")
        env_slider("Nitrogen (0=low)", self._nit_var,   0.0,   5.0, "{:.2f}")
        env_slider("SOS/DNA damage",   self._sos_var,   0.0,   1.0, "{:.2f}")
        env_slider("Ethanol %",        self._eth_var,   0.0,  10.0, "{:.2f}")
        env_slider("Phosphate (0=low)",self._phos_var,  0.0,   5.0, "{:.2f}")
        env_slider("Magnesium (0=low)",self._mg_var,    0.0,   5.0, "{:.2f}")
        env_slider("Potassium (0=low)",self._k_var,     0.0,   5.0, "{:.2f}")
        env_slider("Heavy metals",     self._hm_var,    0.0,   3.0, "{:.2f}")
        env_slider("Bile salts (gut)", self._bile_var,  0.0,   3.0, "{:.2f}")

        # Antibiotic selector
        abr = tk.Frame(ec, bg=BG_CARD); abr.pack(fill="x", padx=10, pady=2)
        tk.Label(abr, text="Antibiotic:", bg=BG_CARD, fg=FG_DIM,
                 font=("Courier", fs(7)), width=16, anchor="w").pack(side="left")
        ab_menu = ttk.Combobox(abr, textvariable=tk.StringVar(),
                               values=list(ANTIBIOTIC_NAMES.values()),
                               state="readonly", width=14,
                               font=("Courier", fs(7)))
        ab_menu.current(0)
        ab_menu.pack(side="right")
        ab_menu.bind("<<ComboboxSelected>>",
                     lambda e: self._ab_var.set(ab_menu.current()))
        self._ab_menu = ab_menu

        # Preset buttons
        for row_presets in [
            [("Baseline",    self._preset_baseline),
             ("Heat Shock",  self._preset_heat),
             ("Acid pH 5",   self._preset_acid),
             ("Alkaline 9",  self._preset_base)],
            [("Osmotic",     self._preset_osmotic),
             ("Oxidative",   self._preset_oxidative),
             ("Starvation",  self._preset_starvation),
             ("Anaerobic",   self._preset_anaerobic)],
            [("Iron Poor",   self._preset_iron),
             ("Ampicillin",  self._preset_amp),
             ("Cipro",       self._preset_cipro),
             ("SOS/UV",      self._preset_sos)],
            # ── extreme / natural environments ──
            [("Deep Freeze", self._preset_deep_freeze),
             ("Volcano",     self._preset_volcano),
             ("Acid Cave",   self._preset_acid_extreme),
             ("Alkaline Lk", self._preset_alkaline_extreme)],
            [("Gut",         self._preset_gut),
             ("Desert",      self._preset_desert),
             ("Heavy Metal", self._preset_heavy_metal),
             ("All Starve",  self._preset_all_starvation)],
            [("Kanamycin",   self._preset_kan),
             ("Rifampicin",  self._preset_rif),
             ("Trimethoprim",self._preset_tmp),
             ("Max Stress",  self._preset_max_stress)],
        ]:
            prow = tk.Frame(ec, bg=BG_CARD); prow.pack(fill="x", padx=10, pady=1)
            for name, cmd in row_presets:
                tk.Button(prow, text=name, bg=BG_INPUT, fg=FG_DIM,
                          font=("Courier", fs(7)), relief="flat", cursor="hand2",
                          command=cmd).pack(side="left", padx=2, fill="x", expand=True)

        self._env_desc = tk.StringVar(value="Custom environment change")
        tk.Entry(ec, textvariable=self._env_desc, bg=BG_INPUT, fg=FG_TEXT,
                 insertbackground=ACCENT, relief="flat",
                 font=("Courier", fs(8))).pack(fill="x", padx=10, pady=3, ipady=4)
        tk.Button(ec, text="⚡  INJECT ENVIRONMENT CHANGE",
                  bg=WARNING, fg=BG_DARK,
                  font=("Courier", fs(9), "bold"), relief="flat", cursor="hand2",
                  command=self._do_inject).pack(fill="x", padx=10, pady=(0, 4))

        # ── AI natural-language environment ───────────────────────────
        tk.Label(ec, text="🤖  AI ENVIRONMENT  (describe any scenario)",
                 bg=BG_CARD, fg="#a78bfa",
                 font=("Courier", fs(8), "bold")).pack(anchor="w", padx=10, pady=(6,1))
        self._ai_env_var = tk.StringVar(
            value="E.g.: simulate gut conditions with bile and low oxygen")
        ai_entry = tk.Entry(ec, textvariable=self._ai_env_var,
                            bg=BG_INPUT, fg=FG_TEXT,
                            insertbackground="#a78bfa", relief="flat",
                            font=("Courier", fs(8)))
        ai_entry.pack(fill="x", padx=10, pady=2, ipady=4)
        self._ai_env_btn = tk.Button(
            ec, text="🤖  ASK AI TO SET ENVIRONMENT",
            bg="#4c1d95", fg="#e9d5ff",
            font=("Courier", fs(8), "bold"), relief="flat", cursor="hand2",
            command=self._do_ai_environment)
        self._ai_env_btn.pack(fill="x", padx=10, pady=(0, 8))

        # Reaction feed
        fc = tk.Frame(p, bg=BG_CARD)
        fc.pack(fill="both", expand=True, pady=(0, 3))
        fh = tk.Frame(fc, bg=BG_CARD); fh.pack(fill="x", padx=10, pady=(5, 1))
        tk.Label(fh, text="⚗  CELL REACTION FEED", bg=BG_CARD, fg=ACCENT,
                 font=("Courier", fs(11), "bold")).pack(side="left")
        tk.Button(fh, text="clear", bg=BG_CARD, fg=FG_DIM,
                  font=("Courier", fs(7)), relief="flat", cursor="hand2",
                  command=self._clear_feed).pack(side="right")
        self._feed = scrolledtext.ScrolledText(
            fc, bg=BG_DARK, fg=FG_TEXT, font=("Courier", fs(9)),
            relief="flat", state="disabled", wrap="word")
        self._feed.pack(fill="both", expand=True, padx=4, pady=(0, 3))
        for tag, col, bold in [
            ("env",      WARNING,  True),
            ("round",    ACCENT,   True),
            ("positive", SUCCESS,  False),
            ("negative", DANGER,   False),
            ("neutral",  FG_DIM,   False),
        ]:
            font = ("Courier", fs(7), "bold") if bold else ("Courier", fs(7))
            self._feed.tag_config(tag, foreground=col, font=font)

        # Gene detail panel
        dc = tk.Frame(p, bg=BG_CARD, height=290)
        dc.pack(fill="x")
        dc.pack_propagate(False)
        dh = tk.Frame(dc, bg=BG_CARD); dh.pack(fill="x", padx=10, pady=(5, 1))
        tk.Label(dh, text="🔬  GENE DETAIL  (click any dot)",
                 bg=BG_CARD, fg=ACCENT,
                 font=("Courier", fs(9), "bold")).pack(side="left")
        self._gen_pers_btn = tk.Button(dh, text="✨ Personality",
                                        bg=BG_INPUT, fg=FG_DIM,
                                        font=("Courier", fs(7)), relief="flat",
                                        cursor="hand2",
                                        command=self._do_gen_personality,
                                        state="disabled")
        self._gen_pers_btn.pack(side="right")
        self._detail = scrolledtext.ScrolledText(
            dc, bg=BG_DARK, fg=FG_TEXT, font=("Courier", fs(7)),
            relief="flat", state="disabled", wrap="word")
        self._detail.pack(fill="both", expand=True, padx=4, pady=(0, 3))
        for tag, col in [("head", ACCENT), ("lbl", FG_DIM), ("val", FG_TEXT),
                         ("pos", SUCCESS), ("neg", DANGER), ("dim", FG_DIM),
                         ("pers", PURPLE)]:
            self._detail.tag_config(tag, foreground=col,
                font=("Courier", fs(7), "bold") if tag in ("head","pos","neg") else ("Courier", fs(7)))

    # ══════════════════════════════════════════
    #  GRAPH DRAWING  (circular chromosome)
    # ══════════════════════════════════════════
    def _draw_empty_graph(self):
        self._ax.clear()
        self._ax.set_facecolor(BG_DARK)
        self._ax.text(0, 0, 0,
                      "Click  ⬡ Build Cell  to load all 4761 gene agents\ninside the virtual E. coli cell",
                      ha="center", va="center", color=FG_DIM, fontsize=fs(10))
        self._ax.axis("off")
        self._ax.xaxis.pane.set_facecolor((0.024, 0.039, 0.078, 1.0))
        self._ax.yaxis.pane.set_facecolor((0.024, 0.039, 0.078, 1.0))
        self._ax.zaxis.pane.set_facecolor((0.024, 0.039, 0.078, 1.0))
        self._ax.xaxis.pane.fill = False
        self._ax.yaxis.pane.fill = False
        self._ax.zaxis.pane.fill = False
        self._ax.grid(False)
        self._canvas.draw_idle()

    @staticmethod
    def _hex_to_rgb(hx: str) -> Tuple[float, float, float]:
        hx = hx.lstrip("#")
        return tuple(int(hx[i:i+2], 16) / 255 for i in (0, 2, 4))

    def _activity_color(self, activity: float) -> Tuple[float, float, float]:
        a = max(-1.0, min(1.0, activity))
        if a >= 0:
            return (0.15 + (1 - a) * 0.22,  0.50 + a * 0.50,  0.15 + (1 - a) * 0.20)
        else:
            return (0.50 + abs(a) * 0.50,   0.15 + (1 + a) * 0.35, 0.15 + (1 + a) * 0.25)

    def _node_colors(self, agents: List[GeneAgent]) -> np.ndarray:
        mode = self._color_mode.get()
        out = []
        for g in agents:
            if mode == "Activity":
                out.append(self._activity_color(g.activity))
            elif mode == "Gene Type":
                out.append(self._hex_to_rgb(
                    TYPE_CONFIG.get(g.gene_type, {"color": "#90a4ae"})["color"]))
            elif mode == "Operon Family":
                hx = (self.engine.operon_colors.get(g.operon, "#445870")
                      if g.operon else "#1e2d44")
                out.append(self._hex_to_rgb(hx))
            else:  # Subcell. Location
                loc = g.subcell.lower()
                if "outer"      in loc: out.append((0.94, 0.60, 0.60))
                elif "periplasm"in loc: out.append((0.65, 0.84, 0.65))
                elif "membrane" in loc: out.append((1.00, 0.80, 0.50))
                elif "cytosol"  in loc or "cytoplasm" in loc:
                    out.append((0.31, 0.76, 0.97))
                else: out.append((0.27, 0.35, 0.44))
        return np.array(out, dtype=float)

    def _draw_graph(self):
        agents = self.engine.all_genes
        if not agents:
            return

        self._ax.clear()
        self._ax.set_facecolor(BG_DARK)
        # set_box_aspect resets _dist to 10 — restore immediately after
        self._ax.set_box_aspect([1.25, 1.0, 1.0])
        self._ax._dist = self._ax_dist

        # ── Set axis limits NOW so get_proj() later returns correct matrix ──
        _z  = self._zoom_level
        _cx, _cy, _cz = self._view_center
        self._ax.set_xlim(_cx - 1.42 * _z, _cx + 1.42 * _z)
        self._ax.set_ylim(_cy - 1.15 * _z, _cy + 1.15 * _z)
        self._ax.set_zlim(_cz - 1.15 * _z, _cz + 1.15 * _z)

        self._node_pos = {g.gene_name: (g.cx, g.cy, g.cz) for g in agents}

        # ── Cell membrane — ellipsoid wireframes ──────────────────
        u = np.linspace(0, 2 * np.pi, 40)
        v = np.linspace(0, np.pi, 20)
        sin_u, cos_u = np.sin(u), np.cos(u)
        sin_v, cos_v = np.sin(v), np.cos(v)
        for rx, ry, rz, al, col in [
            (1.25, 1.00, 1.00, 0.10, "#2a6a8a"),   # outer membrane
            (0.98, 0.78, 0.78, 0.06, "#1a3a52"),   # inner membrane
        ]:
            X = rx * np.outer(cos_u, sin_v)
            Y = ry * np.outer(sin_u, sin_v)
            Z = rz * np.outer(np.ones(len(u)), cos_v)
            self._ax.plot_wireframe(X, Y, Z, alpha=al, color=col,
                                    linewidth=0.25, rstride=4, cstride=4)

        # Compartment label at top of cell
        self._ax.text(0, 0, 1.05, "E. coli K-12  3D Cell",
                      ha="center", va="bottom", color="#1e4a60",
                      fontsize=fs(6), alpha=0.8)

        # ── Background PPI edges ──────────────────────────────────
        if self._show_ppi.get() and hasattr(self.engine, "_ppi_segs") and self.engine._ppi_segs:
            lc = Line3DCollection(self.engine._ppi_segs,
                                  colors="#2a5a8a", linewidths=0.35, alpha=0.45)
            self._ax.add_collection3d(lc)

        # ── Operon edges ──────────────────────────────────────────
        if self._show_op.get() and hasattr(self.engine, "_op_by_col"):
            for col, segs in self.engine._op_by_col.items():
                lc = Line3DCollection(segs, colors=col,
                                      linewidths=0.7, alpha=0.45)
                self._ax.add_collection3d(lc)

        # ── Active reaction edges (color by direction: green=up, red=down) ──
        if self.engine.last_edges:
            up_ppi, dn_ppi, up_op, dn_op = [], [], [], []
            up_ppi_w, dn_ppi_w, up_op_w, dn_op_w = [], [], [], []
            for (src, dst, etype, score) in self.engine.last_edges:
                sg = self.engine.gene_map.get(src)
                dg = self.engine.gene_map.get(dst)
                if not (sg and dg):
                    continue
                seg = [(sg.cx, sg.cy, sg.cz), (dg.cx, dg.cy, dg.cz)]
                avg_act = (sg.activity + dg.activity) / 2.0
                lw = max(0.8, min(3.5, 1.2 + abs(avg_act) * 3.0))
                if etype == "ppi":
                    if avg_act >= 0: up_ppi.append(seg); up_ppi_w.append(lw)
                    else:            dn_ppi.append(seg); dn_ppi_w.append(lw)
                else:
                    if avg_act >= 0: up_op.append(seg);  up_op_w.append(lw)
                    else:            dn_op.append(seg);  dn_op_w.append(lw)
            for segs, lws, col in [
                (up_ppi, up_ppi_w, "#00ff88"),   # green  — activated PPI
                (dn_ppi, dn_ppi_w, "#ff4444"),   # red    — repressed PPI
                (up_op,  up_op_w,  "#ffd740"),   # yellow — activated operon
                (dn_op,  dn_op_w,  "#ff8800"),   # orange — repressed operon
            ]:
                if segs:
                    lc = Line3DCollection(segs, colors=col,
                                          linewidths=lws, alpha=0.80, zorder=5)
                    self._ax.add_collection3d(lc)

        # ── Selected gene connections ──────────────────────────────
        if self._selected:
            sg = self._selected
            sel_ppi = [[(sg.cx, sg.cy, sg.cz),
                        (self.engine.gene_map[p["name"]].cx,
                         self.engine.gene_map[p["name"]].cy,
                         self.engine.gene_map[p["name"]].cz)]
                       for p in sg.ppi_partners
                       if p["name"] in self.engine.gene_map]
            if sel_ppi:
                lc = Line3DCollection(sel_ppi, colors="#00e5ff",
                                      linewidths=1.6, alpha=0.85)
                self._ax.add_collection3d(lc)
            op_col = self.engine.operon_colors.get(sg.operon, PURPLE) if sg.operon else PURPLE
            sel_op = [[(sg.cx, sg.cy, sg.cz),
                       (self.engine.gene_map[oname].cx,
                        self.engine.gene_map[oname].cy,
                        self.engine.gene_map[oname].cz)]
                      for oname in self.engine.operons.get(sg.operon, [])
                      if oname != sg.gene_name and oname in self.engine.gene_map]
            if sel_op:
                lc = Line3DCollection(sel_op, colors=op_col,
                                      linewidths=2.2, alpha=0.90,
                                      linestyles="dashed")
                self._ax.add_collection3d(lc)

        # ── Draw all nodes ─────────────────────────────────────────
        xs      = np.array([g.cx for g in agents])
        ys      = np.array([g.cy for g in agents])
        zs      = np.array([g.cz for g in agents])
        acts    = np.array([g.activity for g in agents])
        abs_acts= np.abs(acts)
        colors  = self._node_colors(agents)

        # ── Node size = MW × Protein_Abundance_PPM (normalised) ───────────
        # Both factors are log-scaled so a 2668 PPM protein doesn't dwarf all others.
        import math as _math
        mw_arr  = np.array([max(g.mw_da, 1.0)                    for g in agents], dtype=float)
        ppm_arr = np.array([max(g.protein_abundance_ppm, 0.1)     for g in agents], dtype=float)
        # log-transform to compress the huge dynamic range
        mw_log  = np.log10(mw_arr)
        ppm_log = np.log10(ppm_arr)
        # combined score = log(MW) × log(PPM)
        combined = mw_log * ppm_log
        combined = np.clip(combined, 0, None)           # no negatives
        max_comb = combined.max() if combined.max() > 0 else 1.0
        size_norm = combined / max_comb                 # 0 → 1
        ns      = max(1.0, self._node_scale)

        # Ball size: 80pt² minimum → 900pt² maximum, scaled by MW×PPM.
        # zoom_boost makes them grow as the user zooms in (up to ×8).
        zoom_boost = max(1.0, 0.5 / max(self._zoom_level, 0.02))
        zoom_boost = min(zoom_boost, 8.0)
        node_s = (80 + size_norm * 820) * ns * zoom_boost
        node_s = np.where(abs_acts > 0.35,  node_s * 1.5, node_s)
        node_s = np.where((abs_acts > 0.12) & (abs_acts <= 0.35), node_s * 1.2, node_s)
        # Keep mw_norm for selected-gene highlight (unchanged behaviour)
        max_mw  = mw_arr.max()
        mw_norm = mw_arr / max_mw

        # Inactive genes: slightly smaller & transparent
        inact = abs_acts < 0.12
        if inact.any():
            self._ax.scatter(xs[inact], ys[inact], zs[inact],
                             s=node_s[inact] * 0.6,
                             c=colors[inact], alpha=0.65,
                             linewidths=0, depthshade=False, zorder=6)
        rest = ~inact
        if rest.any():
            self._ax.scatter(xs[rest], ys[rest], zs[rest],
                             s=node_s[rest], c=colors[rest],
                             alpha=0.93, linewidths=0.7,
                             edgecolors="#ffffff",
                             depthshade=False, zorder=7)
        if self._selected:
            sg   = self._selected
            sg_ppm = max(sg.protein_abundance_ppm, 0.1)
            sg_mw  = max(sg.mw_da, 1.0)
            sg_comb= (_math.log10(sg_mw) * _math.log10(sg_ppm)) / max_comb
            sg_comb= max(0.0, sg_comb)
            sg_s   = (80 + sg_comb * 820) * ns * zoom_boost * 2.2
            self._ax.scatter([sg.cx], [sg.cy], [sg.cz],
                             s=sg_s, c=[[0, 0.9, 1]], alpha=0.95,
                             linewidths=2.5, edgecolors="#ffffff",
                             depthshade=False, zorder=9)

        # ── Gene ID labels ────────────────────────────────────────────────
        # Rules: checkbox must be ON, and zoom_level < 0.85 (somewhat zoomed in).
        # No count threshold — every ball visible on screen gets a label.
        if self._show_labels.get() and self._zoom_level < 0.85:
            z        = self._zoom_level
            lbl_fs   = fs(max(7, min(13, int(8 + (0.5 / max(z, 0.02)) * 2))))
            proj_mat = self._ax.get_proj()
            inv_axes = self._ax.transAxes.inverted()

            all_x2d, all_y2d, _ = proj3d.proj_transform(xs, ys, zs, proj_mat)
            all_disp = self._ax.transData.transform(
                np.column_stack([all_x2d, all_y2d]))
            all_frac = inv_axes.transform(all_disp)

            for i, g in enumerate(agents):
                fx, fy = all_frac[i]
                if not (0.01 < fx < 0.99 and 0.01 < fy < 0.99):
                    continue
                act    = g.activity
                is_sel = (g == self._selected)
                col = "#00e5ff" if is_sel else (
                      "#00e676" if act > 0.2 else
                      "#ff5252" if act < -0.2 else "#c8d8e8")
                disp_up = all_disp[i] + np.array([0.0, 14.0])
                ax_up   = inv_axes.transform(disp_up)
                self._ax.text2D(
                    float(ax_up[0]), float(ax_up[1]),
                    g.gene_name,
                    transform=self._ax.transAxes,
                    ha="center", va="bottom",
                    color=col, fontsize=lbl_fs, fontweight="bold",
                    clip_on=False, zorder=20,
                    bbox=dict(boxstyle="round,pad=0.2",
                              fc="#060a14", ec="#1e2d44",
                              alpha=0.82, linewidth=0.6)
                )

        # axis limits + _dist already set at top of _draw_graph — no need to repeat.
        self._ax.axis("off")
        self._ax.xaxis.pane.set_facecolor((0.024, 0.039, 0.078, 1.0))
        self._ax.yaxis.pane.set_facecolor((0.024, 0.039, 0.078, 1.0))
        self._ax.zaxis.pane.set_facecolor((0.024, 0.039, 0.078, 1.0))
        self._ax.xaxis.pane.fill = False
        self._ax.yaxis.pane.fill = False
        self._ax.zaxis.pane.fill = False
        self._ax.grid(False)
        self._draw_legend()
        self._canvas.draw_idle()

    def _draw_legend(self):
        mode = self._color_mode.get()
        handles = []
        if mode == "Activity":
            for col, lbl in [("#00e676","Induced (▲)"),
                             ("#445870","Baseline (─)"),
                             ("#ff5252","Repressed (▼)"),
                             ("#ffffff","Selected gene")]:
                handles.append(mpatches.Patch(color=col, label=lbl))
        elif mode == "Gene Type":
            for gtype, cfg in TYPE_CONFIG.items():
                handles.append(mpatches.Patch(color=cfg["color"], label=cfg["label"]))
        elif mode == "Subcell. Location":
            for col, lbl in [("#ffcc80","Membrane"),("#4fc3f7","Cytosol"),
                             ("#ef9a9a","Outer Membrane"),("#a5d6a7","Periplasm")]:
                handles.append(mpatches.Patch(color=col, label=lbl))
        # Connection legend — shows after INJECT
        from matplotlib.lines import Line2D as _L2D
        handles += [
            _L2D([0],[0], color="#00ff88", lw=2, label="PPI — activated"),
            _L2D([0],[0], color="#ff4444", lw=2, label="PPI — repressed"),
            _L2D([0],[0], color="#ffd740", lw=2, label="Operon — activated"),
            _L2D([0],[0], color="#ff8800", lw=2, label="Operon — repressed"),
        ]
        if handles:
            self._ax.legend(handles=handles, loc="lower left",
                            ncol=1, fontsize=fs(5.5),
                            framealpha=0.35, facecolor=BG_CARD, edgecolor=BG_BORDER,
                            labelcolor=FG_TEXT)

    def _redraw_graph(self):
        if self.engine.all_genes:
            self._draw_graph()

    def _on_graph_click(self, event):
        if not self._node_pos or event.xdata is None or event.inaxes != self._ax:
            return
        best_name, best_d = None, float("inf")
        mat = self._ax.get_proj()
        for name, (x, y, z) in self._node_pos.items():
            x2, y2, _ = proj3d.proj_transform(x, y, z, mat)
            d = math.sqrt((event.xdata - x2) ** 2 + (event.ydata - y2) ** 2)
            if d < best_d:
                best_d, best_name = d, name
        if best_name and best_d < 0.10:
            g = self.engine.gene_map.get(best_name)
            if g:
                self._selected = g
                self._show_detail(g)
                self._draw_graph()
                self._graph_status.set(
                    f"  {g.gene_name} | {g.gene_type} | {g.product[:55]}"
                    f" | activity={g.activity:+.2f} ({g.activity_label.split()[0]})")
                self._gen_pers_btn.config(state="normal")
                self._btn_zoom_gene.config(state="normal")

    # ══════════════════════════════════════════
    #  DETAIL PANEL
    # ══════════════════════════════════════════
    def _show_detail(self, g: GeneAgent):
        self._detail.configure(state="normal")
        self._detail.delete("1.0", "end")

        def row(lbl, val, tag="val"):
            self._detail.insert("end", f"  {lbl:<22}", "lbl")
            self._detail.insert("end", f"{val}\n", tag)

        act_tag = "pos" if g.activity > 0.2 else "neg" if g.activity < -0.2 else "dim"

        self._detail.insert("end", f"=== {g.gene_name}  [{g.gene_type}] ===\n\n", "head")

        row("Locus Tag",       g.locus_tag)
        row("Strand",          "(+) forward" if g.strand == "1" else "(−) reverse")
        row("Genome Position", f"{g.start:,} – {g.end:,}  ({g.length} {g.unit})")
        row("Operon Family",   g.operon or "—")
        row("Product",         g.product[:65] or "—")
        row("Function",        (g.function[:65] or "—"))
        row("Subcell. Loc.",   g.subcell or "—")
        row("GO Biol. Proc.",  g.go_bp[:60] or "—")
        row("GO Mol. Funct.",  g.go_mf[:60] or "—")
        row("GO Cell. Comp.",  g.go_cc[:60] or "—")
        row("Mol. Weight",     f"{g.mw_da:,.0f} Da" if g.mw_da else "—")
        row("Abundance",       f"{g.protein_abundance_ppm:.1f} PPM" if g.protein_abundance_ppm else "—")
        row("MW × Abundance",  f"{g.mw_da * g.protein_abundance_ppm:,.0f}" if (g.mw_da and g.protein_abundance_ppm) else "—")
        row("Max Size",        f"{g.max_size_a:.1f} Å" if g.max_size_a else "—")
        row("UniProt",         g.uniprot_id or "—")
        row("PPI Partners",    str(g.ppi_count))

        self._detail.insert("end", "\n─ SIMULATION STATE ─\n", "head")
        row("Activity",        f"{g.activity:+.2f}  {g.activity_label}", act_tag)
        row("Rounds Active",   str(g.rounds_active))

        if g.sensitivity:
            top_sens = sorted(g.sensitivity.items(), key=lambda x: -x[1])[:4]
            top_sens = [(k, v) for k, v in top_sens if v > 0]
            if top_sens:
                row("Sensitive to", ", ".join(f"{k}({v:.1f})" for k, v in top_sens))

        if g.personality:
            self._detail.insert("end", "\n─ PERSONALITY ─\n", "head")
            self._detail.insert("end", f"  {g.personality}\n", "pers")

        if g.memory:
            self._detail.insert("end", "\n─ REACTION LOG ─\n", "head")
            for i, m in enumerate(g.memory[-5:], 1):
                self._detail.insert("end", f"  {i}. {m}\n", "dim")

        self._detail.insert("end", "\n─ KEGG ─\n", "head")
        row("KO",    g.kegg_ko[:60] or "—")
        row("Pathways", g.kegg_pathways[:60] or "—")

        self._detail.configure(state="disabled")

    # ══════════════════════════════════════════
    #  PRESETS
    # ══════════════════════════════════════════
    def _env_snapshot(self) -> Dict:
        return {
            "pH":          self._ph_var.get(),
            "temperature": self._temp_var.get(),
            "glucose":     self._glc_var.get(),
            "nacl":        self._nacl_var.get(),
            "h2o2":        self._h2o2_var.get(),
            "oxygen":      self._oxy_var.get(),
            "iron":        self._iron_var.get(),
            "nitrogen":    self._nit_var.get(),
            "antibiotic":  self._ab_var.get(),
            "sos":         self._sos_var.get(),
            "ethanol":     self._eth_var.get(),
            "phosphate":   self._phos_var.get(),
            "magnesium":   self._mg_var.get(),
            "potassium":   self._k_var.get(),
            "heavy_metal": self._hm_var.get(),
            "bile":        self._bile_var.get(),
        }

    def _set_env(self, vals: Dict, desc: str):
        for k, v in vals.items():
            if k == "pH":           self._ph_var.set(v)
            elif k == "temperature":self._temp_var.set(v)
            elif k == "glucose":    self._glc_var.set(v)
            elif k == "nacl":       self._nacl_var.set(v)
            elif k == "h2o2":       self._h2o2_var.set(v)
            elif k == "oxygen":     self._oxy_var.set(v)
            elif k == "iron":       self._iron_var.set(v)
            elif k == "nitrogen":   self._nit_var.set(v)
            elif k == "antibiotic":
                self._ab_var.set(v)
                self._ab_menu.current(int(v))
            elif k == "sos":        self._sos_var.set(v)
            elif k == "ethanol":    self._eth_var.set(v)
            elif k == "phosphate":  self._phos_var.set(v)
            elif k == "magnesium":  self._mg_var.set(v)
            elif k == "potassium":  self._k_var.set(v)
            elif k == "heavy_metal":self._hm_var.set(v)
            elif k == "bile":       self._bile_var.set(v)
        self._env_desc.set(desc)

    def _preset_baseline(self):
        self._set_env(dict(ENV_BASELINE, antibiotic=0),
                      "Return to standard conditions (pH 7.0, 37°C, glucose 1mM)")
    def _preset_heat(self):
        self._set_env({"temperature": 45.0},
                      "Heat shock: temperature raised to 45°C")
    def _preset_acid(self):
        self._set_env({"pH": 5.0},
                      "Acid stress: pH 5.0 — triggers glutamate decarboxylase, Gad system")
    def _preset_base(self):
        self._set_env({"pH": 9.0},
                      "Alkaline stress: pH 9.0")
    def _preset_osmotic(self):
        self._set_env({"nacl": 700.0},
                      "Osmotic stress: NaCl 700 mOsm — triggers OsmY, trehalose, betaine")
    def _preset_oxidative(self):
        self._set_env({"h2o2": 0.8},
                      "Oxidative stress: H₂O₂ 0.8 mM — activates OxyR, KatG, AhpCF")
    def _preset_starvation(self):
        self._set_env({"glucose": 0.0},
                      "Carbon starvation: glucose depleted — triggers CRP-cAMP, RpoS")
    def _preset_anaerobic(self):
        self._set_env({"oxygen": 0.0},
                      "Anaerobic switch: O₂ = 0 — activates Fnr, Arc, nitrate reductases")
    def _preset_iron(self):
        self._set_env({"iron": 0.0},
                      "Iron depletion — activates Fur regulon, enterobactin siderophore")
    def _preset_amp(self):
        self._set_env({"antibiotic": 1},
                      "Ampicillin: β-lactam attack on cell wall — activates AmpC, SOS")
    def _preset_cipro(self):
        self._set_env({"antibiotic": 4, "sos": 0.7},
                      "Ciprofloxacin: DNA gyrase inhibition — triggers SOS (RecA, LexA)")
    def _preset_sos(self):
        self._set_env({"sos": 1.0},
                      "SOS response / UV damage — RecA, LexA, error-prone polymerases")

    # ── Extreme / natural environment presets ─────────────────────────
    def _preset_deep_freeze(self):
        self._set_env({"temperature": -2.0, "oxygen": 0.3},
                      "Deep freeze -2°C — cold shock proteins CspA-E, membrane lipid adaptation")
    def _preset_volcano(self):
        self._set_env({"temperature": 95.0, "pH": 2.0, "h2o2": 8.0},
                      "Volcanic vent: 95°C, pH 2.0, oxidative — extreme heat+acid multi-stress")
    def _preset_acid_extreme(self):
        self._set_env({"pH": 1.5, "glucose": 0.5},
                      "Stomach acid pH 1.5 — extreme acid resistance (Gad, Adi, AR systems)")
    def _preset_alkaline_extreme(self):
        self._set_env({"pH": 12.5, "nacl": 3000.0},
                      "Soda lake pH 12.5 + 3000 mOsm — extreme alkaline+osmotic")
    def _preset_gut(self):
        self._set_env({"pH": 6.0, "oxygen": 0.05, "bile": 2.0,
                       "nacl": 600.0, "glucose": 0.3},
                      "Gut conditions: high bile salts, low O₂, pH 6 — AcrAB-TolC, MarA, OmpF")
    def _preset_desert(self):
        self._set_env({"nacl": 4000.0, "glucose": 0.05, "nitrogen": 0.1,
                       "phosphate": 0.1, "temperature": 55.0},
                      "Desert/desiccation: extreme osmotic, nutrient starvation, 55°C heat")
    def _preset_heavy_metal(self):
        self._set_env({"heavy_metal": 2.5, "h2o2": 5.0, "sos": 0.8},
                      "Heavy metal toxicity (Hg/Cd/As) — mer operon, ars, extreme oxidative")
    def _preset_all_starvation(self):
        self._set_env({"glucose": 0.0, "nitrogen": 0.0, "phosphate": 0.0,
                       "iron": 0.0, "magnesium": 0.0, "potassium": 0.0},
                      "Total starvation: C/N/P/Fe/Mg/K all depleted — RpoS, stringent response")
    def _preset_kan(self):
        self._set_env({"antibiotic": 5},
                      "Kanamycin: aminoglycoside — 30S ribosome, mistranslation, membrane damage")
    def _preset_rif(self):
        self._set_env({"antibiotic": 6},
                      "Rifampicin: RNA polymerase β inhibition — blocks transcription initiation")
    def _preset_tmp(self):
        self._set_env({"antibiotic": 7},
                      "Trimethoprim: dihydrofolate reductase inhibition — folate/thymine starvation")
    def _preset_max_stress(self):
        self._set_env({"pH": 2.5, "temperature": 100.0, "nacl": 4500.0,
                       "h2o2": 15.0, "sos": 1.0, "ethanol": 8.0,
                       "glucose": 0.0, "oxygen": 0.0, "heavy_metal": 2.0,
                       "bile": 2.0, "magnesium": 0.0, "potassium": 0.0},
                      "LETHAL multi-stress: pH 2.5, 100°C, 4500mOsm, H₂O₂ 15mM — cell death scenario")

    # ── AI natural-language environment ───────────────────────────────
    def _do_ai_environment(self):
        if not self.engine.use_llm:
            self._feed_text(
                "⚠ LLM not enabled — enable LLM in the LLM REACTIONS panel first\n", "env")
            return
        scenario = self._ai_env_var.get().strip()
        if not scenario:
            return
        backend = self.engine.llm_backend.upper()
        self._ai_env_btn.config(state="disabled", text=f"🤖 Asking {backend}…")
        threading.Thread(target=self._ai_env_thread,
                         args=(scenario,), daemon=True).start()

    def _ai_env_thread(self, scenario: str):
        """Ask the active LLM to interpret the scenario and set sliders."""
        import re as _re, json as _json
        try:
            prompt = (
                "You are a microbiology expert for an E. coli K-12 simulation.\n"
                "The user describes an environment scenario. Return a JSON object "
                "with values for these keys (use baseline if not relevant):\n"
                "pH (2-12), temperature (2-80), glucose (0-20), nacl (0-2000), "
                "h2o2 (0-5), oxygen (0-1), iron (0-2), nitrogen (0-2), "
                "antibiotic (0=none,1=ampicillin,2=tetracycline,3=chloramphenicol,"
                "4=ciprofloxacin,5=kanamycin,6=rifampicin,7=trimethoprim), "
                "sos (0-1), ethanol (0-2), phosphate (0-2), "
                "magnesium (0-2), potassium (0-2), heavy_metal (0-1), bile (0-1).\n\n"
                "Baseline values: pH=7,temp=37,glucose=1,nacl=300,h2o2=0,oxygen=1,"
                "iron=1,nitrogen=1,antibiotic=0,sos=0,ethanol=0,phosphate=1,"
                "magnesium=1,potassium=1,heavy_metal=0,bile=0.\n\n"
                f"Scenario: {scenario}\n\n"
                "Return ONLY valid JSON, no explanation. Example:\n"
                '{"pH":6.0,"temperature":37,"glucose":0.5,"nacl":400,'
                '"h2o2":0,"oxygen":0.1,"iron":1,"nitrogen":1,"antibiotic":0,'
                '"sos":0,"ethanol":0,"phosphate":1,"magnesium":1,"potassium":1,'
                '"heavy_metal":0,"bile":0.8}'
            )
            raw = self.engine.active_llm.generate_environment(prompt)
            m = _re.search(r'\{.*\}', raw, _re.DOTALL)
            if not m:
                raise ValueError("No JSON in response")
            vals = _json.loads(m.group())
            desc = f"AI ({self.engine.llm_backend}) environment: {scenario}"
            self.after(0, lambda: self._ai_env_apply(vals, desc))
        except Exception as ex:
            self.after(0, lambda: self._feed_text(
                f"⚠ AI environment error: {ex}\n", "env"))
        finally:
            self.after(0, lambda: self._ai_env_btn.config(
                state="normal", text="🤖  ASK AI TO SET ENVIRONMENT"))

    def _ai_env_apply(self, vals: Dict, desc: str):
        self._set_env(vals, desc)
        self._feed_text(f"🤖 AI set environment: {desc}\n", "env")

    # ══════════════════════════════════════════
    #  HANDLERS
    # ══════════════════════════════════════════
    def _do_build(self):
        self._status("Loading 4761 genes from k12info.csv …")
        self._btn_build.config(state="disabled")
        threading.Thread(target=self._do_build_thread, daemon=True).start()

    def _do_build_thread(self):
        self.engine.build()
        self.after(0, self._do_build_done)

    def _do_build_done(self):
        self._selected = None
        self._draw_graph()
        self._update_stats()
        self._clear_feed()
        s = self.engine.stats()
        self._feed_text(
            f"🧬 Cell built: {s['Total Genes']} gene agents loaded\n"
            f"   3D cell layout — drag=rotate  scroll=zoom\n"
            f"   {s['Operons']} operon families detected (colored lines)\n"
            f"   PPI network: {sum(g.ppi_count for g in self.engine.all_genes)//2} interactions\n"
            f"   Use presets or sliders below — then click ⚡ INJECT\n\n"
            f"   TIP: green dots = induced  |  red = repressed\n"
        )
        self._btn_build.config(state="normal")
        self._btn_start.config(state="normal")
        self._status(f"Cell ready — {len(self.engine.all_genes)} genes loaded.")

    def _do_start(self):
        self.engine.use_llm     = self._llm_var.get()
        self.engine.llm_backend = self._llm_backend_var.get()
        self.engine.start()
        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._status("Auto-simulation running")

    def _do_stop(self):
        self.engine.stop()
        self._btn_start.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._status("Paused")

    def _do_reset(self):
        self.engine.stop()
        self.engine.all_genes.clear()
        self.engine.gene_map.clear()
        self.engine.graph.clear()
        self.engine.round = 0
        self._selected = None
        self._node_pos = {}
        self._draw_empty_graph()
        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="disabled")
        self._set_widget(self._detail, "")
        self._clear_feed()
        self._update_stats()
        self._gen_pers_btn.config(state="disabled")
        self._status("Reset")

    def _do_inject(self):
        if not self.engine.all_genes:
            self._status("Build the cell first"); return
        new_env = self._env_snapshot()
        desc = self._env_desc.get().strip() or "Environment change"
        self.engine.inject_environment(new_env, desc)
        self._status(f"Injected: {desc[:65]}")

    def _do_gen_personality(self):
        if not self._selected: return
        g = self._selected
        self._gen_pers_btn.config(state="disabled", text="⏳ …")
        def _run():
            self.engine.ensure_personality(g)
            self.after(0, lambda: [
                self._show_detail(g),
                self._gen_pers_btn.config(state="normal", text="✨ Personality"),
                self._status(f"Personality generated for {g.gene_name}"),
            ])
        threading.Thread(target=_run, daemon=True).start()

    def _on_node_scale(self, val):
        self._node_scale = float(val)
        self._ns_lbl.config(text=f"{float(val):.0f}x")
        if self.engine.all_genes:
            self._draw_graph()

    def _on_speed(self, val):
        v = float(val)
        self._spd_lbl.config(text=f"{v:.0f}s")
        self.engine.interval = v

    def _on_llm(self):
        self.engine.use_llm = self._llm_var.get()

    def _on_llm_backend(self):
        backend = self._llm_backend_var.get()
        self.engine.llm_backend = backend
        # Lazily create Ollama client with current model name
        if backend == "ollama":
            model = self._ollama_model_var.get().strip() or "llama3"
            self.engine.ollama_client = OllamaClient(model)
        self._refresh_ollama_row()

    def _on_ollama_model_apply(self):
        model = self._ollama_model_var.get().strip() or "llama3"
        self.engine.ollama_client = OllamaClient(model)
        self._feed_text(f"🦙 Ollama model set to: {model}\n", "env")

    def _refresh_ollama_row(self):
        """Show/hide the Ollama model entry and test rows."""
        if self._llm_backend_var.get() == "ollama":
            self._ollama_row.pack(fill="x", padx=10, pady=1)
            self._ollama_test_row.pack(fill="x", padx=10, pady=2)
        else:
            self._ollama_row.pack_forget()
            self._ollama_test_row.pack_forget()

    def _on_ollama_test(self):
        """Ping Ollama in background and update the status label."""
        self._ollama_status_lbl.config(text="● testing…", fg="#aaaaaa")
        model = self._ollama_model_var.get().strip() or "llama3"
        threading.Thread(target=self._ollama_test_thread,
                         args=(model,), daemon=True).start()

    def _ollama_test_thread(self, model: str):
        import urllib.request as _ur, json as _j, time as _t
        t0 = _t.time()
        try:
            payload = _j.dumps({
                "model": model,
                "messages": [{"role": "user", "content": "Say OK"}],
                "stream": False,
            }).encode()
            req = _ur.Request("http://localhost:11434/api/chat",
                              data=payload,
                              headers={"Content-Type": "application/json"})
            with _ur.urlopen(req, timeout=30) as r:
                _j.loads(r.read())
            ms = int((_t.time() - t0) * 1000)
            self.after(0, lambda: self._ollama_status_lbl.config(
                text=f"✅ ready  ({ms}ms)", fg="#4dff88"))
            self.after(0, lambda: self._feed_text(
                f"🦙 Ollama [{model}] connected — {ms}ms response\n", "env"))
        except Exception as ex:
            self.after(0, lambda: self._ollama_status_lbl.config(
                text="❌ not connected", fg="#ff4444"))
            self.after(0, lambda: self._feed_text(
                f"❌ Ollama error: {ex}\n   Make sure Ollama is running: ollama serve\n", "env"))

    def _append_feed(self, text: str, tag: str = ""):
        def _do():
            self._feed.configure(state="normal")
            self._feed.insert("end", text, tag)
            self._feed.see("end")
            self._feed.configure(state="disabled")
        self.after(0, _do)

    def _feed_text(self, text: str, tag: str = ""):
        self._feed.configure(state="normal")
        if tag:
            self._feed.insert("end", text, tag)
        else:
            self._feed.insert("end", text)
        self._feed.see("end")
        self._feed.configure(state="disabled")

    def _clear_feed(self):
        self._feed.configure(state="normal")
        self._feed.delete("1.0", "end")
        self._feed.configure(state="disabled")

    def _set_widget(self, w, text):
        w.configure(state="normal")
        w.delete("1.0", "end")
        if text: w.insert("end", text)
        w.configure(state="disabled")

    def _status(self, msg: str):
        self._status_lbl.config(text=msg)

    def _refresh(self):
        self._draw_graph()
        self._update_stats()
        if self._selected:
            self._show_detail(self._selected)

    def _update_stats(self):
        s = self.engine.stats()
        for key, sv in self._stat_vars.items():
            sv.set(str(s.get(key, "—")))

    def _on_scroll(self, event):
        # Scroll zoom: shrink/expand BOTH axis limits AND camera distance together.
        # This way genes within the zoom window stay visible (within axis range)
        # and distant genes disappear naturally — labels can then appear.
        if event.button == "up":      # zoom in — each step ×0.72
            self._zoom_level = max(0.02, self._zoom_level * 0.72)
        elif event.button == "down":  # zoom out
            self._zoom_level = min(1.0, self._zoom_level * 1.38)
        # Camera distance tracks zoom level (full-view dist = 10)
        self._ax_dist = max(1.2, self._zoom_level * 10.0)
        if self.engine.all_genes:
            self._draw_graph()
        else:
            self._ax._dist = self._ax_dist
            self._canvas.draw_idle()

    def _zoom_to_selected(self):
        if not self._selected:
            return
        g = self._selected
        self._view_center = [g.cx, g.cy, g.cz]
        self._zoom_level  = 0.18   # tight but not absurdly small
        self._ax_dist     = 3.5    # pull camera close
        self._apply_zoom()

    def _zoom(self, delta):
        if delta == 0:
            # Full reset
            self._zoom_level  = 1.0
            self._view_center = [0.0, 0.0, 0.0]
            self._ax_dist     = 10.0
        else:
            # +/- buttons: each step ~30 %
            factor = 0.72 if delta < 0 else 1.38
            for _ in range(abs(int(delta))):
                self._zoom_level = max(0.02, min(1.0, self._zoom_level * factor))
            self._ax_dist = max(1.2, self._zoom_level * 10.0)
        self._apply_zoom()

    def _apply_zoom(self):
        if self.engine.all_genes:
            self._draw_graph()
        else:
            z = self._zoom_level
            cx, cy, cz = self._view_center
            self._ax.set_xlim(cx - 1.42 * z, cx + 1.42 * z)
            self._ax.set_ylim(cy - 1.15 * z, cy + 1.15 * z)
            self._ax.set_zlim(cz - 1.15 * z, cz + 1.15 * z)
            self._ax._dist = self._ax_dist
            self._canvas.draw_idle()

    def _on_close(self):
        self.engine.stop()
        plt.close("all")
        self.destroy()


# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = GenesysApp()
    app.mainloop()
