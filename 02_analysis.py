import pandas as pd
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
import json
import glob
import os
import re

# --- 1. CONFIGURE YOUR SETTINGS HERE ---

# Paste your Gemini API Key
# (Best practice is to set this as an environment variable)
GEMINI_API_KEY = "key plzzz"

# This script will try to find the MOST RECENT search_results_...csv file
# You can also set a specific filename:
INPUT_CSV_FILE = "search_results_2025-11-02.csv" 

# How much text to send to Gemini (in characters).
# Keeps API calls fast and cheap.
MAX_TEXT_LENGTH = 35000 

# -----------------------------------------

# Suppress Gemini warnings (optional)
import logging
logging.basicConfig(level=logging.ERROR)

def get_latest_search_file(pattern="search_results_*.csv"):
    """Finds the most recently created file matching the pattern."""
    try:
        list_of_files = glob.glob(pattern)
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file
    except Exception as e:
        print(f"Error finding latest file: {e}")
        return None

def fetch_and_clean_text(url):
    """
    Fetches content from a URL and extracts clean text using BeautifulSoup.
    """
    try:
        # Set a user-agent to pretend we're a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Add a timeout to avoid hanging on slow sites
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check for successful response
        if response.status_code != 200:
            return None, f"Failed: HTTP {response.status_code}"
            
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            return None, "Failed: Not an HTML page"

        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # Get text, strip whitespace, and join with spaces
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            return None, "Failed: No text found on page"
            
        # Truncate to save API tokens
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH] + "..."
            
        return text, "Success"

    except requests.exceptions.RequestException as e:
        return None, f"Failed: {type(e).__name__}"
    except Exception as e:
        return None, f"Failed: {e}"

def get_gemini_analysis(text_content, model):
    """
    Sends text to Gemini and asks for a structured JSON analysis.
    """
    
    # This prompt asks Gemini to act as an analyst and return JSON
    prompt = f"""
    You are an expert public relations and sentiment analyst. 
    Your task is to analyze the following article text. 
    The primary subject of interest is "ENEC" (Emirates Nuclear Energy Corporation).
    
    Based *only* on the text provided, return a JSON object with the following schema:
    
    {{
      "summary": "A concise 1-2 sentence summary of the article.",
      "sentiment_score": "A float between -1.0 (very negative) and 1.0 (very positive) representing the sentiment towards ENEC. If ENEC is not mentioned, this should be 0.0.",
      "sentiment_label": "A single word: 'Positive', 'Negative', or 'Neutral'.",
      "key_topics": "A list of 2-3 main topics discussed (e.g., ['Nuclear Safety', 'Government Policy', 'Barakah Plant']).",
      "relevance_to_enec": "An integer from 1 (Not relevant) to 5 (Highly relevant) indicating if the article is about the Emirates Nuclear Energy Corporation."
    }}

    Here is the article text:
    ---
    {text_content}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Clean the response text to extract the JSON block
        json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
        if not json_match:
            # Fallback if it just returns raw JSON without markdown
            json_match = re.search(r'\{\s*"summary":', response.text, re.DOTALL)
            if not json_match:
                print("  > ERROR: Gemini did not return valid JSON.")
                return None, f"Analysis Error: {response.text}"
            
            json_str = response.text[json_match.start():]
        else:
            json_str = json_match.group(1)
        
        # Parse the JSON string
        analysis_data = json.loads(json_str)
        return analysis_data, "Analysis Success"

    except json.JSONDecodeError as e:
        return None, f"JSON Decode Error: {e}"
    except Exception as e:
        # Handle API errors (e.g., safety blocks, quota)
        return None, f"Gemini API Error: {e}"

def main():
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("ERROR: Please update the GEMINI_API_KEY variable at the top of the script.")
        return

    # --- 1. Configure Gemini API ---
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Set up the model with JSON response type
        generation_config = {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        }
        model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash", 
            generation_config=generation_config
        )
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return

    # --- 2. Find and Read Input CSV ---
    input_file = INPUT_CSV_FILE
    if not input_file:
        input_file = get_latest_search_file()
        
    if not input_file or not os.path.exists(input_file):
        print(f"ERROR: Input file not found. Looked for '{input_file}'")
        print("Please run your first script (main.py) to generate a search_results_...csv file.")
        return
        
    print(f"Reading input file: {input_file}")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # --- 3. Process Each Link ---
    print(f"Found {len(df)} links to analyze. This may take a while...")
    
    # Lists to store our new data
    results = []

    for index, row in df.iterrows():
        url = row['Link']
        search_term = row['Search Term']
        
        # Skip invalid URLs
        if not isinstance(url, str) or not url.startswith('http'):
            print(f"\nSkipping [#{index+1}] (Invalid URL): {url}")
            results.append({
                'scrape_status': 'Invalid URL',
                'summary': '', 'sentiment_score': 0.0, 'sentiment_label': 'N/A',
                'key_topics': [], 'relevance_to_enec': 1
            })
            continue

        print(f"\nAnalyzing [#{index+1}/{len(df)}]: {url}")
        
        # Step 3a: Fetch and Clean Text
        text, status = fetch_and_clean_text(url)
        
        if not text:
            print(f"  > Scrape Status: {status}")
            results.append({
                'scrape_status': status,
                'summary': '', 'sentiment_score': 0.0, 'sentiment_label': 'N/A',
                'key_topics': [], 'relevance_to_enec': 1
            })
            continue
        
        print(f"  > Scrape Status: Success (found {len(text)} chars)")
        
        # Step 3b: Analyze with Gemini
        analysis_data, analysis_status = get_gemini_analysis(text, model)
        
        if not analysis_data:
            print(f"  > Analysis Status: {analysis_status}")
            results.append({
                'scrape_status': status,
                'summary': analysis_status, 'sentiment_score': 0.0, 'sentiment_label': 'Error',
                'key_topics': [], 'relevance_to_enec': 1
            })
            continue
            
        print(f"  > Analysis Status: Success (Sentiment: {analysis_data.get('sentiment_label')})")
        
        # Add scrape status to the results
        analysis_data['scrape_status'] = status
        results.append(analysis_data)
        
        # Be polite to servers and the API
        time.sleep(1) 

    # --- 4. Save Output CSV ---
    
    # Convert list of dicts to a DataFrame
    results_df = pd.DataFrame(results)
    
    # Combine original data with new analysis data
    final_df = pd.concat([df, results_df], axis=1)
    
    # Create the output filename
    output_filename = f"analysis_of_{os.path.basename(input_file)}"
    
    try:
        final_df.to_csv(output_filename, index=False, encoding='utf-8')
        print(f"\n--- ALL DONE! ---")
        print(f"Successfully saved analysis to: {output_filename}")
    except Exception as e:
        print(f"\nError saving final CSV: {e}")

if __name__ == "__main__":
    main()