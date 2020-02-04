import pandas as pd
import requests
import json
import re
from urllib.parse import quote

with open('config.json', 'r') as f:
    API_KEY = json.load(f)
url = 'https://api.elsevier.com/content/search/scopus'
q = '"inverse reinforcement learning"  AND  ( "system"  OR  "e-learning"  OR  "stochastic"  OR  "smart grids"  OR  "control"  OR  "system controller"  OR  "control tuning"  OR  "optimization")'

class scopus_df:
    def __init__(self):
        self.columns = ['Authors', 'Title', 'Year', 'Cited By', 'Affiliations', 'Author Keywords', 'Source title']
        self.csv = pd.DataFrame(columns=self.columns)

    def get_authors(self, publication: dict) -> list:
        return [author['authname'] for author in publication['author']]

    def get_affiliations(self, publication: dict) -> list:
        return [aff['affilname'].replace(',', ';') for aff in publication['affiliation']]

    def append(self, publication: dict) -> None:
        try:
            authors = ','.join(self.get_authors(publication))
        except KeyError as e:
            return None
        title = publication['dc:title']
        year = re.findall(r'([\d]{4})', publication['prism:coverDisplayDate'])[0]
        source_title = publication['prism:publicationName']
        cites = publication['citedby-count']
        try:
            affiliations = ','.join(self.get_affiliations(publication))
        except KeyError as e:
            affiliations = ''
        try:
            author_kw = ','.join([ii.lstrip().strip() for ii in publication['authkeywords'].split('|')])
        except KeyError as e:
            author_kw = ''
        self.csv = self.csv.append(pd.DataFrame([[authors, title, year, cites, affiliations, author_kw, source_title]], columns=self.columns), ignore_index=True)

def query_to_scopus(url: str, query: str, api: str, start_item: int = 0) -> list:
    return requests.get(url,
                        headers={'Accept': 'application/json', 'X-ELS-APIKey': api},
                        params={'query': query, 'view': 'COMPLETE', 'start': start_item}).json()
def create_df_from_scopus(url: str, query: str, api: str, num_items: int) -> pd.DataFrame():
    assert num_items > 0
    start_item = 0
    publications = scopus_df()
    while start_item < num_items:
        response = query_to_scopus(url, query, api, start_item)
        try:
            batch = response['search-results']['entry']
        except KeyError as e:
            break
        for item in batch:
            publications.append(item)
            start_item += 1
    return publications.csv
    
def check_query(query: str = q) -> int:
    query_parsed = f'TITLE-ABS-KEY({query})' # TODO: Save a history of all the querys with the number of results
    api = API_KEY['api-key']
    return int(query_to_scopus(url, query_parsed, api)['search-results']['opensearch:totalResults'])

def get_csv(num_items: int, query: str = q) -> pd.DataFrame():
    query_parsed = f'TITLE-ABS-KEY({query})'
    api = API_KEY['api-key']
    return create_df_from_scopus(url, query_parsed, api, num_items)

def main():
    num_items = check_query()
    action = input(f'The query returned {num_items} results. Do you want to continue? [y/n] ')
    if 'y' in action or 'Y' in action:
        return get_csv(num_items)
    else:
        print('Aborting...')

if __name__ == '__main__':
    main()