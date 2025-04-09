import streamlit as st
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
import pandas as pd
from backend.utils.receipt_parser import (
    extract_text_from_image,
    extract_receipt_fields,
    add_transaction_to_state,
    categorize_transaction,
    delete_receipt_transaction
)
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

def show_receipt_parser():
    # 🔁 Initialize session state
    if "webcam_img" not in st.session_state:
        st.session_state["webcam_img"] = None
    if "webcam_capture_requested" not in st.session_state:
        st.session_state["webcam_capture_requested"] = False

    st.title("📸 Receipt Scanner")
    tab1, tab2 = st.tabs(["📁 Upload Receipts", "📷 Scan via Webcam"])

    # ========== 📁 Upload Receipts Tab ==========
    with tab1:
        uploaded_files = st.file_uploader(
            "Upload one or more receipt images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.info(f"📎 You uploaded {len(uploaded_files)} receipt(s).")
            added_count = 0

            for uploaded_file in uploaded_files:
                st.image(uploaded_file, caption=f"🖼️ {uploaded_file.name}", width=300)

                with st.spinner(f"🔍 Extracting text from {uploaded_file.name}..."):
                    text = extract_text_from_image(uploaded_file)
                    vendor, amount, tx_date = extract_receipt_fields(text)
                    category = categorize_transaction(vendor, text)
                    add_transaction_to_state(vendor, amount, tx_date, text)
                    added_count += 1

            st.success(f"✅ Added {added_count} new transaction(s) from uploaded receipts!")

        # ✅ Show all receipt transactions
        if "transactions" in st.session_state:
            receipt_tx = [
                {
                    "Date": tx["date"],
                    "Vendor": tx["merchant_name"],
                    "Amount ($)": tx["amount"],
                    "Category": ", ".join(tx.get("category", [])),
                    "Source": tx.get("source", "")
                }
                for tx in st.session_state.transactions
                if tx.get("source") == "manual_upload"
            ]

            if receipt_tx:
                st.subheader("🧾 Uploaded Receipt Transactions")

                # Render a header row
                header_cols = st.columns([2, 3, 2, 2, 1])
                header_cols[0].markdown("**Date**")
                header_cols[1].markdown("**Vendor**")
                header_cols[2].markdown("**Amount ($)**")
                header_cols[3].markdown("**Category**")
                header_cols[4].markdown("**Delete**")

                for tx in receipt_tx:
                    cols = st.columns([2, 3, 2, 2, 1])
                    cols[0].markdown(tx["Date"])
                    cols[1].markdown(tx["Vendor"])
                    cols[2].markdown(f"${tx['Amount ($)']:.2f}")
                    cols[3].markdown(tx["Category"])

                    # Use transaction_id for accurate targeting
                    matching = [
                        t for t in st.session_state.transactions
                        if t["date"] == tx["Date"] and t["merchant_name"] == tx["Vendor"]
                    ]
                    if matching:
                        transaction_id = matching[0]["transaction_id"]
                        if cols[4].button("❌", key=f"del_{transaction_id}"):
                            from backend.utils.receipt_parser import delete_receipt_transaction
                            delete_receipt_transaction(transaction_id)
                            st.success("🗑️ Receipt deleted.")
                            st.rerun()



            else:
                st.info("No receipt transactions found yet.")

    # ========== 📷 Webcam Capture Tab ==========
    with tab2:
        st.markdown("Click below to enable your webcam and scan the receipt.")

        if not st.session_state["webcam_capture_requested"] and st.session_state["webcam_img"] is None:
            if st.button("📷 Start Webcam & Capture"):
                st.session_state["webcam_capture_requested"] = True
                st.rerun()

        if st.session_state["webcam_capture_requested"]:
            class CaptureProcessor(VideoTransformerBase):
                def __init__(self):
                    self.frame = None

                def transform(self, frame):
                    self.frame = frame.to_ndarray(format="bgr24")
                    return self.frame

            ctx = webrtc_streamer(
                key="receipt-webrtc",
                video_processor_factory=CaptureProcessor,
                desired_playing_state=True,
                media_stream_constraints={"video": True, "audio": False},
                video_html_attrs={
                    "style": {"width": "100%", "height": "300px"},
                    "autoPlay": True,
                    "muted": True
                }
            )

            st.info("Wait a few seconds for webcam to start...")

            if st.button("📸 Capture Photo"):
                if ctx.video_processor and ctx.video_processor.frame is not None:
                    img = Image.fromarray(ctx.video_processor.frame)
                    st.session_state["webcam_img"] = img
                    st.session_state["webcam_capture_requested"] = False
                    st.rerun()
                else:
                    st.warning("⚠️ No frame captured yet. Wait a moment and try again.")

        if st.session_state["webcam_img"] is not None:
            col = st.columns([1, 2, 1])  # center align the image
            with col[1]:
                st.image(st.session_state["webcam_img"], caption="🖼️ Captured Image", width=300)

            with st.spinner("🔍 Extracting from image..."):
                buf = BytesIO()
                st.session_state["webcam_img"].save(buf, format="PNG")
                buf.seek(0)

                text = extract_text_from_image(buf)
                vendor, amount, tx_date = extract_receipt_fields(text)
                category = categorize_transaction(vendor, text)

                st.subheader("🧾 Parsed Data")
                st.markdown(f"**Vendor:** {vendor}")
                st.markdown(f"**Amount:** ${amount:.2f}")
                st.markdown(f"**Date:** {tx_date}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔁 Retake Photo"):
                        st.session_state["webcam_img"] = None
                        st.session_state["webcam_capture_requested"] = True
                        st.rerun()
                with col2:
                    if st.button("➕ Add to Transactions (Webcam)"):
                        add_transaction_to_state(vendor, amount, tx_date, text)
                        st.success("✅ Transaction added!")
                        st.subheader("✅ Added Transaction")
                        st.table([{
                            "Date": str(tx_date),
                            "Name": vendor,
                            "Amount ($)": amount,
                            "Category": category,
                            "Source": "manual_upload"
                        }])
