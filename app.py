import streamlit as st
import pandas as pd
import openpyxl

# =============================================================================
# PART 1: CORE PYTHON CLASSES (UNCHANGED)
# =============================================================================
# Your PlantingPlanner and HybridPlanner classes are perfect. No changes needed here.
class PlantingPlanner:
    """Calculates and displays a split planting recommendation for one hybrid pair."""
    def __init__(self, gdu_male_p50d: int, gdu_female_s50d: int, split_gdu_interval: int = 40):
        self.gdu_male_p50d = gdu_male_p50d
        self.gdu_female_s50d = gdu_female_s50d
        self.split_gdu_interval = split_gdu_interval
        self.gdu_difference = self.gdu_male_p50d - self.gdu_female_s50d
        self.recommendation = self._generate_recommendation()

    def _generate_recommendation(self) -> dict:
        male_central_delay = -self.gdu_difference
        male_1_delay = male_central_delay - self.split_gdu_interval
        male_2_delay = male_central_delay + self.split_gdu_interval
        plan = {'Female': {'gdu_delay': 0, 'timing_notes': 'Plant on Day 0'},'Male 1': {'gdu_delay': male_1_delay, 'timing_notes': ''},'Male 2': {'gdu_delay': male_2_delay, 'timing_notes': ''}}
        for male_key in ['Male 1', 'Male 2']:
            delay = plan[male_key]['gdu_delay']
            if delay > 0: plan[male_key]['timing_notes'] = f"Plant {delay} GDU AFTER the female"
            elif delay < 0: plan[male_key]['timing_notes'] = f"Plant {abs(delay)} GDU BEFORE the female"
            else: plan[male_key]['timing_notes'] = "Plant at the SAME TIME as the female"
        return plan

class HybridPlanner:
    """Manages pedigree data and provides an interface to generate plans."""
    def __init__(self, pedigree_df: pd.DataFrame):
        self.df = pedigree_df.set_index('pedigree')

# =============================================================================
# PART 2: DATA LOADING AND HELPER FUNCTIONS
# =============================================================================

@st.cache_data
def load_data(file_path):
    """Loads and validates the master pedigree data."""
    try:
        df = pd.read_csv(file_path)
        required_cols = {'pedigree', 'P50_GDUs', 'S50_GDUs'}
        if not required_cols.issubset(df.columns):
            st.error(f"Master Data Error: CSV must have columns {required_cols}.")
            return None
        df['pedigree'] = df['pedigree'].str.strip()
        return df
    except FileNotFoundError:
        st.error(f"Fatal Error: Master data file not found at '{file_path}'.")
        return None

@st.cache_data
def convert_df_to_csv(df):
    """Helper function to convert a DataFrame to a CSV string for downloading."""
    return df.to_csv(index=False).encode('utf-8')

# =============================================================================
# PART 3: THE STREAMLIT USER INTERFACE FOR BULK UPLOAD
# =============================================================================

st.set_page_config(page_title="Corn Planting Planner (Bulk)", page_icon="🌽", layout="wide")
st.title("🌽 Bulk Corn Planting Synchronization Planner")
st.markdown("Upload a list of hybrid combinations to get planting recommendations for all of them at once.")
st.divider()

# --- Load Master Pedigree Data ---
# IMPORTANT: Use a relative path if deploying, or keep the full path for local use.

from pathlib import Path

DATA_FILE = Path(__file__).parent / "GDUs_corn_data.csv"
pedigree_data_df = load_data(DATA_FILE)


# The app proceeds only if the master data is available
if pedigree_data_df is not None:
    tool = HybridPlanner(pedigree_data_df)

    # --- Section 1: Instructions and Template Download ---
    st.subheader("1. Prepare Your Upload File")
    st.markdown("Your file must be a CSV or Excel file with two columns: `Female` and `Male`.")
    
    # Create a sample template for the user to download
    template_df = pd.DataFrame({
        'Female': ['INBRED_A', 'INBRED_A'],
        'Male': ['INBRED_B', 'INBRED_C']
    })
    template_csv = convert_df_to_csv(template_df)
    st.download_button(
        label="Download Template CSV",
        data=template_csv,
        file_name="hybrid_list_template.csv",
        mime="text/csv",
    )

    # --- Section 2: File Uploader ---
    st.subheader("2. Upload Your Hybrid List")
    uploaded_file = st.file_uploader(
        "Choose your hybrid list file",
        type=['csv', 'xlsx']
    )

    # --- Section 3: Processing and Displaying Results ---
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            if uploaded_file.name.endswith('.csv'):
                uploaded_df = pd.read_csv(uploaded_file)
            else:
                uploaded_df = pd.read_excel(uploaded_file)

            if not {'Female', 'Male'}.issubset(uploaded_df.columns):
                st.error("Upload Error: Your file must contain 'Female' and 'Male' columns.")
            else:
                results_list = []
                warnings_list = []

                # --- The Core Processing Loop ---
                for index, row in uploaded_df.iterrows():
                    female_name = row['Female'].strip()
                    male_name = row['Male'].strip()
                    
                    try:
                        # Get GDU values from the master data
                        gdu_female = tool.df.loc[female_name, 'S50_GDUs']
                        gdu_male = tool.df.loc[male_name, 'P50_GDUs']

                        # Generate the plan for this row
                        plan = PlantingPlanner(gdu_male_p50d=int(gdu_male), gdu_female_s50d=int(gdu_female))
                        
                        # Append the results to our list
                        results_list.append({
                            'Female': female_name,
                            'Male': male_name,
                            'GDU Difference (Male-Female)': plan.gdu_difference,
                            'Female S50D': gdu_female,
                            'Male P50D': gdu_male,
                            'Male 1 Planting': plan.recommendation['Male 1']['timing_notes'],
                            'Male 2 Planting': plan.recommendation['Male 2']['timing_notes']
                        })
                    except KeyError as e:
                        # Handle cases where a pedigree in the upload is not in the master data
                        warnings_list.append(f"Skipped row {index + 1}: Pedigree '{e.args[0]}' not found in the master data.")
                
                # --- Display Warnings and Results ---
                st.divider()
                st.subheader("✅ Processing Complete")

                if warnings_list:
                    st.warning("Some rows could not be processed:")
                    for warning in warnings_list:
                        st.write(warning)

                if results_list:
                    summary_df = pd.DataFrame(results_list)
                    st.dataframe(summary_df) # Use st.dataframe for scrollable tables

                    # --- Add a download button for the results ---
                    results_csv = convert_df_to_csv(summary_df)
                    st.download_button(
                        label="Download Results as CSV",
                        data=results_csv,
                        file_name="planting_plan_results.csv",
                        mime="text/csv",
                    )
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

else:
    st.error("Application cannot start because the master pedigree data failed to load.")
