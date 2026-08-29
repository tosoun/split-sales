import streamlit as st
import pandas as pd
import openpyxl

# Ρύθμιση σελίδας
st.set_page_config(page_title="Dashboard Πωλήσεων - 2 Προϊόντα", page_icon="📊", layout="wide")

st.title("📊 Dashboard Πωλήσεων (2 Προϊόντα)")
st.write("Παρακολούθηση και ανάλυση πωλήσεων για τα δύο βασικά προϊόντα.")

# Ορισμός ονομάτων αρχείων Excel
FILE_PRODUCT_1 = "product1_sales.xlsx"
FILE_PRODUCT_2 = "product2_sales.xlsx"

# Συνάρτηση για φόρτωση δεδομένων με ασφάλεια
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        return None

# Δημιουργία Tabs για τα δύο προϊόντα και τη συνολική σύγκριση
tab1, tab2, tab3 = st.tabs(["📦 Προϊόν 1", "📦 Προϊόν 2", "📈 Σύγκριση / Dashboard"])

# --- TAB 1: ΠΡΟΪΟΝ 1 ---
with tab1:
    st.header("Διαχείριση & Πωλήσεις: Προϊόν 1")
    df1 = load_data(FILE_PRODUCT_1)
    
    if df1 is not None:
        st.success(using_file_msg := f"Φορτώθηκε επιτυχώς το αρχείο: {FILE_PRODUCT_1}")
        
        # Επεξεργασία δεδομένων (Editable dataframe)
        edited_df1 = st.data_editor(df1, num_rows="dynamic", key="editor_p1")
        
        # Κουμπί αποθήκευσης αλλαγών
        if st.button("💾 Αποθήκευση αλλαγών Προϊόντος 1", key="save_p1"):
            edited_df1.to_excel(FILE_PRODUCT_1, index=False)
            st.success("Οι αλλαγές αποθηκεύτηκαν επιτυχώς στο αρχείο Excel!")
            st.rerun()
            
        # Οπτικοποίηση
        if 'Ημερομηνία' in df1.columns and 'Πωλήσεις' in df1.columns:
            st.subheader("Γράφημα Πωλήσεων - Προϊόν 1")
            st.line_chart(df1.set_index('Ημερομηνία')['Πωλήσεις'])
    else:
        st.warning(f"Δεν βρέθηκε το αρχείο `{FILE_PRODUCT_1}`. Παρακαλώ ανεβάστε το στο repository.")

# --- TAB 2: ΠΡΟΪΟΝ 2 ---
with tab2:
    st.header("Διαχείριση & Πωλήσεις: Προϊόν 2")
    df2 = load_data(FILE_PRODUCT_2)
    
    if df2 is not None:
        st.success(f"Φορτώθηκε επιτυχώς το αρχείο: {FILE_PRODUCT_2}")
        
        # Επεξεργασία δεδομένων (Editable dataframe)
        edited_df2 = st.data_editor(df2, num_rows="dynamic", key="editor_p2")
        
        # Κουμπί αποθήκευσης αλλαγών
        if st.button("💾 Αποθήκευση αλλαγών Προϊόντος 2", key="save_p2"):
            edited_df2.to_excel(FILE_PRODUCT_2, index=False)
            st.success("Οι αλλαγές αποθηκεύτηκαν επιτυχώς στο αρχείο Excel!")
            st.rerun()
            
        # Οπτικοποίηση
        if 'Ημερομηνία' in df2.columns and 'Πωλήσεις' in df2.columns:
            st.subheader("Γράφημα Πωλήσεων - Προϊόν 2")
            st.line_chart(df2.set_index('Ημερομηνία')['Πωλήσεις'])
    else:
        st.warning(f"Δεν βρέθηκε το αρχείο `{FILE_PRODUCT_2}`. Παρακαλώ ανεβάστε το στο repository.")

# --- TAB 3: ΣΥΓΚΡΙΣΗ / DASHBOARD ---
with tab3:
    st.header("📈 Συνολική Εικόνα & Σύγκριση")
    
    if df1 is not None and df2 is not None:
        col1, col2 = st.columns(2)
        with col1:
            if 'Πωλήσεις' in df1.columns:
                total_p1 = df1['Πωλήσεις'].sum()
                st.metric(label="Συνολικές Πωλήσεις - Προϊόν 1", value=f"{total_p1:,.2f} €")
        with col2:
            if 'Πωλήσεις' in df2.columns:
                total_p2 = df2['Πωλήσεις'].sum()
                st.metric(label="Συνολικές Πωλήσεις - Προϊόν 2", value=f"{total_p2:,.2f} €")
                
        st.info("Εδώ μπορείτε να προσθέσετε επιπλέον συγκριτικά γραφήματα αν το επιθυμείτε.")
    else:
        st.warning("Παρακαλώ βεβαιωθείτε ότι υπάρχουν και τα δύο αρχεία Excel για να εμφανιστεί η σύγκριση.")