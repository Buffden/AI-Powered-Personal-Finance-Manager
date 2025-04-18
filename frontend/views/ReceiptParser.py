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
import backend.utils.receipt_parser as rp
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

def show_receipt_parser():
    # 🔁 Initialize session state
    if "webcam_img" not in st.session_state:
        st.session_state["webcam_img"] = None
    if "webcam_capture_requested" not in st.session_state:
        st.session_state["webcam_capture_requested"] = False
    if "pending_receipts" not in st.session_state:
        st.session_state["pending_receipts"] = []
    if "processing_status" not in st.session_state:
        st.session_state["processing_status"] = {}
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []
    if "just_saved" not in st.session_state:
        st.session_state["just_saved"] = False

    # Always show the title
    st.title("📸 Receipt Scanner")

    # Show success message and scan new button prominently if we just saved
    if st.session_state["just_saved"]:
        st.success("✅ Transactions saved successfully!")
        if st.button("📸 Upload More Receipts", type="primary", use_container_width=True):
            # Ensure all states are cleared when starting fresh
            st.session_state["just_saved"] = False
            st.session_state["uploaded_files"] = []
            st.session_state["processing_status"] = {}
            st.session_state["pending_receipts"] = []
            st.session_state["webcam_img"] = None
            st.session_state["webcam_capture_requested"] = False
            st.rerun()

    # Show main interface if not just saved
    if not st.session_state["just_saved"]:
        st.markdown("""
        ### How to use:
        1. 📁 Upload receipt images or 📷 scan them with your webcam
        2. Review the extracted information
        3. Add receipts to pending transactions
        4. Save all pending transactions to finalize
        """)

        # Create tabs for different input methods
        tab1, tab2 = st.tabs(["📁 Upload Receipts", "📷 Scan via Webcam"])

        # Only show the upload interface and processing if we haven't just saved
        if not st.session_state["just_saved"]:
            # ========== 📁 Upload Receipts Tab ==========
            with tab1:
                new_files = st.file_uploader(
                    "Upload one or more receipt images",
                    type=["jpg", "jpeg", "png"],
                    accept_multiple_files=True,
                    help="You can select multiple files at once"
                )

                # Handle new files being added
                if new_files:
                    # Keep existing files that weren't removed and add new ones
                    existing_filenames = {f.name for f in st.session_state["uploaded_files"]}
                    new_filenames = {f.name for f in new_files}
                    
                    # Keep files that weren't removed and add new ones
                    st.session_state["uploaded_files"] = [
                        f for f in st.session_state["uploaded_files"]
                        if f.name in existing_filenames and f.name not in new_filenames
                    ] + list(new_files)
                    
                if st.session_state["uploaded_files"]:
                    st.info(f"📎 You uploaded {len(st.session_state['uploaded_files'])} receipt(s).")
                    
                    # Create a grid layout for receipts
                    cols = st.columns(3)  # 3 columns for the grid
                    remaining_files = []  # Track files that aren't removed
                    
                    for idx, uploaded_file in enumerate(st.session_state["uploaded_files"]):
                        col_idx = idx % 3
                        with cols[col_idx]:
                            with st.container():
                                # Add remove button at the top right of the container
                                col_title, col_remove = st.columns([5, 1])
                                with col_title:
                                    st.markdown(f"**{uploaded_file.name}**")
                                with col_remove:
                                    remove_clicked = st.button("❌", key=f"remove_{uploaded_file.name}")
                                    
                                if not remove_clicked:
                                    # Only show the image and process it if not being removed
                                    remaining_files.append(uploaded_file)
                                    st.image(uploaded_file, use_container_width=True)
                                    
                                    # Show processing status
                                    if uploaded_file.name not in st.session_state["processing_status"]:
                                        st.session_state["processing_status"][uploaded_file.name] = "pending"
                                    
                                    if st.session_state["processing_status"][uploaded_file.name] == "pending":
                                        with st.spinner("🔍 Processing..."):
                                            text = extract_text_from_image(uploaded_file)
                                            vendor, amount, tx_date = extract_receipt_fields(text)
                                            category = categorize_transaction(vendor, text)
                                            st.session_state["processing_status"][uploaded_file.name] = {
                                                "text": text,
                                                "vendor": vendor,
                                                "amount": amount,
                                                "date": tx_date,
                                                "category": category
                                            }
                                    
                                    # Show extracted information in a collapsible section
                                    with st.expander("📝 Details", expanded=False):
                                        if isinstance(st.session_state["processing_status"][uploaded_file.name], dict):
                                            info = st.session_state["processing_status"][uploaded_file.name]
                                            st.markdown(f"**Vendor:** {info['vendor']}")
                                            st.markdown(f"**Amount:** ${info['amount']:.2f}")
                                            st.markdown(f"**Date:** {info['date']}")
                                            st.markdown(f"**Category:** {info['category']}")
                                    
                                    # Check if receipt is already in pending
                                    is_pending = any(
                                        receipt["file"].name == uploaded_file.name 
                                        for receipt in st.session_state["pending_receipts"]
                                    )
                                    
                                    # Automatically add to pending if not already added
                                    if not is_pending:
                                        if isinstance(st.session_state["processing_status"][uploaded_file.name], dict):
                                            info = st.session_state["processing_status"][uploaded_file.name]
                                            st.session_state["pending_receipts"].append({
                                                "file": uploaded_file,
                                                "vendor": info["vendor"],
                                                "amount": info["amount"],
                                                "date": info["date"],
                                                "category": info.get("category", "Uncategorized"),  # Ensure category is always present
                                                "text": info["text"]
                                            })
                                            st.rerun()
                                else:
                                    # Remove from processing status
                                    if uploaded_file.name in st.session_state["processing_status"]:
                                        del st.session_state["processing_status"][uploaded_file.name]
                                    # Remove from pending receipts if present
                                    st.session_state["pending_receipts"] = [
                                        r for r in st.session_state["pending_receipts"]
                                        if r["file"].name != uploaded_file.name
                                    ]
                    
                    # Update the uploaded files list with remaining files
                    if len(remaining_files) != len(st.session_state["uploaded_files"]):
                        st.session_state["uploaded_files"] = remaining_files
                        st.rerun()

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
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("**Captured Receipt**")
                        st.image(st.session_state["webcam_img"], use_container_width=True)

                    with col2:
                        with st.spinner("🔍 Extracting from image..."):
                            buf = BytesIO()
                            st.session_state["webcam_img"].save(buf, format="PNG")
                            buf.seek(0)

                            text = extract_text_from_image(buf)
                            vendor, amount, tx_date = extract_receipt_fields(text)
                            category = categorize_transaction(vendor, text)

                            st.markdown("### 📝 Extracted Information")
                            st.markdown(f"**Vendor:** {vendor}")
                            st.markdown(f"**Amount:** ${amount:.2f}")
                            st.markdown(f"**Date:** {tx_date}")
                            st.markdown(f"**Category:** {category}")

                            # Add to pending receipts
                            if st.button("➕ Add to Pending", key="add_webcam"):
                                st.session_state["pending_receipts"].append({
                                    "file": st.session_state["webcam_img"],
                                    "vendor": vendor,
                                    "amount": amount,
                                    "date": tx_date,
                                    "category": category if category else "Uncategorized",  # Default to "Uncategorized"
                                    "text": text
                                })
                                st.success("✅ Added to pending transactions!")
                                st.session_state["webcam_img"] = None
                                st.session_state["webcam_capture_requested"] = False
                                st.rerun()

        # ========== 📋 Pending Transactions Section ==========
        if st.session_state["pending_receipts"]:
            st.markdown("---")
            st.subheader("📋 Pending Transactions")

            # Build editable DataFrame from pending receipts
            df_pending = pd.DataFrame([
                {
                    "Vendor": r["vendor"],
                    "Amount ($)": r["amount"],
                    "Date": r["date"],
                    "Category": r["category"]
                }
                for r in st.session_state["pending_receipts"]
            ])

            # Show editable table
            edited_df = st.data_editor(
                df_pending,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "Vendor": st.column_config.TextColumn(),
                    "Amount ($)": st.column_config.NumberColumn(format="$%.2f"),
                    "Date": st.column_config.TextColumn(),
                    "Category": st.column_config.TextColumn()
                }
            )

            # Sync changes back to session state
            for i in range(len(edited_df)):
                st.session_state["pending_receipts"][i]["vendor"] = edited_df.at[i, "Vendor"]
                st.session_state["pending_receipts"][i]["amount"] = edited_df.at[i, "Amount ($)"]
                st.session_state["pending_receipts"][i]["date"] = edited_df.at[i, "Date"]
                st.session_state["pending_receipts"][i]["category"] = edited_df.at[i, "Category"]

                # Future date warning
                try:
                    edited_date = pd.to_datetime(edited_df.at[i, "Date"])
                    if edited_date.date() > datetime.today().date():
                        st.warning(f"⚠️ Row {i+1}: Date '{edited_date.date()}' is in the future. Please correct it.")
                except Exception:
                    st.warning(f"⚠️ Row {i+1}: Invalid date format.")

            # Confirm Save Button
            if st.button("💾 Save All Pending Transactions", type="primary", use_container_width=True):
                temp_receipts = st.session_state["pending_receipts"].copy()

                with st.spinner("Saving transactions..."):
                    transaction_ids = []
                    import backend.utils.receipt_parser as rp
                    original_categorize = rp.categorize_transaction

                    for receipt in temp_receipts:
                        # Override categorization to respect user-edited category
                        def dummy_categorize(vendor, text):
                            return receipt["category"]
                        rp.categorize_transaction = dummy_categorize

                        tx_id = add_transaction_to_state(
                            receipt["vendor"],
                            receipt["amount"],
                            receipt["date"],
                            receipt["text"]
                        )

                        rp.categorize_transaction = original_categorize  # Restore original

                        if st.session_state.get("duplicate_warning"):
                            st.warning("⚠️ This transaction already exists and was skipped.")
                            st.session_state.duplicate_warning = False
                            continue
                        transaction_ids.append(tx_id)

                # Clean up after saving
                st.session_state["pending_receipts"] = []
                st.session_state["uploaded_files"] = []
                st.session_state["processing_status"] = {}
                st.session_state["webcam_img"] = None
                st.session_state["webcam_capture_requested"] = False

                if transaction_ids:
                    st.session_state["just_saved"] = True
                else:
                    st.warning("⚠️ Duplicate transactions were skipped. No new transactions were saved.")
                    st.session_state["just_saved"] = False

                st.rerun()


    # ========== 📊 Recent Receipt Transactions Section ==========
    if "transactions" in st.session_state:
        receipt_tx = [tx for tx in st.session_state.transactions if tx.get("source") == "manual_upload"]
        
        if receipt_tx:
            st.markdown("---")
            st.subheader("📊 Recent Receipt Transactions")
            
            # Show transactions in a table with delete option
            for tx in receipt_tx:
                cols = st.columns([2, 3, 2, 2, 1])
                # cols[0].markdown(tx["date"])
                parsed_date = pd.to_datetime(tx["date"], errors="coerce")
                cols[0].markdown(parsed_date.strftime("%Y-%m-%d") if not pd.isnull(parsed_date) else tx["date"])
                cols[1].markdown(tx["merchant_name"])
                if len(cols) > 2:  # Ensure cols[2] exists
                    cols[2].markdown(f"${tx['amount']:.2f}")
                else:
                    st.error("Insufficient columns to display transaction amount.")
                cols[3].markdown(", ".join(tx.get("category", [])))
                
                with cols[4]:
                    if st.button("❌", key=f"del_btn_{tx['transaction_id']}"):
                        st.session_state["confirm_delete_id"] = tx["transaction_id"]

                # Display confirmation area after the row (outside the columns)
                if st.session_state.get("confirm_delete_id") == tx["transaction_id"]:
                    tx_id = tx["transaction_id"]
                    st.markdown("----")
                    st.error(
                        f"🗑️ **Confirm deletion** of **{tx['merchant_name']}** "
                        f"(${tx['amount']:.2f}) on {tx['date'].split()[0]}?"
                    )
                    confirm_col, cancel_col = st.columns([1, 1])

                    with confirm_col:
                        if st.button("✅ Yes, Delete", key=f"confirm_yes_{tx_id}"):
                            delete_receipt_transaction(tx_id)
                            st.success("Transaction deleted.")
                            del st.session_state["confirm_delete_id"]
                            st.rerun()

                    with cancel_col:
                        if st.button("❌ Cancel", key=f"confirm_no_{tx_id}"):
                            del st.session_state["confirm_delete_id"]
                            st.rerun()
