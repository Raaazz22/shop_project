"""
app.py

Streamlit UI only. All AI/API logic lives in backend.py — import from there.
Run with: streamlit run app.py
"""

import base64
from pathlib import Path

import streamlit as st

from backend import (
    save_uploaded_file,
    enhance_image,
    create_passport_photo,
    image_data_extraction,
    chat_with_ai,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="VISHAL VIDEO MIXING LAB",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# PATHS
# ============================================================

ASSETS_DIR = Path("assets")

HOME_BACKGROUND = ASSETS_DIR / "home-background.jpg"
IMAGE_ENHANCEMENT_IMAGE = ASSETS_DIR / "enhancement.jpg"
PASSPORT_IMAGE = ASSETS_DIR / "passport.jpg"
SCAN_IMAGE = ASSETS_DIR / "ocr.jpg"
CHAT_IMAGE = ASSETS_DIR / "chat.png"


# ============================================================
# UI HELPER
# ============================================================

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return ""


# ============================================================
# CUSTOM CSS
# ============================================================

background_base64 = get_base64_image(HOME_BACKGROUND)

st.markdown(
    f"""
    <style>
    /* Only paint html/body black as a fallback — the app container itself
       must stay transparent so the fixed background image behind it
       (.home-background, z-index -1) is actually visible instead of being
       covered by an opaque black layer. */
    html, body {{
        background-color: #000000 !important;
    }}
    [data-testid="stAppViewContainer"] {{
        background-color: transparent !important;
        color: white;
    }}
    [data-testid="stHeader"] {{
        display: none !important;
        height: 0px !important;
    }}

    .block-container {{
        padding-top: 0.6rem !important;
        padding-bottom: 0.8rem !important;
        max-width: 1400px;
    }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    /* Hide the visible scrollbar everywhere, but keep scrolling working */
    ::-webkit-scrollbar {{
        display: none;
    }}
    html {{
        scrollbar-width: none;
        -ms-overflow-style: none;
    }}
    body {{
        overflow-x: hidden;
    }}

    .home-background {{
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100vh;
        background-image:
            linear-gradient(rgba(0,0,0,0.68), rgba(0,0,0,0.88)),
            url("data:image/jpeg;base64,{background_base64}");
        background-size: cover;
        background-position: center;
        z-index: -1;
    }}

    .hero {{ text-align: center; padding-top: 12px; padding-bottom: 12px; }}
    .hero-title {{
        font-size: 34px; font-weight: 900; letter-spacing: 2px;
        color: #ffffff; margin-bottom: 4px;
        text-shadow: 0 4px 20px rgba(0,0,0,0.8);
    }}
    .hero-subtitle {{ font-size: 13px; color: #d1d5db; letter-spacing: 1.5px; }}
    .hero-line {{ width: 70px; height: 2px; background: white; margin: 12px auto; }}

    .service-card {{
        position: relative; height: 240px; border-radius: 16px; overflow: hidden;
        background: #111111; border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 10px 40px rgba(0,0,0,0.55);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
        margin-bottom: 0px;
    }}
    .service-card:hover {{
        transform: translateY(-8px) scale(1.015);
        border: 1px solid rgba(255,255,255,0.45);
        box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    }}
    .service-image {{
        width: 100%; height: 100%; object-fit: cover; opacity: 0.72;
        transition: transform 0.4s ease, opacity 0.4s ease;
    }}
    .service-card:hover .service-image {{ transform: scale(1.08); opacity: 0.55; }}
    .service-overlay {{
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.95), rgba(0,0,0,0.20));
        display: flex; flex-direction: column; justify-content: flex-end; padding: 14px;
    }}
    .service-title {{ font-size: 16px; font-weight: 800; color: white; margin-bottom: 4px; }}
    .service-description {{ font-size: 11.5px; color: #d1d5db; line-height: 1.35; }}
    .service-arrow {{ margin-top: 8px; font-size: 11px; font-weight: 700; color: white; letter-spacing: 1px; }}

    .footer {{ text-align: center; color: #6b7280; font-size: 11px; margin-top: 10px; }}

    /* Compact the nav-bar and service-open buttons */
    div.stButton > button {{
        padding: 0.3rem 0.5rem;
        font-size: 0.8rem;
        min-height: 2rem;
    }}

    /* Tighten default vertical gaps Streamlit adds around elements/dividers */
    hr {{ margin: 0.4rem 0 !important; }}
    div[data-testid="stVerticalBlock"] > div {{ gap: 0.4rem; }}

    @media (max-width: 768px) {{
        .hero {{ padding-top: 10px; }}
        .hero-title {{ font-size: 24px; }}
        .hero-subtitle {{ font-size: 11px; }}
        .service-card {{ height: 160px; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if background_base64:
    st.markdown('<div class="home-background"></div>', unsafe_allow_html=True)


# ============================================================
# SESSION STATE / NAVIGATION
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "messages" not in st.session_state:
    st.session_state.messages = []


PAGES = [
    "Home",
    "Image Enhancement",
    "Passport Size Photo",
    "Scan Image → Text",
    "Chat Support",
]

NAV_LABELS = {
    "Home": "🏠 Home",
    "Image Enhancement": "✨ Image Enhance",
    "Passport Size Photo": "🪪 Passport Photo",
    "Scan Image → Text": "📄 Scan→Text",
    "Chat Support": "💬 Chat",
}


def navigate(page):
    st.session_state.page = page


def render_nav():
    """Persistent nav bar with all service options — shown on every page."""
    cols = st.columns(len(PAGES))
    for i, page in enumerate(PAGES):
        with cols[i]:
            is_current = st.session_state.page == page
            if st.button(
                NAV_LABELS[page],
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                if not is_current:
                    st.session_state.page = page
                    st.rerun()
    st.divider()


def service_card(image_path, title, description, button_key, target_page):
    image_b64 = get_base64_image(image_path)
    st.markdown(
        f"""
        <div class="service-card">
            <img class="service-image" src="data:image/jpeg;base64,{image_b64}" />
            <div class="service-overlay">
                <div class="service-title">{title}</div>
                <div class="service-description">{description}</div>
                <div class="service-arrow">OPEN SERVICE →</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(f"Open {title}", key=button_key, use_container_width=True):
        navigate(target_page)
        st.rerun()


render_nav()


# ============================================================
# HOME PAGE
# ============================================================

if st.session_state.page == "Home":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">VISHAL VIDEO MIXING LAB</div>
            <div class="hero-line"></div>
            <div class="hero-subtitle">AI POWERED IMAGE & DIGITAL SERVICES</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        service_card(
            IMAGE_ENHANCEMENT_IMAGE,
            "Image Enhancement",
            "Improve sharpness, lighting, colors and details using AI.",
            "enhancement",
            "Image Enhancement",
        )
    with col2:
        service_card(
            PASSPORT_IMAGE,
            "Passport Size Photo",
            "Professional passport photos with your chosen background.",
            "passport",
            "Passport Size Photo",
        )
    with col3:
        service_card(
            SCAN_IMAGE,
            "Scan Image → Text",
            "Scan documents/images and extract readable text using AI.",
            "scan",
            "Scan Image → Text",
        )
    with col4:
        service_card(
            CHAT_IMAGE,
            "Chat Support",
            "Get instant assistance from our AI-powered assistant.",
            "chat",
            "Chat Support",
        )

    st.markdown(
        """
        <div class="footer">
            VISHAL VIDEO MIXING LAB<br>
            AI Powered Digital Videography and Photgraphy Services
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# OTHER PAGES
# ============================================================

else:
    # --------------------------------------------------------
    # IMAGE ENHANCEMENT
    # --------------------------------------------------------
    if st.session_state.page == "Image Enhancement":
        st.header("Image Enhancement")
        st.write("Upload an image and enhance its quality using AI.")

        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"])

        if uploaded_file:
            # st.image(uploaded_file, caption="Original Image", width=500)

            prompt = st.text_area(
                "Enhancement Instructions",
                value="""Enhance this image while preserving the main subject's identity, face, hairstyle, clothing, body proportions, pose and expression.

Improve:
- sharpness
- lighting
- contrast
- color balance
- fine details
- clarity
- noise reduction

Keep the result natural and photorealistic.
Do not change the person's identity.
Do not add another person.
Do not change the clothing.""",
                height=220,
            )

            if st.button("Enhance Image", type="primary", use_container_width=True):
                with st.spinner("Enhancing image..."):
                    try:
                        input_path = save_uploaded_file(uploaded_file)
                        output_path = enhance_image(input_path, prompt)
                        st.success("Done!")
                        st.image(output_path, caption="Enhanced Image", width=500)
                        with open(output_path, "rb") as f:
                            st.download_button(
                                "Download Enhanced Image",
                                data=f,
                                file_name="enhanced.jpg",
                                mime="image/jpeg",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.error(str(e))

    # --------------------------------------------------------
    # PASSPORT PHOTO
    # --------------------------------------------------------
    elif st.session_state.page == "Passport Size Photo":
        st.header("Passport Size Photo")

        uploaded_file = st.file_uploader("Upload Photo", type=["jpg", "jpeg", "png", "webp"])

        st.subheader("Select Background Color")
        colors = {
            "White": "#FFFFFF",
            "Light Blue": "#ADD8E6",
            "Blue": "#0000FF",
            "Red": "#FF0000",
            "Green": "#008000",
            "Gray": "#808080",
        }
        selected_color = st.selectbox("Background Color", list(colors.keys()))
        st.write(f"Selected color: **{selected_color}**")

        if uploaded_file:
            # st.image(uploaded_file, caption="Original Photo", width=400)

            if st.button("Create Passport Photo", type="primary", use_container_width=True):
                with st.spinner("Creating passport photo..."):
                    try:
                        input_path = save_uploaded_file(uploaded_file)
                        output_path = create_passport_photo(input_path, selected_color)
                        st.success("Done!")
                        st.image(output_path, caption="Passport Photo", width=400)
                        with open(output_path, "rb") as f:
                            st.download_button(
                                "Download Passport Photo",
                                data=f,
                                file_name="passport_photo.jpg",
                                mime="image/jpeg",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.error(str(e))

    # --------------------------------------------------------
    # SCAN TO TEXT
    # --------------------------------------------------------
    elif st.session_state.page == "Scan Image → Text":
        st.header("Scan Image → Text")

        uploaded_file = st.file_uploader("Upload Scanned Image", type=["jpg", "jpeg", "png", "webp"])

        if uploaded_file:
            # st.image(uploaded_file, width=600)

            if st.button("Extract Text", type="primary", use_container_width=True):
                with st.spinner("Reading image..."):
                    try:
                        input_path = save_uploaded_file(uploaded_file)
                        extracted = image_data_extraction(input_path)
                        st.success("Done!")
                        st.text_area("Extracted Content", value=extracted, height=300)
                        st.download_button(
                            "Download as .txt",
                            data=extracted,
                            file_name="extracted_text.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(str(e))

    # --------------------------------------------------------
    # CHAT SUPPORT
    # --------------------------------------------------------
    elif st.session_state.page == "Chat Support":
        st.header("Chat Support")

        # Load the system prompt once, not on every rerun.
        @st.cache_data
        def load_system_prompt():
            with open("prompts/chat_prompt.txt", "r") as f:
                return f.read()

        system_prompt = load_system_prompt()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        user_message = st.chat_input("Ask something...")

        if user_message:
            # Store the RAW user text for display/history — never the
            # formatted prompt, or it leaks into the chat UI on rerender.
            st.session_state.messages.append({"role": "user", "content": user_message})
            with st.chat_message("user"):
                st.write(user_message)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Build the model-facing message list separately:
                        # system prompt + raw conversation history.
                        model_messages = [
                            {"role": "system", "content": system_prompt}
                        ] + st.session_state.messages

                        reply = chat_with_ai(model_messages)
                    except Exception as e:
                        reply = f"⚠️ {e}"
                    st.write(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})