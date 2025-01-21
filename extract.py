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
    Fetch recommendations from MongoDB using the provided job ID.
    """
    try:
        # Query to fetch documents with the matching job ID
        documents = collection.find({"job_id": job_id}, {
            "_id": 0,  # Exclude the MongoDB document ID
            "recommendation_content": 1,
            "recommendation_class": 1,
            "rating": 1
        })
        return list(documents)
    except Exception as e:
        st.error(f"Error fetching recommendations: {e}")
        return []


# Streamlit app
st.title("Fetch Recommendations from MongoDB")

# MongoDB Configuration Inputs
st.header("MongoDB Configuration")
db_url = st.text_input("MongoDB URL", "mongodb://localhost:27017")
db_name = st.text_input("Database Name", "document-parsing")
collection_name = st.text_input("Collection Name", "dps_data")

# Input for job ID
st.header("Enter Metadata for Job")
job_id = st.text_input("Job ID (used for fetching MongoDB recommendations)", "")
title = st.text_input("Guide Title", "Distal Radius Fracture Rehabilitation")
stage = st.text_input("Stage", "Rehabilitation")
disease = st.text_input("Disease Title", "Fracture")
specialty = st.text_input("Specialty", "orthopedics")

# Process the data if all inputs are provided
if st.button("Fetch Recommendations"):
    if db_url and db_name and collection_name and job_id:
        try:
            # Connect to MongoDB
            collection = connect_to_mongo(db_url, db_name, collection_name)

            # Fetch recommendations based on job ID
            recommendations = fetch_recommendations_from_mongo(collection, job_id)

            if recommendations:
                st.success(f"Fetched {len(recommendations)} recommendations from the database.")

                # Generate JSON output with metadata and recommendations
                json_output = {
                    "title": title,
                    "stage": [stage],
                    "disease": [disease],
                    "specialty": [specialty],
                    "job_id": job_id,
                    "recommendations": recommendations
                }

                # Display JSON output
                st.subheader("Generated JSON:")
                st.json(json_output)

                # Option to download JSON file
                json_file = json.dumps(json_output, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_file,
                    file_name="recommendations.json",
                    mime="application/json"
                )
            else:
                st.warning("No recommendations found for the provided Job ID.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")
    else:
        st.warning("Please fill in all required fields.")
