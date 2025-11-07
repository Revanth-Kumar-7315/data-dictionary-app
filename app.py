import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Automated Data Dictionary Generator",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Application Title and Description ---
st.title("📖 Automated Data Dictionary Generator")
st.markdown("Upload a CSV file, and let AI create the data dictionary for you. This tool analyzes your column headers to guess data types and generate plain-English descriptions.")

# --- API Key Input ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Google API Key", type="password")

# --- Main Application Logic ---
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read only the header to get column names without loading the whole file
    try:
        df_columns = pd.read_csv(uploaded_file, nrows=0).columns.tolist()
        st.info(f"**Detected Columns:** `{', '.join(df_columns)}` ({len(df_columns)} columns found)")

        if st.button("✨ Generate Data Dictionary", use_container_width=True, type="primary"):
            if not api_key:
                st.error("Please enter your Google API Key in the sidebar to proceed.")
            else:
                try:
                    # --- AI Generation Logic ---
                    with st.spinner("AI is analyzing your columns and generating the dictionary... 🧠"):
                        # Configure the Gemini API
                        genai.configure(api_key=api_key)

                        # Define the JSON schema for the expected response
                        dictionary_schema = {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "The name of the column."},
                                    "type": {"type": "string", "description": "The guessed data type (e.g., String, Integer, Float, Date)."},
                                    "description": {"type": "string", "description": "A plain-English description of what the column represents."},
                                },
                                "required": ["name", "type", "description"]
                            }
                        }
                        
                        # Set up the model with the JSON response type
                        model = genai.GenerativeModel(
                            model_name='gemini-1.5-flash',
                            generation_config={"response_mime_type": "application/json"},
                        )

                        # Create the prompt using the user's template
                        column_list_string = ", ".join(df_columns)
                        prompt = f"""
                        You are a professional data analyst. Your task is to create a data dictionary.

                        Based on this list of column names from a CSV file:
                        {column_list_string}

                        Please generate a plain-English 'description' and a 'data type' guess for each column.
                        Return the result ONLY as a clean JSON array that adheres to the provided schema. Do not include any text before or after the JSON array.
                        """

                        # Call the API
                        response = model.generate_content(
                            prompt,
                            safety_settings={
                                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                            }
                        )

                        # Parse the response and display it
                        dictionary_list = json.loads(response.text)
                        df_dictionary = pd.DataFrame(dictionary_list)
                        
                        st.success("Data Dictionary Generated Successfully!")
                        st.dataframe(df_dictionary, use_container_width=True)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.error("Please check your API key and the file format. If the issue persists, check the console for more details.")

    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
else:
    st.warning("Please upload a CSV file to begin.")