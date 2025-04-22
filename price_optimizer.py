# Web Dashboard for Reptile Price Optimization

import statistics
from difflib import get_close_matches
import requests
from bs4 import BeautifulSoup
import re
import streamlit as st

# --- Scrape MorphMarket listings ---
from playwright.sync_api import sync_playwright  # Ensure playwright is imported

def scrape_morphmarket(morph_query):
    search_term = morph_query.replace(" ", "+")
    url = f"https://www.morphmarket.com/us/search?q={search_term}"
    listings = []

    with sync_playwright() as p:  # Correct way to use playwright
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_selector('div.price', timeout=10000)

        # Log part of the page content to see if we are getting the correct data
        page_content = page.content()
        print(page_content[:1000])  # Print the first 1000 characters for debugging

        price_elements = page.query_selector_all('div.price')
        if price_elements:
            print(f"Found {len(price_elements)} price elements.")
        else:
            print("No price elements found.")

        for el in price_elements:
            price_text = el.inner_text()
            match = re.search(r'\$(\d+)', price_text)
            if match:
                price = int(match.group(1))
                listings.append({"morph": morph_query, "price": price, "quality": "unknown"})

        browser.close()

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

