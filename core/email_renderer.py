from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path

DEFAULT_FORM_LINK = "https://example.com/form"

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:16px;background:#f6f7fb;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #eef2ff;">
    <img src="cid:upper_banner" style="display:block;width:100%;height:auto;" alt="header">
    <div style="padding:24px;">
      {greeting_block}
      {body_block}
      <div style="text-align:center;margin-top:24px;">
        <a href="{form_link}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:700;display:inline-block;">
          Fill the Form
        </a>
      </div>
    </div>
    <img src="cid:low_banner" style="display:block;width:100%;height:auto;" alt="footer">
  </div>
  <div style="text-align:center;color:#64748b;font-size:12px;margin-top:12px;">This message was sent automatically.</div>
</body>
</html>'''

def render_html(subject:str, greeting:str, body_html:str, form_link:str) -> str:
    greeting_html = f"<p style='margin:0 0 12px 0;font-size:16px;color:#0f172a;'>{greeting}</p>" if greeting else ""
    body_html = f"<div style='font-size:15px;color:#1f2937;line-height:1.6'>{body_html}</div>"
    return HTML_TEMPLATE.format(subject=subject, greeting_block=greeting_html, body_block=body_html, form_link=form_link or DEFAULT_FORM_LINK)

def build_mime_message(from_email:str, to_email:str, subject:str, html_body:str, upper_path:str, lower_path:str, from_name:str|None=None) -> MIMEMultipart:
    msg = MIMEMultipart("related")
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("This is an HTML email. Please enable HTML view.", "plain", "utf-8"))
    alt.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt)

    def attach_cid_image(path:str, cid:str):
        p = Path(path) if path else None
        if p and p.exists():
            with p.open("rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=p.name)
                msg.attach(img)

    attach_cid_image(upper_path, "upper_banner")
    attach_cid_image(lower_path, "low_banner")
    return msg
