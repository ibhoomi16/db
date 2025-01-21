import streamlit as st
from pymongo import MongoClient
import json
import re


# Function to connect to MongoDB
def connect_to_mongo(db_url, db_name, collection_name):
    """
    Connect to MongoDB and return the collection.
    """
    client = MongoClient(db_url = "mongodb://localhost:27017")
    db = client[db_name]
    return db[collection_name]


# Function to fetch data from MongoDB based on job ID
def fetch_data_from_mongo(collection, job_id):
    """
    Fetch data from MongoDB collection using the provided job ID.
    """
    try:
        documents = collection.find({"job_id": job_id})
        return list(documents)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []


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
def generate_json_chunks(recommendations, title, stage, disease, specialty, job_id, fetched_data):
    """
    Generate JSON chunks using the extracted recommendations, user inputs, and MongoDB data.
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
        "job_id": job_id,
        "fetched_data": fetched_data  # Include MongoDB fetched data
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
job_id = st.text_input("Job ID (used for fetching MongoDB data)", "")
title = st.text_input("Guide Title", "Distal Radius Fracture Rehabilitation")
stage = st.text_input("Stage", "Rehabilitation")
disease = st.text_input("Disease Title", "Fracture")
specialty = st.text_input("Specialty", "orthopedics")

# File uploader for Markdown file
st.header("Upload Markdown File")
uploaded_file = st.file_uploader("Upload a Markdown (.md) file", type=["md"])

# Process the data if a job ID and markdown file are provided
if st.button("Process Data"):
    if db_url and db_name and collection_name and job_id and uploaded_file:
        try:
            # Connect to MongoDB and fetch data
            collection = connect_to_mongo(db_url, db_name, collection_name)
            fetched_data = fetch_data_from_mongo(collection, job_id)

            if fetched_data:
                st.success(f"Fetched {len(fetched_data)} documents from the database.")

                # Process the uploaded Markdown file
                md_content = uploaded_file.read().decode("utf-8")
                recommendations = extract_recommendations(md_content)

                if recommendations:
                    # Generate JSON chunks using user inputs and MongoDB data
                    json_chunks = generate_json_chunks(recommendations, title, stage, disease, specialty, job_id, fetched_data)

                    # Display the generated JSON
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
                    st.warning("No recommendations found in the uploaded Markdown file. Please check the file format.")
            else:
                st.warning("No data found for the provided Job ID in the database.")

        except Exception as e:
            st.error(f"Error processing data: {e}")
    else:
        st.warning("Please fill in all required fields and upload a Markdown file.")

