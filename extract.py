import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionError
import json
import re

# Function to connect to MongoDB
def connect_to_mongo(db_url, db_name, collection_name):
    """
    Connect to MongoDB and return the collection.
    """
    try:
        client = MongoClient(db_url, serverSelectionTimeoutMS=5000)  # Timeout after 5 seconds
        client.server_info()  # Test the connection
        db = client[db_name]
        return db[collection_name]
    except ConnectionError as e:
        st.error(f"Could not connect to MongoDB: {e}")
        return None


# Function to fetch Markdown content from MongoDB based on job ID
def fetch_markdown_from_mongo(collection, job_id):
    """
    Fetch Markdown content from MongoDB collection using the provided job ID.
    """
    try:
        document = collection.find_one({"job_id": job_id})
        if document and "markdown_content" in document:
            return document["markdown_content"]
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching Markdown content: {e}")
        return None


# Function to extract recommendations from Markdown content
def extract_recommendations(md_content):
    """
    Extract recommendations from Markdown table content.
    """
    # Split content by lines and filter out the header and separator lines
    lines = md_content.splitlines()
    table_lines = [line for line in lines if "|" in line and not re.match(r"^-+$", line)]

    recommendations = []
    for line in table_lines:
        # Split the line into cells
        cells = [cell.strip() for cell in line.split("|")[1:-1]]  # Ignore outer empty cells
        if len(cells) == 3:  # Ensure the row has the correct number of columns
            cor, loe, recommendation = cells
            # Skip header row
            if cor.lower() == "cor" and loe.lower() == "loe":
                continue
            recommendations.append({
                "recommendation_content": recommendation.strip(),
                "recommendation_class": cor.strip(),
                "rating": loe.strip()
            })

    return recommendations


# Function to generate JSON chunks
def generate_json_chunks(recommendations, title, stage, disease, specialty, job_id):
    """
    Generate JSON chunks using the extracted recommendations and user inputs.
    """
    base_json = {
        "title": title,
        "subCategory": [],
        "guide_title": title,
        "stage": [stage],
        "disease": [disease],
        "rationales": [],
        "references": [],
        "specialty": [specialty],
        "job_id": job_id
    }

    json_chunks = []
    for rec in recommendations:
        chunk = base_json.copy()
        chunk.update({
            "recommendation_content": rec["recommendation_content"],
            "recommendation_class": rec["recommendation_class"],
            "rating": rec["rating"]
        })
        json_chunks.append(chunk)

    return json_chunks


# Streamlit app
st.title("Markdown to JSON with MongoDB Integration")

# MongoDB Configuration Inputs
st.header("MongoDB Configuration")
db_url = st.text_input("MongoDB URL", "mongodb://localhost:27017")
db_name = st.text_input("Database Name", "document-parsing")
collection_name = st.text_input("Collection Name", "dps_data")

# Input for job ID
st.header("Enter Metadata for Job")
job_id = st.text_input("Job ID (used for fetching Markdown from MongoDB)", "")
title = st.text_input("Guide Title", "Distal Radius Fracture Rehabilitation")
stage = st.text_input("Stage", "Rehabilitation")
disease = st.text_input("Disease Title", "Fracture")
specialty = st.text_input("Specialty", "orthopedics")

# Process the data if a job ID is provided
if st.button("Process Data"):
    if db_url and db_name and collection_name and job_id:
        collection = connect_to_mongo(db_url, db_name, collection_name)

        if collection:
            try:
                markdown_content = fetch_markdown_from_mongo(collection, job_id)

                if markdown_content:
                    recommendations = extract_recommendations(markdown_content)

                    if recommendations:
                        json_chunks = generate_json_chunks(recommendations, title, stage, disease, specialty, job_id)
                        st.subheader("Generated JSON:")
                        st.json(json_chunks)

                        # Option to download JSON file
                        json_output = json.dumps(json_chunks, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_output,
                            file_name="output.json",
                            mime="application/json"
                        )
                    else:
                        st.warning("No recommendations found in the Markdown content.")
                else:
                    st.warning(f"No Markdown content found for Job ID: {job_id}")
            except Exception as e:
                st.error(f"Error fetching recommendations: {e}")
        else:
            st.error("Failed to connect to MongoDB. Please check your connection details.")
    else:
        st.warning("Please fill in all required fields.")



