# Google Search Sentiment Analysis

This project uses Python to perform sentiment analysis on Google search results. It fetches search results for a given query, analyzes the sentiment of the titles and descriptions, and saves the results to a CSV file.

## Features

- Fetches Google search results for a given query.
- Performs sentiment analysis on the search result titles and descriptions.
- Saves the search results and analysis to CSV files.
- Allows for the use of different sentiment analysis models from the Hugging Face library.

## Requirements

- Python 3.6+
- The following Python libraries:
  - `googlesearch-python`
  - `transformers`
  - `pandas`
  - `torch`
  - `scipy`

You can install the required libraries using pip:

```bash
pip install googlesearch-python transformers pandas torch scipy
```

## How to Use

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/google-search-sentiment-analysis.git
   ```

2. **Run the search script:**

   ```bash
   python 01_search.py "your search query"
   ```

   This will create a `search_results_YYYY-MM-DD.csv` file with the search results.

3. **Run the analysis script:**

   ```bash
   python 02_analysis.py
   ```

   This will create an `analysis_of_search_results_YYYY-MM-DD.csv` file with the sentiment analysis of the search results.

## Project Structure

- `01_search.py`: Python script to fetch Google search results.
- `02_analysis.py`: Python script to perform sentiment analysis on the search results.
- `search_results_YYYY-MM-DD.csv`: CSV file containing the search results.
- `analysis_of_search_results_YYYY-MM-DD.csv`: CSV file containing the sentiment analysis of the search results.
- `zz_list_models`: A text file containing a list of sentiment analysis models that can be used with this project.

## Sentiment Analysis Models

The following models from the Hugging Face library can be used for sentiment analysis:

- `cardiffnlp/twitter-roberta-base-sentiment`
- `distilbert-base-uncased-finetuned-sst-2-english`
- `nlptown/bert-base-multilingual-uncased-sentiment`
- `siebert/sentiment-roberta-large-english`
- `finiteautomata/bertweet-base-sentiment-analysis`
- `j-hartmann/emotion-english-distilroberta-base`
