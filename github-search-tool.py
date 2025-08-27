import requests
import json
import csv
import os
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from requests.adapters import HTTPAdapter
# Corrected import for Retry
from urllib3.util.retry import Retry
from time import sleep

# Optional: For translation and language detection
try:
    from langdetect import detect
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Warning: 'langdetect' not installed. Translation disabled. Install with 'pip install langdetect'.")


def translate_text(text, target_lang='en'):
    """Translate text using LibreTranslate API (free, no key needed)."""
    if not TRANSLATION_AVAILABLE:
        return text
    try:
        url = "https://libretranslate.de/translate"
        data = {'q': text, 'source': 'auto', 'target': target_lang}
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()['translatedText']
    except Exception as e:
        print(f"Translation error: {e}. Returning original text.")
        return text


def search_github(query, sort='stars', order='desc', language=None, min_stars=0, per_page=30, token=None):
    """Search GitHub repositories with pagination support."""
    base_url = "https://api.github.com/search/repositories"
    params = {'q': query, 'sort': sort, 'order': order, 'per_page': per_page}
    if language:
        params['q'] += f' language:{language}'
    if min_stars > 0:
        params['q'] += f' stars:>={min_stars}'

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-Scraper-App'
    }
    if token:
        headers['Authorization'] = f'token {token}'

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1,
                     status_forcelist=[403, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    return session, base_url, params, headers


def fetch_results(session, base_url, params, headers, num_results):
    """Fetch paginated results."""
    results = []
    page = 1
    while len(results) < num_results:
        params['page'] = page
        try:
            response = session.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            if not items:
                break
            results.extend(items)
            page += 1
            sleep(1)
        except requests.exceptions.HTTPError as err:
            print(f"HTTP Error: {err}")
            if response.status_code == 403:
                print("Rate limit exceeded. Waiting 60 seconds...")
                sleep(60)
            else:
                break
        except Exception as e:
            print(f"Error: {e}")
            break
    return results[:num_results]


def save_to_json(data, filename, translate=False):
    """Save results to JSON file, with optional translation."""
    for repo in data:
        if translate and repo.get('description'):
            lang = detect(repo['description']
                         ) if TRANSLATION_AVAILABLE else 'en'
            # Translate if language is not English or Arabic
            if lang not in ['en', 'ar']:
                repo['description_translated'] = translate_text(
                    repo['description'])
            else:
                repo['description_translated'] = ''
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {filename} (JSON format)")


def save_to_csv(data, filename, translate=False, delimiter=','):
    """Save results to CSV or TSV file, with optional translation."""
    if not data:
        return

    fieldnames = ['name', 'full_name', 'html_url', 'description', 'description_translated',
                  'stargazers_count', 'watchers_count', 'forks_count',
                  'language', 'license', 'updated_at']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()

        for repo in data:
            row = {field: repo.get(field, '') for field in fieldnames}
            if 'license' in repo and repo['license']:
                row['license'] = repo['license'].get('name', '')
            if translate and repo.get('description'):
                lang = detect(repo['description']
                              ) if TRANSLATION_AVAILABLE else 'en'
                # Translate if language is not English or Arabic
                if lang not in ['en', 'ar']:
                    row['description_translated'] = translate_text(
                        repo['description'])
                else:
                    row['description_translated'] = ''
            writer.writerow(row)
    print(f"Results saved to {filename} ({'TSV' if delimiter == '\t' else 'CSV'} format)")


def save_to_xml(data, filename, translate=False):
    """Save results to XML file, with optional translation."""
    root = ET.Element('repositories')
    for repo in data:
        repo_element = ET.SubElement(root, 'repository')
        for key, value in repo.items():
            if key in ['owner', 'license']:
                # Skip complex objects
                continue
            if isinstance(value, (dict, list)):
                continue

            if key == 'description' and translate and repo.get('description'):
                lang = detect(repo['description']) if TRANSLATION_AVAILABLE else 'en'
                if lang not in ['en', 'ar']:
                    translated_text = translate_text(repo['description'])
                    ET.SubElement(repo_element, 'description').text = value
                    ET.SubElement(repo_element, 'description_translated').text = translated_text
                else:
                    ET.SubElement(repo_element, key).text = str(value)
            else:
                ET.SubElement(repo_element, key).text = str(value)
    
    tree = ET.ElementTree(root)
    tree.write(filename, encoding='utf-8', xml_declaration=True)
    print(f"Results saved to {filename} (XML format)")


def display_results(repos, num_to_display=5):
    """Display top N results in console."""
    for idx, repo in enumerate(repos[:num_to_display], 1):
        print(f"\n{idx}. {repo['name']} (⭐ {repo['stargazers_count']})")
        print(f"  {repo.get('description', 'No description')}")
        print(f"  Language: {repo.get('language', 'Unknown')}")
        print(f"  URL: {repo['html_url']}")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Repository Search Tool")
    parser.add_argument(
        '--query', help="Search query (e.g., 'machine learning')")
    parser.add_argument('--token', default=os.getenv('GITHUB_TOKEN'),
                        help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument('--num-results', type=int, default=30,
                        help="Number of results to fetch (default: 30)")
    parser.add_argument('--sort', default='stars', choices=[
                        'stars', 'forks', 'help-wanted-issues', 'updated'], help="Sort by (default: stars)")
    parser.add_argument('--order', default='desc',
                        choices=['asc', 'desc'], help="Order (default: desc)")
    parser.add_argument('--language', help="Filter by language (e.g., python)")
    parser.add_argument('--min-stars', type=int, default=0,
                        help="Minimum stars (default: 0)")
    parser.add_argument('--translate', action='store_true',
                        help="Translate non-English descriptions (requires langdetect)")
    parser.add_argument('--display-num', type=int, default=5,
                        help="Number of results to display (default: 5)")
    args = parser.parse_args()

    # Fallback to prompt for query if not provided
    if not args.query:
        args.query = input(
            "Enter your search term (e.g., 'machine learning'): ").strip()
        if not args.query:
            print("Error: Search query is required!")
            return

    # Prompt for file format and name after the search query
    print("Select the desired file format:")
    print("1. JSON")
    print("2. CSV")
    print("3. TSV")
    print("4. XML")
    format_choice = input("Enter the number (1, 2, 3 or 4): ").strip()
    
    file_format = 'json'
    file_extension = 'json'

    if format_choice == '2':
        file_format = 'csv'
        file_extension = 'csv'
    elif format_choice == '3':
        file_format = 'tsv'
        file_extension = 'tsv'
    elif format_choice == '4':
        file_format = 'xml'
        file_extension = 'xml'
    elif format_choice != '1':
        print("Invalid choice. Defaulting to JSON.")


    filename_input = input(f"Enter the filename (without extension) or press Enter to use default: ").strip()
    default_filename = f"github_{args.query.replace(' ', '_')}"
    filename_base = filename_input or default_filename
    filename = f"{filename_base}.{file_extension}"

    print(f"\nSearching GitHub for '{args.query}'...")
    session, base_url, params, headers = search_github(
        args.query, args.sort, args.order, args.language, args.min_stars, per_page=30, token=args.token
    )
    results = fetch_results(session, base_url, params,
                             headers, args.num_results)

    if not results:
        print("No repositories found. Try a different search term.")
        return

    print(f"\nFound {len(results)} repositories. Top results:")
    display_results(results, args.display_num)

    if file_format == 'json':
        save_to_json(results, filename, args.translate)
    elif file_format == 'csv':
        save_to_csv(results, filename, args.translate)
    elif file_format == 'tsv':
        save_to_csv(results, filename, args.translate, delimiter='\t')
    elif file_format == 'xml':
        save_to_xml(results, filename, args.translate)


if __name__ == "__main__":
    main()
