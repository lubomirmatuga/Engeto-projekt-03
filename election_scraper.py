# projekt_3.py: třetí projekt do Engeto Online Python Akademie

# author: Ľubomír Maťuga
# email: matugalubomir@gmail.com
# discord: Ľubomír Maťuga

# ELECTION SCRAPER

# Import knihoven
import sys
import csv
import requests
from bs4 import BeautifulSoup

# Globální seznamy pro uložení dat
voter_counts = []
participation_counts = []
valid_votes_counts = []

# Stahování HTML obsahu z dané URL a vrácení BeautifulSoup objekt
def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Detekce chyb HTML požadavků
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    except requests.exceptions.RequestException as e:
        print(f"CHYBA PŘI STAHOVÁNÍ DAT Z: {url}: {e} !")
        return None

# Ošetření chyby vstupu s argumenty
if len(sys.argv) == 3:
    print("STAHUJI DATA Z VYBRANÉHO URL:", sys.argv[1])
    repeathtml = fetch_html(sys.argv[1])  # Uložení html pro další využití
    if repeathtml is None:
        print("NEBYLO MOŽNÉ STÁHNOUT DATA! UKONČUJI PROGRAM...")
        quit()
else:
    print('ŠPATNÝ VSTUP S ARGUMENTY! UKONČUJI PROGRAM...')
    quit()

# Vracení seznamu měst v daném okrese
def extract_towns() -> list:
    towns = []
    town_elements = repeathtml.find_all("td", class_="overflow_name")
    for element in town_elements:
        towns.append(element.text)
    return towns

# Vrácení seznamu URL odkazů na stránky jednotlivých obcí v daném okresu
def extract_links() -> list:
    links = []
    link_elements = repeathtml.find_all("td", class_="cislo")
    for element in link_elements:
        a_tag = element.find("a")

        # Kontrola existenci <a> tagu s atrubutem href
        if a_tag and "href" in a_tag.attrs:  
            link = a_tag["href"]
            links.append(f"https://volby.cz/pls/ps2017nss/{link}")
    return links

# Vrácení seznamu identifikačních čísel jednotlivých obcí
def extract_ids() -> list:
    ids = []
    id_elements = repeathtml.find_all("td", "cislo")
    for element in id_elements:
        ids.append(element.text)
    return ids

# Vrácení seznamu kandidujících politických stran v daném okresu
def extract_parties() -> list:
    town_links = extract_links()
    response = requests.get(town_links[0])
    town_soup = BeautifulSoup(response.text, "html.parser")
    party_elements = town_soup.find_all("td", class_="overflow_name")
    return [element.text for element in party_elements]

# Přidání počtů registrovaných voličů, zúčastněných voličů a platných hlasů + Zápis do globálních seznamů
def gather_voter_data() -> None:
    town_links = extract_links()
    for link in town_links:
        response = requests.get(link)
        village_soup = BeautifulSoup(response.text, "html.parser")
        
        # Registrovaní voliči
        voters_element = village_soup.find("td", headers="sa2")
        voter_counts.append(voters_element.text.replace('\xa0', ' ') if voters_element else 'N/A')
        
        # Zúčastnení voliči
        participation_element = village_soup.find("td", headers="sa3")
        participation_counts.append(participation_element.text.replace('\xa0', ' ') if participation_element else 'N/A')
        
        # Platné hlasy
        valid_votes_element = village_soup.find("td", headers="sa6")
        valid_votes_counts.append(valid_votes_element.text.replace('\xa0', ' ') if valid_votes_element else 'N/A')

# Vrácení seznamu výsledků hlasování pro každou stranu v jednotlivých obcích (v %)
def collect_vote_percentages() -> list:
    links = extract_links()
    all_votes = []
    for link in links:
        soup = fetch_html(link)
        vote_elements = soup.find_all("td", headers=["t1sb4", "t2sb4"])
        votes = [element.text + ' %' for element in vote_elements if element.text]
        all_votes.append(votes if votes else ['N/A'])
    return all_votes

# Vytváření dat pro výstupní CSV soubor
def prepare_csv_data() -> list:
    rows = []
    gather_voter_data()
    towns = extract_towns()
    ids = extract_ids()
    vote_percentages = collect_vote_percentages()

    data = zip(ids, towns, voter_counts, participation_counts, valid_votes_counts)
    temp_data = [[id, town, voter, participation, valid_vote] for id, town, voter, participation, valid_vote in data]
    combined_data = zip(temp_data, vote_percentages)
    
    for temp_row, vote_row in combined_data:
        rows.append(temp_row + vote_row)
    return rows

# Generování a ukládání CSV souboru
def save_election_results(url, output_file) -> None:
    try:
        header = ['Obecní kód', 'Název obce', 'Registrovaní voliči', 'Vydané obálky', 'Platné hlasy']
        rows = prepare_csv_data()
        parties = extract_parties()
        print("UKLÁDÁM DO SOUBORU:", output_file)
        if parties:
            header.extend(parties)

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(rows)
        
        print("UKONČUJI", sys.argv[0])
    except Exception as e:
        print(f"DOŠLO K NEOČEKÁVANÉ CHYBĚ: {e}. UKONČUJI PROGRAM...")
        quit()

# Hlavní blok programu
if __name__ == '__main__':  
    url_address = sys.argv[1]
    output_filename = sys.argv[2]
    save_election_results(url_address, output_filename)