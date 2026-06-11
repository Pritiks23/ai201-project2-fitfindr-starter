# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.


# FitFindr 🛍️

FitFindr is a lightweight AI-powered thrift shopping agent that:
1. Searches a structured secondhand listings dataset  
2. Selects the most relevant item  
3. Generates outfit suggestions using an LLM  
4. Converts the outfit into a social-media-ready “fit card” caption  

The system is implemented as a three-tool agent pipeline with explicit state passing and controlled failure handling.

---

# 🧰 Tool Inventory

## Tool 1: `search_listings`

### Inputs
- `description (str)`: Natural language description of desired item (e.g. "vintage graphic tee")
- `size (str | None)`: Optional size filter (e.g. "M", "S/M")
- `max_price (float | None)`: Optional maximum price constraint

### Outputs
- `list[dict]`: Ranked list of listing dictionaries containing:
  - id (str)
  - title (str)
  - description (str)
  - category (str)
  - style_tags (list[str])
  - size (str)
  - condition (str)
  - price (float)
  - colors (list[str])
  - brand (str | None)
  - platform (str)

### Purpose
Filters and ranks thrift listings using keyword overlap scoring, optional size filtering, and optional price constraints.

---

## Tool 2: `suggest_outfit`

### Inputs
- `new_item (dict)`: Selected listing from search results
- `wardrobe (dict)`: User wardrobe containing:
  - `items (list[dict])`

### Outputs
- `str`: Natural language outfit suggestions (1–2 outfits)

### Purpose
Uses an LLM (Groq) to generate outfit combinations that:
- integrate the selected thrift item
- incorporate wardrobe pieces when available
- provide styling logic and aesthetic direction

---

## Tool 3: `create_fit_card`

### Inputs
- `outfit (str)`: Outfit description from `suggest_outfit`
- `new_item (dict)`: Selected listing

### Outputs
- `str`: 2–4 sentence social-media-style caption

### Purpose
Transforms outfit reasoning into a casual OOTD-style caption including:
- item name
- price
- platform
- aesthetic vibe

---

# 🔁 Planning Loop (Agent Logic)

The agent follows a strict linear pipeline with one early-exit condition:

### Step 1: Parse query
Extract:
- description
- size (optional)
- max_price (optional)

### Step 2: Search listings
Call:
`search_listings(description, size, max_price)`

Store results in:
`session["search_results"]`

### Step 3: Early exit condition
If `search_results == []`:
- set `session["error"]`
- STOP execution immediately
- DO NOT call downstream tools

### Step 4: Select item
Choose top-ranked listing:
`session["selected_item"]`

### Step 5: Generate outfit
Call:
`suggest_outfit(selected_item, wardrobe)`

Store in:
`session["outfit_suggestion"]`

### Step 6: Generate fit card
Call:
`create_fit_card(outfit, selected_item)`

Store in:
`session["fit_card"]`

### Step 7: Return session

---

# 🧠 State Management Approach

The system uses a single mutable dictionary (`session`) as the source of truth.

### Session fields:
- `query`: raw user input
- `parsed`: extracted filters
- `search_results`: listing matches
- `selected_item`: chosen listing
- `wardrobe`: user wardrobe
- `outfit_suggestion`: LLM output
- `fit_card`: final caption
- `error`: early termination message

### Key principle:
- Each tool reads/writes to session sequentially
- No recomputation between steps
- Downstream tools depend on upstream outputs
- Early exit enforced via `session["error"]`

---
<img width="2366" height="1612" alt="image" src="https://github.com/user-attachments/assets/e6c4013f-4925-4d68-bf7d-0a991876904c" />


# ⚠️ Error Handling Strategy (with Concrete Test Evidence)

The system implements **graceful failure handling at both tool and agent level**, ensuring no crashes and predictable outputs across all failure modes.

