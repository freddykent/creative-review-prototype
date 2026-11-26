"""Creative Review Queue: a test prototype with preset (simulated) AI scores.

No live AI model runs here. Brand C is a fictional sample brand.
"""
import csv
import io
import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"

# Preset first-level review: (criterion, score, confidence, reason, compared with)
REVIEW = [
    ("Brand alignment", 5, "High",
     "The logo, headline panel, date label and button use the approved Brand Kit colours.",
     "Brand Kit colours and approved reference"),
    ("Message clarity", 4, "High",
     "Headline, date, city and one action are present. The supporting sentence is long.",
     "Campaign brief"),
    ("Visual execution", 3, "Medium",
     "The supporting text is small and light against the sand background.",
     "Approved reference"),
    ("Audience relevance", 4, "Medium",
     "Spreadsheet, safety and work profile sessions suit first-time job seekers.",
     "Campaign brief"),
    ("Creative concept", 3, "Medium",
     "A plain announcement. No single visual idea links the day to getting work.",
     "Campaign brief"),
    ("Marketing effectiveness", 4, "Medium",
     "One clear action. The image shows no registration link or QR code.",
     "Campaign brief"),
]

st.set_page_config(page_title="Creative Review Queue", layout="wide")
st.markdown(
    """<style>
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none;}
    header[data-testid="stHeader"] {background:transparent;}
    .block-container {padding-top:2rem; max-width:1200px;}
    .score {font-size:1.7rem; font-weight:700; color:#12355B; line-height:1.2;}
    .was {font-size:.85rem; color:#6b6b6b;}
    .swatch {display:inline-block; width:92px; padding:22px 0 6px; margin:0 6px 6px 0;
             border-radius:8px; border:1px solid #d6d6d6; font-size:.75rem;
             text-align:center; font-weight:600;}
    </style>""",
    unsafe_allow_html=True,
)

ss = st.session_state
if "screen" not in ss:
    ss.screen = "queue"
    ss.session_id = secrets.token_hex(3).upper()
    ss.tester = str(st.query_params.get("tester", "unlabelled"))[:20]
    ss.scores = {row[0]: row[1] for row in REVIEW}
    ss.editing = None
    ss.events = []
    ss.opened_at = None
    ss.decision = None
    ss.loaded_at = time.time()


def log(event, criterion="", old="", new="", note=""):
    start = ss.opened_at or ss.loaded_at
    row = {
        "session": ss.session_id,
        "tester": ss.tester,
        "utc_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": round(time.time() - start, 1),
        "event": event,
        "criterion": criterion,
        "from_score": old,
        "to_score": new,
        "note": note,
    }
    ss.events.append(row)
    # Visible to the app owner only, in the Streamlit Cloud log panel.
    print("REVIEWLOG " + json.dumps(row), flush=True)


if not ss.events:
    log("queue_shown")


def open_creative():
    ss.opened_at = time.time()
    ss.screen = "review"
    log("creative_opened")


def start_edit(name):
    other = ss.editing
    if other and other != name:
        picked = ss.get(f"new_{other}")
        if picked is not None and picked != ss.scores[other]:
            log("change_discarded", other, ss.scores[other], picked, "opened another score")
    ss.editing = name
    log("change_started", name, ss.scores[name])


def save_edit(name):
    old, new = ss.scores[name], ss.get(f"new_{name}")
    note = ss.get(f"why_{name}", "").strip()
    if new is not None and new != old:
        ss.scores[name] = new
        log("score_changed", name, old, new, note)
    else:
        log("change_closed_no_edit", name, old, old, note)
    ss.editing = None


def cancel_edit(name):
    log("change_cancelled", name, ss.scores[name])
    ss.editing = None


def decide(choice):
    ss.decision = choice
    typed = ss.get("decision_note", "").strip()
    final = "; ".join(f"{k}={v}" for k, v in ss.scores.items())
    log("decision_" + choice, note=f"note: {typed or 'none'} | final scores: {final}")
    ss.screen = "done"


def queue_screen():
    st.title("Creative Review Queue")
    st.write("AI gives each creative a first-level score on six criteria. "
             "You make the final decision.")
    with st.container(border=True):
        left, mid, right = st.columns([1, 3, 1.2], vertical_alignment="center")
        left.image(str(ASSETS / "under_review.png"), width=150)
        mid.markdown("**Brand C: Free Digital Skills Day**")
        mid.write("Social post from the graphics team. Waiting for your review.")
        right.button("Open creative", type="primary", on_click=open_creative,
                     width="stretch")


