"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.
"""

import os
import re
from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to .env file.")
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:

    listings = load_listings()
    desc_tokens = set(description.lower().split())

    scored = []

    for item in listings:
        # --- size filter ---
        if size:
            if size.lower() not in item["size"].lower():
                continue

        # --- price filter ---
        if max_price is not None:
            if item["price"] > max_price:
                continue

        # --- relevance scoring ---
        text = (
            item["title"] + " " +
            item["description"] + " " +
            " ".join(item["style_tags"])
        ).lower()

        score = sum(1 for token in desc_tokens if token in text)

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [item for score, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = f"""
You are a fashion stylist.

A user wants styling advice for this thrifted item:

Item:
{new_item['title']}
{new_item['description']}

Give:
- 2 outfit ideas
- vibe description
- what it pairs well with

Keep it concise and aesthetic.
"""
    else:
        wardrobe_text = "\n".join(
            f"- {w['name']} ({w['category']}, {', '.join(w['style_tags'])})"
            for w in wardrobe_items
        )

        prompt = f"""
You are a fashion stylist.

Thrifted item:
{new_item['title']}
{new_item['description']}

User wardrobe:
{wardrobe_text}

Task:
Suggest 1–2 complete outfits using wardrobe items + the thrifted piece.
Explain styling choices briefly.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "No outfit generated — cannot create fit card."

    client = _get_groq_client()

    prompt = f"""
You are writing a TikTok/Instagram thrift fashion caption.

Item:
Name: {new_item['title']}
Price: {new_item['price']}
Platform: {new_item['platform']}

Outfit:
{outfit}

Rules:
- 2–4 sentences
- casual, aesthetic, Gen Z tone
- mention item + price + platform once each
- include outfit vibe
- do NOT sound like an ad
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )

    return response.choices[0].message.content.strip()