import streamlit as st
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
from backend.utils.receipt_parser import extract_text_from_image, extract_receipt_fields, add_transaction_to_state
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

def show_receipt_parser():
    # 🔁 Initialize session state
    if "webcam_img" not in st.session_state:
        st.session_state["webcam_img"] = None
    if "webcam_capture_requested" not in st.session_state:
        st.session_state["webcam_capture_requested"] = False

    st.title("📸 Receipt Scanner")
    tab1, tab2 = st.tabs(["📁 Upload Receipt", "📷 Scan via Webcam"])

    # ========== 📁 Upload Receipt Tab ==========
    with tab1:
        uploaded_file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="📎 Uploaded Receipt", width=300)
            with st.spinner("🔍 Extracting text..."):
                text = extract_text_from_image(uploaded_file)
                vendor, amount, tx_date = extract_receipt_fields(text)
                st.subheader("🧾 Parsed Data")
                st.markdown(f"**Vendor:** {vendor}")
                st.markdown(f"**Amount:** ${amount:.2f}")
                st.markdown(f"**Date:** {tx_date}")
                if st.button("➕ Add to Transactions (Upload)"):
                    add_transaction_to_state(vendor, amount, tx_date, "Receipt upload")
                    st.success("✅ Transaction added!")

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
                        add_transaction_to_state(vendor, amount, tx_date)
                        st.success("✅ Transaction added!")
