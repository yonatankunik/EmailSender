import streamlit as st

def header():
    st.markdown(
        '''
        <div style="background:linear-gradient(120deg,#E0EAFF,#FFFFFF);border:1px solid #e6ecff;padding:16px 18px;border-radius:14px;margin-bottom:10px;">
          <h1 style="margin:0;font-size:1.6rem;">📧 Mail-Merge Mailer</h1>
          <p style="margin:6px 0 0;color:#334155;">Bulk personalized emails with top & bottom banners and a CTA button.</p>
        </div>
        ''', unsafe_allow_html=True
    )

def sidebar():
    with st.sidebar:
        st.header("⚙️ Settings")
        provider = st.selectbox("Email Provider", ["Gmail SMTP", "SendGrid (API)"], index=0)
        st.caption("Gmail SMTP uses App Password. SendGrid provides analytics and better deliverability.")
        st.markdown("---")
        from_name = st.text_input("From Name", value="Events Team")
        from_email = st.text_input("From Email (sender)", value="your.name@gmail.com")
        st.markdown("---")
        st.subheader("Credentials")
        if provider == "Gmail SMTP":
            secret = st.text_input("Gmail App Password", type="password")
        else:
            secret = st.text_input("SendGrid API Key", type="password")
        return provider, from_name, from_email, secret
