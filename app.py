import streamlit as st
from backend import extract_supply_chain_for_company

st.set_page_config(page_title="Supply Chain Extractor", layout="wide")
st.title("🔗 Supply Chain Finder")

company_name = st.text_input("Enter Company Name:", "Apple Inc")

if st.button("Get Suppliers and Customers"):
    with st.spinner("Fetching data..."):
        result = extract_supply_chain_for_company(company_name)
        st.subheader("🔺 Suppliers")
        if result["suppliers_raw"]:
            for s in result["suppliers_raw"]:
                st.markdown(f"- {s}")
        else:
            st.markdown("_No suppliers found._")

        st.subheader("🔻 Customers")
        if result["customers_raw"]:
            for c in result["customers_raw"]:
                st.markdown(f"- {c}")
        else:
            st.markdown("_No customers found._")
