import requests
import pandas as pd
import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON


coauthor_list_query = """
PREFIX dblp: <https://dblp.org/rdf/schema#> 
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX datacite: <http://purl.org/spar/datacite/>

SELECT DISTINCT ?dblp_id ?name ?wikidata ?orcid ?orkg ?scholar ?acm ?github ?twitter {
    ?paper a dblp:Publication, dblp:Inproceedings;
        dblp:hasSignature ?sign;
		dblp:hasSignature ?sign_coauthor .
	
	?sign dblp:signatureCreator <__replace_author_id__> .
    ?sign_coauthor dblp:signatureCreator ?dblp_id .
	
    ?dblp_id dblp:primaryCreatorName ?name .
    OPTIONAL { ?dblp_id dblp:orcid ?orcid }
    OPTIONAL { ?dblp_id dblp:wikidata ?wikidata }
    OPTIONAL { ?dblp_id dblp:webpage ?scholar . FILTER (STRSTARTS(str(?scholar), "https://scholar.google.com/")) }
    OPTIONAL { ?dblp_id dblp:webpage ?github . FILTER (STRSTARTS(str(?github), "https://github.com/")) }
    OPTIONAL { ?dblp_id dblp:webpage ?twitter . FILTER (STRSTARTS(str(?twitter), "https://twitter.com/")) }
    OPTIONAL { ?dblp_id dblp:webpage ?acm . FILTER (STRSTARTS(str(?acm), "https://dl.acm.org/profile/")) }
    OPTIONAL { ?dblp_id owl:sameAs ?orkg . FILTER (STRSTARTS(str(?orkg), "https://orkg.org/resource/")) }
}
ORDER BY ?dblp_id
"""
coauthor_list_vars = ['dblp_id', 'name', 'wikidata', 'orcid', 'orkg', 'scholar', 'acm', 'github', 'twitter']

proceedings_list_query = """
PREFIX dblp: <https://dblp.org/rdf/schema#> 
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX datacite: <http://purl.org/spar/datacite/>

SELECT DISTINCT ?dblp_id ?title ?doi ?isbn ?year ?series ?seriesVolume ?publisher {
    ?paper a dblp:Publication, dblp:Inproceedings;
        dblp:hasSignature ?sign;
        dblp:publishedAsPartOf  ?dblp_id .
	?sign dblp:signatureCreator <__replace_author_id__> .

    ?dblp_id dblp:title ?title .
    OPTIONAL { ?dblp_id dblp:isbn ?isbn }
    OPTIONAL { ?dblp_id dblp:yearOfPublication ?year }
    OPTIONAL { ?dblp_id dblp:doi ?doi }
    OPTIONAL { ?dblp_id dblp:publishedBy ?publisher }
    OPTIONAL { ?dblp_id dblp:publishedInSeries ?series }
    OPTIONAL { ?dblp_id dblp:publishedInSeriesVolume ?seriesVolume }
}
ORDER BY ?dblp_id
"""
proceedings_list_vars = ['dblp_id', 'title', 'doi', 'isbn', 'year', 'series', 'seriesVolume', 'publisher']

proceedings_editor_list_query = """
PREFIX dblp: <https://dblp.org/rdf/schema#> 
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX datacite: <http://purl.org/spar/datacite/>

SELECT DISTINCT ?proceedings ?ord ?name {
    ?paper a dblp:Publication, dblp:Inproceedings;
        dblp:hasSignature ?sign;
        dblp:publishedAsPartOf  ?proceedings .
	?sign dblp:signatureCreator <__replace_author_id__> .

    ?proceedings dblp:title ?title .
    ?proceedings dblp:hasSignature ?proc_sign .
    ?proc_sign dblp:signatureCreator ?editor;
        dblp:signatureOrdinal ?ord .
    ?editor dblp:primaryCreatorName ?name .
}
"""
proceedings_editor_list_vars = ['proceedings', 'ord', 'name']

scholarly_article_list_query = """
PREFIX dblp: <https://dblp.org/rdf/schema#> 
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX datacite: <http://purl.org/spar/datacite/>

SELECT DISTINCT ?dblp_id ?title ?doi ?pages ?year ?proceedings_id {
    ?dblp_id a dblp:Publication, dblp:Inproceedings;
        dblp:hasSignature ?sign;
        dblp:title ?title;
        dblp:publishedAsPartOf  ?proceedings_id .
	?sign dblp:signatureCreator <__replace_author_id__> .

    OPTIONAL { ?dblp_id dblp:doi ?doi }
    OPTIONAL { ?dblp_id dblp:pagination ?pages }
    OPTIONAL { ?dblp_id dblp:yearOfPublication ?year }
}
""" 
scholarly_article_list_vars = ['dblp_id', 'title', 'doi', 'pages', 'year', 'proceedings_id']

scholarly_article_author_list_query = """
PREFIX dblp: <https://dblp.org/rdf/schema#> 
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX datacite: <http://purl.org/spar/datacite/>

SELECT DISTINCT ?dblp_id ?title ?ordinal ?name  {
    ?dblp_id a dblp:Publication, dblp:Inproceedings;
        dblp:title ?title;
        dblp:hasSignature ?sign;
        dblp:hasSignature ?sign_coauthor .
	
	?sign dblp:signatureCreator <__replace_author_id__> .
    ?sign_coauthor dblp:signatureCreator ?dblp_person;
        dblp:signatureOrdinal ?ordinal .
    
    ?dblp_person dblp:primaryCreatorName ?name .
}
"""
scholarly_article_author_list_vars = ['dblp_id', 'title', 'ordinal', 'name']

