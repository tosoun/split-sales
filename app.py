import base64
import datetime
import glob
import json
import os
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Πωλήσεις 2 Προϊόντων ανά Κατάστημα", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #2c3e50 !important; }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden; display: none;}
    [data-testid="stDecoration"] {visibility: hidden; display: none;}
    div[data-baseweb="select"] > div, .stRadio label p { color: white !important; }
    .block-container { padding: 0rem 0.5rem !important; max-width: 100% !important; }
    </style>

    <script>
    function removeManageButton() {
        const doc = window.parent.document;
        const buttons = doc.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText.includes('Manage app') || btn.innerHTML.includes('Manage')) {
                btn.style.display = 'none';
            }
        });
    }
    setInterval(removeManageButton, 500);
    </script>
    """,
    unsafe_allow_html=True,
)

excel_path_1 = "product1_sales.xlsx"
excel_path_2 = "product2_sales.xlsx"
time_path = "upload_time.txt"
date_path = "upload_date.txt"
confetti_path = "confetti_status.txt"
cheer_path = "cheer_status.txt"


def upload_to_github(file_path, repo_name, token, commit_message="Update sales file"):
    if not token or not repo_name:
        return False
    try:
        url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        r = requests.get(url, headers=headers)
        sha = None
        if r.status_code == 200:
            sha = r.json().get("sha")

        with open(file_path, "rb") as f:
            content_bytes = f.read()
        content_encoded = base64.b64encode(content_bytes).decode("utf-8")

        data = {"message": commit_message, "content": content_encoded}
        if sha:
            data["sha"] = sha

        put_r = requests.put(url, headers=headers, data=json.dumps(data))
        return put_r.status_code in [200, 201]
    except Exception:
        return False


confetti_enabled = True
if os.path.exists(confetti_path):
    try:
        with open(confetti_path, "r", encoding="utf-8") as cf:
            confetti_enabled = cf.read().strip() == "True"
    except Exception:
        pass

cheer_enabled = True
if os.path.exists(cheer_path):
    try:
        with open(cheer_path, "r", encoding="utf-8") as ch:
            cheer_enabled = ch.read().strip() == "True"
    except Exception:
        pass

with st.expander("⚙️ Διαχείριση Αρχείων (Admin)"):
    password = st.text_input("Εισάγετε κωδικό διαχειριστή:", type="password")
    if password == "2845":
        st.markdown("---")
        col_up1, col_up2 = st.columns(2)

        with col_up1:
            uploaded_file_1 = st.file_uploader(
                "Αρχείο για Προϊόν 1 (product1_sales.xlsx):",
                type=["xlsx"],
                key="up1",
            )

        with col_up2:
            uploaded_file_2 = st.file_uploader(
                "Αρχείο για Προϊόν 2 (product2_sales.xlsx):",
                type=["xlsx"],
                key="up2",
            )

        st.markdown("---")
        time_options = []
        for hour in range(8, 23):
            for minute in (0, 30):
                time_options.append(datetime.time(hour, minute))
        time_options.append(datetime.time(22, 0))
        time_options = sorted(list(set(time_options)))

        now = datetime.datetime.now() - datetime.timedelta(hours=1)
        default_minute = 0 if now.minute < 30 else 30
        default_hour = max(8, min(22, now.hour))
        default_time = datetime.time(default_hour, default_minute)

        if "selected_half_hour" not in st.session_state:
            st.session_state.selected_half_hour = default_time

        if "selected_report_date" not in st.session_state:
            st.session_state.selected_report_date = datetime.date.today()

        col_date, col_time, col_confetti, col_cheer = st.columns([1.2, 1.2, 1, 1])

        with col_date:
            selected_date = st.date_input(
                "Ημερομηνία αναφοράς:",
                value=st.session_state.selected_report_date,
            )
            st.session_state.selected_report_date = selected_date

        with col_time:
            selected_time = st.selectbox(
                "Ώρα αναφοράς:",
                options=time_options,
                index=(
                    time_options.index(st.session_state.selected_half_hour)
                    if st.session_state.selected_half_hour in time_options
                    else 0
                ),
                format_func=lambda x: x.strftime("%H:%M"),
            )
            st.session_state.selected_half_hour = selected_time

        with col_confetti:
            confetti_choice = st.radio(
                "Κομφετί:",
                ["ΝΑΙ", "ΟΧΙ"],
                index=0 if confetti_enabled else 1,
                horizontal=True,
                key="conf_radio"
            )

        with col_cheer:
            cheer_choice = st.radio(
                "Χειροκρότημα:",
                ["ΝΑΙ", "ΟΧΙ"],
                index=0 if cheer_enabled else 1,
                horizontal=True,
                key="cheer_radio"
            )

        if uploaded_file_1 is not None and uploaded_file_2 is not None:
            upload_signature = (
                f"{uploaded_file_1.name}_{uploaded_file_2.name}_"
                f"{uploaded_file_1.size}_{uploaded_file_2.size}"
            )

            if st.session_state.get("last_uploaded_sig") != upload_signature:
                try:
                    gh_token = st.secrets["GITHUB_TOKEN"]
                    repo_name = st.secrets["REPO_NAME"]
                except Exception:
                    gh_token, repo_name = None, None

                current_time_str = selected_time.strftime("%H:%M")
                current_date_str = selected_date.strftime("%d/%m/%Y")

                with open(time_path, "w", encoding="utf-8") as tf:
                    tf.write(current_time_str)

                with open(date_path, "w", encoding="utf-8") as df_file:
                    df_file.write(current_date_str)

                with open(confetti_path, "w", encoding="utf-8") as cf:
                    cf.write(str(confetti_choice == "ΝΑΙ"))

                with open(cheer_path, "w", encoding="utf-8") as ch:
                    ch.write(str(cheer_choice == "ΝΑΙ"))

                with open(excel_path_1, "wb") as f:
                    f.write(uploaded_file_1.getbuffer())
                if gh_token and repo_name:
                    upload_to_github(
                        excel_path_1,
                        repo_name,
                        gh_token,
                        "Auto-update product1_sales.xlsx",
                    )

                with open(excel_path_2, "wb") as f:
                    f.write(uploaded_file_2.getbuffer())
                if gh_token and repo_name:
                    upload_to_github(
                        excel_path_2,
                        repo_name,
                        gh_token,
                        "Auto-update product2_sales.xlsx",
                    )

                if gh_token and repo_name:
                    upload_to_github(
                        time_path, repo_name, gh_token, "Auto-update upload time"
                    )
                    upload_to_github(
                        date_path, repo_name, gh_token, "Auto-update upload date"
                    )
                    upload_to_github(
                        confetti_path, repo_name, gh_token, "Auto-update confetti status"
                    )
                    upload_to_github(
                        cheer_path, repo_name, gh_token, "Auto-update cheer status"
                    )

                st.session_state["last_uploaded_sig"] = upload_signature
                st.success("Και τα δύο αρχεία ανέβηκαν αυτόματα και συγχρονίστηκαν επιτυχώς!")

                components.html(
                    """
                    <script>
                        setTimeout(function() {
                            window.parent.location.reload();
                        }, 1500);
                    </script>
                    """,
                    height=0,
                )

    elif password:
        st.error("Λάθος κωδικός!")


def load_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, header=None)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def clean_quantity_value(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)

    s_val = str(val).strip()
    if "," in s_val and "." in s_val:
        s_val = s_val.replace(".", "").replace(",", ".")
    elif "," in s_val:
        s_val = s_val.replace(",", ".")

    try:
        return float(s_val)
    except Exception:
        return 0.0


def format_smart_num(num):
    if num == int(num):
        return f"{int(num):,}".replace(",", ".")
    else:
        parts = f"{num:.3f}".split(".")
        int_part = int(parts[0])
        dec_part = parts[1].rstrip("0")
        formatted_int = f"{int_part:,}".replace(",", ".")
        return f"{formatted_int},{dec_part}"


def process_sales_df(df):
    if df.empty:
        return "ΕΙΔΟΣ", pd.DataFrame(), 0.0, 1.0

    custom_title = "ΕΙΔΟΣ"
    for i in range(min(5, len(df))):
        for j in range(len(df.columns)):
            val = str(df.iloc[i, j]).strip()
            if (
                val
                and val.lower() != "nan"
                and "κατάστημα" not in val.lower()
                and "καταστημα" not in val.lower()
                and "πληρωτ" not in val.lower()
                and "ποσοτ" not in val.lower()
                and "αξια" not in val.lower()
                and "κοστος" not in val.lower()
            ):
                custom_title = val
                break
        if custom_title != "ΕΙΔΟΣ":
            break

    header_row_idx = 0
    for i in range(min(5, len(df))):
        row_str = str(df.iloc[i].values).lower()
        if "κατάστημα" in row_str or "καταστημα" in row_str:
            header_row_idx = i
            break

    df = df.iloc[header_row_idx + 1:].reset_index(drop=True)

    if len(df.columns) >= 3:
        df = df.iloc[:, [0, 2]]
    elif len(df.columns) >= 2:
        df = df.iloc[:, [0, 1]]
    else:
        df = df.iloc[:, [0, 0]]

    df.columns = ["Κατάστημα", "Ποσότητα"]
    df = df.dropna(subset=["Κατάστημα", "Ποσότητα"])
    df["Κατάστημα"] = df["Κατάστημα"].astype(str).str.strip()

    df = df[
        ~df["Κατάστημα"].str.contains(
            "Κατάστημα|ΠΟΣΟΤ|ΠΑΡΑΔΕΙΓΜΑ|NaN", case=False, na=False
        )
    ]

    df_clean = df[
        ~df["Κατάστημα"].str.contains("Total|Συνολο|ΣΥΝΟΛΟ", case=False, na=False)
    ].copy()

    df_clean["Num_Sales"] = df_clean["Ποσότητα"].apply(clean_quantity_value)
    df_stores = df_clean.sort_values(by="Num_Sales", ascending=False).reset_index(drop=True)

    total_sum = df_stores["Num_Sales"].sum()
    max_sales = df_stores["Num_Sales"].max() if not df_stores.empty else 1.0

    return custom_title, df_stores, total_sum, max_sales


file_time_str = "--:--"
if os.path.exists(time_path):
    try:
        with open(time_path, "r", encoding="utf-8") as tf:
            file_time_str = tf.read().strip()
    except Exception:
        pass

file_date_str = datetime.date.today().strftime("%d/%m/%Y")
if os.path.exists(date_path):
    try:
        with open(date_path, "r", encoding="utf-8") as df_file:
            file_date_str = df_file.read().strip()
    except Exception:
        pass

title_1, df_stores_1, total_sum_1, max_sales_1 = process_sales_df(load_data(excel_path_1))
title_2, df_stores_2, total_sum_2, max_sales_2 = process_sales_df(load_data(excel_path_2))

# =========================
# BANNER / GIF LOADER
# =========================
img_src = ""

preferred_banner_files = [
    "Τομέας3_σφυρί_τιμές_τρέχουν.gif",
    "banner.gif",
    "banner.png",
    "banner.jpg",
    "banner.jpeg",
]

banner_filename = None

for fname in preferred_banner_files:
    if os.path.exists(fname):
        banner_filename = fname
        break

if banner_filename is None:
    banner_files = (
        glob.glob("*banner*.gif")
        + glob.glob("*.gif")
        + glob.glob("ChatGPT Image*.png")
        + glob.glob("*banner*.jpg")
        + glob.glob("*banner*.jpeg")
        + glob.glob("*banner*.png")
    )
    if banner_files:
        banner_filename = banner_files[0]

if banner_filename:
    extension = os.path.splitext(banner_filename)[1].lower()
    mime_types = {
        ".gif": "image/gif",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    mime_type = mime_types.get(extension, "image/png")

    with open(banner_filename, "rb") as image_file:
        img_src = f"data:{mime_type};base64,{base64.b64encode(image_file.read()).decode()}"


try:
    banner_html = ""
    if img_src:
        banner_html = f"""
        <div class="banner-container">
            <img src="{img_src}" class="banner-img" alt="banner">
            <div class="rotate-hint-overlay">
                <span class="phone-icon-wrap">📱</span>
                <span class="turn-mobile-text">TURN MOBILE</span>
            </div>
        </div>
        """

    html_content = f"""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&display=swap" rel="stylesheet">

    <style>
    @keyframes blink-number-slow {{
        0% {{ opacity: 1; color: #2ecc71; text-shadow: 0 0 12px rgba(46, 204, 113, 0.7); }}
        50% {{ opacity: 0.25; color: #27ae60; text-shadow: none; }}
        100% {{ opacity: 1; color: #2ecc71; text-shadow: 0 0 12px rgba(46, 204, 113, 0.7); }}
    }}

    @keyframes rotate-phone-smooth {{
        0% {{ transform: rotate(0deg) scale(1); }}
        35% {{ transform: rotate(-90deg) scale(1.15); }}
        65% {{ transform: rotate(-90deg) scale(1.15); }}
        100% {{ transform: rotate(0deg) scale(1); }}
    }}

    body {{
        font-family: 'Montserrat', sans-serif;
        margin: 0;
        padding: 0;
        background: transparent;
        width: 100%;
        overflow-x: hidden;
    }}

    .main-container {{
        position: relative;
        background: rgba(0, 0, 0, 0.6);
        padding: 0;
        border-radius: 0;
        box-shadow: none;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        text-align: center;
        overflow: hidden;
    }}

    .banner-container {{
        position: relative;
        width: 100%;
    }}

    .banner-img {{
        width: 100%;
        height: auto;
        display: block;
        border-radius: 0;
        margin: 0;
        padding: 0;
    }}

    .rotate-hint-overlay {{
        position: absolute;
        bottom: 8px;
        right: 12px;
        display: flex;
        align-items: center;
        gap: 5px;
        background: transparent;
        padding: 0;
    }}

    .phone-icon-wrap {{
        display: inline-block;
        font-size: 20px;
        transform-origin: center;
        animation: rotate-phone-smooth 3.5s infinite ease-in-out;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.8));
    }}

    .turn-mobile-text {{
        font-size: 10px;
        color: #ffffff;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 0.5px;
        white-space: nowrap;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);
    }}

    @media (orientation: landscape) {{
        .rotate-hint-overlay {{
            display: none !important;
        }}
    }}

    .content-wrapper {{ padding: 25px; }}

    .header-area {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }}

    .top-left-area {{ text-align: left; }}
    .top-left-text {{
        color: #3498db;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }}
    .top-left-subtext {{
        color: #2ecc71;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 3px;
    }}
    .top-left-date {{
        color: #bdc3c7;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }}
    .top-left-time {{
        color: #95a5a6;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }}

    .columns-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
        width: 100%;
    }}

    .product-column {{ width: 100%; }}

    .sub-title {{
        color: #3498db;
        font-size: 18px;
        margin-bottom: 15px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
    }}

    .poll-item {{
        background: rgba(255, 255, 255, 0.08);
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 12px;
        text-align: left;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .poll-info {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        color: white;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 8px;
        gap: 10px;
    }}

    .poll-info span:first-child {{
        word-break: break-word;
        overflow-wrap: break-word;
        flex: 1;
    }}

    .poll-info span:last-child {{
        white-space: nowrap;
        text-align: right;
        flex-shrink: 0;
    }}

    .win-number-first {{
        color: #2ecc71;
        animation: blink-number-slow 2.5s infinite ease-in-out;
        font-weight: 700;
    }}

    .progress-bar-bg {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        height: 12px;
        width: 100%;
        overflow: hidden;
    }}

    .progress-fill {{
        background: #3498db;
        height: 100%;
        border-radius: 10px;
    }}

    .total-item {{
        background: rgba(52, 152, 219, 0.25);
        border: 1px solid #3498db;
    }}

    .watermark {{
        text-align: right;
        color: rgba(255, 255, 255, 0.2);
        font-size: 10px;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-right: 5px;
        text-transform: uppercase;
        user-select: none;
    }}
    </style>

    <div class="main-container">
        {banner_html}
        <div class="content-wrapper">
            <audio id="cheerAudio" preload="auto">
                <source src="https://www.myinstants.com/media/sounds/applause.mp3" type="audio/mpeg">
            </audio>

            <div class="header-area">
                <div class="top-left-area">
                    <div class="top-left-text">ΤΟΜΕΑΣ 3</div>
                    <div class="top-left-subtext">UPDATE SALES</div>
                    <div class="top-left-date">{file_date_str}</div>
                    <div class="top-left-time">εως: {file_time_str}</div>
                </div>
            </div>

            <div class="columns-container">
    """

    # --- ΣΤΗΛΗ 1 ---
    html_content += '<div class="product-column">'
    html_content += f'<div class="sub-title">{title_1}</div>'

    if not df_stores_1.empty:
        for index, row in df_stores_1.iterrows():
            katastima = str(row["Κατάστημα"])
            if katastima.lower() == "nan" or not katastima.strip():
                continue

            num = row["Num_Sales"]
            formatted_num = format_smart_num(num)
            bar_width = round((num / max_sales_1) * 100) if max_sales_1 > 0 else 0
            if bar_width > 100:
                bar_width = 100

            if index == 0:
                html_content += f"""
                    <div class="poll-item">
                        <div class="poll-info">
                            <span><b>{katastima}</b></span>
                            <span class="win-number-first">{formatted_num} τμχ/κιλ</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-fill" style="width: {bar_width}%;"></div>
                        </div>
                    </div>
                """
            else:
                html_content += f"""
                    <div class="poll-item">
                        <div class="poll-info">
                            <span><b>{katastima}</b></span>
                            <span><b>{formatted_num} τμχ/κιλ</b></span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-fill" style="width: {bar_width}%;"></div>
                        </div>
                    </div>
                """

        formatted_total_1 = format_smart_num(total_sum_1)
        html_content += f"""
            <div class="poll-item total-item">
                <div class="poll-info">
                    <span><b>TOTAL</b></span>
                    <span><b>{formatted_total_1} τμχ/κιλ</b></span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-fill" style="width: 100%;"></div>
                </div>
            </div>
        """
    else:
        html_content += '<div style="color: white; padding: 20px;">Δεν βρέθηκαν δεδομένα.</div>'

    html_content += "</div>"

    # --- ΣΤΗΛΗ 2 ---
    html_content += '<div class="product-column">'
    html_content += f'<div class="sub-title">{title_2}</div>'

    if not df_stores_2.empty:
        for index, row in df_stores_2.iterrows():
            katastima = str(row["Κατάστημα"])
            if katastima.lower() == "nan" or not katastima.strip():
                continue

            num = row["Num_Sales"]
            formatted_num = format_smart_num(num)
            bar_width = round((num / max_sales_2) * 100) if max_sales_2 > 0 else 0
            if bar_width > 100:
                bar_width = 100

            if index == 0:
                html_content += f"""
                    <div class="poll-item">
                        <div class="poll-info">
                            <span><b>{katastima}</b></span>
                            <span class="win-number-first">{formatted_num} τμχ/κιλ</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-fill" style="width: {bar_width}%;"></div>
                        </div>
                    </div>
                """
            else:
                html_content += f"""
                    <div class="poll-item">
                        <div class="poll-info">
                            <span><b>{katastima}</b></span>
                            <span><b>{formatted_num} τμχ/κιλ</b></span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-fill" style="width: {bar_width}%;"></div>
                        </div>
                    </div>
                """

        formatted_total_2 = format_smart_num(total_sum_2)
        html_content += f"""
            <div class="poll-item total-item">
                <div class="poll-info">
                    <span><b>TOTAL</b></span>
                    <span><b>{formatted_total_2} τμχ/κιλ</b></span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-fill" style="width: 100%;"></div>
                </div>
            </div>
        """
    else:
        html_content += '<div style="color: white; padding: 20px;">Δεν βρέθηκαν δεδομένα.</div>'

    html_content += "</div>"
    html_content += "</div>"

    if confetti_enabled:
        html_content += """
            <script>
                setTimeout(function() {
                    confetti({ particleCount: 90, spread: 90, origin: { x: 0.5, y: 0.25 } });
                    setTimeout(function() {
                        confetti({ particleCount: 110, spread: 110, origin: { x: 0.5, y: 0.25 } });
                    }, 3000);
                }, 300);
            </script>
        """

    if cheer_enabled:
        html_content += """
            <script>
                function playCheer() {
                    const audio = document.getElementById('cheerAudio');
                    if(audio) {
                        audio.volume = 0.5;
                        audio.play().then(() => {
                            window.removeEventListener('click', playCheer);
                            window.removeEventListener('touchstart', playCheer);
                        }).catch(function(error) {
                            console.log("Audio play blocked:", error.message);
                        });
                    }
                }

                window.addEventListener('DOMContentLoaded', function() {
                    playCheer();
                });

                window.addEventListener('click', playCheer, { once: true });
                window.addEventListener('touchstart', playCheer, { once: true });
            </script>
        """

    html_content += '<div class="watermark">tosoun 2026</div></div></div>'
    components.html(html_content, height=1400, scrolling=True)

except Exception as e:
    st.error(f"Σφάλμα: {e}")
