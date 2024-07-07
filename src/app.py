import streamlit as st
from app_utils import get_person_candidates, get_coauthors_list, get_proceedings_list, get_scholarly_article_list, get_scholarly_article_author_list
import pandas as pd

def split_name_and_id(selected_id):
    if selected_id == "Not Selected":
        return None, None
    else:
        name, dblp_id = selected_id.split("(")
        name = name.strip()
        dblp_id = dblp_id.replace(")","").strip()
        return name, dblp_id

def set_current_view(c_view: str):
    st.session_state.current_view = c_view

def clear_dblp_id():
    st.session_state.current_view = "search_id"
    st.session_state["selected_name"] = None
    st.session_state["selected_dblp_id"] = None

def on_selectbox_change():
    selected_value = st.session_state["selected_id"]
    name, dblp_id = split_name_and_id(selected_value)
    st.session_state["selected_name"] = name
    st.session_state["selected_dblp_id"] = dblp_id

def view_search_id():
    st.subheader("Search for your DBLP ID")
    st.info("You can also search for your ID in the DBLP search, https://dblp.org/search")
    author_name = st.text_input("Your name", key='text_input')
    search_button = st.button('Search for DBLP ID')

    if "selected_name" in st.session_state and "selected_dblp_id" in st.session_state:
        selected_results_container = st.container(border=True)
        selected_results_container.subheader("Selected Person:")
        selected_results_container.write(f"\tFull Name: {st.session_state['selected_name']}")
        selected_results_container.write(f"\tDBLP ID: {st.session_state['selected_dblp_id']}")

    if search_button:
        res_list = get_person_candidates(author_name)
        res_list = ["Not Selected"] + [f"{res[0]} ({res[1]})" for res in res_list]
        st.session_state["res_list"] = res_list
        
    if "res_list" in st.session_state:
        selected_id = st.radio(
        "DBLP search results:",
        st.session_state["res_list"],
        key="selected_id",
        on_change=on_selectbox_change)


def generate_coauthors_and_proceedings():
    st.subheader("Generate coauthor and proceedings files for Wikidata linking")
    # "https://dblp.org/pid/134/6661"
    if "selected_dblp_id" in st.session_state:
        dblp_id = st.text_input("Your DBLP ID", key='dblp_id', value=st.session_state["selected_dblp_id"], disabled=True)
        st.button("Clear DBLP ID", on_click=clear_dblp_id, key="clear_id_1")
    else:
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
    if "selected_dblp_id" in st.session_state:
        dblp_id = st.text_input("Your DBLP ID", key='dblp_id_2', value=st.session_state["selected_dblp_id"], disabled=True)
        st.button("Clear DBLP ID", on_click=clear_dblp_id, key="clear_id_2")
    else:
        dblp_id = st.text_input("Your DBLP ID", key='dblp_id_2')
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


# Initialize session state if not already done
if 'current_view' not in st.session_state:
    st.session_state.current_view = "search_id"

st.title('DBLP to Wikidata: Publish Your Scholar Data to Wikidata')
st.sidebar.title("Follow the steps:")
st.sidebar.button("1. Search your DBLP ID", on_click=set_current_view, args=('search_id',))
st.sidebar.button("2. Generate coauthors and proceedings", on_click=set_current_view, args=('coauthor_proceeding',))
st.sidebar.button("3. Generate scholarly articles and article authors", on_click=set_current_view, args=('articles_authors',))

if st.session_state.current_view == "search_id":
    view_search_id()
elif st.session_state.current_view == "coauthor_proceeding":
    generate_coauthors_and_proceedings()
elif st.session_state.current_view == "articles_authors":
    generate_articles_and_authors()













