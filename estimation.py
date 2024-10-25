import streamlit as st
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
    st.write("Uploaded data:", data)

    # Convert VGA Width and Height from inches to feet
    data['VGA Width (ft)'] = data['VGA Width in'] / 12
    data['VGA Height (ft)'] = data['VGA Height in'] / 12

    # Total Area (sq ft): Sum of (VGA Width (ft) * VGA Height (ft) * Qty)
    total_area = (data['VGA Width (ft)'] * data['VGA Height (ft)'] * data['Qty']).sum()

    # Total Vertical (ft): Sum of (VGA Height (ft) * Qty)
    total_vertical = (data['VGA Height (ft)'] * data['Qty']).sum()*2

    # Total Horizontal (ft): Sum of (VGA Width (ft) * Qty)
    total_horizontal = (data['VGA Width (ft)'] * data['Qty']).sum()*2

    # Total Perimeter (ft): Total Vertical + Total Horizontal
    total_perimeter = total_vertical + total_horizontal

    # Display the calculated values with 3 digits after the decimal point
    st.markdown("### Calculated Variables:")
    st.write(f"Total Quantity: {data['Qty'].sum()}")
    st.write(f"Total Area (sq ft): {total_area:.3f}")
    st.write(f"Total Horizontal (ft): {total_horizontal:.3f}")
    st.write(f"Total Vertical (ft): {total_vertical:.3f}")
    st.write(f"Total Perimeter (ft): {total_perimeter:.3f}")

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
cost_by_category = {}

# Utilization Table
utilization = {
    1: 0.93,
    2: 0.75,
    **{category: 0.95 for category in range(3, 12)}  # Utilization for categories 3-11
}

# Function to calculate costs per category
def calculate_cost(category_num, cost, utilization_factor):
    if category_num == 1:  # Category 1 (Glass)
        return total_area * cost * utilization_factor
    elif category_num in [2, 3]:  # Categories 2-3 (Total perimeter)
        return total_perimeter * cost * utilization_factor
    elif category_num == 4:  # Category 4 (Total vertical)
        return total_vertical * cost * utilization_factor
    elif category_num == 5:  # Category 5 (Total panels * 4)
        return data['Qty'].sum() * 4 * utilization_factor
    elif category_num == 6:  # Category 6 (Total vertical)
        return total_vertical * cost * utilization_factor
    elif category_num == 7:  # Category 7 (Total horizontal)
        return total_horizontal * cost * utilization_factor
    elif category_num == 8:  # Category 8 (Total horizontal)
        return total_horizontal * cost * utilization_factor
    elif category_num == 9:  # Category 9 (Total perimeter)
        return total_perimeter * cost * utilization_factor
    elif category_num == 10:  # Category 10 (Total panels * 4)
        return data['Qty'].sum() * 4 * cost * utilization_factor
    elif category_num == 11:  # Category 11 (Total perimeter)
        return total_perimeter * cost * utilization_factor

# Function to display materials based on category and store selections
def display_materials_by_category(category_num):
    st.markdown(f"### Available Materials for Category {category_num}")
    
    # Query the database for entries of the specific category
    query = f"SELECT * FROM materials WHERE category = {category_num}"
    try:
        data = pd.read_sql(query, engine)
        
        # Display only 'nickname', 'description', and 'cost' columns
        filtered_data = data[['nickname', 'description', 'cost']]

        # Combine table display with selection
        st.write(f"Materials for Category {category_num}:")
        st.dataframe(filtered_data)

        # Allow the user to select a row based on 'nickname'
        selected_nickname = st.selectbox(f"Select a material for Category {category_num} by nickname", filtered_data['nickname'])

        # Save the selection in the dictionary
        user_selections[category_num] = selected_nickname

        # Get the cost of the selected material
        selected_cost = filtered_data[filtered_data['nickname'] == selected_nickname]['cost'].values[0]

        # Calculate cost for the category
        category_cost = calculate_cost(category_num, selected_cost, utilization[category_num])
        cost_by_category[category_num] = round(category_cost)

    except Exception as e:
        st.write(f"Error connecting to the database for Category {category_num}:", e)

# If SWR is selected, display material choices for categories 1 to 11
if system_type == "SWR":
    for category in range(1, 12):  # Only categories 1 to 11
        display_materials_by_category(category)

# Display the saved selections and costs
st.markdown("### Your Selections and Costs:")

# Convert the selections dictionary to a DataFrame for a tidy table
if len(user_selections) == 11:
    selections_df = pd.DataFrame.from_dict(user_selections, orient='index', columns=['Selected Material'])
    selections_df.index.name = 'Category'
    selections_df['Cost ($)'] = selections_df.index.map(cost_by_category)
    
    # Calculate total cost
    total_cost = sum(cost_by_category.values())
    total_row = pd.DataFrame({'Selected Material': ['Total'], 'Cost ($)': [round(total_cost)]}, index=['Total'])
    selections_df = pd.concat([selections_df, total_row])

    st.write("Here is an overview of your selected materials and their costs:")
    st.table(selections_df)
else:
    st.write("Please make a selection for each category.")