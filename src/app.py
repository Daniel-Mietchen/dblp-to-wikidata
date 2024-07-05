import streamlit as st
from app_utils import get_person_candidates, get_coauthors_list, get_proceedings_list, get_scholarly_article_list, get_scholarly_article_author_list
import pandas as pd

def on_name_change():
    pass

def on_search_click():
    st.session_state['search_done'] = True

def view_search_id():
    st.title("Search for your DBLP ID")
    author_name = st.text_input("Your name", key='text_input', on_change=on_name_change)

    if search_button:
        res_list = get_person_candidates(author_name)
        df = pd.DataFrame(res_list, columns=['Name', 'URL'])
        st.dataframe(
        df,
        column_config={
            "URL": st.column_config.LinkColumn(
            ),
        },
        hide_index=True,
        )
    else:
        pass

    st.info("You can also search for your ID in the DBLP search, https://dblp.org/search")
    

def generate_coauthors_and_proceedings():
    st.subheader("Generate coauthor and proceedings files for Wikidata linking")
    # "https://dblp.org/pid/134/6661"
    dblp_id = st.text_input("Your DBLP ID", key='dblp_id')
    generate_coauthors_button = st.button('Generate Files')
    if generate_coauthors_button:
        print("Querying for coauthors in DBLP")
        progress_bar = st.progress(33)
        status_text = st.empty()
        status_text.text(f"Progress: 33%")
        coauthor_list = get_coauthors_list(dblp_id)
        st.write(f"A CSV file is generated with {len(coauthor_list)} coauthors ...")
        csv = coauthor_list.to_csv(index=False)
        csv_bytes = csv.encode('utf-8')
        st.dataframe(coauthor_list)
        st.download_button(
            label="Download data as CSV",
            data=csv_bytes,
            file_name='coauthor_list.csv',
            mime='text/csv'
        )
        progress_bar.progress(66)
        status_text.text(f"Progress: 66%")

        proceedings_list = get_proceedings_list(dblp_id)
        st.write(f"A CSV file is generated with {len(proceedings_list)} proceedings ...")
        pro_csv = proceedings_list.to_csv(index=False)
        pro_csv_bytes = pro_csv.encode('utf-8')
        st.dataframe(proceedings_list)
        st.download_button(
            label="Download proceedings list as CSV",
            data=pro_csv_bytes,
            file_name='proceedings_list.csv',
            mime='text/csv',
        )
        progress_bar.progress(100)
        status_text.text(f"Progress: 100%")

def generate_articles_and_authors():
    st.subheader("Generate scholary article list for ingesting to Wikidata")
    st.subheader("Linked Coauthors File:")
    coauthor_map_file = st.file_uploader("Upload coauthor map file", type="csv")
    if coauthor_map_file is not None:
        coauthor_map_df = pd.read_csv(coauthor_map_file)
        coauthor_map_df = coauthor_map_df[['dblp_id', 'name', 'wd_id']]
        coauthor_map_df = coauthor_map_df[coauthor_map_df['wd_id'].notna() & (coauthor_map_df['wd_id'] != '')]
        st.write(coauthor_map_df)
        author_map_dict = coauthor_map_df.set_index('name')['wd_id'].to_dict()

    proceedings_map_file = st.file_uploader("Upload proceedings map file", type="csv")
    if proceedings_map_file is not None:
        proceedings_map_df = pd.read_csv(proceedings_map_file)
        proceedings_map_df = proceedings_map_df[proceedings_map_df['wd_id'].notna() & (proceedings_map_df['wd_id'] != '')]
        proceedings_map_df = proceedings_map_df[['title', 'dblp_id', 'wd_id']]
        st.write(proceedings_map_df)
        proceedings_map_dict = proceedings_map_df.set_index('dblp_id')['wd_id'].to_dict()

    #df_dict = proceedings_map_df.set_index('proceedings')['name'].to_dict()

    dblp_id = "https://dblp.org/pid/134/6661"
    generate_articles_button = st.button('Generate Files')
    if generate_articles_button:
        scholarly_article_list = get_scholarly_article_list(dblp_id)
        if proceedings_map_dict:
            scholarly_article_list['proceedings_id'] = scholarly_article_list['proceedings_id'].map(proceedings_map_dict)
        st.dataframe(scholarly_article_list)

        scholarly_article_author_list = get_scholarly_article_author_list(dblp_id)
        if author_map_dict:
            scholarly_article_author_list['author_wd_id'] = scholarly_article_author_list['name'].map(author_map_dict)
        scholarly_article_author_list['author_name_string'] = scholarly_article_author_list.apply(lambda row: row['name'] if pd.isna(row['author_wd_id']) else None, axis=1)

        scholarly_article_author_list = scholarly_article_author_list[['dblp_id', 'title', 'ordinal', 'author_wd_id', 'author_name_string']]
        st.dataframe(scholarly_article_author_list)


st.title('DBLP to Wikidata: Publish Your Scholar Data to Wikidata')
st.sidebar.title("Follow the steps:")
st.sidebar.button("1. Search your DBLP ID", on_click=view_search_id)
st.sidebar.button("2. Generate coauthors and proceedings", on_click=generate_coauthors_and_proceedings)
st.sidebar.button("3. Generate scholarly articles and article authors", on_click=generate_coauthors_and_proceedings,)
#generate_coauthors_and_proceedings()
generate_articles_and_authors()













