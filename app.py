import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Page Config (MUST BE FIRST)
st.set_page_config(page_title="KIU Portal", layout="wide")

# 2. Database Connection
URL = "https://uxtmgdenwfyuwhezcleh.supabase.co"
KEY = "sb_publishable_1BIwMEH8FVDv7fFafz31uA_9FqAJr0-"

@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)

supabase = get_supabase()

st.title("🎓 KIU Learning Portal")

# 3. Stable App Logic
try:
    # Fetch existing columns safely
    response = supabase.table("materials").select("course_program, material_title").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        search = st.text_input("🔍 Search for a program", placeholder="e.g. Computer Science")
        
        if not search:
            st.subheader("Explore All Programs")
            unique_courses = df['course_program'].unique()
            cols = st.columns(3)
            for i, course in enumerate(unique_courses):
                with cols[i % 3]:
                    st.info(f"📚 {course}")
        else:
            filtered = df[df['course_program'].str.contains(search, case=False, na=False)]
            # width='stretch' is the modern replacement for use_container_width
            st.dataframe(filtered, width='stretch')
    else:
        st.warning("Database connected, but no course materials found.")

except Exception as e:
    st.error("Synchronizing with database... please refresh.")
    print(f"STABLE_ERROR: {e}")
