import io
from datetime import datetime

import streamlit as st
import barcode
from barcode.writer import ImageWriter, SVGWriter
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Pro Barcode Studio",
    page_icon="▥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(59, 130, 246, 0.10),
                    transparent 30%
                ),
                radial-gradient(
                    circle at bottom left,
                    rgba(139, 92, 246, 0.08),
                    transparent 30%
                ),
                #0b1020;
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 28px 32px;
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    rgba(30, 41, 59, 0.95),
                    rgba(15, 23, 42, 0.95)
                );
            border: 1px solid rgba(148, 163, 184, 0.15);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
            margin-bottom: 25px;
        }

        .hero-title {
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -1.5px;
            margin-bottom: 5px;
            color: #f8fafc;
        }

        .hero-subtitle {
            font-size: 16px;
            color: #94a3b8;
        }

        .card {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.13);
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.18);
        }

        .card-title {
            color: #f8fafc;
            font-size: 19px;
            font-weight: 700;
            margin-bottom: 14px;
        }

        .stat-card {
            text-align: center;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.13);
            border-radius: 16px;
            padding: 18px 10px;
        }

        .stat-number {
            font-size: 25px;
            font-weight: 800;
            color: #60a5fa;
        }

        .stat-label {
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 650;
            min-height: 42px;
        }

        section[data-testid="stSidebar"] {
            background: #080d1a;
            border-right: 1px solid rgba(148, 163, 184, 0.10);
        }

        input,
        textarea {
            border-radius: 10px !important;
        }

        .preview-box {
            background: white;
            border-radius: 18px;
            padding: 25px;
            min-height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: 0 15px 45px rgba(0,0,0,0.25);
        }
        .preview-box img {
            max-width: 500px !important;
            width: auto !important;
            height: auto !important;
            object-fit: contain;
        }

        .footer {
            text-align: center;
            color: #64748b;
            font-size: 13px;
            margin-top: 45px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "generated_count" not in st.session_state:
    st.session_state.generated_count = 0

if "current_png" not in st.session_state:
    st.session_state.current_png = None

if "current_svg" not in st.session_state:
    st.session_state.current_svg = None

if "current_filename" not in st.session_state:
    st.session_state.current_filename = "barcode"


# ============================================================
# BARCODE FORMATS
# ============================================================

BARCODE_FORMATS = {
    "Code 128": "code128",
    "Code 39": "code39",
    "EAN-13": "ean13",
    "EAN-8": "ean8",
    "UPC-A": "upca",
    "ITF-14": "itf14",
}


# ============================================================
# VALIDATION
# ============================================================

def validate_barcode(code_value, barcode_format):
    """Validate barcode value according to barcode format."""

    code_value = code_value.strip()

    if not code_value:
        return False, "Please enter a barcode value."

    if barcode_format == "ean13":
        if not code_value.isdigit():
            return False, "EAN-13 must contain only numbers."

        if len(code_value) not in (12, 13):
            return False, (
                "EAN-13 requires 12 digits or 13 digits."
            )

    elif barcode_format == "ean8":
        if not code_value.isdigit():
            return False, "EAN-8 must contain only numbers."

        if len(code_value) not in (7, 8):
            return False, (
                "EAN-8 requires 7 digits or 8 digits."
            )

    elif barcode_format == "upca":
        if not code_value.isdigit():
            return False, "UPC-A must contain only numbers."

        if len(code_value) not in (11, 12):
            return False, (
                "UPC-A requires 11 digits or 12 digits."
            )

    elif barcode_format == "itf14":
        if not code_value.isdigit():
            return False, "ITF-14 must contain only numbers."

        if len(code_value) not in (13, 14):
            return False, (
                "ITF-14 requires 13 digits or 14 digits."
            )

    elif barcode_format == "code39":
        allowed = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"

        if not all(
            char in allowed
            for char in code_value.upper()
        ):
            return False, (
                "Code 39 contains unsupported characters."
            )

    return True, ""


# ============================================================
# FONT
# ============================================================

def get_font(size=30):
    """Find a suitable bold font."""

    font_paths = [
        # Windows
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",

        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/"
        "LiberationSans-Bold.ttf",

        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue

    return ImageFont.load_default()


# ============================================================
# GENERATE PNG BARCODE
# ============================================================

def generate_barcode(
    code_value,
    barcode_format,
    foreground,
    background,
    module_width,
    module_height,
    quiet_zone,
    font_size,
    text_distance,
    write_text,
):
    """Generate barcode as PNG."""

    barcode_class = barcode.get_barcode_class(
        barcode_format
    )

    options = {
        "module_width": module_width,
        "module_height": module_height,
        "quiet_zone": quiet_zone,
        "font_size": font_size,
        "text_distance": text_distance,
        "write_text": write_text,
        "foreground": foreground,
        "background": background,
        "dpi": 300,
    }

    barcode_instance = barcode_class(
        code_value,
        writer=ImageWriter(),
    )

    output = io.BytesIO()

    barcode_instance.write(
        output,
        options=options,
    )

    output.seek(0)

    return output


# ============================================================
# GENERATE SVG
# ============================================================

def generate_svg(
    code_value,
    barcode_format,
    foreground,
    background,
    module_width,
    module_height,
    quiet_zone,
    font_size,
    text_distance,
    write_text,
):
    """Generate barcode as SVG."""

    barcode_class = barcode.get_barcode_class(
        barcode_format
    )

    options = {
        "module_width": module_width,
        "module_height": module_height,
        "quiet_zone": quiet_zone,
        "font_size": font_size,
        "text_distance": text_distance,
        "write_text": write_text,
        "foreground": foreground,
        "background": background,
    }

    barcode_instance = barcode_class(
        code_value,
        writer=SVGWriter(),
    )

    output = io.BytesIO()

    barcode_instance.write(
        output,
        options=options,
    )

    output.seek(0)

    return output


# ============================================================
# ADD NAME ABOVE BARCODE
# ============================================================

def add_name_to_image(
    image_bytes,
    name,
    text_color="#111827",
):
    """Add product name above the barcode."""

    image = Image.open(image_bytes).convert("RGB")

    width, height = image.size

    header_height = 90

    canvas = Image.new(
        "RGB",
        (width, height + header_height),
        "white",
    )

    draw = ImageDraw.Draw(canvas)

    font = get_font(30)

    bbox = draw.textbbox(
        (0, 0),
        name,
        font=font,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = max(
        (width - text_width) // 2,
        10,
    )

    y = max(
        (header_height - text_height) // 2,
        5,
    )

    draw.text(
        (x, y),
        name,
        fill=text_color,
        font=font,
    )

    canvas.paste(
        image,
        (0, header_height),
    )

    output = io.BytesIO()

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    output.seek(0)

    return output


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            ▥ Pro Barcode Studio
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚙️ Barcode Settings")

    barcode_name = st.text_input(
        "Barcode Name",
        placeholder="e.g. JD MANGO LOTA",
        help="Name displayed above the barcode.",
    )

    barcode_format_label = st.selectbox(
        "Barcode Format",
        list(BARCODE_FORMATS.keys()),
        index=0,
    )

    barcode_format = BARCODE_FORMATS[
        barcode_format_label
    ]

    st.markdown("---")

    st.markdown("### 🎨 Appearance")

    foreground = st.color_picker(
        "Barcode Color",
        "#000000",
    )

    background = st.color_picker(
        "Background Color",
        "#FFFFFF",
    )

    write_text = st.checkbox(
        "Show code below barcode",
        value=True,
    )

    st.markdown("### 📐 Dimensions")

    module_width = st.slider(
        "Bar Width",
        min_value=0.20,
        max_value=1.00,
        value=0.33,
        step=0.01,
    )

    module_height = st.slider(
        "Bar Height",
        min_value=5.0,
        max_value=50.0,
        value=15.0,
        step=1.0,
    )

    quiet_zone = st.slider(
        "Quiet Zone",
        min_value=1.0,
        max_value=10.0,
        value=6.5,
        step=0.5,
    )

    font_size = st.slider(
        "Text Size",
        min_value=6,
        max_value=24,
        value=10,
    )

    text_distance = st.slider(
        "Text Distance",
        min_value=1,
        max_value=10,
        value=5,
    )

    st.markdown("---")

    st.caption(
        "For reliable scanning, black bars on a white "
        "background are recommended."
    )


# ============================================================
# MAIN INPUT
# ============================================================

left, right = st.columns(
    [1, 1.35],
    gap="large",
)


# ============================================================
# LEFT SIDE
# ============================================================

with left:

    st.markdown(
        """
        <div class="card">
            <div class="card-title">
                📝 Barcode Information
            </div>
        """,
        unsafe_allow_html=True,
    )

    code_value = st.text_input(
        "Barcode Code",
        placeholder="Enter product or barcode number",
        help="Value that will be encoded.",
    )

    st.caption(
        f"Selected format: **{barcode_format_label}**"
    )

    examples = {
        "Code 128": "JD123456",
        "Code 39": "PRODUCT-123",
        "EAN-13": "890123456789",
        "EAN-8": "1234567",
        "UPC-A": "12345678901",
        "ITF-14": "1234567890123",
    }

    st.info(
        f"Example: `{examples[barcode_format_label]}`"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    generate_clicked = st.button(
        "✨ Generate Barcode",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# GENERATE BARCODE
# ============================================================

if generate_clicked:

    valid, error_message = validate_barcode(
        code_value,
        barcode_format,
    )

    if not barcode_name.strip():

        st.error(
            "Please enter a barcode name."
        )

    elif not valid:

        st.error(error_message)

    else:

        try:

            # -----------------------------------------------
            # Generate PNG
            # -----------------------------------------------

            png_buffer = generate_barcode(
                code_value=code_value,
                barcode_format=barcode_format,
                foreground=foreground,
                background=background,
                module_width=module_width,
                module_height=module_height,
                quiet_zone=quiet_zone,
                font_size=font_size,
                text_distance=text_distance,
                write_text=write_text,
            )

            # -----------------------------------------------
            # Add product name
            # -----------------------------------------------

            named_png = add_name_to_image(
                png_buffer,
                barcode_name.strip(),
            )

            # -----------------------------------------------
            # Generate SVG
            # -----------------------------------------------

            svg_buffer = generate_svg(
                code_value=code_value,
                barcode_format=barcode_format,
                foreground=foreground,
                background=background,
                module_width=module_width,
                module_height=module_height,
                quiet_zone=quiet_zone,
                font_size=font_size,
                text_distance=text_distance,
                write_text=write_text,
            )

            # -----------------------------------------------
            # Store results
            # -----------------------------------------------

            st.session_state.current_png = (
                named_png.getvalue()
            )

            st.session_state.current_svg = (
                svg_buffer.getvalue()
            )

            st.session_state.current_filename = (
                barcode_name
                .strip()
                .replace(" ", "_")
                .replace("/", "_")
            )

            st.session_state.generated_count += 1

            # -----------------------------------------------
            # History
            # -----------------------------------------------

            st.session_state.history.insert(
                0,
                {
                    "name": barcode_name.strip(),
                    "code": code_value.strip(),
                    "format": barcode_format_label,
                    "time": datetime.now().strftime(
                        "%d %b %Y, %H:%M"
                    ),
                },
            )

            st.session_state.history = (
                st.session_state.history[:10]
            )

            st.success(
                "Barcode generated successfully!"
            )

        except Exception as error:

            st.error(
                f"Unable to generate barcode: {error}"
            )


# ============================================================
# RIGHT SIDE — PREVIEW
# ============================================================
# ============================================================
# RIGHT SIDE — PREVIEW
# ============================================================

with right:

    st.markdown(
        """
        <div class="card">
            <div class="card-title">
                👁️ Barcode Preview
            </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.current_png:

        st.markdown(
            """
            <div class="preview-box">
            """,
            unsafe_allow_html=True,
        )

        # Properly sized barcode preview
        st.image(
            st.session_state.current_png,
            width=500,
        )

        st.markdown(
            """
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="preview-box">
                <span style="
                    color:#64748b;
                    font-size:16px;
                ">
                    Your generated barcode will appear here.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

# ============================================================
# DOWNLOAD
# ============================================================

if st.session_state.current_png:

    st.success(
        "Barcode is ready for download."
    )

    download_col1, download_col2 = st.columns(2)

    filename = st.session_state.current_filename

    with download_col1:

        st.download_button(
            label="⬇️ Download PNG",
            data=st.session_state.current_png,
            file_name=f"{filename}.png",
            mime="image/png",
            use_container_width=True,
        )

    with download_col2:

        st.download_button(
            label="⬇️ Download SVG",
            data=st.session_state.current_svg,
            file_name=f"{filename}.svg",
            mime="image/svg+xml",
            use_container_width=True,
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# STATISTICS
# ============================================================

st.markdown(
    "### 📊 Studio Statistics"
)

stat1, stat2, stat3, stat4 = st.columns(4)


with stat1:

    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-number">
                {st.session_state.generated_count}
            </div>
            <div class="stat-label">
                Generated
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with stat2:

    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-number">
                {len(st.session_state.history)}
            </div>
            <div class="stat-label">
                History
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with stat3:

    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-number">
                {barcode_format_label}
            </div>
            <div class="stat-label">
                Current Format
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with stat4:

    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-number">
                300 DPI
            </div>
            <div class="stat-label">
                Output Quality
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HISTORY
# ============================================================

if st.session_state.history:

    st.markdown(
        "### 🕘 Recent Barcodes"
    )

    for item in st.session_state.history:

        col1, col2, col3, col4 = st.columns(
            [2.2, 2.2, 1.4, 1.8]
        )

        with col1:

            st.write(
                f"**{item['name']}**"
            )

        with col2:

            st.code(
                item["code"],
                language=None,
            )

        with col3:

            st.caption(
                item["format"]
            )

        with col4:

            st.caption(
                item["time"]
            )


# ============================================================
# BARCODE FORMAT GUIDE
# ============================================================

with st.expander(
    "ℹ️ Barcode Format Guide"
):

    st.markdown(
        """
        | Format | Typical Use | Characters |
        |---|---|---|
        | **Code 128** | Shipping, inventory, logistics | Numbers + letters |
        | **Code 39** | Industrial / manufacturing | Numbers + uppercase letters |
        | **EAN-13** | Retail products | Numeric |
        | **EAN-8** | Small retail products | Numeric |
        | **UPC-A** | Retail products | Numeric |
        | **ITF-14** | Cartons / logistics | Numeric |

        ### Recommended format

        **Code 128** is generally the best option if you want
        to create your own internal product barcodes because it
        supports letters and numbers.

        For official retail products, use the appropriate EAN
        or UPC number assigned to the product.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        Pro Barcode Studio · Built with Streamlit ·
        High-quality barcode generation
    </div>
    """,
    unsafe_allow_html=True,
)