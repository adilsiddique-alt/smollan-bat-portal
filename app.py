import streamlit as st
from google import genai
from PIL import Image
import hashlib
import os
import csv
import pandas as pd
from datetime import datetime
import time
import shutil

# 1. PAGE SETUP & CORPORATE STYLING
st.set_page_config(page_title="Smollan BAT Portal", page_icon="📸", layout="centered")

# Master CSS Stylesheet (Slate Base, Emerald Green Accents, Clean Navigation Pills)
st.markdown("""
    <style>
    /* Main Background & Text Colors */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0F172A !important; 
        color: #F8FAFC !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 🚫 HIDE THE DEPLOYER TOOLBAR COMPLETELY (Removes Fork, GitHub & Status Header) */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 1. SLEEK SIDEBAR NAVIGATION PACKAGING */
    [data-testid="stSidebar"] {
        background-color: #090D16 !important; 
        border-right: 1px solid #1E293B;
    }
    
    /* Style the Navigation Menu header text */
    div[data-testid="stRadio"] [data-testid="stWidgetLabel"] p {
        color: #64748B !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        font-weight: bold !important;
        margin-bottom: 12px !important;
    }
    
    /* Tighten the spacing between button options */
    div[data-testid="stRadio"] > div {
        gap: 10px !important; 
    }
    
    /* Transform options into wide, clean menu buttons */
    div[data-testid="stRadio"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        background-color: #1E293B !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        color: #94A3B8 !important;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
    }
    
    /* Active State styling (Smollan operational green glow) */
    div[data-testid="stRadio"] label:has(input[checked]) {
        border-color: #10B981 !important;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: bold !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    
    /* Target and erase ONLY the custom radio circle icon cleanly */
    div[data-testid="stCustomControl"] {
        display: none !important;
    }
    
    /* Enforce clear, readable font positioning for button text */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        margin: 0px !important;
        font-size: 14px !important;
        color: inherit !important;
    }

    /* 2. MAIN INTERFACE CARD STYLE */
    div[data-testid="stVerticalBlock"] > div:has(div.stSelectbox) {
        background-color: #1E293B; 
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Modern Full-Width Mobile Action Button */
    div.stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important; 
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 14px 28px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important; 
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
        transition: all 0.2s ease;
    }
    
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }
    
    /* File Dropzone Style */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #0F172A !important;
        border: 2px dashed #10B981 !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FILE CONFIGURATION PATHS
DB_FILE = "audit_log.csv"
STORAGE_FOLDER = "approved_submissions"
STORES_CONFIG_FILE = "stores.csv"

# ==========================================
# LOAD MASTER STORES DIRECTORY (CSV)
# ==========================================
try:
    stores_df = pd.read_csv(STORES_CONFIG_FILE)
    ALL_STORES = stores_df['Store Name'].tolist()
    STORE_QUOTAS = dict(zip(stores_df['Store Name'], stores_df['Required Images']))
except FileNotFoundError:
    st.error(f"Critical Error: Could not find '{STORES_CONFIG_FILE}'. Please verify file location.")
    st.stop()

# Sidebar Navigation Control
view_mode = st.sidebar.radio("Navigation Menu", ["Store Upload Portal", "Smollan Admin Dashboard"])

# ==========================================
# VIEW 1: STORE UPLOAD PORTAL
# ==========================================
if view_mode == "Store Upload Portal":
    st.markdown("<p style='color: #10B981; font-weight: bold; margin-bottom: -10px;'>🌐 SMOLLAN FIELD OPERATIONS</p>", unsafe_allow_html=True)
    st.title("📸 BAT Execution Portal")
    st.write("Please select your outlet below and upload compliant merchandising execution images.")
    st.markdown("---")
    
    selected_store = st.selectbox("Select your Store:", ["Select a store..."] + ALL_STORES)

    if selected_store != "Select a store...":
        required_images = int(STORE_QUOTAS[selected_store])
        st.info(f"📋 **Target Quota:** This location requires **{required_images} unique display images** for successful logging.")

        # Secure client setup reading variables from hidden dashboard secrets
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"]) 

        uploaded_files = st.file_uploader(
            "Select display capture files:", 
            type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True
        )

        if uploaded_files:
            unique_files = []
            seen_hashes = set()
            duplicate_count = 0

            for file in uploaded_files:
                file_bytes = file.read()
                file_hash = hashlib.md5(file_bytes).hexdigest()
                file.seek(0)
                
                if file_hash not in seen_hashes:
                    seen_hashes.add(file_hash)
                    unique_files.append(file)
                else:
                    duplicate_count += 1

            if duplicate_count > 0:
                st.warning(f"⚠️ Flagged and removed {duplicate_count} duplicate file uploads.")

            st.write(f"Validated unique images: **{len(unique_files)} / {required_images}**")

            if st.button("🚀 Run Quality Control & Submit Audit"):
                if len(unique_files) < required_images:
                    st.error(f"❌ Submission denied. You have provided {len(unique_files)} unique image(s), but this store profile requires exactly {required_images}.")
                else:
                    all_passed = True
                    temp_results = []
                    
                    for index, file in enumerate(unique_files):
                        st.markdown(f"### 🔍 Auditing Image {index + 1}...")
                        img = Image.open(file)
                        st.image(img, width=320)
                        
                        try:
                            with open("prompt.txt", "r", encoding="utf-8") as f:
                                prompt = f.read()
                        except FileNotFoundError:
                            st.error("Missing rule configuration file: prompt.txt")
                            st.stop()
                        
                        with st.spinner(f"AI inspecting parameters on image {index + 1}..."):
                            time.sleep(5)  
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[img, prompt]
                            )
                        
                        ai_report = response.text
                        
                        if "STATUS: APPROVED" in ai_report:
                            st.success(f"Image {index + 1}: COMPLIANT")
                            st.text_area(f"Audit Summary {index + 1}:", value=ai_report, height=100, key=f"rep_{index}")
                            temp_results.append({"file": file, "img_obj": img, "report": ai_report})
                        else:
                            st.error(f"Image {index + 1}: NON-COMPLIANT")
                            st.text_area(f"Correction Breakdown {index + 1}:", value=ai_report, height=100, key=f"rep_{index}")
                            all_passed = False
                    
                    st.markdown("---")
                    if all_passed:
                        now = datetime.now()
                        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                        
                        current_month_folder = now.strftime("%Y-%m")
                        target_monthly_path = os.path.join(STORAGE_FOLDER, current_month_folder)
                        
                        if not os.path.exists(target_monthly_path):
                            os.makedirs(target_monthly_path)

                        clean_store_name = selected_store.replace(" ", "_").replace("(", "").replace(")", "")

                        for i, result in enumerate(temp_results):
                            new_filename = f"{clean_store_name}_{timestamp}_img{i+1}.jpg"
                            save_path = os.path.join(target_monthly_path, new_filename)
                            result["img_obj"].convert('RGB').save(save_path, "JPEG")
                            
                            file_exists = os.path.isfile(DB_FILE)
                            with open(DB_FILE, mode='a', newline='', encoding='utf-8') as csv_file:
                                writer = csv.writer(csv_file)
                                if not file_exists:
                                    writer.writerow(["Timestamp", "Store", "Image Folder Path", "Image Name", "AI Report Summary"])
                                
                                short_report = result["report"].replace("\n", " | ")
                                writer.writerow([timestamp, selected_store, current_month_folder, new_filename, short_report])
                        
                        st.success(f"💾 ARCHIVED! Verification complete. Images filed securely under directory: /{current_month_folder}")
                    else:
                        st.error("❌ Process Halting. One or more images failed the compliance rubric.")

# ==========================================
# VIEW 2: SMOLLAN ADMIN DASHBOARD
# ==========================================
elif view_mode == "Smollan Admin Dashboard":
    st.title("📊 Compliance & Oversight Command")
    
    admin_password = st.text_input("Enter Admin Credentials:", type="password")
    
    if admin_password == "Smollan2026":
        st.write("Real-time regional compliance matrix:")
        st.markdown("---")
        
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            div_options = ["All Divisions"] + sorted(stores_df['Division'].dropna().unique().tolist())
            selected_div = st.selectbox("Filter by Division:", div_options)
            
        with col_filter2:
            if selected_div != "All Divisions":
                regional_df = stores_df[stores_df['Division'] == selected_div]
            else:
                regional_df = stores_df
                
            reg_options = ["All Regions"] + sorted(regional_df['Region'].dropna().unique().tolist())
            selected_reg = st.selectbox("Filter by Region:", reg_options)
        
        st.markdown("---")

        filtered_stores_df = stores_df.copy()
        if selected_div != "All Divisions":
            filtered_stores_df = filtered_stores_df[filtered_stores_df['Division'] == selected_div]
        if selected_reg != "All Regions":
            filtered_stores_df = filtered_stores_df[filtered_stores_df['Region'] == selected_reg]
            
        active_target_stores = filtered_stores_df['Store Name'].tolist()

        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            all_submitted_stores = set(df['Store'].unique())
        else:
            all_submitted_stores = set()
            df = None

        submitted_in_filter = [store for store in active_target_stores if store in all_submitted_stores]
        missing_stores = [store for store in active_target_stores if store not in all_submitted_stores]
        
        col1, col2 = st.columns(2)
        col1.metric("Logged Submissions", f"{len(submitted_in_filter)} / {len(active_target_stores)}")
        col2.metric("Outstanding Escalations", len(missing_stores))
        
        if missing_stores:
            for store in missing_stores:
                st.error(f"❌ {store} - Awaiting mandatory monthly upload execution profiles.")
        else:
            st.success("🎉 Target Complete! 100% compliance logged for this filtered criteria.")

        st.markdown("---")
        st.markdown("### 📜 Data Audit Logs")
        if df is not None:
            filtered_log_df = df[df['Store'].isin(active_target_stores)]
            st.dataframe(filtered_log_df)
        else:
            st.info("No submission entries logged in current ledger.")
            
        # LIFECYCLE RESET OPERATIONS TOOL
        st.markdown("---")
        st.markdown("### ⚙️ Lifecycle Utility Control")
        st.write("Clear operational ledger and remove physical image archives ahead of the next monthly cycle.")
        
        if st.button("⚠️ Trigger Full System Reset for New Month"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                
            if os.path.exists(STORAGE_FOLDER):
                shutil.rmtree(STORAGE_FOLDER)  
                os.makedirs(STORAGE_FOLDER)    
                
            st.success("🔄 Action complete. Database tables dropped and target photo storage directory purged cleanly.")
            time.sleep(2)
            st.rerun() 
            
    elif admin_password != "":
        st.error("🔒 Unauthorized signature token. Access denied.")