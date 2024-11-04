import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO
from datetime import datetime
import xlsxwriter

# Scroll to top on page load
def scroll_to_top():
    st.write("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)

# Initialize session state for page if it doesn't exist
if "page" not in st.session_state:
    st.session_state["page"] = "estimation"
    st.session_state["panel_index"] = 0  # Track the current panel type
    st.session_state["panel_costs"] = []  # Store costs per panel type
    st.session_state["current_selections"] = None  # Store material choices for current panel type

# Display the first page (Cost Estimation) if in "estimation" state
if st.session_state["page"] == "estimation":
    scroll_to_top()  # Ensure page starts at top
    st.image("ilogo.png", use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Cost Estimation")

    # Step 1: Read the Project Name (no display)
    project_name = st.text_input("Enter the Project Name")

    # Step 2: Read in the CSV file with the openings
    uploaded_file = st.file_uploader("Upload your CSV file with openings", type=["csv"])
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        st.write("Uploaded data:", data)
        st.session_state["data"] = data  # Save data for access in other pages
        st.session_state["project_name"] = project_name

        # Ensure panel_costs matches the number of rows in data
        if len(st.session_state["panel_costs"]) < len(data):
            st.session_state["panel_costs"].extend([0] * (len(data) - len(st.session_state["panel_costs"])))

        # Retrieve the current panel's data
        panel_index = st.session_state["panel_index"]
        current_panel = data.iloc[panel_index]

        # Calculated values for the current panel type
        width_ft = current_panel['VGA Width in'] / 12
        height_ft = current_panel['VGA Height in'] / 12
        qty = current_panel['Qty']
        area = width_ft * height_ft * qty

        # Apply minimum area rule if the calculated area is less than 5 sq ft
        effective_area = max(area, 5)
        area_display = round(area, 3)
        effective_area_display = round(effective_area, 3)

        # Save total area for all panels to session state (if not already set)
        st.session_state["total_area"] = (
            st.session_state.get("total_area", 0) + effective_area
        )

        perimeter = round(2 * (width_ft + height_ft) * qty, 3)
        horizontal = round(width_ft * qty * 2, 3)
        vertical = round(height_ft * qty * 2, 3)

        # Display calculated values for the current panel type
        st.write("### Calculated Values for Panel Type")
        st.write(f"Panel Type {panel_index + 1} - {current_panel['Item']}")
        st.write(f"Total Area (sq ft): {area_display}")
        st.write(f"Effective Area for Cost Calculation (sq ft): {effective_area_display}")
        st.write(f"Total Quantity of Panels: {qty}")
        st.write(f"Total Perimeter (ft): {perimeter}")
        st.write(f"Total Horizontal (ft): {horizontal}")
        st.write(f"Total Vertical (ft): {vertical}")

        # Database connection for material selection
        DATABASE_URL = "postgresql://u7vukdvn20pe3c:p918802c410825b956ccf24c5af8d168b4d9d69e1940182bae9bd8647eb606845@cb5ajfjosdpmil.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcobttk99a5sie"
        engine = create_engine(DATABASE_URL)

        # Display materials selection for each category
        def select_materials_for_panel_type(category_num):
            st.markdown(f"### Select Material for Category {category_num}")
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

        # Material selection for each panel type
        if st.session_state["current_selections"] is None:
            st.session_state["current_selections"] = {
                category: select_materials_for_panel_type(category) for category in range(1, 12)
            }

        # Calculate the cost for the current panel type based on selections and effective area
        panel_cost = sum(st.session_state["current_selections"].values()) * effective_area
        st.write("### Total Cost for Current Panel Type")
        st.write(f"${round(panel_cost)}")

        # Show the next panel's details if available in a horizontal layout
        if panel_index + 1 < len(data):
            next_panel = data.iloc[panel_index + 1]
            st.write("### Next Panel Type Preview")
            next_panel_data = pd.DataFrame({
                "Panel Type": [f"{panel_index + 2} - {next_panel['Item']}"],
                "VGA Width (in)": [next_panel['VGA Width in']],
                "VGA Height (in)": [next_panel['VGA Height in']],
                "Quantity": [next_panel['Qty']]
            })
            st.table(next_panel_data)

        # Horizontal layout for panel type options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use same materials for next panel type"):
                st.session_state["panel_costs"][panel_index] = panel_cost  # Store the calculated cost for this panel
                st.session_state["panel_index"] += 1  # Move to the next panel type
                st.session_state["current_selections"] = st.session_state["current_selections"]  # Keep same selections
                if st.session_state["panel_index"] >= len(data):  # Check if at the last panel type
                    st.session_state["page"] = "logistics"
        with col2:
            if st.button("Select new materials for next panel type"):
                st.session_state["panel_costs"][panel_index] = panel_cost  # Store the calculated cost for this panel
                st.session_state["panel_index"] += 1  # Move to the next panel type
                st.session_state["current_selections"] = None  # Reset selections for the next panel type
                if st.session_state["panel_index"] >= len(data):  # Check if at the last panel type
                    st.session_state["page"] = "logistics"

        # Always show the navigation to the logistics page at the bottom
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Next"):
            st.session_state["page"] = "logistics"

# Display the logistics page if in "logistics" state
elif st.session_state["page"] == "logistics":
    scroll_to_top()  # Ensure page starts at top
    st.image("ilogo.png", use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Logistics")

    # Input fields for logistics details
    num_trucks = st.number_input("Enter the number of trucks needed", min_value=0, step=1)
    cost_per_truck = st.number_input("Enter the cost per truck ($):", min_value=0, step=1)

    # Calculate total truck cost
    total_truck_cost = num_trucks * cost_per_truck
    st.session_state["total_truck_cost"] = total_truck_cost

    # Installation Section
    st.title("Installation")
    hourly_rate = st.number_input("Enter the hourly rate for installation ($/hour):", min_value=0.0, step=0.01)
    hours_per_panel = st.number_input("Enter the man hours required per panel:", min_value=0.0, step=0.1)
    total_qty = st.session_state["data"]['Qty'].sum()

    # Calculate installation cost
    installation_cost = hourly_rate * hours_per_panel * total_qty
    st.session_state["installation_cost"] = installation_cost

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

    # Navigation button
    if st.button("Next", key="next_summary"):
        st.session_state["page"] = "summary"

# Function to create the Excel file with specified content
def create_excel():
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    
    # Sheet 1: Project Name and Date
    project_name = st.session_state.get("project_name", "Unnamed Project")
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Panels Table with Material Choices and Costs
    panels_data = st.session_state["data"].copy()
    panels_data["Total Cost"] = st.session_state["panel_costs"]

    for category_num in range(1, 12):
        panels_data[f"Category {category_num} Material"] = [
            st.session_state["current_selections"].get(category_num, "")
            for _ in range(len(panels_data))
        ]

    # Add Project name and Date to the first sheet
    panels_data.to_excel(writer, sheet_name="Project Details", index=False, startrow=2)
    worksheet = writer.sheets["Project Details"]
    worksheet.write(0, 0, f"Project Name: {project_name}")
    worksheet.write(1, 0, f"Date: {current_date}")

    # Total Cost Row
    worksheet.write(len(panels_data) + 3, 0, "Total Panel Cost")
    worksheet.write(len(panels_data) + 3, panels_data.shape[1] - 1, sum(st.session_state["panel_costs"]))

    # Logistics and Other Costs Table
    logistics_costs = {
        "Category": ["Logistics", "Installation", "Equipment", "Travel", "Sales"],
        "Cost": [
            st.session_state.get("total_truck_cost", 0),
            st.session_state.get("installation_cost", 0),
            st.session_state.get("total_equipment_cost", 0),
            st.session_state.get("total_travel_cost", 0),
            st.session_state.get("sales_cost_total", 0)
        ]
    }
    logistics_df = pd.DataFrame(logistics_costs)
    logistics_df.to_excel(writer, sheet_name="Costs Breakdown", index=False, startrow=2)

    worksheet = writer.sheets["Costs Breakdown"]
    worksheet.write(0, 0, "Logistics and Additional Costs")
    worksheet.write(len(logistics_df) + 3, 0, "Total Additional Cost")
    worksheet.write(len(logistics_df) + 3, 1, sum(logistics_df["Cost"]))

    # Markup Input Section
    worksheet.write(len(logistics_df) + 6, 0, "Markup Input")
    markups = {}
    for i, category in enumerate(["Panel Total", "Logistics", "Equipment", "Travel", "Sales", "Installation"], start=1):
        markups[category] = st.slider(f"{category} Markup (%)", 0, 100, 0, key=f"{category}_markup_excel")
        worksheet.write(len(logistics_df) + 6, i, f"{category} Markup (%)")
        worksheet.write(len(logistics_df) + 7, i, markups[category])

    # Final Summary Table with Markups
    summary_data = {
        "Category": ["Panel Total", "Logistics", "Equipment", "Travel", "Sales", "Installation"],
        "Original Cost": [
            sum(st.session_state["panel_costs"]),
            logistics_costs["Cost"][0],
            logistics_costs["Cost"][2],
            logistics_costs["Cost"][3],
            logistics_costs["Cost"][4],
            st.session_state.get("installation_cost", 0)
        ],
        "Markup (%)": [markups[cat] for cat in summary_data["Category"]],
        "Cost with Markup": [
            cost * (1 + markups[cat] / 100)
            for cost, cat in zip(summary_data["Original Cost"], summary_data["Category"])
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name="Final Summary", index=False)

    worksheet = writer.sheets["Final Summary"]
    worksheet.write(len(summary_df) + 3, 0, "Total Cost After Markup")
    worksheet.write(len(summary_df) + 3, 3, sum(summary_df["Cost with Markup"]))

    # Close and save the Excel file
    writer.save()
    output.seek(0)
    return output

# Download Button on the summary page
if st.session_state["page"] == "summary":
    scroll_to_top()  # Ensure page starts at top
    st.image("ilogo.png", use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Summary of Costs")

    # Calculate total cost across all panel types
    panel_total_cost = sum(st.session_state["panel_costs"])
    total_cost = (
        panel_total_cost
        + st.session_state.get("total_truck_cost", 0)
        + st.session_state.get("total_equipment_cost", 0)
        + st.session_state.get("total_travel_cost", 0)
        + st.session_state.get("sales_cost_total", 0)
        + st.session_state.get("installation_cost", 0)
    )

    # Display summary table
    summary_data = {
        "Total Cost ($)": [
            round(panel_total_cost),
            round(st.session_state.get("total_truck_cost", 0)),
            round(st.session_state.get("total_equipment_cost", 0)),
            round(st.session_state.get("total_travel_cost", 0)),
            round(st.session_state.get("sales_cost_total", 0)),
            round(st.session_state.get("installation_cost", 0))
        ],
        "Cost per SF ($/sf)": [
            round(panel_total_cost / max(st.session_state["total_area"], 1), 2),
            "", "", "", "", ""
        ],
    }
    summary_df = pd.DataFrame(
        summary_data, 
        index=["Panel Total", "Logistics", "Equipment", "Travel", "Sales", "Installation"]
    )

    # Add total row to table
    summary_df.loc["Total"] = [total_cost, ""]
    st.table(summary_df)

    # Margin Adjustments
    st.markdown("### Markup Adjustments")
    markups = {}
    for category in ["Panel Total", "Logistics", "Equipment", "Travel", "Sales", "Installation"]:
        markups[category] = st.slider(f"{category} Markup (%)", 0, 100, 0, key=f"{category}_markup")

    # Apply markups and recalculate costs
    new_costs = {
        "Panel Total": round(panel_total_cost * (1 + markups["Panel Total"] / 100)),
        "Logistics": round(st.session_state.get("total_truck_cost", 0) * (1 + markups["Logistics"] / 100)),
        "Equipment": round(st.session_state.get("total_equipment_cost", 0) * (1 + markups["Equipment"] / 100)),
        "Travel": round(st.session_state.get("total_travel_cost", 0) * (1 + markups["Travel"] / 100)),
        "Sales": round(st.session_state.get("sales_cost_total", 0) * (1 + markups["Sales"] / 100)),
        "Installation": round(st.session_state.get("installation_cost", 0) * (1 + markups["Installation"] / 100)),
    }

    # Display adjusted total cost
    adjusted_total_cost = sum(new_costs.values())
    st.write("### Adjusted Total Project Cost with Markup")
    st.write(f"${round(adjusted_total_cost, 2)}")

    # Display adjusted summary table with markups
    adjusted_summary_data = {
        "Adjusted Total Cost ($)": list(new_costs.values()),
        "Adjusted Cost per SF ($/sf)": [
            round(new_costs["Panel Total"] / max(st.session_state["total_area"], 1), 2),
            "", "", "", "", ""
        ]
    }
    adjusted_summary_df = pd.DataFrame(
        adjusted_summary_data, 
        index=["Panel Total", "Logistics", "Equipment", "Travel", "Sales", "Installation"]
    )

    # Add adjusted total row
    adjusted_summary_df.loc["Total"] = [adjusted_total_cost, ""]
    st.write("### Adjusted Summary Table with Markup")
    st.table(adjusted_summary_df)

    # Display Total Markup %
    total_markup_percentage = (
        sum(markups[cat] * new_costs[cat] for cat in new_costs) / total_cost
    )
    st.write(f"**Total Markup**: {total_markup_percentage:.2f}%")

    # Generate and Download Excel File Button
    excel_data = create_excel()
    st.download_button(
        label="Download Project Cost Summary as Excel",
        data=excel_data,
        file_name="Project_Cost_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )