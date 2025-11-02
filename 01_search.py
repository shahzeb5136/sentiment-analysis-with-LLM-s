import json
import csv
import datetime
import time # NEW: Import time for a small delay between paged requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import math # NEW: Import math to calculate number of pages

# --- 1. CONFIGURE YOUR SETTINGS HERE ---

API_KEY = "key plzzz" 
CSE_ID = "161afb0a86d3f4b9d"

SEARCH_TERMS = [
    "News"
]

# NEW: Set how many results you want in total
# This must be a multiple of 10 (e.g., 10, 20, 30).
# The API max is 100 (10 requests of 10 results each).
TOTAL_RESULTS_TO_GET = 5 

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d")
OUTPUT_FILENAME = f"search_results_{TIMESTAMP}.csv"

# -----------------------------------------

# MODIFIED: Updated function to handle pagination
def google_search(search_term, api_key, cse_id, total_results):
    """
    Performs Google searches, handling pagination to get more than 10 results.
    """
    all_links = []
    
    # Calculate how many "pages" (requests) we need to make
    # The API's 'num' parameter can be max 10
    results_per_request = 10
    
    # Ensure total_results is not over the 100-result API limit
    if total_results > 100:
        print(f"Warning: API limit is 100 results. Clamping {total_results} to 100.")
        total_results = 100
        
    # Calculate the number of requests needed
    num_requests = math.ceil(total_results / results_per_request)

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        
        for i in range(num_requests):
            # Calculate the start index for this request
            # Page 1: start=1
            # Page 2: start=11
            # Page 3: start=21
            start_index = (i * results_per_request) + 1
            
            # Check if this is the last page and we need fewer than 10 results
            num_for_this_request = min(results_per_request, total_results - len(all_links))
            
            if num_for_this_request <= 0:
                break # We've already collected all the results we need

            print(f"  ...fetching results {start_index} - {start_index + num_for_this_request - 1}")

            res = service.cse().list(
                q=search_term,
                cx=cse_id,
                num=num_for_this_request,  # num is 10 (or less on the last page)
                start=start_index      # start index for pagination
            ).execute()
            
            # Extract links and add them to our master list
            links = [item['link'] for item in res.get('items', [])]
            all_links.extend(links)
            
            # A small delay is polite to avoid hammering the API
            time.sleep(0.1) 

        return all_links

    except HttpError as e:
        print(f"An error occurred while searching for '{search_term}': {e}")
        return all_links # Return any links we found before the error
    except Exception as e:
        print(f"A general error occurred: {e}")
        return all_links

# (This function remains unchanged)
def save_results_to_csv(results_data, filename):
    print(f"\nSaving results to {filename}...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Search Term', 'Link'])
            
            for term, links in results_data.items():
                if not links:
                    writer.writerow([term, 'No results found'])
                else:
                    for link in links:
                        writer.writerow([term, link])
                        
        print(f"Successfully saved all results to {filename}")
    except IOError as e:
        print(f"Error: Could not write to file {filename}. {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}")

def main():
    if API_KEY == "YOUR_API_KEY_HERE" or CSE_ID == "YOUR_CSE_ID_HERE":
        print("ERROR: Please update the API_KEY and CSE_ID variables at the top of the script.")
        return

    # NEW: Check if total_results is valid
    if TOTAL_RESULTS_TO_GET > 100:
        print("ERROR: Google's API limit is 100 results total (10 pages of 10).")
        print("Please set TOTAL_RESULTS_TO_GET to 100 or less.")
        return
    if TOTAL_RESULTS_TO_GET <= 0:
        print("ERROR: TOTAL_RESULTS_TO_GET must be greater than 0.")
        return

    all_results = {}
    print(f"Starting Google searches... (aiming for {TOTAL_RESULTS_TO_GET} results per term)")

    for term in SEARCH_TERMS:
        print(f"\nSearching for: '{term}'...")
        # MODIFIED: Pass TOTAL_RESULTS_TO_GET to the function
        links = google_search(term, API_KEY, CSE_ID, total_results=TOTAL_RESULTS_TO_GET)
        all_results[term] = links
        print(f"Found {len(links)} total results for '{term}'.")

    print("\n--- ALL SEARCHES COMPLETE ---")

    if all_results:
        save_results_to_csv(all_results, OUTPUT_FILENAME)
    else:
        print("No results were found to save.")

    print("\n--- CONSOLE OUTPUT PREVIEW ---")
    for term, links in all_results.items():
        print(f"\n--- Results for '{term}' ---")
        if not links:
            print("No results found.")
        else:
            for i, link in enumerate(links, 1):
                print(f"{i}. {link}")

if __name__ == "__main__":
    main()