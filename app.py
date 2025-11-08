from pathlib import Path
import pandas as pd
import streamlit as st

from core.excel_loader import load_excel
from core.email_renderer import render_html, build_mime_message, DEFAULT_FORM_LINK
from core.utils import replace_placeholders, format_subject
from core.mail_sender import send_via_gmail_smtp, send_via_sendgrid
from ui.layout import header, sidebar

st.set_page_config(page_title="Mail-Merge Mailer", page_icon="📧", layout="wide")
header()

provider, from_name, from_email, secret = sidebar()

left, right = st.columns([0.55, 0.45], gap="large")

with left:
    st.subheader("1) Upload Excel")
    st.caption("Must include at least an 'Email' column. Add any other columns you want to use as placeholders (e.g., FullName, Institution, Group, etc.).")
    excel_file = st.file_uploader("Choose Excel (XLSX)", type=["xlsx"])
    df = None
    if excel_file:
        try:
            df = load_excel(excel_file)
            st.success(f"Loaded Excel with {len(df)} rows and {len(df.columns)} columns.")
            st.dataframe(df.head(12), use_container_width=True)
        except Exception as e:
            st.error(str(e))

    st.subheader("2) Subject & Greeting")
    st.caption("Use double curly placeholders like {{Full Name}} or {{Institution}}. Subject supports Python-style {FullName}.")
    subject_t = st.text_input("Subject pattern", value="Invitation to our event for {FullName}")
    greeting_t = st.text_input("Greeting (optional)", value="Dear {{Full Name}},")

    st.subheader("3) Per-Group Templates")
    st.caption("Pick a Group column (e.g., Group) and define a template per group value. If a row's group is missing, the fallback template will be used.")
    fallback_body = st.text_area("Fallback body (used if no group template matches)", height=160, value="We are delighted to invite you to our upcoming event at {{Institution}}.<br>Please confirm your attendance.")

    group_col = None
    group_templates = {}
    unique_groups = []
    if df is not None and len(df.columns) > 0:
        all_cols = list(df.columns)
        group_col = st.selectbox("Group column", options=["(none)"] + all_cols, index=(all_cols.index("Group")+1 if "Group" in all_cols else 0))
        if group_col != "(none)":
            # build dynamic text areas for unique group values
            unique_groups = sorted(set(str(x) for x in df[group_col].dropna().astype(str)))
            with st.expander(f"Define templates for {len(unique_groups)} group values", expanded=True):
                for g in unique_groups:
                    group_templates[g] = st.text_area(f"Template for group '{g}'", height=140,
                        value=f"Hello {{Full Name}},<br>You are in group '{g}'. We look forward to seeing you at {{Institution}}.")

    st.subheader("4) CTA Button")
    form_link = st.text_input("Form Link (CTA target)", value=DEFAULT_FORM_LINK)

with right:
    st.subheader("5) Banners")
    st.caption("Default banners are in ./assets. You may override by uploading here.")
    upper_upload = st.file_uploader("Upper banner (PNG/JPG)", type=["png","jpg","jpeg"], key="up_bnr")
    lower_upload = st.file_uploader("Lower banner (PNG/JPG)", type=["png","jpg","jpeg"], key="lo_bnr")

    workdir = Path(".")
    upper_path = workdir / "assets" / "upper_banner.png"
    lower_path = workdir / "assets" / "low_banner.png"
    if upper_upload:
        up_path = workdir / "_upper_uploaded.png"
        up_path.write_bytes(upper_upload.read())
        upper_path = up_path
    if lower_upload:
        lo_path = workdir / "_lower_uploaded.png"
        lo_path.write_bytes(lower_upload.read())
        lower_path = lo_path

    st.subheader("6) Preview")
    if df is not None and len(df) > 0:
        options = list(range(len(df)))
        label_col = "FullName" if "FullName" in df.columns else None
        def _fmt(i): return f"{i}: {df.iloc[i][label_col]}" if label_col else str(i)
        pick = st.selectbox("Pick a row to preview", options=options, format_func=_fmt)

        row = df.iloc[int(pick)].to_dict()
        subject = format_subject(subject_t, row)
        greeting = replace_placeholders(greeting_t, row)

        # choose body by group
        body_template = fallback_body
        if group_col and group_col != "(none)":
            gval = str(row.get(group_col, ""))
            if gval in group_templates:
                body_template = group_templates[gval]
        body = replace_placeholders(body_template, row)

        html = render_html(subject, greeting, body, form_link)

        st.write("**Subject →**", subject)
        st.markdown("---")
        st.markdown("**HTML preview (unsafe):**", help="Rendered below")
        st.components.v1.html(html, height=600, scrolling=True)

        # Build MIME for test download
        msg = build_mime_message(from_email, row.get("Email",""), subject, html, str(upper_path), str(lower_path), from_name=from_name)
        raw_bytes = msg.as_bytes()
        st.download_button("⬇️ Download EML (preview)", data=raw_bytes, file_name="preview.eml", mime="message/rfc822")

    st.subheader("7) Send")
    st.caption("We recommend testing first.")
    test_to = st.text_input("Test send to (single email)", value="")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Send TEST email", use_container_width=True, disabled=not (df is not None and secret and test_to)):
            try:
                row0 = df.iloc[0].to_dict()
                subject = format_subject(subject_t, row0)
                greeting = replace_placeholders(greeting_t, row0)
                bt = fallback_body
                if group_col and group_col != "(none)":
                    gval0 = str(row0.get(group_col, ""))
                    if gval0 in group_templates:
                        bt = group_templates[gval0]
                body = replace_placeholders(bt, row0)
                html = render_html(subject, greeting, body, form_link)
                msg = build_mime_message(from_email, test_to, subject, html, str(upper_path), str(lower_path), from_name=from_name)
                if "Gmail" in provider:
                    sent, failed = send_via_gmail_smtp(from_email, secret, [msg])
                else:
                    sent, failed = send_via_sendgrid(secret, [msg])
                if failed == 0:
                    st.success(f"Test sent successfully to {test_to}.")
                else:
                    st.warning(f"Test attempted: sent={sent}, failed={failed}. Check credentials/logs.")
            except Exception as e:
                st.error(f"Test send error: {e}")

    with col2:
        if st.button("🚀 Send ALL", use_container_width=True, disabled=not (df is not None and secret)):
            try:
                msgs = []
                for _, r in df.iterrows():
                    row = r.to_dict()
                    to_addr = str(row.get("Email","")).strip()
                    if not to_addr:
                        continue
                    subject = format_subject(subject_t, row)
                    greeting = replace_placeholders(greeting_t, row)
                    bt = fallback_body
                    if group_col and group_col != "(none)":
                        gval = str(row.get(group_col, ""))
                        if gval in group_templates:
                            bt = group_templates[gval]
                    body = replace_placeholders(bt, row)
                    html = render_html(subject, greeting, body, form_link)
                    msgs.append(build_mime_message(from_email, to_addr, subject, html, str(upper_path), str(lower_path), from_name=from_name))
                if "Gmail" in provider:
                    sent, failed = send_via_gmail_smtp(from_email, secret, msgs)
                else:
                    sent, failed = send_via_sendgrid(secret, msgs)
                st.success(f"Done. Sent: {sent}, Failed: {failed}.")
            except Exception as e:
                st.error(f"Bulk send error: {e}")