author_search_api = "https://dblp.org/search/author/api"
dblp_sparql_endpoint = "https://sparql.dblp.org/sparql"

def remove_clean_fullstop(value):
    if isinstance(value, str) and value.endswith('.'):
        return value[:-1]
    return value

def get_results(query):
    sparql = SPARQLWrapper(dblp_sparql_endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

def parse_results(results, var_list):
    processed_results = list()
    for result in results["results"]["bindings"]:
        result_array = list()
        for var in var_list:
            if var in result:
                result_array.append(result[var]['value'])
            else:
                result_array.append(None)
        processed_results.append(result_array)
    df = pd.DataFrame(processed_results, columns=var_list, index=None)
    return df

def execute_query(query, var_list):
    res = get_results(query)
    return parse_results(res, var_list)

def get_person_candidates(name: str):
    params = {'format': 'json', 'q': name}
    response = requests.get(author_search_api, params=params)

    response.raise_for_status()
    json_data = response.json()
    
    res_list = []
    if 'result' in json_data and 'hits' in json_data['result'] and 'hit' in json_data['result']['hits']:
        for res in json_data['result']['hits']['hit']:
            res_list.append([res['info']['author'], res['info']['url']])
    return res_list

def get_proceedings_list(dblp_person_id):
    query = proceedings_list_query.replace("__replace_author_id__", dblp_person_id)
    df = execute_query(query, proceedings_list_vars)
    df = sort_based_on_completeness(df, ['dblp_id'])
    editors_dict  = get_proceedings_editor_list(dblp_person_id)
    df['entity_to_link'] = df['title']
    df['editors'] = df['dblp_id'].map(editors_dict)
    df['doi'] = df['doi'].str.replace("https://doi.org/", "", regex=False)
    df['dblp_id'] = df['dblp_id'].str.replace("https://dblp.org/rec/", "", regex=False)
    df = df[['title', 'entity_to_link', 'editors', 'dblp_id', 'doi', 'isbn', 'year', 'series', 'seriesVolume', 'publisher']]
    return df

def get_proceedings_editor_list(dblp_person_id):
    query = proceedings_editor_list_query.replace("__replace_author_id__", dblp_person_id)
    df = execute_query(query, proceedings_editor_list_vars)
    df = df.sort_values(by=['proceedings', 'ord'])
    df = df.groupby('proceedings')['name'].apply(list).reset_index()
    df_dict = df.set_index('proceedings')['name'].to_dict()
    return df_dict

def get_scholarly_article_list(dblp_person_id):
    query = scholarly_article_list_query.replace("__replace_author_id__", dblp_person_id)
    df = execute_query(query, scholarly_article_list_vars)
    df['dblp_id'] = df['dblp_id'].str.replace("https://dblp.org/rec/", "", regex=False)
    df['proceedings_id'] = df['proceedings_id'].str.replace("https://dblp.org/rec/", "", regex=False)
    df['doi'] = df['doi'].str.replace("https://doi.org/", "", regex=False)
    df['title'] = df['title'].apply(remove_clean_fullstop)
    df['entity_to_link'] = df['title']
    df = df[['title', 'entity_to_link', 'dblp_id', 'doi', 'pages', 'year', 'proceedings_id']]
    return df

def get_scholarly_article_author_list(dblp_person_id):
    query = scholarly_article_author_list_query.replace("__replace_author_id__", dblp_person_id)
    df = execute_query(query, scholarly_article_author_list_vars)
    df['dblp_id'] = df['dblp_id'].str.replace("https://dblp.org/rec/", "", regex=False)
    df['title'] = df['title'].apply(remove_clean_fullstop)
    return df

def get_coauthors_list(dblp_person_id):
    query = coauthor_list_query.replace("__replace_author_id__", dblp_person_id)
    df = execute_query(query, coauthor_list_vars)
    df = sort_based_on_completeness(df, ['dblp_id'])
    df['scholar'] = df['scholar'].str.replace("https://scholar.google.com/citations?user=", "", regex=False)
    df['orcid'] = df['orcid'].str.replace("https://orcid.org/", "", regex=False)
    df['dblp_id'] = df['dblp_id'].str.replace("https://dblp.org/pid/", "", regex=False)
    df['acm'] = df['acm'].str.replace("https://dl.acm.org/profile/", "", regex=False)
    df['github'] = df['github'].str.replace("https://github.com/", "", regex=False)
    df['twitter'] = df['twitter'].str.replace("https://twitter.com/", "", regex=False)
    df['orkg'] = df['orkg'].str.replace("https://orkg.org/resource/", "", regex=False)
    df['entity_to_link'] = np.where(df['wikidata'].notnull(), df['wikidata'].str.replace("http://www.wikidata.org/entity/", "", regex=False), df['name'])
    df = df[['name', 'entity_to_link', 'wikidata', 'dblp_id', 'orcid', 'orkg', 'scholar', 'acm', 'github', 'twitter']]
    return df

def sort_based_on_completeness(df, sort_by):
    df['non_null_count'] = df.notnull().sum(axis=1)
    df = df.sort_values(by=['non_null_count']+sort_by, ascending=False)
    df = df.drop(columns=['non_null_count'])
    df = df.reset_index(drop=True)
    return df




