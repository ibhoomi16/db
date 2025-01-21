import streamlit as st
from pymongo import MongoClient
import json

# Function to connect to MongoDB
def connect_to_mongo(db_url, db_name, collection_name):
    """
    Connect to MongoDB and return the collection.
    """
    try:
        client = MongoClient(db_url)
        db = client[db_name]
        return db[collection_name]
    except Exception as e:
        raise Exception(f"Error connecting to MongoDB: {e}")

# Function to fetch recommendations from MongoDB based on job ID
def fetch_recommendations_from_mongo(collection, job_id):
    """
    Fetch recommendations and related data from MongoDB collection using the provided job ID.
    """
    try:
        documents = collection.find({"job_id": job_id})
        recommendations = []
        for document in documents:
            for rec in document.get("recommendations", []):
                recommendations.append({
                    "recommendation_content": rec.get("recommendation_content", "").strip(),
                    "rating": rec.get("loe", "").strip(),
                    "recommendation_class": rec.get("cor", "").strip()
                })
        return recommendations
    except Exception as e:
        raise Exception(f"Error fetching recommendations: {e}")

# Function to generate JSON chunks
def generate_json_chunks(recommendations, title, stage, disease, specialty, job_id, fetched_data):
    """
    Generate JSON chunks using the extracted recommendations, user inputs, and MongoDB data.
    """
    try:
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
    except Exception as e:
        raise Exception(f"Error generating JSON chunks: {e}")

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
    if all([db_url, db_name, collection_name, job_id, title, stage, disease, specialty]):
        try:
            # Connect to MongoDB and fetch data
            st.info("Connecting to MongoDB...")
            collection = connect_to_mongo(db_url, db_name, collection_name)

            st.info("Fetching recommendations from MongoDB...")
            fetched_data = fetch_recommendations_from_mongo(collection, job_id)

            if fetched_data:
                st.success(f"Fetched {len(fetched_data)} recommendations from the database.")

                # Generate JSON chunks using MongoDB data
                st.info("Generating JSON...")
                json_chunks = generate_json_chunks(
                    recommendations=fetched_data,
                    title=title,
                    stage=stage,
                    disease=disease,
                    specialty=specialty,
                    job_id=job_id,
                    fetched_data=fetched_data
                )

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
