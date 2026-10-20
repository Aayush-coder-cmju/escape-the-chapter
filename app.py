from __future__ import annotations

import html
import json
import os
import random
import re
import time
import unicodedata
from urllib.parse import quote

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Escape the Chapter", page_icon="🗝️", layout="wide")


APP_TITLE = "Escape the Chapter"
MODEL_NAME = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PASSAGE_CHARS = 20_000
LEVELS = ["Easy", "Medium", "Hard"]
REWARDS = [100, 150, 200]
WORD_BANK = ["ADVENTURE", "TREASURE", "MYSTERY", "JOURNEY", "STARDUST", "ESCAPE"]

THEMES = [
    {"name": "Mosswild Jungle", "bg": "#071e22", "accent": "#58d68d", "second": "#20b8a6", "gold": "#f6c85f"},
    {"name": "Amber Ruins", "bg": "#24170f", "accent": "#f39c3d", "second": "#e65353", "gold": "#ffd166"},
    {"name": "Moonlit Reef", "bg": "#101b39", "accent": "#69b7ff", "second": "#9876ff", "gold": "#55e4d2"},
    {"name": "Solar Citadel", "bg": "#281424", "accent": "#ff718e", "second": "#f2b84b", "gold": "#ffe187"},
    {"name": "Crystal Tundra", "bg": "#10232c", "accent": "#80e0e9", "second": "#72a7ff", "gold": "#d3f6ff"},
    {"name": "Violet Nebula", "bg": "#1a1430", "accent": "#bc8cff", "second": "#f079ca", "gold": "#ffe085"},
]

