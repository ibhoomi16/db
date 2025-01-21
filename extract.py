import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json
import re

# Function to connect to MongoDB
def connect_to_mongo(db_url, db_name, collection_name):
    """
    Connect to MongoDB and return the collection.
    """
    try:
        client = MongoClient(db_url)
        db = client[db_name]
        return db[collection_name]
    except ConnectionFailure as e:
        st.error(f"MongoDB connection failed: {e}")
        return None

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

# Function to extract recommendations from MongoDB documents
def extract_recommendations_from_db(documents):
    """
    Extract recommendations, ratings, and classes from MongoDB documents.
    """
    recommendations = []
    for doc in documents:
        recommendations.append({
            "recommendation_content": doc.get("recommendation_content", "").strip(),
            "recommendation_class": doc.get("recommendation_class", "").strip(),
            "rating": doc.get("rating", "").strip()
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
        "job_id": job_id,
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
st.title("Job Recommendations JSON Generator with MongoDB")

# MongoDB Configuration Inputs
st.header("MongoDB Configuration")
db_url = st.text_input("MongoDB URL", "mongodb://localhost:27017")
db_name = st.text_input("Database Name", "document-parsing")
collection_name = st.text_input("Collection Name", "dps_data")

# Input for job metadata
st.header("Enter Metadata for Job")
job_id = st.text_input("Job ID (used for fetching MongoDB data)", "")
title = st.text_input("Guide Title", "Distal Radius Fracture Rehabilitation")
stage = st.text_input("Stage", "Rehabilitation")
disease = st.text_input("Disease Title", "Fracture")
specialty = st.text_input("Specialty", "orthopedics")

# Process the data if the job ID is provided
if st.button("Generate JSON"):
    if db_url and db_name and collection_name and job_id:
        try:
            # Connect to MongoDB
            collection = connect_to_mongo(db_url, db_name, collection_name)
            if collection is None:
                st.error("Failed to connect to MongoDB.")
            else:
                # Fetch data from MongoDB
                fetched_data = fetch_data_from_mongo(collection, job_id)

                if fetched_data:
                    st.success(f"Fetched {len(fetched_data)} documents from the database.")

                    # Extract recommendations
                    recommendations = extract_recommendations_from_db(fetched_data)

                    if recommendations:
                        # Generate JSON chunks
                        json_chunks = generate_json_chunks(recommendations, title, stage, disease, specialty, job_id)

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
                        st.warning("No recommendations found for the given Job ID.")
                else:
                    st.warning("No data found for the provided Job ID in the database.")

        except Exception as e:
            st.error(f"Error processing data: {e}")
    else:
        st.warning("Please fill in all required fields.")

    



