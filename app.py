import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st

# Load the environment variables from the .env file
load_dotenv()

# Connect to the PostgreSQL database
con = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = con.cursor()

# Define the updated Genre Options
GENRE_OPTIONS = [
    'Writing Refinement', 
    'Article Summary', 
    'Conversation Starter', 
    'Brainstorming Session', 
    'Creative Writing', 
    'Problem Solving',
    'Question Generation',
    'Research Inquiry',
    'Other'
]

# Create the prompts table if it does not exist
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS prompts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        prompt TEXT NOT NULL,
        genre TEXT NOT NULL,
        is_favorite BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """
)
con.commit()

# Define the function to add a new prompt
def add_prompt(title, prompt_text, genre, is_favorite):
    with con:
        cur.execute(
            """
            INSERT INTO prompts (title, prompt, genre, is_favorite)
            VALUES (%s, %s, %s, %s)
            """,
            (title, prompt_text, genre, is_favorite)
        )
        con.commit()

# Define the function to get existing prompts, with optional search
def get_prompts(search_query=''):
    with con:
        if search_query:
            cur.execute(
                """
                SELECT * FROM prompts
                WHERE title ILIKE %s OR prompt ILIKE %s
                ORDER BY created_at DESC
                """,
                (f'%{search_query}%', f'%{search_query}%')
            )
        else:
            cur.execute("SELECT * FROM prompts ORDER BY created_at DESC")
        return cur.fetchall()

# Define the function to update an existing prompt
def update_prompt(id, title, prompt_text, genre, is_favorite):
    with con:
        cur.execute(
            """
            UPDATE prompts
            SET title = %s, prompt = %s, genre = %s, is_favorite = %s, updated_at = %s
            WHERE id = %s
            """,
            (title, prompt_text, genre, is_favorite, datetime.now(), id)
        )
        con.commit()

# Define the function to delete a prompt
def delete_prompt(prompt_id):
    with con:
        cur.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
        con.commit()

# Define the function to toggle the favorite status of a prompt
def toggle_favorite(prompt_id):
    with con:
        cur.execute(
            """
            UPDATE prompts
            SET is_favorite = NOT is_favorite
            WHERE id = %s
            """,
            (prompt_id,)
        )
        con.commit()

# Streamlit UI
st.title("Promptbase")
st.subheader("Manage your ChatGPT prompts")

# Form for adding new prompts
with st.form("New Prompt", clear_on_submit=True):
    new_title = st.text_input("Title", "")
    new_prompt_text = st.text_area("Prompt", "", height=200)
    new_genre = st.selectbox("Genre", GENRE_OPTIONS)
    new_is_favorite = st.checkbox("Favorite this prompt")
    submit_button = st.form_submit_button("Submit")

    if submit_button:
        if new_title and new_prompt_text:
            add_prompt(new_title, new_prompt_text, new_genre, new_is_favorite)
            st.success("Prompt added successfully!")
        else:
            st.error("Title and prompt cannot be empty.")

# Search functionality
search_query = st.text_input('Search prompts')
search_button = st.button('Search')
if search_button:
    prompts = get_prompts(search_query)
else:
    prompts = get_prompts()

# Display existing prompts
for p in prompts:
    with st.expander(f"{p[1]} - {p[3]} ({'Favorite' if p[4] else 'Not Favorite'})"):
        st.text(p[2])  # The prompt content
        # Buttons for editing, deleting, and toggling favorite status
        if st.button("Edit", key=f"edit-{p[0]}"):
            # Pre-fill form with current data for editing
            with st.form(f"edit_prompt_{p[0]}", clear_on_submit=True):
                edit_title = st.text_input("Title", value=p[1])
                edit_prompt_text = st.text_area("Prompt", value=p[2], height=200)
                edit_genre = st.selectbox("Genre", GENRE_OPTIONS, index=GENRE_OPTIONS.index(p[3]))
                edit_is_favorite = st.checkbox("Favorite this prompt", value=p[4])
                submit_update = st.form_submit_button("Update Prompt")

                if submit_update:
                    update_prompt(p[0], edit_title, edit_prompt_text, edit_genre, edit_is_favorite)
                    st.experimental_rerun()

        if st.button("Delete", key=f"del-{p[0]}"):
            delete_prompt(p[0])
            st.experimental_rerun()
            
        if st.button("Toggle Favorite", key=f"fav-{p[0]}"):
            toggle_favorite(p[0])
            st.experimental_rerun()

