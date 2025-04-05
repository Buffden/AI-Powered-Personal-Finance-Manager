import streamlit as st
from PIL import Image
from backend.utils.receipt import (
    extract_text_from_image,
    extract_receipt_fields,
    add_transaction_to_state
)
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np

class VideoCaptureTransformer(VideoTransformerBase):
    def __init__(self):
        self.frame = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img
        return img

def show_receipt_parser():
    st.title("📸 Receipt Scanner & Parser")

    st.markdown("### Upload from file or use webcam to scan a receipt:")

    # --- Upload option
    uploaded_file = st.file_uploader("🖼️ Upload a receipt image", type=["png", "jpg", "jpeg"])

    # --- Webcam option
    st.markdown("---")
    st.markdown("### 📷 Or capture receipt from webcam:")
    ctx = webrtc_streamer(key="receipt-cam", video_processor_factory=VideoCaptureTransformer, desired_playing_state=False)

    captured_img = None
    if ctx.video_processor and st.button("📸 Capture from Webcam"):
        frame = ctx.video_processor.frame
        if frame is not None:
            captured_img = Image.fromarray(frame)
            st.image(captured_img, caption="Captured from Webcam", use_column_width=True)
        else:
            st.warning("No frame captured. Try again.")

    # --- Extract and Process
    if uploaded_file or captured_img:
        with st.spinner("🔍 Extracting receipt data..."):
            image_to_process = uploaded_file if uploaded_file else captured_img
            text = extract_text_from_image(image_to_process)
            vendor, amount, tx_date = extract_receipt_fields(text)

            st.subheader("📄 Parsed Receipt Info:")
            st.write(f"**Vendor:** {vendor}")
            st.write(f"**Amount:** ${amount:.2f}")
            st.write(f"**Date:** {tx_date}")

            if st.button("➕ Add to Transactions"):
                add_transaction_to_state(vendor, amount, tx_date)
                st.success("✅ Receipt added to transactions and CSV.")
