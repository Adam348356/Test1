import base64
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
import streamlit as st
from PIL import Image


# ============================================================
# FUNDGRUBE – Katharineum zu Lübeck
# ============================================================

APP_TITLE = "HalloDuHund"
MODEL_PATH = Path("keras_model.h5")
LABELS_PATH = Path("labels.txt")
FRONT_IMAGE = Path("assets/Frontseite.jpg")
UPLOAD_IMAGE = Path("assets/Seite2.jpg")
OLDEST_IMAGE = Path("assets/letzteSeite.jpg")

METADATA_PATH = "data/items.json"
IMAGE_DIR = "data/images"
IMAGE_SIZE = (224, 224)

# Die vier Klassen deines Teachable-Machine-Modells.
# Die Namen werden zusätzlich aus labels.txt gelesen.
KNOWN_CATEGORIES = {
    "Hosen": ["hose", "hosen", "jeans", "stoffhose"],
    "Sporthosen": [
        "sporthose",
        "sporthosen",
        "trainingshose",
        "jogginghose",
    ],
    "Hoodies": [
        "hoodie",
        "hoodies",
        "kapuzenpullover",
        "kapuzenpulli",
    ],
    "Polohemden": [
        "polo",
        "polohemd",
        "polohemden",
        "poloshirt",
    ],
}


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Fundgrube – Katharineum zu Lübeck",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --pink: #f28a91;
        --blue: #a6def4;
        --black: #080808;
        --grey: #666666;
        --light: #f7f7f7;
        --border: #111111;
    }

    html, body, [class*="css"] {
        font-family: Inter, Arial, sans-serif;
    }

    .stApp {
        background: #ffffff;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        display: none;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    /* Streamlit-Buttons */
    div.stButton > button {
        border: 2px solid var(--border);
        border-radius: 999px;
        background: white;
        color: var(--black);
        font-weight: 700;
        min-height: 48px;
        transition: 0.15s ease;
    }

    div.stButton > button:hover {
        background: var(--black);
        color: white;
        border-color: var(--black);
    }

    /* Popover-Button */
    div[data-testid="stPopover"] > button {
        border: 2px solid var(--black);
        border-radius: 999px;
        background: white;
        color: var(--black);
        font-size: 24px;
        font-weight: 800;
        width: 54px;
        height: 54px;
        padding: 0;
    }

    /* Textfelder */
    div[data-baseweb="input"] {
        border: 2px solid var(--black);
        border-radius: 999px;
        background: white;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: var(--black);
        box-shadow: none;
    }

    /* Datei-Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--black);
        border-radius: 24px;
        padding: 12px;
        background: #fafafa;
    }

    /* Karten */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 22px;
    }

    .page-heading {
        font-size: clamp(28px, 4vw, 48px);
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: -1.5px;
        margin: 0 0 10px 0;
    }

    .page-subheading {
        color: var(--grey);
        font-size: 16px;
        line-height: 1.5;
        margin-bottom: 25px;
    }

    .search-intro {
        text-align: center;
        max-width: 760px;
        margin: 35px auto 20px auto;
    }

    .search-intro h2 {
        font-size: clamp(24px, 3vw, 36px);
        margin-bottom: 8px;
        letter-spacing: -0.8px;
    }

    .search-intro p {
        color: var(--grey);
        margin: 0;
    }

    .category-pill {
        display: inline-block;
        border: 1.5px solid var(--black);
        border-radius: 999px;
        padding: 5px 11px;
        font-size: 13px;
        font-weight: 700;
        margin-top: 8px;
    }

    .confidence {
        color: var(--grey);
        font-size: 13px;
        margin-top: 4px;
    }

    .empty-state {
        text-align: center;
        padding: 45px 20px;
        border: 2px dashed #aaa;
        border-radius: 24px;
        color: var(--grey);
        background: #fafafa;
    }

    .notice {
        border: 2px solid var(--black);
        border-radius: 18px;
        padding: 15px 18px;
        margin: 20px 0;
        background: #fff;
    }

    .menu-caption {
        color: #666;
        font-size: 13px;
        margin-bottom: 8px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }

    .design-image {
        width:100%;
        margin:0 0 10px 0;
        line-height:0;
        overflow:hidden;
    }

    .design-image img {
        display:block;
        width:100%;
        height:auto;
        border:0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GITHUB
# ============================================================

def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


GITHUB_TOKEN = get_secret("GITHUB_TOKEN")
GITHUB_REPO = get_secret("GITHUB_REPO")
GITHUB_BRANCH = get_secret("GITHUB_BRANCH", "main")
GITHUB_API = "https://api.github.com"


def github_enabled():
    return bool(GITHUB_REPO)


def github_headers():
    headers = {
        "Accept": "application/vnd.github+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def github_read_file(path):
    if not github_enabled():
        return None

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}"

    try:
        response = requests.get(
            url,
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=20,
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()

    if data.get("encoding") == "base64":
        content = data.get("content", "")
        return base64.b64decode(content)

    return None


def github_write_file(path, content_bytes, commit_message):
    if not github_enabled():
        raise RuntimeError(
            "GITHUB_REPO wurde nicht eingerichtet."
        )

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN wurde nicht eingerichtet."
        )

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}"

    try:
        existing = requests.get(
            url,
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=20,
        )

        payload = {
            "message": commit_message,
            "content": base64.b64encode(
                content_bytes
            ).decode("ascii"),
            "branch": GITHUB_BRANCH,
        }

        if existing.status_code == 200:
            payload["sha"] = existing.json()["sha"]

        response = requests.put(
            url,
            headers=github_headers(),
            json=payload,
            timeout=30,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Verbindung zu GitHub fehlgeschlagen: {error}"
        ) from error

    if response.status_code not in (200, 201):
        raise RuntimeError(
            "GitHub-Fehler: "
            f"{response.status_code}\n"
            f"{response.text}"
        )

    return response.json()