SAMPLES = {
    "Biology — Photosynthesis": {
        "topic": "Photosynthesis",
        "subject": "Biology",
        "text": (
            "Photosynthesis is the process by which green plants make their own food. "
            "It takes place mainly in the leaves, inside tiny structures called chloroplasts. "
            "Chloroplasts contain chlorophyll, the green pigment that absorbs sunlight. "
            "Using the energy of sunlight, the plant combines carbon dioxide from the air with "
            "water absorbed by the roots to produce glucose and oxygen. The oxygen is released "
            "into the atmosphere through small pores called stomata. Glucose is used by the plant "
            "for energy and growth, and any extra is stored as starch."
        ),
        "variants": [
            [
                {"level": "Easy", "question": "Which green pigment absorbs sunlight?", "options": ["Chlorophyll", "Starch", "Glucose", "Stomata"], "answer": 0, "evidence": "Chloroplasts contain chlorophyll, the green pigment that absorbs sunlight.", "hints": ["Look for the green pigment inside chloroplasts.", "It begins with the letters chlo…"]},
                {"level": "Medium", "question": "Which two materials does a plant combine using sunlight?", "options": ["Carbon dioxide and water", "Oxygen and starch", "Glucose and chlorophyll", "Water and oxygen"], "answer": 0, "evidence": "Using the energy of sunlight, the plant combines carbon dioxide from the air with water absorbed by the roots to produce glucose and oxygen.", "hints": ["One comes from the air; the other is absorbed by roots.", "The pair is carbon dioxide plus …"]},
                {"level": "Hard", "question": "Why is sunlight important in the process described?", "options": ["It supplies energy for making glucose and oxygen", "It turns starch into chlorophyll", "It carries water from the roots", "It releases glucose through the stomata"], "answer": 0, "evidence": "Using the energy of sunlight, the plant combines carbon dioxide from the air with water absorbed by the roots to produce glucose and oxygen.", "hints": ["Find what the plant uses sunlight's energy to do.", "The passage says sunlight's energy helps produce glucose and oxygen."]},
            ],
            [
                {"level": "Easy", "question": "Where does photosynthesis take place mainly?", "options": ["In the leaves", "In the roots", "In the flowers", "In the soil"], "answer": 0, "evidence": "It takes place mainly in the leaves, inside tiny structures called chloroplasts.", "hints": ["The passage names a plant part first.", "It takes place mainly in the …"]},
                {"level": "Medium", "question": "What happens to oxygen made during photosynthesis?", "options": ["It is released through stomata", "It is stored as starch", "It is absorbed by roots", "It becomes chlorophyll"], "answer": 0, "evidence": "The oxygen is released into the atmosphere through small pores called stomata.", "hints": ["Look for the sentence about small pores.", "The pores are called stomata."]},
                {"level": "Hard", "question": "What can the plant do with extra glucose?", "options": ["Store it as starch", "Release it through stomata", "Use it to absorb sunlight", "Turn it into carbon dioxide"], "answer": 0, "evidence": "Glucose is used by the plant for energy and growth, and any extra is stored as starch.", "hints": ["Check the final sentence for what happens to any extra.", "Extra glucose is stored as …"]},
            ],
            [
                {"level": "Easy", "question": "What do green plants make through photosynthesis?", "options": ["Their own food", "Soil", "Sunlight", "Chloroplasts"], "answer": 0, "evidence": "Photosynthesis is the process by which green plants make their own food.", "hints": ["The answer is in the first sentence.", "Plants make their own …"]},
                {"level": "Medium", "question": "Which structure contains chlorophyll?", "options": ["Chloroplasts", "Stomata", "Roots", "Starch"], "answer": 0, "evidence": "Chloroplasts contain chlorophyll, the green pigment that absorbs sunlight.", "hints": ["Find the tiny structures mentioned in the leaves.", "The structure starts with chloro…"]},
                {"level": "Hard", "question": "How does glucose help the plant, according to the passage?", "options": ["It is used for energy and growth", "It absorbs sunlight through stomata", "It brings water to the leaves", "It releases oxygen from the roots"], "answer": 0, "evidence": "Glucose is used by the plant for energy and growth, and any extra is stored as starch.", "hints": ["Look at how the passage describes glucose.", "The passage names two uses: energy and …"]},
            ],
        ],
    },
    "History — The French Revolution": {
        "topic": "The French Revolution",
        "subject": "History",
        "text": (
            "The French Revolution began in 1789 when France faced a severe financial crisis and "
            "unequal taxation. Society was divided into three estates, and the Third Estate, which "
            "included peasants and workers, paid most of the taxes while having little political "
            "power. On 14 July 1789, a crowd stormed the Bastille, a fortress prison that symbolised "
            "royal tyranny. Later that year the National Assembly adopted the Declaration of the "
            "Rights of Man and of the Citizen, which proclaimed liberty and equality. In 1792 France "
            "became a republic, and King Louis XVI was executed in 1793."
        ),
        "variants": [
            [
                {"level": "Easy", "question": "In which year did the French Revolution begin?", "options": ["1789", "1792", "1793", "1776"], "answer": 0, "evidence": "The French Revolution began in 1789 when France faced a severe financial crisis and unequal taxation.", "hints": ["The opening sentence gives the year.", "It began in 17…"]},
                {"level": "Medium", "question": "Why was the Third Estate unhappy with the social system?", "options": ["It paid most taxes but had little political power", "It controlled the National Assembly", "It paid no taxes and held most power", "It was made up only of nobles"], "answer": 0, "evidence": "The Third Estate, which included peasants and workers, paid most of the taxes while having little political power.", "hints": ["Compare its tax burden with its political power.", "It paid most taxes but had little political …"]},
                {"level": "Hard", "question": "What did the Bastille represent to the crowd?", "options": ["Royal tyranny", "Liberty and equality", "The new republic", "The National Assembly"], "answer": 0, "evidence": "On 14 July 1789, a crowd stormed the Bastille, a fortress prison that symbolised royal tyranny.", "hints": ["The passage says the prison symbolised something about royal rule.", "It symbolised royal …"]},
            ],
            [
                {"level": "Easy", "question": "What did the Declaration proclaim?", "options": ["Liberty and equality", "Unequal taxation", "Royal tyranny", "A financial crisis"], "answer": 0, "evidence": "Later that year the National Assembly adopted the Declaration of the Rights of Man and of the Citizen, which proclaimed liberty and equality.", "hints": ["Look at the words describing the Declaration.", "It proclaimed liberty and …"]},
                {"level": "Medium", "question": "Which groups did the Third Estate include?", "options": ["Peasants and workers", "Only nobles", "The king and royal family", "The National Assembly"], "answer": 0, "evidence": "The Third Estate, which included peasants and workers, paid most of the taxes while having little political power.", "hints": ["The passage describes the people in that estate.", "It included peasants and …"]},
                {"level": "Hard", "question": "Which sequence matches the events described?", "options": ["Bastille stormed, Declaration adopted, France became a republic", "France became a republic, Bastille stormed, Declaration adopted", "Declaration adopted, King executed, Revolution began", "King executed, Revolution began, Bastille stormed"], "answer": 0, "evidence": "On 14 July 1789, a crowd stormed the Bastille, a fortress prison that symbolised royal tyranny. Later that year the National Assembly adopted the Declaration of the Rights of Man and of the Citizen, which proclaimed liberty and equality. In 1792 France became a republic, and King Louis XVI was executed in 1793.", "hints": ["Follow the dates: 1789, later that year, then 1792.", "The Bastille action came before the Declaration; the republic came in 1792."]},
            ],
            [
                {"level": "Easy", "question": "What happened in France in 1792?", "options": ["It became a republic", "The Revolution began", "The Bastille was built", "The Declaration was written"], "answer": 0, "evidence": "In 1792 France became a republic, and King Louis XVI was executed in 1793.", "hints": ["Find the sentence that mentions 1792.", "France became a …"]},
                {"level": "Medium", "question": "What financial problems did France face?", "options": ["A severe financial crisis and unequal taxation", "A shortage of workers", "A conflict with the National Assembly", "An excess of political power"], "answer": 0, "evidence": "The French Revolution began in 1789 when France faced a severe financial crisis and unequal taxation.", "hints": ["The first sentence names two pressures.", "One was a financial crisis; the other was unequal …"]},
                {"level": "Hard", "question": "Why could the storming of the Bastille be seen as a challenge to royal rule?", "options": ["The Bastille symbolised royal tyranny", "The Bastille proclaimed equality", "The Bastille was the National Assembly", "The Bastille created a republic"], "answer": 0, "evidence": "A crowd stormed the Bastille, a fortress prison that symbolised royal tyranny.", "hints": ["Connect the crowd's action with what the prison stood for.", "The passage says it symbolised royal …"]},
            ],
        ],
    },
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.findall(r"[\w]+", text, flags=re.UNICODE))


def new_word_puzzle() -> tuple[str, list[str], list[str], list[str]]:
    word = random.choice(WORD_BANK)
    quotient, remainder = divmod(len(word), 3)
    parts: list[str] = []
    start = 0
    for index in range(3):
        size = quotient + (1 if index < remainder else 0)
        parts.append(word[start : start + size])
        start += size
    display_parts = parts[:]
    random.shuffle(display_parts)
    award_parts = parts[:]
    random.shuffle(award_parts)
    return word, parts, display_parts, award_parts


