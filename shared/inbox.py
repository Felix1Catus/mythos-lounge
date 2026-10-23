#!/usr/bin/env python3
"""Fetch recent emails from the yumna Gmail via IMAP and extract verification links/codes.
Usage:
  inbox.py [--since-min N] [--from SUBSTR] [--subject SUBSTR] [--limit N] [--urls-only]
Prints matching messages: date | from | subject, then extracted URLs (http/https) and 6-digit codes.
Read-only (uses IMAP readonly examine). Credentials from ~/.config/yumna-pipeline/credentials.env.
"""
import imaplib, email, re, sys, argparse, os
from email.header import decode_header

def load_creds(path=os.path.expanduser('~/.config/yumna-pipeline/credentials.env'), alt=False):
    d = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            v = v.strip().strip('"').strip("'")
            if 'PASSWORD' in k:
                v = v.replace(' ', '')
            d[k.strip()] = v
    if alt:
        return d['YUMNA_ALT_EMAIL'], d['YUMNA_ALT_APP_PASSWORD'], d['YUMNA_ALT_IMAP_HOST'], int(d['YUMNA_ALT_IMAP_PORT'])
    return d['YUMNA_EMAIL'], d['YUMNA_APP_PASSWORD'], d['YUMNA_IMAP_HOST'], int(d['YUMNA_IMAP_PORT'])

def hdr_str(v):
    if not v: return ''
    parts = decode_header(v)
    out = []
    for t, enc in parts:
        out.append(t.decode(enc or 'utf-8', errors='replace') if isinstance(t, bytes) else t)
    return ' '.join(out)

def body_text(msg):
    chunks = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ('text/plain', 'text/html'):
                try: chunks.append(part.get_payload(decode=True).decode('utf-8', errors='replace'))
                except Exception: pass
    else:
        try: chunks.append(msg.get_payload(decode=True).decode('utf-8', errors='replace'))
        except Exception: pass
    return '\n'.join(chunks)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since-min', type=int, default=1440)
    ap.add_argument('--from', dest='frm', default='')
    ap.add_argument('--subject', dest='subj', default='')
    ap.add_argument('--limit', type=int, default=10)
    ap.add_argument('--urls-only', action='store_true')
    ap.add_argument('--alt', action='store_true')
    ap.add_argument('--mailbox', default='INBOX')
    a = ap.parse_args()

    user, pw, host, port = load_creds(alt=a.alt)
    M = imaplib.IMAP4_SSL(host, port)
    M.login(user, pw)
    M.select(f'"{a.mailbox}"', readonly=True)
    import datetime
    since = (datetime.datetime.now() - datetime.timedelta(minutes=a.since_min)).strftime('%d-%b-%Y')
    crit = f'(SINCE {since})'
    typ, data = M.search(None, crit)
    ids = data[0].split()
    shown = 0
    for mid in reversed(ids):
        if shown >= a.limit: break
        typ, msg_data = M.fetch(mid, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        subj, frm, date = hdr_str(msg.get('Subject')), hdr_str(msg.get('From')), msg.get('Date')
        if a.frm.lower() not in frm.lower(): continue
        if a.subj.lower() not in subj.lower(): continue
        text = body_text(msg)
        urls = [u for u in re.findall(r'https?://[^\s<>"\')\]]+', text)]
        codes = re.findall(r'\b\d{6}\b', text)
        if not a.urls_only:
            print(f'--- {date} | {frm} | {subj}')
        for u in urls: print('URL:', u)
        for c in set(codes): print('CODE:', c)
        shown += 1
    M.logout()

if __name__ == '__main__':
    main()