def review_screen():
    st.subheader("Brand C: Free Digital Skills Day")
    a, b, c = st.columns([1.15, 1, 1], gap="large")
    with a:
        st.markdown("**Creative under review**")
        st.image(str(ASSETS / "under_review.png"), width="stretch")
    with b:
        st.markdown("**Approved reference**")
        st.image(str(ASSETS / "approved_reference.png"), width="stretch")
    with c:
        st.markdown("**Brand Kit**")
        chips = "".join(
            f'<span class="swatch" style="background:{bg};color:{fg}">{n}<br>{bg}</span>'
            for n, bg, fg in [("Navy", "#12355B", "#fff"), ("Teal", "#1B998B", "#fff"),
                              ("Sand", "#F4E9CD", "#222"), ("White", "#FFFFFF", "#222")])
        st.markdown(chips, unsafe_allow_html=True)
        st.write("Buttons and labels use Teal. Logo sits top left on Navy. "
                 "Tone is plain and encouraging.")
        st.markdown("**Campaign brief**")
        st.write("Audience: first-time job seekers aged 18 to 25 in Lagos.")
        st.write("Goal: registrations for a free skills day.")
        st.write("Format: square social post.")

    st.divider()
    st.subheader("AI first-level review")
    low = min(ss.scores.values())
    weakest = ", ".join(k for k, v in ss.scores.items() if v == low)
    mean = sum(ss.scores.values()) / len(ss.scores)
    m1, m2, m3 = st.columns([1, 2, 2])
    m1.markdown(f'Average<div class="score">{mean:.1f} / 5</div>', unsafe_allow_html=True)
    m2.markdown(f"Weakest  \n**{weakest}**")
    m3.markdown("Wrong information or serious brand violation  \n**None found by AI**")

    for name, ai_score, confidence, reason, source in REVIEW:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.6, 1, 4, 1.2], vertical_alignment="center")
            c1.markdown(f"**{name}**")
            c1.caption(f"Confidence: {confidence}")
            current = ss.scores[name]
            was = (f'<div class="was">Changed by you. AI gave {ai_score}.</div>'
                   if current != ai_score else "")
            c2.markdown(f'<div class="score">{current} / 5</div>{was}',
                        unsafe_allow_html=True)
            c3.write(reason)
            c3.caption(f"Compared with: {source}")
            c4.button("Change score", key=f"edit_{name}", on_click=start_edit,
                      args=(name,), width="stretch")
            if ss.editing == name:
                st.radio("Your score", [1, 2, 3, 4, 5], index=current - 1,
                         key=f"new_{name}", horizontal=True)
                st.text_input("Why? (optional)", key=f"why_{name}")
                s1, s2, _ = st.columns([1, 1, 4])
                s1.button("Save score", key=f"save_{name}", type="primary",
                          on_click=save_edit, args=(name,), width="stretch")
                s2.button("Cancel", key=f"cancel_{name}", on_click=cancel_edit,
                          args=(name,), width="stretch")

    st.divider()
    st.subheader("Your decision")
    st.text_area("Note to the graphics team (optional)", key="decision_note")
    d1, d2, _ = st.columns([1, 1.4, 3])
    # Both decisions carry the same visual weight, so neither one is nudged.
    busy = ss.editing is not None
    d1.button("Approve", on_click=decide, args=("approve",), width="stretch",
              disabled=busy)
    d2.button("Return to graphics team", on_click=decide, args=("return",),
              width="stretch", disabled=busy)
    if busy:
        st.caption("Save or cancel your open score change before you decide.")


def done_screen():
    label = "Approved" if ss.decision == "approve" else "Returned to graphics team"
    st.title("Decision recorded")
    st.success(label)
    changed = [(n, s, ss.scores[n]) for n, s, *_ in REVIEW if ss.scores[n] != s]
    if changed:
        for name, old, new in changed:
            st.write(f"{name}: AI gave {old}. You gave {new}.")
    else:
        st.write("You kept all six AI scores.")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(ss.events[0].keys()))
    writer.writeheader()
    writer.writerows(ss.events)
    st.download_button("Download session record", buf.getvalue(),
                       file_name=f"review_{ss.tester}_{ss.session_id}.csv",
                       mime="text/csv", on_click="ignore")
    st.write("Please hand back to the person running the session.")


{"queue": queue_screen, "review": review_screen, "done": done_screen}[ss.screen]()
st.caption(f"Test prototype. Sample brand. Session {ss.tester}-{ss.session_id}")