---
) search_listings
Command
python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=50)[:2])"
Output
[
  {
    'id': 'lst_002',
    'title': 'Y2K Baby Tee — Butterfly Print',
    'price': 18.0,
    'category': 'tops',
    'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'],
    'size': 'S/M',
    'platform': 'depop'
  },
  {
    'id': 'lst_006',
    'title': 'Graphic Tee — 2003 Tour Bootleg Style',
    'price': 24.0,
    'category': 'tops',
    'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear'],
    'size': 'L',
    'platform': 'depop'
  }
]
2) suggest_outfit
Command
python -c "
from tools import search_listings, suggest_outfit
from utils.data_loader import get_example_wardrobe

item = search_listings('graphic tee', max_price=50)[0]
print(suggest_outfit(item, get_example_wardrobe()))
"
Output
Outfit 1: Streetwear Chic
- baggy straight-leg jeans
- chunky white sneakers
- vintage black denim jacket

Outfit 2: Minimalist Earthy
- wide-leg khaki trousers
- black combat boots
- brown leather belt
3) create_fit_card
Command
python -c "
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe

item = search_listings('graphic tee', max_price=50)[0]
outfit = suggest_outfit(item, get_example_wardrobe())
print(create_fit_card(outfit, item))
"
Output
Just thrifted the cutest Y2K Baby Tee — Butterfly Print for $18.0 on depop and I'm obsessed. I've been styling it in two different ways - casual streetwear with baggy jeans and chunky sneakers for a laid-back vibe, or edgy chic with a vintage denim jacket and combat boots for a night out.
4) agent.py — Happy Path
Command
PYTHONPATH=. python agent.py
Output (success case)
=== Happy path: graphic tee ===

Found: Mesh Long-Sleeve Top — Black

Outfit:
- Streetwear Chic: baggy jeans + combat boots + denim jacket
- Casual Layering: khaki trousers + tank + sneakers

Fit card:
Just scored this sick Mesh Long-Sleeve Top — Black for $15.0 on depop...
5) agent.py — No Results Path
Output
=== No-results path ===
Error message: No listings found matching your query.
6) Edge Case: Empty Fit Card
Command
python -c "from tools import search_listings, create_fit_card; results = search_listings('vintage graphic tee', max_price=50); print(create_fit_card('', results[0]))"
Output
No outfit generated — cannot create fit card.

Spec Reflection
What the spec did well

The milestone specification was effective in enforcing a layered development strategy:

It forced tool-by-tool isolation before agent integration
It explicitly required failure mode testing before Milestone 4
It prevented premature agent wiring, reducing debugging complexity

As a result, each tool could be validated independently before being composed into the planning loop.

Where implementation diverged from the spec

The main divergence was in LLM prompt behavior for suggest_outfit and create_fit_card.

The spec implied deterministic structured outputs, but in practice LLM outputs are inherently variable and non-deterministic.

To handle this, I:

Increased prompt constraints (clear formatting instructions)
Added fallback logic for empty inputs
Shifted expectations from strict formatting to semantic correctness and usability

This improved robustness but reduced strict output uniformity.

AI Usage (Prompt Engineering & Implementation Support)
Instance 1: Tool implementation scaffolding (Claude)

Input provided:

Full tools.py function signatures
Docstrings describing inputs, outputs, and failure modes
Dataset schema (load_listings())
Requirement: Groq LLM integration

AI output:

Initial implementations of:
search_listings
suggest_outfit
create_fit_card

What I changed:

Replaced simplistic matching with keyword scoring over style_tags and description
Added explicit empty-input guards
Improved prompts to produce more natural styling language

Instance 2: Agent planning loop design (ChatGPT assistance)

Input provided:

Full planning.md
State management schema
Architecture diagram (pipeline flowchart)
Requirement: enforce conditional branching on search results

AI output:

Linear pipeline:

parse → search → select → outfit → fit_card
Basic session state flow

What I revised:

Added strict early-exit condition when search_results == []
Ensured suggest_outfit is never called on empty results
Strengthened session state consistency across all tools

Summary Insight

The combination of structured specs + iterative AI-assisted implementation produced a system that is:

modular (tools independently testable)
robust (explicit failure handling paths)
debuggable (clear session state flow)
extensible (new tools plug into pipeline cleanly)