def reset_game_state() -> None:
    word, parts, display_parts, award_parts = new_word_puzzle()
    saved_wallet = int(st.session_state.get("saved_points", 0))
    st.session_state.update(
        {
            "game_state": "setup",
            "escaped": False,
            "topic": "",
            "subject": "",
            "source_text": "",
            "source_image": None,
            "questions": [],
            "level": 0,
            "score": 60,
            "lives": 3,
            "round": 1,
            "round_hints": 0,
            "hints_current": 0,
            "hints_total": 0,
            "saved_points": saved_wallet,
            "saved_spent": 0,
            "bonus_earned": 0,
            "use_saved": False,
            "correct": 0,
            "wrong": 0,
            "attempts": 0,
            "wrong_indexes": [],
            "fragments": [],
            "word": word,
            "word_parts": parts,
            "word_display_parts": display_parts,
            "word_award_parts": award_parts,
            "theme_index": random.randrange(len(THEMES)),
            "sample_name": None,
            "sample_variant": 0,
            "timer_start": None,
            "elapsed_seconds": 0,
            "history": [],
            "message": "",
            "word_error": "",
            "current_question_started": None,
            "round_question_names": [],
        }
    )


if "game_state" not in st.session_state:
    reset_game_state()


def theme() -> dict[str, str]:
    return THEMES[st.session_state.theme_index]


def change_theme() -> None:
    previous = st.session_state.theme_index
    choices = [i for i in range(len(THEMES)) if i != previous]
    st.session_state.theme_index = random.choice(choices)


