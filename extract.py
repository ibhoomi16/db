import streamlit as st
from pymongo import MongoClient
import json

# Function to connect to MongoDB
def connect_to_mongo(db_url, db_name, collection_name):
    """
    Connect to MongoDB and return the collection.
    """
    client = MongoClient(db_url)
    db = client[db_name]
    return db[collection_name]

# Function to fetch recommendations from MongoDB based on job ID
def fetch_recommendations_from_mongo(collection, job_id):
    """
    Fetch recommendations and other related data from MongoDB collection using the provided job ID.
    """
    try:
        documents = collection.find({"job_id": job_id})
        recommendations = []
        for document in documents:
            for rec in document.get("recommendations", []):
                recommendation = rec.get("recommendation_content", "")
                rating = rec.get("loe", "")
                recommendation_class = rec.get("cor", "")
                recommendations.append({
                    "recommendation_content": recommendation.strip(),
                    "rating": rating.strip(),
                    "recommendation_class": recommendation_class.strip()
                })
        return recommendations
    except Exception as e:
        st.error(f"Error fetching recommendations: {e}")
        return []

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
st.title("Recommendations Fetcher with MongoDB Integration")

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

# Process the data when the button is clicked
if st.button("Process Data"):
    if db_url and db_name and collection_name and job_id:
        try:
            # Connect to MongoDB and fetch data
            collection = connect_to_mongo(db_url, db_name, collection_name)
            fetched_data = fetch_recommendations_from_mongo(collection, job_id)

            if fetched_data:
                st.success(f"Fetched {len(fetched_data)} recommendations from the database.")

                # Generate JSON chunks using MongoDB data
                json_chunks = generate_json_chunks(fetched_data, title, stage, disease, specialty, job_id, fetched_data)

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
                st.warning("No recommendations found for the provided Job ID in the database.")
        except Exception as e:
            st.error(f"Error processing data: {e}")
    else:
        st.warning("Please fill in all required fields.")
