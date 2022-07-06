#!/usr/bin/env python
# coding: utf-8

import requests
import json
import sys
from math import ceil

# Function to query DOI from "unpaywall"
def query_doi(doi):    
    doi_num = doi
    #encoded_doi = urllib.parse.quote(doi)
    url = 'https://api.unpaywall.org/v2/'
    params = {'email': 'student@e-uvt.ro'}
    #encoded_url = urllib.parse.quote(url+doi)
    #print (encoded_url)
    try:
        response = requests.get(url+doi_num, params=params)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
        
    received_data = response.json()
    return received_data


# Function to extract metadata from DOI query returned from "unpaywall"
def extract_metadata (json_data, extract_list):
    retrieved_metadata = {}

    for item in extract_list:
        item_value = json_data.get(item)
        retrieved_metadata[item] = item_value
    return retrieved_metadata


# Function to parse the journal records based on ISSN or Title to find occurences
def parse_journal_records (retrieved_metadata, json_data, j_record):    
    item_to_search = retrieved_metadata['journal_issn_l'] if not None else retrieved_metadata['title']
    found_item = [d for i, d in enumerate(json_data) if item_to_search in d.values()]
                    
    if found_item:
        return found_item        

    else:
        return None


# Classify journals basd on the metrics extracted from journal listing(s) and return the best
def classify_journal (best_metrics, issn):
    if any(d['issn'] == issn for d in best_metrics[ : ceil(0.25 * len(best_metrics))]):
        CNATDCU_class = 'ISI ROSU'
    elif any(d['issn'] == issn for d in best_metrics[ceil(0.25 * len(best_metrics)) : ceil(0.5 * len(best_metrics))]):
        CNATDCU_class = 'ISI GALBEN'
    else:
        CNATDCU_class = 'ISI ALB'

    if any(d['issn'] == issn for d in best_metrics[ : ceil(0.20 * 0.25 * len(best_metrics))]):
        CNFIS_class = 'A*'
    elif any(d['issn'] == issn for d in best_metrics[ceil(0.20 * 0.25 * len(best_metrics)) : (ceil(0.25 * len(best_metrics)) + ceil(0.20 * 0.25 * len(best_metrics))) ]):
        CNFIS_class = 'A'
    elif any(d['issn'] == issn for d in best_metrics[(ceil(0.25 * len(best_metrics)) + ceil(0.20 * 0.25 * len(best_metrics))) : ceil(0.5 * len(best_metrics))]):
        CNFIS_class = 'B'
    else:
        CNFIS_class = 'C'
        
    return CNATDCU_class, CNFIS_class
    

# Main function
def main():

    METADATA_TO_RETRIEVE = ['title', 'genre', 'year', 'journal_issn_l']
    METRICS_TO_EXTRACT = ['issn', 'journalImpactFactor', 'articleInfluenceScore']
    
    doi = sys.argv[1]
    #doi = "10.1145/3158661"
    received_data = query_doi(doi)
    retrieved_metadata = extract_metadata(received_data, METADATA_TO_RETRIEVE)
    published_year = retrieved_metadata['year']
    J_RECORDS = ["journals-SCIE-year-" + str(published_year), 
    "journals-SSCI-year-" + str(published_year), 
    "journals-SCIE-year-" + str(published_year - 1), 
    "journals-SSCI-year-" + str(published_year - 1)]

    if retrieved_metadata['genre'] == 'journal-article':
        found_journal_records = None

        while not found_journal_records:    
            for j_record in J_RECORDS:
                file_to_search = j_record + ".json"       
                
                with open(f"data/{file_to_search}", 'r') as opened_file:
                    json_data = json.load(opened_file)
                    found_journal_records = parse_journal_records(retrieved_metadata, json_data, j_record)
                    
                    if found_journal_records:
                        break                                 
                    else:
                        print (f"No records found in {j_record}")

            for found_journal_record in found_journal_records:
                extracted_metrics = []
                cat_sublist = [d for d in json_data if ('categoryName', found_journal_record['categoryName']) in d.items()]
                for long_dict in cat_sublist:
                    short_dict = {metric: long_dict[metric] for metric in METRICS_TO_EXTRACT}
                    extracted_metrics.append(short_dict)
                    
                exist_metrics = f"""
                Journal Database: {j_record}
                ISSN: {found_journal_record['issn']}
                Journal Title: {found_journal_record['journalTitle']}
                Category Name: {found_journal_record['categoryName']}
                Rank: {found_journal_record['rank']} / {len(cat_sublist)}
                Journal Impact Factor: {found_journal_record['journalImpactFactor']}
                Article Influence Score: {found_journal_record['articleInfluenceScore']}
                """                        
                

                sorted_jif = sorted(extracted_metrics, key=lambda k: k['journalImpactFactor'], reverse=True)
                position_in_jif = next((index for (index, d) in enumerate(sorted_jif) if d['issn'] == found_journal_record['issn']))
                sorted_ais = sorted(extracted_metrics, key=lambda k: k['articleInfluenceScore'], reverse=True)
                position_in_ais = next((index for (index, d) in enumerate(sorted_ais) if d['issn'] == found_journal_record['issn']))
                
                best_metrics = None
                if position_in_jif >= position_in_ais:
                    best_metrics = sorted_jif
                else:
                    best_metrics = sorted_ais


                CNATDCU_class, CNFIS_class = classify_journal(best_metrics, found_journal_record['issn'])
                urap_metrics = f"""
                CNATDCU Classification: {CNATDCU_class}
                CNFIS Classification: {CNFIS_class}
                """
            print (exist_metrics)
            print (urap_metrics)

        
    else:
        print(f"The DOI is of genre '{retrieved_metadata['genre']}' and is not a Journal Article")


if __name__ == "__main__":
    main()