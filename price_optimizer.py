# Web Dashboard for Reptile Price Optimization

import statistics
from difflib import get_close_matches
import requests
from bs4 import BeautifulSoup
import re
import streamlit as st

# --- Scrape MorphMarket listings ---
def scrape_morphmarket(morph_query):
    search_term = morph_query.replace(" ", "+")
    url = f"https://www.morphmarket.com/us/search?q={search_term}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    st.write(f"🔄 Status code: {response.status_code}")
    st.code(response.text[:1000])  # Show a preview of the HTML

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    listings = []

    for card in soup.find_all('div', class_='price'):
        price_text = card.get_text(strip=True)
        match = re.search(r'\$(\d+)', price_text)
        if match:
            price = int(match.group(1))
            listings.append({"morph": morph_query, "price": price, "quality": "unknown"})

    st.write(f"✅ Scraped listings: {listings}")  # New debug line
    return listings


# --- Core Pricing Logic ---
def filter_similar_listings(morph, listings):
    morphs_in_market = [entry['morph'] for entry in listings]
    close_match = get_close_matches(morph, morphs_in_market, n=1, cutoff=0.7)
    if close_match:
        return [entry for entry in listings if entry['morph'] == close_match[0]]
    return []

def suggest_price(user_animal, market_data):
    similar = filter_similar_listings(user_animal['morph'], market_data)
    if not similar:
        return None, "No similar morphs found. Suggest manual pricing."

    prices = [entry['price'] for entry in similar]
    median_price = statistics.median(prices)

    quality_multipliers = {
        "pet": 0.95,
        "breeder": 1.05,
        "high-end": 1.15
    }
    multiplier = quality_multipliers.get(user_animal['quality'], 1.0)
    suggested_price = round(median_price * multiplier)

    # Ensure margin above cost
    if suggested_price < user_animal['cost'] * 1.2:
        suggested_price = round(user_animal['cost'] * 1.2)

    # Psychological pricing
    suggested_price = int(str(suggested_price)[:-1] + "9")

    return suggested_price, f"Based on {len(similar)} similar listings. Median: ${median_price}. Quality multiplier: {multiplier}."

# --- Streamlit Web Interface ---
st.title("🦎 Reptile Price Optimization Tool")

morph = st.text_input("Enter Morph (e.g., Banana Ball Python)", "Banana Ball Python")
quality = st.selectbox("Select Quality", ["pet", "breeder", "high-end"])
cost = st.number_input("Enter Your Cost ($)", min_value=0, step=1, value=200)

if st.button("Get Suggested Price"):
    user_animal = {"morph": morph, "quality": quality, "cost": cost}
    
    with st.spinner("Scraping MorphMarket and analyzing..."):
        market_listings = scrape_morphmarket(morph)
        price, explanation = suggest_price(user_animal, market_listings)

        if price:
            st.success(f"💰 Suggested Price: ${price}")
            st.info(explanation)
        else:
            st.error("No price suggestion could be made. Try refining your morph input.")

