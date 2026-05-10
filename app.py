import csv
import json
import os
import re
from collections import defaultdict
from flask import Flask, jsonify, request, send_from_directory
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'k12info.csv')
CACHE_FILE = os.path.join(BASE_DIR, 'personality_cache.json')
CONN_CACHE_FILE = os.path.join(BASE_DIR, 'connections_cache.json')

# ── Data loading ──────────────────────────────────────────────
def load_data():
    genes = []
    with open(DATA_FILE, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            genes.append(row)
    return genes

def detect_operons(genes):
    """Group genes by Gene_Name prefix (all-but-last-char). Groups of 2+ = operon/family."""
    groups = defaultdict(list)
    for g in genes:
        name = g['Gene_Name']
        if len(name) > 1:
            groups[name[:-1]].append(name)
    return {k: v for k, v in groups.items() if len(v) >= 2}

def parse_ppi(ppi_str):
    """Parse 'geneA (0.85), geneB (0.92)' into list of {name, score}."""
    result = []
    if not ppi_str:
        return result
    for part in ppi_str.split(','):
        part = part.strip()
        m = re.match(r'(\S+)\s*\(([0-9.]+)\)', part)
        if m:
            result.append({'name': m.group(1), 'score': float(m.group(2))})
    return result

# Load at startup
GENES = load_data()
GENE_MAP = {g['Gene_Name']: g for g in GENES}
OPERONS = detect_operons(GENES)
GENE_TO_OPERON = {}
for op, members in OPERONS.items():
    for m in members:
        GENE_TO_OPERON[m] = op

# ── Cache helpers ─────────────────────────────────────────────
def load_json(path):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

PERSONALITY_CACHE = load_json(CACHE_FILE)
CONN_CACHE = load_json(CONN_CACHE_FILE)

# ── Routes ────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/stats')
def stats():
    type_counts = defaultdict(int)
    for g in GENES:
        type_counts[g.get('Type', 'Unknown')] += 1

    total_ppi = sum(int(g.get('PPI_Count') or 0) for g in GENES) // 2
    locs = defaultdict(int)
    for g in GENES:
        loc = g.get('Subcellular_Location', '').strip()
        if loc:
            locs[loc] += 1

    return jsonify({
        'total_genes': len(GENES),
        'by_type': dict(type_counts),
        'total_operons': len(OPERONS),
        'total_ppi': total_ppi,
        'cached_personalities': len(PERSONALITY_CACHE),
        'top_locations': sorted(locs.items(), key=lambda x: -x[1])[:6],
    })

@app.route('/api/genes')
def genes_list():
    """Lightweight node list for graph initialisation."""
    result = []
    for g in GENES:
        name = g['Gene_Name']
        product = g.get('Product', '')
        result.append({
            'id': name,
            'locus': g.get('Locus_Tag', ''),
            'type': g.get('Type', 'CDS'),
            'operon': GENE_TO_OPERON.get(name),
            'ppi_count': int(g.get('PPI_Count') or 0),
            'length': g.get('Length', ''),
            'unit': g.get('Unit', 'AA'),
            'product': (product[:80] + '…') if len(product) > 80 else product,
            'strand': g.get('Strand', ''),
            'start': g.get('Start', ''),
            'end': g.get('End', ''),
            'mw': g.get('Molecular_Weight_Da', ''),
            'max_size': g.get('Max_Size_A', ''),
            'go_bp': g.get('GO_Biological_Process', ''),
            'go_mf': g.get('GO_Molecular_Function', ''),
            'go_cc': g.get('GO_Cellular_Component', ''),
            'subcell': g.get('Subcellular_Location', ''),
            'has_personality': name in PERSONALITY_CACHE,
        })
    return jsonify(result)

@app.route('/api/gene/<name>')
def gene_detail(name):
    g = GENE_MAP.get(name)
    if not g:
        return jsonify({'error': 'Gene not found'}), 404

    ppi = parse_ppi(g.get('PPI_Partners', ''))
    operon = GENE_TO_OPERON.get(name)

    # All fields except large sequences
    exclude = {'DNA_Sequence', 'Protein_Sequence'}
    detail = {k: v for k, v in g.items() if k not in exclude}
    detail['ppi_parsed'] = ppi
    detail['operon'] = operon
    detail['operon_members'] = OPERONS.get(operon, []) if operon else []
    detail['has_personality'] = name in PERSONALITY_CACHE
    detail['personality'] = PERSONALITY_CACHE.get(name)
    detail['llm_connections'] = CONN_CACHE.get(name, [])
    return jsonify(detail)

@app.route('/api/gene/<name>/sequence')
def gene_sequence(name):
    g = GENE_MAP.get(name)
    if not g:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'dna': g.get('DNA_Sequence', ''),
        'protein': g.get('Protein_Sequence', ''),
    })

