"""Recall design system: warm editorial surfaces, deep ink, and confident green accents."""
import streamlit as st

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--canvas:#f5f6f2;--paper:#fff;--ink:#17231e;--muted:#728078;--line:#e4e9e4;--green:#176b50;--green-soft:#e8f3ed;--mint:#b9e2cd;--amber:#b87823;--red:#b84942;--radius:18px;--shadow:0 14px 40px rgba(30,52,41,.055)}
html,body,[data-testid="stAppViewContainer"],.stApp{background:var(--canvas)!important;color:var(--ink)!important;font-family:'DM Sans',sans-serif!important;-webkit-font-smoothing:antialiased}
#MainMenu,footer,[data-testid="stHeader"]{visibility:hidden}
.block-container{max-width:1120px;padding:2rem 2rem 4rem!important}
.brand{display:flex;align-items:center;gap:.65rem;font:800 1.08rem 'Manrope',sans-serif;letter-spacing:-.04em;color:var(--ink);margin:0 0 2.2rem}
.mark{width:28px;height:28px;border-radius:9px;background:var(--green);display:inline-flex;position:relative;box-shadow:0 5px 12px #176b5030}
.mark:after{content:'R';color:white;font:800 15px 'Manrope',sans-serif;position:absolute;inset:3px 0 0;text-align:center}
.eyebrow{font-size:.72rem!important;text-transform:uppercase;letter-spacing:.12em;color:var(--green)!important;font-weight:700;margin:0 0 .55rem!important}
.display{font:800 clamp(2.2rem,4.7vw,3.65rem)/1.08 'Manrope',sans-serif!important;letter-spacing:-.065em!important;color:var(--ink)!important;max-width:850px;margin:.1rem 0 .8rem!important}
.lede{font-size:1.03rem;line-height:1.65;color:var(--muted);max-width:700px;margin:0 0 1.6rem}
.label{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:1.05rem 0 .45rem}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:1.25rem!important}
[data-testid="stFileUploader"]{background:#f8faf8;border:1px dashed #b9c9bf;border-radius:14px;padding:.8rem}
[data-testid="stFileUploader"], [data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] [data-baseweb="select"]>div,[data-testid="stSegmentedControl"] button{border-radius:12px!important}
[data-testid="stTextArea"] textarea{background:#fff!important;border:1px solid var(--line)!important;color:var(--ink)!important;padding:.9rem!important}
[data-testid="stTextArea"] textarea:focus{border-color:var(--green)!important;box-shadow:0 0 0 3px #176b5015!important}
[data-testid="stSelectbox"] [data-baseweb="select"]>div{background:#fff!important;border-color:var(--line)!important}
[data-testid="stSegmentedControl"]{background:#f0f3ef!important;padding:4px;border-radius:12px!important}
[data-testid="stSegmentedControl"] button{border-radius:9px!important;color:var(--muted)!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"],[data-testid="stSegmentedControl"] button[aria-checked="true"]{background:#fff!important;color:var(--green)!important;box-shadow:0 2px 7px #17231e12!important}
.stApp [data-testid="stWidgetLabel"],.stApp [data-testid="stWidgetLabel"] p{color:#536259!important;font-size:.82rem!important;font-weight:600!important}
.stButton>button,[data-testid^="stBaseButton"], [data-testid="stDownloadButton"] button{border-radius:11px!important;font-family:'DM Sans',sans-serif!important;font-weight:700!important;min-height:2.75rem;transition:all .18s ease!important}
[data-testid="stBaseButton-primary"]{background:var(--green)!important;color:white!important;border:1px solid var(--green)!important;box-shadow:0 7px 15px #176b5024!important}
[data-testid="stBaseButton-primary"]:hover{background:#10583f!important;transform:translateY(-1px)}
[data-testid="stBaseButton-secondary"],[data-testid="stDownloadButton"] button{background:#fff!important;color:var(--ink)!important;border:1px solid var(--line)!important}
[data-testid="stBaseButton-secondary"]:hover{border-color:#9cb8a7!important;background:#f8fbf8!important}
[data-testid="stSlider"] [role="slider"]{background:var(--green)!important}
.stCaption,.stMarkdown p{line-height:1.6}
.qtext{font:700 clamp(1.15rem,2vw,1.55rem)/1.45 'Manrope',sans-serif!important;letter-spacing:-.025em!important;color:var(--ink)!important;margin:0 0 .8rem!important}
.q-card{background:var(--paper)!important;border:1px solid var(--line)!important;border-radius:var(--radius)!important;padding:1.5rem 1.7rem!important;box-shadow:var(--shadow)!important;margin:.5rem 0 1.25rem!important}
.seg{display:flex;gap:5px;margin:1rem 0 .8rem}.seg span{flex:1;height:5px;border-radius:9px;background:#e1e8e2}.seg span.on{background:var(--green)}.seg span.cur{background:#91c9a9}
[data-testid="stRadio"],[data-testid="stRadio"]>div,[data-testid="stRadio"] [role="radiogroup"]{width:100%!important;display:flex!important;flex-direction:column!important;gap:.65rem!important}
[data-testid="stRadio"] [role="radiogroup"]>label,[data-testid="stRadio"] label[data-baseweb="radio"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:12px!important;padding:.85rem 1rem!important;margin:0!important;transition:.18s ease!important}
[data-testid="stRadio"] [role="radiogroup"]>label:hover{border-color:#9cb8a7!important;background:#f8fbf8!important}
[data-testid="stRadio"] label:has(input:checked){background:var(--green-soft)!important;border-color:#75ad8d!important}
[data-testid="stRadio"] label p,[data-testid="stRadio"] label span{color:var(--ink)!important;font-size:.92rem!important}
[data-testid="stRadio"] input{accent-color:var(--green)!important}
.fb{border-radius:13px;padding:1rem 1.1rem;margin-top:1rem;font-size:.92rem;line-height:1.6}.fb.ok{background:#eaf5ed;color:#21653e;border:1px solid #c9e4d0}.fb.bad{background:#fff0ee;color:#a43e38;border:1px solid #f0d0cc}
.metrics-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px;margin:1.4rem 0}.metric-card{background:#fff;border:1px solid var(--line);border-radius:15px;padding:1.1rem;text-align:left;box-shadow:var(--shadow)}.metric-value{font:800 1.7rem 'Manrope',sans-serif;color:var(--green)}.metric-label{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-top:.35rem}
.score{font:800 clamp(3.2rem,9vw,5rem)/1 'Manrope',sans-serif;letter-spacing:-.07em;color:var(--green);margin:1.25rem 0 .3rem}.score small{font-size:.42em;color:#94a199;font-weight:600}.meta{color:var(--muted);font-size:.95rem;margin:.5rem 0 1rem}.meta b{color:var(--ink)}
.strip{display:flex;flex-wrap:wrap;gap:7px;margin:1.3rem 0}.strip i{width:20px;height:20px;border-radius:7px;background:#dfe6e0}.strip i.right{background:#43a56c}.strip i.wrong{background:#d36a5f}.strip i.open{background:#82b59a}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.3rem 1.4rem;margin:1rem 0;box-shadow:var(--shadow)}.card p{line-height:1.65}.card .k,.k{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;font-weight:700}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;padding:.3rem .65rem;border-radius:99px;margin-bottom:.6rem}.chip.right{background:#eaf5ed;color:#287244}.chip.wrong{background:#fff0ee;color:#a43e38}.chip.open{background:#edf4ef;color:var(--green)}.chip.skipped{background:#f1f3f1;color:#66736a}
.exam-timer{display:inline-flex;gap:.6rem;background:#fff;border:1px solid var(--line);padding:.55rem 1rem;border-radius:99px;font-weight:700;margin:0 0 1rem}.timer-label{color:var(--muted);font-size:.7rem}.exam-timer.urgent{color:var(--red);border-color:#e6aaa4}.q-grid{display:flex;flex-wrap:wrap;gap:7px;margin:1rem 0}.grid-cell{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;font-size:.8rem;background:#fff;border:1px solid var(--line);color:var(--muted)}.grid-cell.answered{background:var(--green-soft);color:var(--green);border-color:#c5dfcf}.grid-cell.current{background:var(--green);color:#fff;border-color:var(--green)}.grid-cell.flagged{outline:2px solid #e9b259}
.source-quote,.grade-details{background:#f6f8f6;border-left:3px solid #79ad8d;padding:.7rem .9rem;margin-top:.8rem;border-radius:0 10px 10px 0;font-size:.86rem;color:#536259}.grade-hit{color:#287244}.grade-miss{color:#a43e38}.confirm-modal{background:#fff8eb;border:1px solid #efdbb8;border-radius:14px;padding:1.25rem;margin:1rem 0}.confirm-modal h3{margin:0 0 .3rem}.confirm-modal p{margin:0;color:var(--muted)}
.stApp pre{background:#f6f8f6!important;border:1px solid var(--line)!important;border-radius:12px!important}.stAlert{border-radius:12px!important}
@media(max-width:700px){.block-container{padding:1.1rem 1rem 3rem!important}.brand{margin-bottom:1.5rem}.display{font-size:2.3rem!important}.q-card{padding:1.15rem!important}}
</style>"""

_P = {
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "pen": '<path d="M12 20h9"/><path d="M16.4 3.6a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "minus": '<path d="M5 12h14"/>',
}


def icon(name: str, size: int = 12) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_P[name]}</svg>')


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
