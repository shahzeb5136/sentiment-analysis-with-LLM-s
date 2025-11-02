# Google Search Sentiment Analysis

This project uses Python to perform sentiment analysis on Google search results. It fetches search results for a given query, analyzes the sentiment of the titles and descriptions, and saves the results to a CSV file.

## Features

- Fetches Google search results for a given query.
- Performs sentiment analysis on the search result titles and descriptions.
- Saves the search results and analysis to CSV files.
- Allows for the use of different sentiment analysis models from the Hugging Face library.

## Project Structure

- `01_search.py`: Python script to fetch Google search results.
- `02_analysis.py`: Python script to perform sentiment analysis on the search results.
- `search_results_YYYY-MM-DD.csv`: CSV file containing the search results.
- `analysis_of_search_results_YYYY-MM-DD.csv`: CSV file containing the sentiment analysis of the search results.
- `zz_list_models`: A text file containing a list of sentiment analysis models that can be used with this project.
