# GENESYS — LLM-Agent Cell Simulator

> *"What happens when you give every gene in a living cell its own identity, memory, and personality — and set all 4,762 of them to work together in real time?"*

**GENESYS** is a living-cell simulator of *Escherichia coli* K-12, powered by **4,762 individual AI gene agents**. Each gene responds to environmental changes using a large language model (Claude or Llama 3), maintains a rolling memory of its last 10 reactions, and communicates through **24,000 validated protein–protein interactions (PPI)**.

---

## Key Features

| Feature | Detail |
|---|---|
| **Gene Agents** | 4,762 autonomous agents — one per E. coli K-12 gene |
| **LLM Backends** | Anthropic Claude (API) · Meta Llama 3 via Ollama (local, free) |
| **PPI Network** | 24,000+ experimentally validated interactions (STRING DB ≥700) |
| **Operon Regulation** | 1,847 co-regulated operons with shared responses |
| **3D Visualization** | Interactive real-time 3D cell graph (Matplotlib) |
| **Node Sizing** | `log₁₀(MW) × log₁₀(PPM)` — cellular importance made visible |
| **Environments** | 16 tunable parameters: pH, temperature (−5 to 121 °C), NaCl, H₂O₂, ethanol, antibiotics, and more |
| **AI Interpreter** | Describe any scenario in plain English → LLM sets all parameters |

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/AS-ai25/GENESYS.git
cd GENESYS
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Anthropic API key (for Claude backend)
```bash
# Windows
set ANTHROPIC_API_KEY=your_key_here

# Linux / macOS
export ANTHROPIC_API_KEY=your_key_here
```

### 4. (Optional) Run Llama 3 locally via Ollama — free, no API key
```bash
# Install Ollama from https://ollama.com
ollama pull llama3
# Ollama runs automatically on localhost:11434
```

### 5. Launch GENESYS
```bash
python genesys_sim.py
```

---

## How It Works

### Gene Agent Architecture
Each of the 4,762 genes is an independent AI agent with:

- **Molecular Identity** — protein name, MW (Da), subcellular location, UniProt ID, GO terms
- **LLM Response Engine** — Claude or Llama 3 generates a unique reaction to each environmental injection
- **Rolling Memory** — stores its last 10 responses to build context-aware behaviour
- **PPI Connectivity** — linked to up to hundreds of protein partners via STRING DB
- **Protein Abundance (PPM)** — real abundance data (PaxDb) used to size nodes in the 3D graph

### Simulation Loop
```
INJECT environment change
  → calculate stressor strengths
  → select top N responding genes
  → each gene calls LLM → generates reaction text + activity score
  → activity propagates through PPI network
  → 3D graph updates: node colour = activity, size = MW × PPM, edges = direction
  → feed panel displays gene reactions in real time
```

### Example Results

**Heat Shock (95 °C injection)**
- groEL, groES, dnaK, ibpA spike within one round
- LLM response: *"All available resources devoted to rescuing misfolded proteins — translation halted"*

**SOS Response (ciprofloxacin)**
- recA activates → lexA auto-cleaves → 47 genes across the SOS regulon respond
- sulA arrests cell division; umuC/umuD enable error-prone repair

**Starvation (all nutrients depleted)**
- 220 genes enter survival mode; rpoS (σˢ) stationary-phase sigma factor rises

---

## Environment Parameters

| Parameter | Range | Effect |
|---|---|---|
| Temperature | −5 to 121 °C | Heat shock / cold stress |
| pH | 0 – 14 | Acid / base stress |
| Glucose | 0 – 50 mM | Carbon source |
| NaCl | 0 – 5000 mOsm | Osmotic stress |
| H₂O₂ | 0 – 20 mM | Oxidative stress |
| Ethanol | 0 – 10 % | Solvent stress |
| Heavy metals | 0 – 3 | Metal toxicity |
| Bile salts | 0 – 3 | Gut environment |
| Antibiotics | Ciprofloxacin, Ampicillin, Chloramphenicol, Tetracycline | |
| Oxygen | Aerobic / anaerobic | |
| UV radiation | 0 – 3 | DNA damage |

---

## Project Structure

```
GENESYS/
├── genesys_sim.py        # Main simulation — all gene agents, UI, LLM logic
├── app.py                # Flask web interface (alternative frontend)
├── k12info.csv           # E. coli K-12 gene database (4,762 genes, PPM, PPI)
├── requirements.txt      # Python dependencies
└── static/               # Web frontend assets
```

---

## The Bigger Idea

> **LLM-agents are not just for human tasks.**

GENESYS is a proof of principle: any biological entity — gene, cell, organism, or ecosystem — can be modelled as an autonomous AI agent. *E. coli* K-12 is the starting point.

| Next target | Genes | Key stressors |
|---|---|---|
| *Arabidopsis thaliana* | ~27,000 | Light, CO₂, drought, pathogens |
| *Saccharomyces cerevisiae* | ~6,000 | Fermentation, osmotic, nitrogen |
| Human gut microbiome | 200,000+ | Diet, antibiotics, immune signals |

---

## References

1. Blattner F.R. et al. (1997) *Science* 277:1453 — doi:[10.1126/science.277.5331.1453](https://doi.org/10.1126/science.277.5331.1453)
2. Keseler I.M. et al. (2021) *Nucleic Acids Res* 49:D543 — doi:[10.1093/nar/gkaa1003](https://doi.org/10.1093/nar/gkaa1003)
3. Szklarczyk D. et al. (2023) *Nucleic Acids Res* 51:D638 — doi:[10.1093/nar/gkac1000](https://doi.org/10.1093/nar/gkac1000)
4. Wang M. et al. (2015) *Mol Cell Proteomics* 14 — doi:[10.1074/mcp.O114.045914](https://doi.org/10.1074/mcp.O114.045914)
5. Guisbert E. et al. (2008) *Microbiol Mol Biol Rev* 72:545 — doi:[10.1128/MMBR.00010-08](https://doi.org/10.1128/MMBR.00010-08)
6. Wei J. et al. (2022) Chain-of-thought prompting — *NeurIPS 35* — doi:[10.48550/arXiv.2210.11610](https://doi.org/10.48550/arXiv.2210.11610)

---

## License

MIT License — open source, free to use and extend.

---

## Author

**Amir Shamash**  
Computational Systems Biology · 2026  
amir.shmaryahu@gmail.com  
[LinkedIn](https://www.linkedin.com/in/amir-shamash)

---

*Built with Anthropic Claude · Meta Llama 3 · STRING DB · EcoCyc · PaxDb*