@app.route('/api/network')
def network():
    """Return all PPI + operon edges."""
    edges = []
    seen = set()

    for g in GENES:
        name = g['Gene_Name']
        for partner in parse_ppi(g.get('PPI_Partners', '')):
            pname = partner['name']
            if pname in GENE_MAP:
                key = tuple(sorted([name, pname]))
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        'source': name,
                        'target': pname,
                        'type': 'ppi',
                        'score': partner['score'],
                    })

    for operon, members in OPERONS.items():
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                key = tuple(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        'source': a,
                        'target': b,
                        'type': 'operon',
                        'score': 1.0,
                        'operon': operon,
                    })

    return jsonify(edges)

@app.route('/api/personality/<name>', methods=['POST'])
def generate_personality(name):
    if name in PERSONALITY_CACHE:
        return jsonify({'personality': PERSONALITY_CACHE[name], 'cached': True})

    g = GENE_MAP.get(name)
    if not g:
        return jsonify({'error': 'Gene not found'}), 404

    client = anthropic.Anthropic()
    prompt = f"""You are creating a personality profile for gene {name} in E. coli K-12, imagined as a citizen in a living cell-city.

Biological identity:
  • Product: {g.get('Product') or 'Unknown'}
  • Function: {g.get('Function') or 'Unknown'}
  • GO Biological Process: {g.get('GO_Biological_Process') or 'Not annotated'}
  • GO Molecular Function: {g.get('GO_Molecular_Function') or 'Not annotated'}
  • GO Cellular Component: {g.get('GO_Cellular_Component') or 'Not annotated'}
  • Mini-Review: {g.get('Mini_Review_Summary') or 'Not available'}

Write exactly 3 sentences as a personality profile:
1. Their "job title" and daily role in the cell-city.
2. Core personality traits derived from their molecular function.
3. How they collaborate with or depend on other genes.

Be creative, scientifically grounded, and engaging. No headers—just the 3 sentences."""

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=350,
        messages=[{'role': 'user', 'content': prompt}],
    )

    personality = message.content[0].text.strip()
    PERSONALITY_CACHE[name] = personality
    save_json(CACHE_FILE, PERSONALITY_CACHE)
    return jsonify({'personality': personality, 'cached': False})

@app.route('/api/connections/<name>', methods=['POST'])
def generate_connections(name):
    """LLM evaluates functional/personality connections from this gene to top candidates."""
    if name in CONN_CACHE:
        return jsonify({'connections': CONN_CACHE[name], 'cached': True})

    g = GENE_MAP.get(name)
    if not g:
        return jsonify({'error': 'Gene not found'}), 404

    # Find candidates by shared GO terms or pathway
    my_go_bp = set(filter(None, g.get('GO_Biological_Process', '').split(' | ')))
    my_go_mf = set(filter(None, g.get('GO_Molecular_Function', '').split(' | ')))
    my_kegg = set(filter(None, g.get('KEGG_Pathways', '').split(' | ')))

    scored = []
    for other in GENES:
        oname = other['Gene_Name']
        if oname == name:
            continue
        shared = (
            len(my_go_bp & set(filter(None, other.get('GO_Biological_Process', '').split(' | ')))) * 2
            + len(my_go_mf & set(filter(None, other.get('GO_Molecular_Function', '').split(' | '))))
            + len(my_kegg & set(filter(None, other.get('KEGG_Pathways', '').split(' | '))))
        )
        if shared > 0:
            scored.append((oname, shared, other.get('Product', 'unknown')))

    scored.sort(key=lambda x: -x[1])
    candidates = scored[:15]

    if not candidates:
        return jsonify({'connections': [], 'cached': False})

    client = anthropic.Anthropic()
    my_personality = PERSONALITY_CACHE.get(name, f"Gene {name}: {g.get('Product', 'unknown function')}")
    cand_text = '\n'.join(f"  • {c[0]}: {c[2]}" for c in candidates)

    prompt = f"""Gene {name} personality in the cell-city:
"{my_personality}"

Candidate connections (genes sharing biological pathways):
{cand_text}

Select 3–6 candidates that most meaningfully interact with {name}.
Reply ONLY with a JSON array (no markdown):
[{{"name": "gene_name", "reason": "one short sentence explaining the connection"}}]"""

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=500,
        messages=[{'role': 'user', 'content': prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip possible markdown fences
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    try:
        connections = json.loads(raw)
    except Exception:
        connections = []

    CONN_CACHE[name] = connections
    save_json(CONN_CACHE_FILE, CONN_CACHE)
    return jsonify({'connections': connections, 'cached': False})

@app.route('/api/operons')
def operons():
    return jsonify(OPERONS)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