def apply_theme() -> None:
    colors = theme()
    st.markdown(
        f"""
        <style>
        :root {{ --quest-accent:{colors['accent']}; --quest-second:{colors['second']}; --quest-gold:{colors['gold']}; }}
        [data-testid="stAppViewContainer"] {{
            background: radial-gradient(ellipse at 8% 0%, {colors['accent']}28, transparent 34%),
                        radial-gradient(ellipse at 95% 15%, {colors['second']}25, transparent 35%),
                        linear-gradient(155deg, {colors['bg']}, #07111f 80%);
            color: #f4f7ff;
        }}
        [data-testid="stHeader"] {{ background:transparent; }}
        [data-testid="stSidebar"] {{ background:linear-gradient(180deg,{colors['bg']},#0b1424); }}
        .block-container {{ max-width:1180px; padding-top:1.3rem; padding-bottom:3rem; }}
        [data-testid="stMetric"] {{ background:#101d31cc; border:1px solid #ffffff20; border-radius:16px; padding:12px 15px; }}
        [data-testid="stMetricLabel"] {{ color:#c0cee2; }}
        [data-testid="stMetricValue"] {{ color:#fff; }}
        div[data-testid="stButton"] > button {{ border-radius:13px; min-height:2.7rem; font-weight:700; border:1px solid #ffffff28; background:#132541; color:#f4f7ff; }}
        div[data-testid="stButton"] > button:hover {{ border-color:var(--quest-accent); color:#fff; box-shadow:0 0 0 2px color-mix(in srgb,var(--quest-accent) 28%,transparent); }}
        div[data-testid="stButton"] > button[kind="primary"] {{ background:linear-gradient(110deg,var(--quest-accent),var(--quest-second)); color:#07111f; border:0; }}
        div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {{ background:#091629; color:#f4f7ff; border-color:#ffffff2b; border-radius:13px; }}
        .sw-brand {{ color:var(--quest-gold); font-size:.78rem; letter-spacing:.19em; font-weight:900; }}
        .sw-hero {{ border:1px solid #ffffff21; border-radius:23px; padding:25px 27px; margin:7px 0 15px; background:linear-gradient(120deg,#101d31e8,#101b2be0); box-shadow:0 18px 55px #0005; }}
        .sw-kicker {{ color:var(--quest-accent); font-size:.78rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }}
        .sw-title {{ color:#fff; font-size:clamp(2rem,5vw,3.5rem); font-weight:950; letter-spacing:-.055em; line-height:1.02; margin:.45rem 0 .7rem; }}
        .sw-subtitle {{ color:#c7d5e8; font-size:1.05rem; max-width:800px; }}
        .sw-panel {{ border:1px solid #ffffff20; border-radius:20px; padding:20px; background:#101d31dc; box-shadow:0 16px 42px #0004; margin:12px 0; }}
        .sw-map {{ display:flex; justify-content:space-between; gap:4px; border:1px solid #ffffff20; border-radius:18px; padding:14px 10px; background:#0b1728d9; margin:12px 0 15px; }}
        .sw-stop {{ flex:1; text-align:center; color:#91a7c2; font-size:.72rem; line-height:1.25; }}
        .sw-stop b {{ display:block; color:#eef4ff; font-size:.78rem; margin-top:4px; }}
        .sw-stop .dot {{ margin:auto; width:37px; height:37px; border-radius:50%; display:grid; place-items:center; border:2px solid #51637d; background:#14233a; font-size:1rem; }}
        .sw-stop.done .dot {{ border-color:#c7f5a7; background:#70ad47; color:#10200e; }}
        .sw-stop.current .dot {{ border-color:#fff; color:#07111f; background:var(--quest-accent); box-shadow:0 0 22px var(--quest-accent); }}
        .sw-fragment {{ display:inline-grid; place-items:center; min-width:58px; margin:5px; padding:11px 13px; border-radius:12px; border:1px dashed var(--quest-accent); color:#fff; background:#ffffff0d; font:900 1.2rem ui-monospace,monospace; letter-spacing:.12em; }}
        .sw-watermark {{ text-align:center; color:var(--quest-gold); font-size:.75rem; font-weight:950; letter-spacing:.22em; opacity:.85; margin-top:22px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    colors = theme()
    st.markdown(
        f"""<div class="sw-brand">SMARTWORLD PRESENTS · {html.escape(colors['name'].upper())}</div>
        <div class="sw-title">🗝️ Escape the Chapter</div>
        <div class="sw-subtitle">Turn a textbook passage into an adventure. Find the answers, collect the fragments, and unlock the final word.</div>""",
        unsafe_allow_html=True,
    )


def timer_display() -> None:
    started = st.session_state.timer_start
    if started:
        seconds = st.session_state.elapsed_seconds
        if st.session_state.game_state not in {"report", "setup"}:
            seconds = max(0, int(time.time() - started))
    else:
        seconds = 0
    minutes, secs = divmod(seconds, 60)
    st.caption(f"⏱️ Adventure time · {minutes:02d}:{secs:02d}")


def render_timer_fragment() -> None:
    is_running = st.session_state.game_state in {"play", "cleared", "word_gate", "restarting", "restart_error"}

    @st.fragment(run_every=1 if is_running else None)
    def live_timer() -> None:
        timer_display()

    live_timer()


def map_position() -> int:
    state = st.session_state.game_state
    if state == "setup":
        return 0
    if state == "play":
        return st.session_state.level + 1
    if state == "cleared":
        return st.session_state.level + 1
    if state == "word_gate":
        return 4
    if state == "report":
        return 5 if st.session_state.escaped else 4
    if state in {"restarting", "restart_error"}:
        return 0
    return 0


def render_map() -> None:
    labels = [("🏁", "Start"), ("🌱", "Easy"), ("🧭", "Medium"), ("🔥", "Hard"), ("🔐", "Word Gate"), ("🚪", "Exit")]
    pos = map_position()
    done_through = st.session_state.level if st.session_state.game_state in {"cleared", "word_gate", "report"} else st.session_state.level - 1
    stops = []
    for index, (emoji, label) in enumerate(labels):
        css = "sw-stop"
        if index < pos or (index in (1, 2, 3) and index - 1 <= done_through):
            css += " done"
        if index == pos:
            css += " current"
        stops.append(f'<div class="{css}"><div class="dot">{emoji}</div><b>{label}</b></div>')
    st.markdown('<div class="sw-map">' + "".join(stops) + "</div>", unsafe_allow_html=True)
    st.progress(min(1.0, pos / 5), text=f"Escape route · {labels[pos][1]}")


def display_stats() -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("⭐ Score", f"{st.session_state.score} pts")
    c2.metric("❤️ Lives", f"{st.session_state.lives}/3")
    c3.metric("✨ Saved bonus", f"{st.session_state.saved_points} pts")
    c4.metric("💡 Hints", str(st.session_state.hints_total))
    c5.metric("🎲 Round", str(st.session_state.round))


def escape_parts(word: str) -> tuple[list[str], list[str]]:
    quotient, remainder = divmod(len(word), 3)
    pieces: list[str] = []
    offset = 0
    for part_index in range(3):
        width = quotient + (1 if part_index < remainder else 0)
        pieces.append(word[offset : offset + width])
        offset += width
    display = pieces[:]
    random.shuffle(display)
    return pieces, display


def shuffle_answers(question: dict) -> dict:
    order = list(range(4))
    random.shuffle(order)
    shuffled = dict(question)
    shuffled["options"] = [question["options"][i] for i in order]
    shuffled["answer"] = order.index(question["answer"])
    return shuffled


def validate_quiz(data: object, expected_source: str | None = None) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Gemma did not return a quiz object. Try again.")
    source = data.get("source_text")
    questions = data.get("questions")
    if not isinstance(source, str) or not source.strip() or not isinstance(questions, list):
        raise ValueError("The quiz response is missing its passage or question list.")
    if expected_source:
        if norm(source) != norm(expected_source):
            raise ValueError("The generated quiz changed your passage. It was rejected; try again.")
        source = expected_source.strip()
    if len(questions) != 3:
        raise ValueError("The quiz must contain exactly three questions.")
    if len(source.split()) < 20:
        raise ValueError("The passage needs at least 20 readable words for three distinct questions.")

    clean_questions = []
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            raise ValueError("One quiz question was malformed. Try again.")
        options = question.get("options")
        answer = question.get("answer")
        hints = question.get("hints")
        evidence = question.get("evidence")
        if question.get("level") != LEVELS[index]:
            raise ValueError("Questions must be in Easy, Medium, Hard order. Try again.")
        if not isinstance(question.get("question"), str) or not question["question"].strip():
            raise ValueError("A question was empty. Try again.")
        if not isinstance(options, list) or len(options) != 4 or not all(isinstance(x, str) and x.strip() for x in options):
            raise ValueError("Each question needs four answer choices.")
        if len({norm(option) for option in options}) != 4:
            raise ValueError("A question contains repeated answer choices. Try again.")
        if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < 4:
            raise ValueError("A correct answer was missing. Try again.")
        if not isinstance(hints, list) or len(hints) != 2 or not all(isinstance(h, str) and h.strip() for h in hints):
            raise ValueError("Each question needs two text-based hints.")
        if not isinstance(evidence, str) or not evidence.strip() or norm(evidence) not in norm(source):
            raise ValueError("An answer quote did not match the passage. The quiz was rejected.")
        clean_questions.append(
            {
                "level": LEVELS[index],
                "question": question["question"].strip(),
                "options": options,
                "answer": answer,
                "hints": hints,
                "evidence": evidence.strip(),
            }
        )
    return {"source_text": source, "questions": clean_questions}


def parse_quiz_json(response_text: str) -> dict:
    text = (response_text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Gemma's reply was not JSON. Please try again.")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("Gemma returned unreadable quiz data. Please try again.") from exc


def quiz_prompt(passage: str, earlier_questions: list[str], is_image: bool) -> str:
    source_instruction = (
        "Read the attached textbook page and transcribe only its readable educational text into source_text. "
        "Create questions only from that transcription. Do not use external facts."
        if is_image
        else "Copy source_text exactly from the supplied passage. Do not add, remove, or change facts."
    )
    payload = {
        "source_text": passage,
        "earlier_questions_to_avoid": earlier_questions,
    }
    return f"""
You create school-friendly escape-room quizzes. Follow the supplied passage only; do not use outside facts.
{source_instruction}
Return ONLY one JSON object with this exact shape:
{{"source_text":"...","questions":[{{"level":"Easy","question":"...","options":["...","...","...","..."],"answer":0,"evidence":"an exact continuous quote from source_text","hints":["gentle hint","stronger hint that still does not reveal the answer"]}}]}}
There must be exactly three questions, in this order: Easy direct recall; Medium explanation or connection; Hard reasoning that is fully supported by the passage. Each has exactly four different options, with answer as the zero-based correct option index. Both hints and the correct option must be answerable from the passage. Every evidence value must be copied exactly as a continuous quote from source_text. Avoid asking anything listed in earlier_questions_to_avoid. Make the passage and every question understandable to a school student.
Input data:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def gemma_client() -> genai.Client:
    api_key = ""
    try:
        api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        api_key = ""
    api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "The server key is not configured yet. Add GEMINI_API_KEY to .streamlit/secrets.toml, then restart the app."
        )
    return genai.Client(api_key=api_key)


