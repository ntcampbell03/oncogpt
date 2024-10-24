import os
import shutil
import threading
from fpdf import FPDF
import requests
import json
import textwrap

NUM_THREADS = 10
DIR = './data'
SEARCH_TERM = "oncology"
NUM_DOCS = 1000

article_url = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{article_id}/ascii"
pmc_id_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={search_term}&retmax={retmax}&retstart={retstart}"
# Filter by years, countries, ``
def get_pmc_ids(search_term, num_docs):
    """ Get PMC IDs from articles from a given search term search """
    res = []
    retmax = min(num_docs, 1000)
    for retstart in range(0, num_docs, 1000):
        search_url = pmc_id_url.format(search_term=search_term, retmax=retmax, retstart=retstart)
        print(f"Searching url: {search_url}")
        r = requests.get(search_url).text.split('\n')
        for i in range(3, len(r)):
            line = r[i]
            if line.startswith("<Id>"):
                pmc_id = "PMC" + line[4:-5] # Just the number
                res.append(pmc_id)
    print(f"Retrieving {len(res)} documents")
    return res

def get_article(article_id):
    """ Get article from its PMC ID """
    search_url = article_url.format(article_id=article_id)
    r = requests.get(search_url).text
    try:
        r_json = json.loads(r)
        print(f'{count}: Got article {article_id}')
    except Exception as e:
        print(e)
        print(f'JSON load failed: {r}')
        return
    passages = [passage['text'] for passage in r_json[0]['documents'][0]['passages']]

    # Write to individual PDFs
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 11)
    for line in passages:
        for wrapped_line in textwrap.wrap(line, 100): # Split lines to length 100
            pdf.cell(200, 10, txt = wrapped_line, ln = 1, align = 'L')
    pdf.output(f"{DIR}/{article_id}.pdf")

count = 0
def get_all_documents(pmc_ids):
    """ Get all documents in a list of PMC ids"""
    global count
    for pmc_id in pmc_ids:
        count += 1
        get_article(pmc_id)
    return f"Got {count} articles"

def split(a, n):
    """ Split a list into roughly n parts """
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))



# Remove and remake directory
if os.path.exists(DIR):
    shutil.rmtree(DIR)
os.makedirs(DIR)

pmc_ids = get_pmc_ids(SEARCH_TERM, NUM_DOCS)

# Multithreading
threads = []
for pmc_ids_part in split(pmc_ids, NUM_THREADS):
    thread = threading.Thread(target=get_all_documents, args=(pmc_ids_part,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
