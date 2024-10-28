import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Scroll to top on page load
def scroll_to_top():
    st.write("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)

# Initialize session state for page if it doesn't exist
if "page" not in st.session_state:
    st.session_state["page"] = "estimation"

# Display the first page (Cost Estimation) if in "estimation" state
if st.session_state["page"] == "estimation":
    scroll_to_top()  # Ensure page starts at top
    # Display the logo at the top of the app
    st.image("ilogo.png", use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
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

        # Total Quantity of Panels
        total_qty = data['Qty'].sum()

        # Store these in session state for use in other pages
        st.session_state["total_area"] = total_area
        st.session_state["total_qty"] = total_qty

    # Database connection for first page
    DATABASE_URL = "postgresql://u7vukdvn20pe3c:p918802c410825b956ccf24c5af8d168b4d9d69e1940182bae9bd8647eb606845@cb5ajfjosdpmil.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcobttk99a5sie"
    engine = create_engine(DATABASE_URL)

    # Display materials and cost calculations
    def display_materials_by_category(category_num):
        st.markdown(f"### Available Materials for Category {category_num}")
        query = f"SELECT * FROM materials WHERE category = {category_num}"
        try:
            data = pd.read_sql(query, engine)
            filtered_data = data[['nickname', 'description', 'cost']]
            st.write(f"Materials for Category {category_num}:")
            st.dataframe(filtered_data)
            selected_nickname = st.selectbox(f"Select a material for Category {category_num} by nickname", filtered_data['nickname'])
            selected_cost = filtered_data[filtered_data['nickname'] == selected_nickname]['cost'].values[0]
            return selected_cost
        except Exception as e:
            st.write(f"Error connecting to the database for Category {category_num}:", e)
            return 0

    # Calculate total material cost
    if system_type == "SWR":
        material_cost = sum(display_materials_by_category(category) for category in range(1, 12))
        st.session_state["total_cost"] = material_cost
        # Display total material cost
        st.markdown("### Total Material Cost")
        st.write(f"${round(material_cost)}")

    # Navigation buttons
    if st.button("Next", key="next_button"):
        st.session_state["page"] = "logistics"

# Display the second page (Logistics) if in "logistics" state
elif st.session_state["page"] == "logistics":
    scroll_to_top()  # Ensure page starts at top
    # Display the logo again at the top
    st.image("ilogo.png", use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Logistics")

    # Input fields for logistics details
    num_trucks = st.number_input("Enter the number of trucks needed", min_value=0, step=1)
    cost_per_truck = st.number_input("Enter the cost per truck ($):", min_value=0, step=1)

    # Calculate total truck cost
    total_truck_cost = num_trucks * cost_per_truck
    st.session_state["total_truck_cost"] = total_truck_cost

    # Equipment Section
    st.title("Equipment")
    equipment_options = ["Scissor Lift", "Lull Rental", "Baker Rolling Staging", "Crane", "Finished Protected Board Blankets"]
    selected_equipment = st.multiselect("Select the required equipment:", equipment_options)
    total_equipment_cost = sum(st.number_input(f"Enter the cost for {item} ($):", min_value=0, step=1) for item in selected_equipment)
    st.session_state["total_equipment_cost"] = total_equipment_cost

    # Travel Section
    st.title("Travel")
    airfare = st.number_input("Air fare ($):", min_value=0, step=1)
    lodging = st.number_input("Lodging ($):", min_value=0, step=1)
    meals_incidentals = st.number_input("Meals & Incidentals ($):", min_value=0, step=1)
    car_rental_gas = st.number_input("Car Rental + Gas ($):", min_value=0, step=1)
    total_travel_cost = airfare + lodging + meals_incidentals + car_rental_gas
    st.session_state["total_travel_cost"] = total_travel_cost

    # Sales Section
    st.title("Sales")
    sales_options = [
        "Building Audit/Survey", "System Design Customization", "Thermal Stress Analysis",
        "Thermal Performance Simulation", "Visual & Performance Mockup", "Window Performance M&V",
        "Building Energy Model", "Cost-Benefit Analysis", "Utility Incentive Application"
    ]
    selected_sales = st.multiselect("Select the required sales items:", sales_options)
    sales_cost_total = sum(st.number_input(f"Enter the cost for {item} ($):", min_value=0, step=1) for item in selected_sales)
    st.session_state["sales_cost_total"] = sales_cost_total

    # Horizontal layout for Back and Next buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state["page"] = "estimation"
    with col2:
        if st.button("Next", key="next_summary"):
            st.session_state["page"] = "summary"

# Display the third page (Summary) if in "summary" state
elif st.session_state["page"] == "summary":
    scroll_to_top()  # Ensure page starts at top
    # Display the logo at the top of the summary page
    st.image("ilogo.png", use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Summary of Costs")

    # Retrieve totals and area/panel information from session state
    total_area = st.session_state.get("total_area", 1)  # default to 1 to avoid division by zero
    total_qty = st.session_state.get("total_qty", 1)  # default to 1 to avoid division by zero

    # Retrieve costs from session state
    material_cost = st.session_state.get("total_cost", 0)
    logistics_cost = st.session_state.get("total_truck_cost", 0)
    equipment_cost = st.session_state.get("total_equipment_cost", 0)
    travel_cost = st.session_state.get("total_travel_cost", 0)
    sales_cost = st.session_state.get("sales_cost_total", 0)

    # Calculate Cost/sf and Cost/panel for each category
    cost_per_sf = {
        "Material": round(material_cost / total_area),
        "Logistics": round(logistics_cost / total_area),
        "Equipment": round(equipment_cost / total_area),
        "Travel": round(travel_cost / total_area),
        "Sales": round(sales_cost / total_area),
    }

    cost_per_panel = {
        "Material": round(material_cost / total_qty),
        "Logistics": round(logistics_cost / total_qty),
        "Equipment": round(equipment_cost / total_qty),
        "Travel": round(travel_cost / total_qty),
        "Sales": round(sales_cost / total_qty),
    }

    # Sum up all total costs
    total_cost = round(material_cost + logistics_cost + equipment_cost + travel_cost + sales_cost)

    # Create a DataFrame to display the summary table
    summary_data = {
        "Total Cost ($)": [round(material_cost), round(logistics_cost), round(equipment_cost), round(travel_cost), round(sales_cost)],
        "Cost per SF ($/sf)": list(cost_per_sf.values()),
        "Cost per Panel ($/panel)": list(cost_per_panel.values())
    }
    summary_df = pd.DataFrame(summary_data, index=["Material", "Logistics", "Equipment", "Travel", "Sales"])

    # Add a row for the Total
    summary_df.loc["Total"] = [total_cost, "", ""]

    # Display the summary table
    st.write("### Summary Table of Costs")
    st.table(summary_df)

    # Markup Section
    st.markdown("### Markup Adjustments")
    markups = {}
    for category in ["Material", "Logistics", "Equipment", "Travel", "Sales"]:
        markups[category] = st.slider(f"{category} Markup (%)", 0, 100, 0)

    # Apply markups and recalculate costs
    new_costs = {
        category: round(summary_data["Total Cost ($)"][i] * (1 + markups[category] / 100))
        for i, category in enumerate(["Material", "Logistics", "Equipment", "Travel", "Sales"])
    }

    new_summary_data = {
        "Adjusted Total Cost ($)": list(new_costs.values()),
        "Adjusted Cost per SF ($/sf)": [round(new_costs[cat] / total_area) for cat in new_costs],
        "Adjusted Cost per Panel ($/panel)": [round(new_costs[cat] / total_qty) for cat in new_costs]
    }
    adjusted_summary_df = pd.DataFrame(new_summary_data, index=["Material", "Logistics", "Equipment", "Travel", "Sales"])

    # Add a total row only for the Adjusted Total Cost
    adjusted_summary_df.loc["Total"] = [sum(new_costs.values()), "", ""]

    # Display the adjusted summary table
    st.write("### Adjusted Summary Table of Costs with Markup")
    st.table(adjusted_summary_df)

    # Calculate Total Markup %
    total_markup_percentage = sum(markups[cat] * summary_data["Total Cost ($)"][i] for i, cat in enumerate(["Material", "Logistics", "Equipment", "Travel", "Sales"])) / total_cost

    # Display Total Markup %
    st.write(f"**Total Markup**: {total_markup_percentage:.2f}%")

    # Navigation buttons
    if st.button("Back"):
        st.session_state["page"] = "logistics"