# ============================================================
# KI-MODELL
# ============================================================

@st.cache_resource
def load_model():
    try:
        import tensorflow as tf
    except ImportError as error:
        raise RuntimeError(
            "TensorFlow ist nicht installiert."
        ) from error

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "keras_model.h5 wurde nicht gefunden."
        )

    return tf.keras.models.load_model(
        str(MODEL_PATH),
        compile=False,
    )


@st.cache_data
def load_labels():
    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            "labels.txt wurde nicht gefunden."
        )

    labels = []

    for line in LABELS_PATH.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line:
            continue

        # Teachable Machine schreibt häufig:
        # 0 Hosen
        # 1 Sporthosen
        # usw.
        match = re.match(
            r"^\s*\d+\s+(.+)$",
            line,
        )

        if match:
            labels.append(match.group(1).strip())
        else:
            labels.append(line)

    return labels


def classify_image(image):
    model = load_model()
    labels = load_labels()

    image = image.convert("RGB")
    image = image.resize(IMAGE_SIZE)

    image_array = np.asarray(
        image
    ).astype(np.float32)

    # Teachable-Machine-Normalisierung
    image_array = (image_array / 127.0) - 1.0
    image_array = np.expand_dims(
        image_array,
        axis=0,
    )

    prediction = model.predict(
        image_array,
        verbose=0,
    )[0]

    class_index = int(np.argmax(prediction))
    confidence = float(prediction[class_index])

    if class_index < len(labels):
        category = labels[class_index]
    else:
        category = f"Klasse {class_index}"

    return category, confidence


# ============================================================
# DATEN
# ============================================================

