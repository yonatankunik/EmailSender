import smtplib, ssl, time
from typing import Iterable, Tuple
from email.utils import formatdate
from email.message import Message

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    HAS_SENDGRID = True
except Exception:
    HAS_SENDGRID = False

def send_via_gmail_smtp(smtp_user:str, app_password:str, messages:Iterable[Message], smtp_host="smtp.gmail.com", smtp_port=587, throttle_sec:float=0.3) -> Tuple[int,int]:
    sent = failed = 0
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(smtp_user, app_password)
        for msg in messages:
            msg["Date"] = formatdate(localtime=True)
            try:
                server.send_message(msg)
                sent += 1
            except Exception as e:
                print("SMTP send error:", e)
                failed += 1
            time.sleep(throttle_sec)
    return sent, failed

def send_via_sendgrid(api_key:str, messages:Iterable[Message], throttle_sec:float=0.1) -> Tuple[int,int]:
    if not HAS_SENDGRID:
        raise RuntimeError("sendgrid package not installed")
    sg = SendGridAPIClient(api_key)
    sent = failed = 0
    for m in messages:
        try:
            # Extract HTML from MIME (alternative part)
            html = None
            if m.is_multipart():
                for part in m.walk():
                    if part.get_content_type() == "text/html":
                        html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                        break
            if html is None:
                html = ""

            mail = Mail(
                from_email=m["From"],
                to_emails=m["To"],
                subject=m["Subject"],
                html_content=html
            )
            # Note: CID inline images are not directly supported via high-level helper; prefer hosting images when using SendGrid.
            resp = sg.send(mail)
            if 200 <= resp.status_code < 300:
                sent += 1
            else:
                failed += 1
        except Exception as e:
            print("SendGrid send error:", e)
            failed += 1
        time.sleep(throttle_sec)
    return sent, failed
