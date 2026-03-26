import time
import uuid
import requests
import streamlit as st

# -------------------- Page config --------------------
st.set_page_config(
    page_title="Zscaler Cyber Support Assistant",
    page_icon="🛡️",
    layout="centered",
)

# -------------------- Cyber/Security Theme CSS --------------------
st.markdown(
    """
    <style>
      :root{
        --bg0:#050814;
        --bg1:#070B1C;
        --glass: rgba(255,255,255,.06);
        --glass2: rgba(255,255,255,.08);
        --stroke: rgba(255,255,255,.12);
        --stroke2: rgba(255,255,255,.18);
        --text: rgba(255,255,255,.92);
        --muted: rgba(255,255,255,.68);

        --cyan:#2CF9FF;
        --violet:#A78BFA;
        --green:#22C55E;
        --amber:#F59E0B;
        --red:#EF4444;
      }

      html, body, [class*="css"]  {
        background: radial-gradient(1200px 600px at 15% 10%, rgba(44,249,255,.12), transparent 50%),
                    radial-gradient(900px 500px at 80% 0%, rgba(167,139,250,.12), transparent 55%),
                    radial-gradient(900px 700px at 70% 90%, rgba(34,197,94,.08), transparent 60%),
                    linear-gradient(180deg, var(--bg0), var(--bg1));
        color: var(--text);
      }

      .block-container {
        padding-top: 2.0rem;
        padding-bottom: 2.2rem;
        max-width: 920px;
      }

      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* ====== Hero Header ====== */
      .hero {
        position: relative;
        border-radius: 22px;
        padding: 18px 18px 14px 18px;
        background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.04));
        border: 1px solid var(--stroke);
        box-shadow:
          0 18px 55px rgba(0,0,0,.55),
          0 0 0 1px rgba(44,249,255,.08) inset;
        overflow: hidden;
      }
      .hero:before {
        content:"";
        position:absolute;
        inset:-2px;
        background: radial-gradient(700px 200px at 12% 10%, rgba(44,249,255,.20), transparent 55%),
                    radial-gradient(700px 200px at 88% 0%, rgba(167,139,250,.18), transparent 55%);
        pointer-events: none;
      }
      .scanline {
        position:absolute;
        inset:-40% -10%;
        background: linear-gradient(120deg, transparent 35%, rgba(44,249,255,.06) 50%, transparent 65%);
        transform: rotate(8deg);
        animation: scan 6s linear infinite;
        pointer-events:none;
      }
      @keyframes scan {
        0% { transform: translateX(-25%) rotate(8deg); }
        100% { transform: translateX(25%) rotate(8deg); }
      }

      .title {
        font-size: 1.65rem;
        font-weight: 900;
        letter-spacing: -0.02em;
        margin: 0;
      }
      .subtitle {
        margin: .35rem 0 0 0;
        color: var(--muted);
        font-size: .98rem;
        line-height: 1.4;
      }
      .chips { margin-top: .8rem; display:flex; flex-wrap:wrap; gap:.5rem; }
      .chip {
        display:inline-flex; align-items:center; gap:.35rem;
        padding: .32rem .62rem;
        border-radius: 999px;
        border: 1px solid var(--stroke);
        background: rgba(255,255,255,.04);
        font-size: .86rem;
        color: rgba(255,255,255,.82);
      }
      .dot {
        width:8px; height:8px; border-radius:50%;
        background: var(--cyan);
        box-shadow: 0 0 14px rgba(44,249,255,.55);
      }
      .dot2 { background: var(--violet); box-shadow: 0 0 14px rgba(167,139,250,.50); }
      .dot3 { background: var(--green); box-shadow: 0 0 14px rgba(34,197,94,.45); }

      /* ====== Chat bubbles ====== */
      .bubble {
        padding: .9rem 1rem;
        border-radius: 18px;
        margin: .6rem 0;
        line-height: 1.45;
        border: 1px solid var(--stroke);
        background: rgba(255,255,255,.04);
        box-shadow: 0 12px 30px rgba(0,0,0,.35);
        position: relative;
        overflow: hidden;
      }
      .bubble.user {
        background: linear-gradient(180deg, rgba(167,139,250,.14), rgba(255,255,255,.03));
        border: 1px solid rgba(167,139,250,.25);
      }
      .bubble.bot {
        background: linear-gradient(180deg, rgba(44,249,255,.10), rgba(255,255,255,.03));
        border: 1px solid rgba(44,249,255,.20);
      }
      .role {
        font-size: .78rem;
        color: rgba(255,255,255,.70);
        margin-bottom: .35rem;
        display:flex;
        align-items:center;
        gap:.45rem;
      }
      .role-badge {
        display:inline-flex;
        align-items:center;
        gap:.35rem;
        padding: .12rem .5rem;
        border-radius: 999px;
        border: 1px solid var(--stroke2);
        background: rgba(0,0,0,.16);
      }
      .role-ico {
        width: 8px; height: 8px; border-radius:50%;
        background: var(--cyan);
        box-shadow: 0 0 12px rgba(44,249,255,.55);
      }
      .role-ico.user { background: var(--violet); box-shadow: 0 0 12px rgba(167,139,250,.55); }

      .cite {
        display:inline-block;
        padding: .05rem .38rem;
        border-radius: 10px;
        border: 1px solid rgba(44,249,255,.22);
        background: rgba(44,249,255,.08);
        font-size: .82rem;
        color: rgba(255,255,255,.90);
        margin: 0 .08rem;
      }

      /* ====== Sidebar polish ====== */
      section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
        border-right: 1px solid rgba(255,255,255,.08);
      }

      /* Buttons */
      .stButton button {
        border-radius: 14px !important;
        border: 1px solid rgba(44,249,255,.25) !important;
        background: rgba(44,249,255,.08) !important;
        color: var(--text) !important;
        box-shadow: 0 10px 26px rgba(0,0,0,.35) !important;
      }
      .stButton button:hover {
        border: 1px solid rgba(44,249,255,.35) !important;
        background: rgba(44,249,255,.12) !important;
      }

      /* Inputs */
      .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 14px !important;
        background: rgba(255,255,255,.04) !important;
        border: 1px solid rgba(255,255,255,.12) !important;
      }
      .stTextArea textarea {
        border-radius: 14px !important;
        background: rgba(255,255,255,.04) !important;
        border: 1px solid rgba(255,255,255,.12) !important;
      }

      .stCaption { color: rgba(255,255,255,.65) !important; }
      hr { border-color: rgba(255,255,255,.10) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("## 🧩 Control Panel")
    api_url = st.text_input("FastAPI URL", value="http://api:8000/chat")
    product = st.selectbox("Product focus", ["Auto", "ZPA", "ZIA"], index=0)

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    st.text_input("Session ID", value=st.session_state.session_id, disabled=True)

    st.markdown("---")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -------------------- Hero header --------------------
st.markdown(
    """
    <div class="hero">
      <div class="scanline"></div>
      <div class="title">🛡️ Zscaler Cyber Support Assistant</div>
      <div class="subtitle">
        Internal support copilot powered by your private docs (FAISS RAG) + LLM reasoning.
        Ask ZIA/ZPA troubleshooting and “how-to” questions.
      </div>
      <div class="chips">
        <span class="chip"><span class="dot"></span>RAG: FAISS</span>
        <span class="chip"><span class="dot dot2"></span>LLM Proxy</span>
        <span class="chip"><span class="dot dot3"></span>Tools: KB / Status / Web</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------- State --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # {"role":"user"/"assistant", "content": str}

def format_citations(text: str) -> str:
    out = text
    for i in range(1, 51):
        token = f"[S{i}]"
        if token in out:
            out = out.replace(token, f'<span class="cite">{token}</span>')
    return out.replace("\n", "<br>")

def render(role: str, content: str):
    bubble_class = "user" if role == "user" else "bot"
    role_dot = "user" if role == "user" else ""
    label = "Operator" if role == "user" else "Assistant"
    safe = content.replace("\n", "<br>") if role == "user" else format_citations(content)

    st.markdown(
        f"""
        <div class="bubble {bubble_class}">
          <div class="role">
            <span class="role-badge"><span class="role-ico {role_dot}"></span>{label}</span>
          </div>
          <div>{safe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------- Render chat history --------------------
for m in st.session_state.messages:
    render(m["role"], m["content"])

# -------------------- Input --------------------
prompt = st.chat_input("Type your question… (e.g., “ZPA connector unhealthy, what checks?”)")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    render("user", prompt)

    payload = {
        "message": prompt,
        "session_id": st.session_state.session_id,
        "product": None if product == "Auto" else product,
        "context": None,
    }

    typing = st.empty()
    typing.markdown(
        """
        <div class="bubble bot">
          <div class="role">
            <span class="role-badge"><span class="role-ico"></span>Assistant</span>
          </div>
          <div>Initializing analysis<span style="opacity:.65">…</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        t0 = time.time()
        r = requests.post(api_url, json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        answer = (data.get("answer") or "").strip() or "No answer returned."

        typing.empty()
        st.session_state.messages.append({"role": "assistant", "content": answer})
        render("assistant", answer)

        st.caption(f"⏱️ Latency: {time.time() - t0:.2f}s")

    except requests.exceptions.RequestException as e:
        typing.empty()
        err = (
            "⚠️ **Backend unreachable.**\n\n"
            f"**Details:** {e}\n\n"
            "Make sure FastAPI is running and the URL in the sidebar is correct."
        )
        st.session_state.messages.append({"role": "assistant", "content": err})
        render("assistant", err)

