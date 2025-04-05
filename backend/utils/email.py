import smtplib
from email.message import EmailMessage

def send_email_reminder(to_email, subject, body, smtp_server='smtp.gmail.com', smtp_port=587,
                        from_email='your@gmail.com', from_password='yourpassword'):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, from_password)
            server.send_message(msg)
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False