def read_items():
    if github_enabled():
        raw = github_read_file(METADATA_PATH)

        if raw:
            try:
                return json.loads(
                    raw.decode("utf-8")
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    local_file = Path(METADATA_PATH)

    if local_file.exists():
        try:
            return json.loads(
                local_file.read_text(
                    encoding="utf-8"
                )
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    return []


def write_items(items):
    content = json.dumps(
        items,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    if github_enabled():
        github_write_file(
            METADATA_PATH,
            content,
            "Fundgrube: Metadaten aktualisieren",
        )
        return

    local_file = Path(METADATA_PATH)
    local_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    local_file.write_bytes(content)


def image_url(path):
    if not github_enabled():
        return None

    return (
        "https://raw.githubusercontent.com/"
        f"{GITHUB_REPO}/"
        f"{GITHUB_BRANCH}/"
        f"{path}"
    )


def add_item(image_bytes, category, confidence):
    now = datetime.now(timezone.utc)

    timestamp = now.isoformat()

    filename = (
        now.strftime("%Y%m%d_%H%M%S_%f")
        + ".jpg"
    )

    image_path = f"{IMAGE_DIR}/{filename}"

    image = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=88,
        optimize=True,
    )

    jpeg_bytes = buffer.getvalue()

    if github_enabled():
        github_write_file(
            image_path,
            jpeg_bytes,
            f"Fundgrube: {category} hinzufügen",
        )
    else:
        local_path = Path(image_path)
        local_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        local_path.write_bytes(jpeg_bytes)

    items = read_items()

    items.append(
        {
            "id": filename,
            "timestamp": timestamp,
            "category": category,
            "confidence": round(
                confidence,
                4,
            ),
            "image_path": image_path,
        }
    )

    # Chronologisch speichern.
    items.sort(
        key=lambda item: item.get(
            "timestamp",
            "",
        )
    )

    write_items(items)


# ============================================================
# BILDER ANZEIGEN
# ============================================================

def show_item_image(item):
    path = item.get("image_path")

    if not path:
        st.info("Kein Foto vorhanden.")
        return

    url = image_url(path)

    if url:
        st.image(
            url,
            use_container_width=True,
        )
        return

    local_path = Path(path)

    if local_path.exists():
        st.image(
            str(local_path),
            use_container_width=True,
        )
    else:
        st.info("Foto konnte nicht geladen werden.")


# ============================================================
# DESIGN-BILDER / USER INTERFACE
# ============================================================

def asset_data_uri(path):
    """Lädt ein Designbild aus assets/ und macht es als HTML-Bild nutzbar."""
    if not path.exists():
        return None
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return None
    suffix = path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/jpeg")
    return f"data:{mime};base64,{encoded}"


def show_design(path):
    """Zeigt genau einen der drei vom Nutzer entworfenen Screens."""
    uri = asset_data_uri(path)
    if uri is None:
        st.error(
            f"Das Designbild wurde nicht gefunden: {path}. "
            "Bitte prüfe, ob die Datei im Ordner assets liegt."
        )
        return False
    st.markdown(
        f"""<div class="design-image"><img src="{uri}" alt="Fundgrube Design"></div>""",
        unsafe_allow_html=True,
    )
    return True


def menu_button():
    """Hamburger-Menü an der Stelle des Entwurfs oben links."""
    menu_col, spacer = st.columns([1, 11], gap="small")
    with menu_col:
        with st.popover("☰", use_container_width=True):
            st.markdown("### Fundgrube")
            st.caption("Katharineum zu Lübeck")
            if st.button("Suche", use_container_width=True, key="menu_search"):
                st.session_state.page = "Suche"
                st.rerun()
            if st.button("Fundstück einstellen", use_container_width=True, key="menu_upload"):
                st.session_state.page = "Fundstück einstellen"
                st.rerun()
            if st.button("Älteste Fundstücke", use_container_width=True, key="menu_oldest"):
                st.session_state.page = "Älteste Fundstücke"
                st.rerun()


# ============================================================
# NAVIGATION
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Suche"


# ============================================================
# SEITE 1 – FRONTSEITE / SUCHE
# ============================================================

if st.session_state.page == "Suche":
    show_design(FRONT_IMAGE)
    menu_button()

    query = st.text_input(
        "Suche nach einem verlorenen Gegenstand",
        placeholder="Beschreibe dein verlorenes Kleidungsstück",
        label_visibility="collapsed",
        key="search_query",
    )

    items = read_items()
    selected_category = None
    query_lower = query.lower()

    for category, words in KNOWN_CATEGORIES.items():
        if any(word in query_lower for word in words):
            selected_category = category
            break

    if selected_category is None and query:
        try:
            labels = load_labels()
            for label in labels:
                if label.lower() in query_lower:
                    selected_category = label
                    break
        except Exception:
            pass

    if query:
        if selected_category:
            results = [
                item for item in items
                if item.get("category") == selected_category
            ]
            results = sorted(
                results,
                key=lambda item: item.get("timestamp", ""),
                reverse=True,
            )
            st.markdown(f"### {len(results)} passende Fundstücke")
            if not results:
                st.markdown(
                    """<div class="empty-state">Für diese Kategorie wurden noch keine Fundstücke eingestellt.</div>""",
                    unsafe_allow_html=True,
                )
            columns = st.columns(3)
            for index, item in enumerate(results):
                with columns[index % 3]:
                    with st.container(border=True):
                        show_item_image(item)
                        st.markdown(f"**{item.get('category', 'Unbekannt')}**")
                        confidence = float(item.get("confidence", 0)) * 100
                        st.caption(f"KI-Sicherheit: {confidence:.1f}%")
        else:
            st.warning(
                "Ich konnte keine der vier Klassen erkennen. "
                "Versuche zum Beispiel: Hose, Sporthose, Hoodie oder Polohemd."
            )


# ============================================================
# SEITE 2 – SEITE2 / FOTO HOCHLADEN
# ============================================================

elif st.session_state.page == "Fundstück einstellen":
    show_design(UPLOAD_IMAGE)
    menu_button()

    uploaded_file = st.file_uploader(
        "Lade ein Foto aus deiner Mediathek hoch",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
        key="upload_image",
    )

    camera_file = st.camera_input(
        "Oder direkt ein Foto aufnehmen",
        key="camera_image",
    )

    selected_file = camera_file if camera_file is not None else uploaded_file

    if selected_file is None:
        st.markdown(
            """<div class="empty-state">Wähle ein Foto aus deiner Mediathek aus oder nimm direkt ein Foto auf.</div>""",
            unsafe_allow_html=True,
        )
    else:
        image_bytes = selected_file.getvalue()
        try:
            preview = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as error:
            st.error(f"Das Bild konnte nicht geöffnet werden: {error}")
            st.stop()

        image_col, result_col = st.columns([1.1, 0.9], gap="large")
        with image_col:
            st.image(preview, caption="Vorschau des Fundstücks", use_container_width=True)

        with result_col:
            with st.spinner("Die KI analysiert das Foto ..."):
                try:
                    category, confidence = classify_image(preview)
                except Exception as error:
                    st.error("Die KI konnte das Bild nicht analysieren.")
                    st.code(str(error))
                    st.stop()

            st.markdown("### KI-Ergebnis")
            st.markdown(
                f"""<div style="border:2px solid #111;border-radius:22px;padding:24px;background:#fafafa;">
                <div style="color:#666;font-size:13px;">Erkannte Klasse</div>
                <div style="font-size:30px;font-weight:800;">{category}</div>
                <div style="margin-top:10px;font-size:15px;color:#555;">Sicherheit: {confidence * 100:.1f}%</div>
                </div>""",
                unsafe_allow_html=True,
            )

            if st.button("Fundstück speichern", use_container_width=True, type="primary", key="save_item"):
                try:
                    add_item(image_bytes, category, confidence)
                    st.success("Fundstück wurde erfolgreich eingestellt.")
                    st.balloons()
                except Exception as error:
                    st.error("Das Fundstück konnte nicht gespeichert werden.")
                    st.code(str(error))


# ============================================================
# SEITE 3 – LETZTE SEITE / DIE 9 ÄLTESTEN
# ============================================================

else:
    show_design(OLDEST_IMAGE)
    menu_button()

    items = read_items()
    oldest_items = sorted(
        items,
        key=lambda item: item.get("timestamp", ""),
    )[:9]

    if not oldest_items:
        st.markdown(
            """<div class="empty-state">Es wurden noch keine Fundstücke eingestellt.</div>""",
            unsafe_allow_html=True,
        )
    else:
        columns = st.columns(3, gap="large")
        for index, item in enumerate(oldest_items):
            with columns[index % 3]:
                with st.container(border=True):
                    show_item_image(item)
                    st.markdown(f"**{item.get('category', 'Unbekannt')}**")
                    confidence = float(item.get("confidence", 0)) * 100
                    st.caption(f"KI-Sicherheit: {confidence:.1f}%")
                    timestamp = item.get("timestamp", "")
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        readable_time = dt.astimezone().strftime("%d.%m.%Y – %H:%M")
                    except Exception:
                        readable_time = timestamp
                    st.caption(f"Eingestellt: {readable_time}")


# ============================================================
# HINWEIS FÜR FEHLENDE GITHUB-EINSTELLUNG
# ============================================================

if not github_enabled():
    st.warning(
        "Hinweis: GITHUB_REPO ist noch nicht eingerichtet. "
        "Fundstücke werden dann nicht dauerhaft über GitHub gespeichert. "
        "Für die Online-Version müssen die GitHub-Secrets eingerichtet sein."
    )