def generate_quiz(
    passage: str,
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
    earlier_questions: list[str] | None = None,
) -> dict:
    client = gemma_client()
    prompt = quiz_prompt(passage, earlier_questions or [], bool(image_bytes))
    contents: list[object] = []
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime or "image/jpeg"))
    contents.append(prompt)
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=3500),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemma could not build the quiz. Check the server key, network, and model access. Details: {exc}") from exc
    return validate_quiz(parse_quiz_json(response.text or ""), expected_source=passage if passage.strip() and not image_bytes else None)


def read_upload(uploaded_file) -> tuple[str, bytes | None, str | None]:
    if uploaded_file is None:
        return "", None, None
    file_bytes = uploaded_file.getvalue()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("That file is larger than 10 MB. Choose a smaller file or paste the text.")
    suffix = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
    if suffix in {"txt", "md", "csv"}:
        try:
            return file_bytes.decode("utf-8-sig").strip()[:MAX_PASSAGE_CHARS], None, None
        except UnicodeDecodeError as exc:
            raise ValueError("This text file is not UTF-8. Save it as UTF-8 or paste the passage.") from exc
    if suffix == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(uploaded_file)
            extracted = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as exc:
            raise ValueError(f"I couldn't read this PDF. Try a text PDF or upload a clear page photo. Details: {exc}") from exc
        if len(extracted.split()) < 20:
            raise ValueError("This PDF has little selectable text. Upload a clear photo of the page instead.")
        return extracted[:MAX_PASSAGE_CHARS], None, None
    if suffix in {"png", "jpg", "jpeg", "webp"}:
        mime = uploaded_file.type or "image/jpeg"
        return "", file_bytes, mime
    raise ValueError("Upload a .txt, .md, .csv, .pdf, .png, .jpg, .jpeg, or .webp file.")


def load_sample(name: str) -> None:
    sample = SAMPLES[name]
    st.session_state.sample_name = name
    st.session_state.sample_variant = random.randrange(len(sample["variants"]))
    st.session_state.topic_input = sample["topic"]
    st.session_state.subject_input = sample["subject"]
    st.session_state.passage_input = sample["text"]
    st.session_state.uploaded_book = None


def clear_sample() -> None:
    st.session_state.sample_name = None
    st.session_state.topic_input = ""
    st.session_state.subject_input = ""
    st.session_state.passage_input = ""
    st.session_state.uploaded_book = None


def choose_new_word() -> None:
    word, pieces, display_pieces, award_pieces = new_word_puzzle()
    st.session_state.word = word
    st.session_state.word_parts = pieces
    st.session_state.word_display_parts = display_pieces
    st.session_state.word_award_parts = award_pieces
    st.session_state.fragments = []


def begin_round(quiz: dict, topic: str, subject: str, keep_timer: bool = False) -> None:
    st.session_state.questions = [shuffle_answers(q) for q in quiz["questions"]]
    st.session_state.source_text = quiz["source_text"]
    st.session_state.topic = topic or "Textbook chapter"
    st.session_state.subject = subject or "Your subject"
    st.session_state.level = 0
    st.session_state.lives = 3
    st.session_state.round_hints = 0
    st.session_state.hints_current = 0
    st.session_state.wrong_indexes = []
    st.session_state.round_question_names = [q["question"] for q in quiz["questions"]]
    st.session_state.current_question_started = time.time()
    st.session_state.message = ""
    st.session_state.word_error = ""
    st.session_state.game_state = "play"
    st.session_state.escaped = False
    choose_new_word()
    change_theme()
    if not keep_timer or not st.session_state.timer_start:
        st.session_state.timer_start = time.time()
        st.session_state.elapsed_seconds = 0


def start_adventure(passage_input: str, topic: str, subject: str, uploaded_file) -> None:
    try:
        file_text, image_bytes, image_mime = read_upload(uploaded_file)
        passage = passage_input.strip()
        if file_text:
            passage = f"{passage}\n\n{file_text}".strip() if passage else file_text
        if not passage and not image_bytes:
            raise ValueError("Paste a passage, upload a textbook page, or choose one of the samples.")
        if passage and len(passage.split()) < 20:
            raise ValueError("Add at least 20 words so Gemma can make three distinct questions.")
        if len(passage) > MAX_PASSAGE_CHARS:
            passage = passage[:MAX_PASSAGE_CHARS]

        selected_sample = st.session_state.sample_name
        if selected_sample and norm(passage) == norm(SAMPLES[selected_sample]["text"]) and not image_bytes:
            sample = SAMPLES[selected_sample]
            source_questions = sample["variants"][st.session_state.sample_variant]
            quiz = validate_quiz({"source_text": sample["text"], "questions": source_questions}, expected_source=sample["text"])
            begin_round(quiz, topic or sample["topic"], subject or sample["subject"])
            return

        with st.spinner("Gemma is reading your chapter and making three passage-based questions…"):
            quiz = generate_quiz(passage, image_bytes, image_mime)
        st.session_state.sample_name = None
        begin_round(quiz, topic or "Your chapter", subject or "Your subject")
    except Exception as exc:
        st.session_state.game_state = "setup"
        st.error(str(exc))


