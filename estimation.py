import streamlit as st
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

# Display the logo at the top of the app
st.image("ilogo.png", use_column_width=True)

# Add some space between the logo and the title
st.markdown("<br>", unsafe_allow_html=True)

# Set the title of the app below the logo
st.title("Cost Estimation")

# Step 1: Read the Project Name (no display)
project_name = st.text_input("Enter the Project Name")

# Step 2: Toggle between SWR and IGR (no display)
system_type = st.radio("Select System Type", ("SWR", "IGR"))

# Step 3: Read in the CSV file with the openings
uploaded_file = st.file_uploader("Upload your CSV file with openings", type=["csv"])
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write(data)

# Step 4: Add buttons for downloading templates
st.markdown("### Download Templates")

col1, col2 = st.columns(2)

with col1:
    with open("estimation_swr.csv", "rb") as swr_file:
        swr_button = st.download_button(label="Download SWR-Template", data=swr_file, file_name="estimation_swr.csv")

with col2:
    with open("estimation_igr.csv", "rb") as igr_file:
        igr_button = st.download_button(label="Download IGR-Template", data=igr_file, file_name="estimation_igr.csv")

# SQLAlchemy Database connection using the correct DATABASE_URL
DATABASE_URL = "postgresql://u7vukdvn20pe3c:p918802c410825b956ccf24c5af8d168b4d9d69e1940182bae9bd8647eb606845@cb5ajfjosdpmil.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcobttk99a5sie"

# Create an SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Dictionary to store user selections by category
user_selections = {}

# Utilization Table
utilization = {
    1: 0.93,
    2: 0.75,
    **{category: 0.95 for category in range(3, 12)}  # Utilization for categories 3-11
}

# Function to display materials based on category and store selections
def display_materials_by_category(category_num):
    st.markdown(f"### Available Materials for Category {category_num}")
    
    # Query the database for entries of the specific category
    query = f"SELECT * FROM materials WHERE category = {category_num}"
    try:
        data = pd.read_sql(query, engine)
        
        # Display only 'nickname' and 'description' columns
        filtered_data = data[['nickname', 'description']]

        # Combine table display with selection
        st.write(f"Materials for Category {category_num}:")
        st.dataframe(filtered_data)

        # Allow the user to select a row based on 'nickname'
        selected_nickname = st.selectbox(f"Select a material for Category {category_num} by nickname", filtered_data['nickname'])

        # Save the selection in the dictionary
        user_selections[category_num] = selected_nickname

    except Exception as e:
        st.write(f"Error connecting to the database for Category {category_num}:", e)

# If SWR is selected, display material choices for categories 1 to 11
if system_type == "SWR":
    for category in range(1, 12):  # Only categories 1 to 11
        display_materials_by_category(category)

# Display the saved selections (for debugging or user feedback)
st.markdown("### Your Selections:")

# Convert the selections dictionary to a DataFrame for a tidy table
if len(user_selections) == 11:
    # Replace 'NULL' or missing values with 'No Selection'
    selections_df = pd.DataFrame.from_dict(user_selections, orient='index', columns=['Selected Material'])
    selections_df.index.name = 'Category'
    selections_df.fillna('No Selection', inplace=True)  # Replace any None or NaN values

    # Display a clean, tidy table
    st.write("Here is an overview of your selected materials:")
    st.table(selections_df)
else:
    st.write("Please make a selection for each category.")