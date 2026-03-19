import streamlit as st
import pandas as pd
import os

st.title("🌽 Test App")
st.write("If you see this, Streamlit is working!")

# Test 1: Check if pandas works
st.write(f"✅ Pandas version: {pd.__version__}")

# Test 2: Check file existence
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(SCRIPT_DIR, "GDUs_corn_data.csv")

st.write(f"📁 Looking for file at: {csv_path}")
st.write(f"📁 File exists: {os.path.exists(csv_path)}")

# Test 3: List all files in directory
st.write("📂 Files in app directory:")
for f in os.listdir(SCRIPT_DIR):
    st.write(f"  - {f}")

# Test 4: Try to load the CSV
if os.path.exists(csv_path):
    try:
        df = pd.read_csv(csv_path)
        st.success(f"✅ CSV loaded successfully! Shape: {df.shape}")
        st.write("Columns:", df.columns.tolist())
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error loading CSV: {e}")
else:
    st.error("❌ CSV file not found!")