def answer_question(option_index: int) -> None:
    if st.session_state.game_state != "play":
        return
    question = st.session_state.questions[st.session_state.level]
    st.session_state.attempts += 1
    if option_index == question["answer"]:
        level = st.session_state.level
        reward = REWARDS[level]
        st.session_state.score += reward
        st.session_state.correct += 1
        elapsed = max(1, int(time.time() - (st.session_state.current_question_started or time.time())))
        fragment = st.session_state.word_award_parts[level]
        st.session_state.fragments.append(fragment)
        st.session_state.history.append(
            {
                "Round": st.session_state.round,
                "Level": LEVELS[level],
                "Result": "Cleared",
                "Points": reward,
                "Time (s)": elapsed,
                "Hints": st.session_state.hints_current,
                "Wrong tries": len(st.session_state.wrong_indexes),
            }
        )
        st.session_state.message = f"Clue fragment collected: {fragment} · +{reward} points"
        st.session_state.game_state = "cleared"
        change_theme()
        if level == 2 and st.session_state.round_hints == 0:
            st.session_state.saved_points += 20
            st.session_state.bonus_earned += 1
            st.session_state.message += " · Perfect hint-free round: +20 saved bonus points"
        return

    st.session_state.wrong += 1
    st.session_state.lives -= 1
    st.session_state.wrong_indexes.append(option_index)
    if st.session_state.lives <= 0:
        elapsed = max(1, int(time.time() - (st.session_state.current_question_started or time.time())))
        st.session_state.history.append(
            {
                "Round": st.session_state.round,
                "Level": LEVELS[st.session_state.level],
                "Result": "Fresh round after all lives were used",
                "Points": 0,
                "Time (s)": elapsed,
                "Hints": st.session_state.hints_current,
                "Wrong tries": len(st.session_state.wrong_indexes),
            }
        )
        st.session_state.round += 1
        st.session_state.game_state = "restarting"
        st.session_state.message = "All three lives are used. The chapter is opening a fresh round."
        change_theme()
    else:
        st.session_state.message = "That choice isn't supported by the passage. One life used — read the clue and try again."


def use_hint() -> None:
    if st.session_state.hints_current >= 2:
        return
    if st.session_state.use_saved and st.session_state.saved_points >= 20:
        st.session_state.saved_points -= 20
        st.session_state.saved_spent += 20
    elif st.session_state.score >= 20:
        st.session_state.score -= 20
    else:
        st.session_state.message = "You need 20 points to reveal a hint."
        return
    st.session_state.hints_current += 1
    st.session_state.round_hints += 1
    st.session_state.hints_total += 1
    st.session_state.message = ""


def advance_after_clear() -> None:
    if st.session_state.level < 2:
        st.session_state.level += 1
        st.session_state.hints_current = 0
        st.session_state.wrong_indexes = []
        st.session_state.current_question_started = time.time()
        st.session_state.game_state = "play"
    else:
        st.session_state.game_state = "word_gate"
        st.session_state.word_error = ""
    st.session_state.message = ""


def restart_with_fresh_questions() -> None:
    st.info("New round · same topic · fresh questions. Your score and timer carry on.")
    try:
        selected_sample = st.session_state.sample_name
        if selected_sample and selected_sample in SAMPLES:
            sample = SAMPLES[selected_sample]
            variant_count = len(sample["variants"])
            st.session_state.sample_variant = (st.session_state.sample_variant + 1) % variant_count
            quiz = validate_quiz(
                {"source_text": sample["text"], "questions": sample["variants"][st.session_state.sample_variant]},
                expected_source=sample["text"],
            )
        else:
            with st.spinner("Gemma is preparing three new questions from the same passage…"):
                quiz = generate_quiz(
                    st.session_state.source_text,
                    earlier_questions=st.session_state.round_question_names,
                )
        st.session_state.round_question_names = [q["question"] for q in quiz["questions"]]
        begin_round(quiz, st.session_state.topic, st.session_state.subject, keep_timer=True)
        st.session_state.message = f"Round {st.session_state.round}: fresh {st.session_state.subject} questions."
    except Exception as exc:
        st.session_state.game_state = "restart_error"
        st.error(f"I couldn't create the fresh round: {exc}")


def render_setup() -> None:
    st.markdown(
        '<div class="sw-panel"><div class="sw-kicker">Choose your chapter</div><h2>Pick a sample or bring your own text</h2><p>Gemma will make one Easy, one Medium, and one Hard question using only the passage. Students never see or enter the API key.</p></div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    for col, sample_name, emoji in (
        (left, "Biology — Photosynthesis", "🌿"),
        (right, "History — The French Revolution", "🏛️"),
    ):
        sample = SAMPLES[sample_name]
        with col:
            st.markdown(
                f'<div class="sw-panel"><div class="sw-kicker">{emoji} {html.escape(sample["subject"])}</div><h3>{html.escape(sample["topic"])}</h3><p>{html.escape(sample["text"][:190])}…</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Try {sample['subject']} sample", key=f"sample-{sample_name}", use_container_width=True):
                load_sample(sample_name)
                start_adventure(sample["text"], sample["topic"], sample["subject"], None)
                st.rerun()

    st.markdown("### Or build an escape from your chapter")
    st.text_input("Topic or chapter title", key="topic_input", placeholder="e.g. Water cycle")
    st.text_input("Subject (optional)", key="subject_input", placeholder="e.g. Science")
    st.text_area(
        "Paste a textbook passage",
        key="passage_input",
        height=165,
        placeholder="Paste at least 20 words here. Questions and answer evidence will be checked against this text.",
    )
    st.file_uploader(
        "Or upload a page or text file",
        type=["png", "jpg", "jpeg", "webp", "pdf", "txt", "md", "csv"],
        key="uploaded_book",
        help="Images are read by Gemma. Text PDFs and text files are extracted on the server. Maximum file size: 10 MB.",
    )
    st.checkbox("Use saved bonus points before regular points for hints", key="use_saved")
    if st.button("🚪 Start the adventure", type="primary", use_container_width=True):
        start_adventure(
            st.session_state.passage_input,
            st.session_state.topic_input,
            st.session_state.subject_input,
            st.session_state.uploaded_book,
        )
        if st.session_state.game_state == "play":
            st.rerun()
    if st.session_state.game_state == "setup" and not st.session_state.source_text:
        st.caption("Starting score: 60 · Hint: −20 · 3 lives · Correct answers award clue fragments")


def render_play() -> None:
    level = st.session_state.level
    question = st.session_state.questions[level]
    colors = theme()
    st.markdown(
        f'<div class="sw-panel"><div class="sw-kicker">{html.escape(colors["name"])} · {html.escape(st.session_state.subject)} · Round {st.session_state.round}</div><h2>{LEVELS[level]} room · {REWARDS[level]} points</h2><p style="font-size:1.35rem;font-weight:800">{html.escape(question["question"])}</p></div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    for index, option in enumerate(question["options"]):
        column = left if index % 2 == 0 else right
        with column:
            disabled = index in st.session_state.wrong_indexes
            if st.button(
                f"{'ABCD'[index]} · {option}",
                key=f"answer-{st.session_state.round}-{level}-{st.session_state.attempts}-{index}",
                disabled=disabled,
                use_container_width=True,
            ):
                answer_question(index)
                st.rerun()
    if st.session_state.message:
        st.warning(st.session_state.message)
    if st.session_state.hints_current:
        for hint_index in range(st.session_state.hints_current):
            st.info(f"Hint {hint_index + 1} · −20 points: {question['hints'][hint_index]}")
    hint_col, saved_col, end_col = st.columns([1.2, 1.6, 1])
    with hint_col:
        if st.button(
            "💡 Reveal a hint · −20",
            key=f"hint-{st.session_state.round}-{level}-{st.session_state.hints_current}",
            disabled=st.session_state.hints_current >= 2 or (st.session_state.score < 20 and not (st.session_state.use_saved and st.session_state.saved_points >= 20)),
            use_container_width=True,
        ):
            use_hint()
            st.rerun()
    with saved_col:
        st.caption("Saved bonus is spent first when its checkbox is on." if st.session_state.use_saved else "Use the setup checkbox to spend saved bonus first.")
    with end_col:
        if st.button("End and report", key="end-from-play"):
            st.session_state.elapsed_seconds = int(time.time() - st.session_state.timer_start)
            st.session_state.game_state = "report"
            st.rerun()


def render_cleared() -> None:
    level = st.session_state.level
    question = st.session_state.questions[level]
    st.markdown('<div class="sw-panel"><div class="sw-kicker">Room unlocked</div><h2>🗝️ Clue fragment secured!</h2></div>', unsafe_allow_html=True)
    st.success(st.session_state.message)
    st.markdown(f"**From your passage:** “{question['evidence']}”")
    for fragment in st.session_state.fragments:
        st.markdown(f'<span class="sw-fragment">{html.escape(fragment)}</span>', unsafe_allow_html=True)
    button_text = "Go to the final word gate" if level == 2 else f"Enter the {LEVELS[level + 1]} room"
    if st.button(f"➡️ {button_text}", type="primary", use_container_width=True):
        advance_after_clear()
        st.rerun()


def render_word_gate() -> None:
    st.markdown(
        '<div class="sw-panel"><div class="sw-kicker">Final lock · all three fragments collected</div><h2>🧩 Assemble the escape word</h2><p>Rearrange the three clue fragments into the secret word. Type the completed word, then press Enter.</p></div>',
        unsafe_allow_html=True,
    )
    tiles = "".join(f'<span class="sw-fragment">{html.escape(part)}</span>' for part in st.session_state.word_display_parts)
    st.markdown(f'<div style="text-align:center;margin:12px 0 20px">{tiles}</div>', unsafe_allow_html=True)
    with st.form("word-gate-form", clear_on_submit=False):
        guess = st.text_input("Your assembled word", placeholder="Type the letters in the correct order")
        submitted = st.form_submit_button("🔓 Enter the word", type="primary", use_container_width=True)
    if submitted:
        if norm(guess).replace(" ", "") == st.session_state.word.casefold():
            st.session_state.escaped = True
            st.session_state.elapsed_seconds = int(time.time() - st.session_state.timer_start)
            st.session_state.game_state = "report"
            change_theme()
            st.rerun()
        else:
            st.session_state.word_error = "That word doesn't fit the fragments yet. Rearrange them and try again."
            st.rerun()
    if st.session_state.word_error:
        st.warning(st.session_state.word_error)
    st.caption("You can try as many combinations as you need. The word check does not use a life or points.")


def improvement_tips() -> list[str]:
    tips = []
    attempts = st.session_state.attempts
    accuracy = round(st.session_state.correct / attempts * 100) if attempts else 0
    if accuracy < 75:
        tips.append("Pause before answering and find the sentence that supports your choice.")
    if st.session_state.hints_total:
        tips.append("Read the whole passage once before using a hint; save hints for details that remain unclear.")
    if st.session_state.wrong:
        tips.append("Read all four choices and rule out answers the passage does not support.")
    if st.session_state.escaped and st.session_state.hints_total == 0 and st.session_state.wrong == 0:
        tips.append("Excellent recall. Try a longer passage or a new subject next time.")
    if not tips:
        tips.append("Keep practising with a fresh passage to build recall across subjects.")
    return tips[:4]


def make_report_text() -> str:
    elapsed = st.session_state.elapsed_seconds
    minutes, seconds = divmod(elapsed, 60)
    accuracy = round(st.session_state.correct / st.session_state.attempts * 100) if st.session_state.attempts else 0
    result = "Escaped the chapter" if st.session_state.escaped else "Adventure ended early"
    lines = [
        "🗝️ ESCAPE THE CHAPTER · SMARTWORLD",
        f"Topic: {st.session_state.topic} ({st.session_state.subject})",
        f"Result: {result}",
        f"Score: {st.session_state.score} · Saved bonus: {st.session_state.saved_points} · Rounds: {st.session_state.round}",
        f"Accuracy: {accuracy}% · Correct answers: {st.session_state.correct} · Wrong answers: {st.session_state.wrong}",
        f"Time: {minutes:02d}:{seconds:02d} · Hints: {st.session_state.hints_total} · Lives: {st.session_state.lives}/3",
        f"Clue fragments: {' · '.join(st.session_state.fragments) or 'None'}",
        "Question record:",
    ]
    for row in st.session_state.history[-25:]:
        lines.append(f"Round {row['Round']} · {row['Level']} · {row['Result']} · {row['Points']} pts · {row['Hints']} hints · {row['Wrong tries']} wrong")
    lines += ["Try next:"] + [f"• {tip}" for tip in improvement_tips()]
    lines.append("SMARTWORLD · ESCAPE THE CHAPTER")
    return "\n".join(lines)


def render_report() -> None:
    st.markdown('<div class="sw-panel"><div class="sw-kicker">SMARTWORLD · Adventure recap</div><h2>📊 Final report</h2></div>', unsafe_allow_html=True)
    if st.session_state.escaped:
        st.balloons()
        st.success("The fragments formed the secret word. You escaped the chapter!")
    else:
        st.info("Here is the report for this adventure so far.")
    accuracy = round(st.session_state.correct / st.session_state.attempts * 100) if st.session_state.attempts else 0
    minutes, seconds = divmod(st.session_state.elapsed_seconds, 60)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score", f"{st.session_state.score} pts")
    c2.metric("Accuracy", f"{accuracy}%")
    c3.metric("Time", f"{minutes:02d}:{seconds:02d}")
    c4.metric("Rounds", str(st.session_state.round))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Correct", str(st.session_state.correct))
    c2.metric("Wrong", str(st.session_state.wrong))
    c3.metric("Hints", str(st.session_state.hints_total))
    c4.metric("Lives left", f"{st.session_state.lives}/3")
    c1, c2, c3 = st.columns(3)
    c1.metric("Saved bonus", f"{st.session_state.saved_points} pts")
    c2.metric("Bonus earned", str(st.session_state.bonus_earned))
    c3.metric("Bonus spent", f"{st.session_state.saved_spent} pts")
    st.subheader("Question record")
    if st.session_state.history:
        st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
    else:
        st.caption("No questions were answered in this adventure.")
    st.subheader("What to practise next")
    for tip in improvement_tips():
        st.markdown(f"- {tip}")
    report = make_report_text()
    encoded = quote(report, safe="")
    subject = quote("Escape the Chapter report · SmartWorld", safe="")
    wa_url = f"https://wa.me/?text={encoded}"
    mail_url = f"mailto:?subject={subject}&body={encoded}"
    left, right = st.columns(2)
    left.link_button("💬 Share with WhatsApp", wa_url, use_container_width=True)
    right.link_button("✉️ Share by email", mail_url, use_container_width=True)
    with st.expander("View copy-ready report"):
        st.code(report, language=None)
    st.markdown('<div class="sw-watermark">SMARTWORLD · ESCAPE THE CHAPTER</div>', unsafe_allow_html=True)
    if st.button("🔁 Start a new adventure", type="primary", use_container_width=True):
        reset_game_state()
        for key in ("passage_input", "topic_input", "subject_input", "uploaded_book"):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def render_restarting() -> None:
    st.markdown('<div class="sw-panel"><div class="sw-kicker">The chapter shifts</div><h2>🔄 Three fresh rooms are opening…</h2></div>', unsafe_allow_html=True)
    restart_with_fresh_questions()
    if st.session_state.game_state == "play":
        st.rerun()
    elif st.session_state.game_state == "restart_error":
        if st.button("Try making fresh questions again", type="primary", key="retry-round-inline"):
            st.session_state.game_state = "restarting"
            st.rerun()
        if st.button("End and report", key="end-after-restart-error"):
            st.session_state.elapsed_seconds = int(time.time() - st.session_state.timer_start)
            st.session_state.game_state = "report"
            st.rerun()


def main() -> None:
    apply_theme()
    render_header()
    render_timer_fragment()
    if st.session_state.game_state != "setup":
        display_stats()
    render_map()
    state = st.session_state.game_state
    if state == "setup":
        render_setup()
    elif state == "play":
        render_play()
    elif state == "cleared":
        render_cleared()
    elif state == "word_gate":
        render_word_gate()
    elif state == "restarting":
        render_restarting()
    elif state == "restart_error":
        st.error("The fresh round could not be made. Your current adventure is still here.")
        if st.button("Try making fresh questions again", type="primary"):
            st.session_state.game_state = "restarting"
            st.rerun()
        if st.button("End and report"):
            st.session_state.elapsed_seconds = int(time.time() - st.session_state.timer_start)
            st.session_state.game_state = "report"
            st.rerun()
    elif state == "report":
        render_report()
    st.markdown('<div class="sw-watermark">SMARTWORLD · ESCAPE THE CHAPTER</div>', unsafe_allow_html=True)


main()
