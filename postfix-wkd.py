#!/usr/bin/env python3

import sys,getopt
import gpg
import email
import smtplib
import copy
import re
from email.mime.base import MIMEBase
import email.mime.multipart
from email.mime.application import MIMEApplication
import email.encoders

home_dir = '/home/wkd-user/.gnupg'
c = gpg.Context(armor=True, home_dir=home_dir)
sender = sys.argv[2]
recipients = sys.argv[4:]
orig_message = email.message_from_bytes(sys.stdin.buffer.read())

def set_header(message, header, value, **params):

    if header in message:
        message.replace_header(header, value)
    else:
        message.add_header(header, value, **params)

def process_email(recipient, keyid):

    out_msg = copy.copy(orig_message)

    if(out_msg.is_multipart() or out_msg.get_content_type() == 'text/html'):

        # It looks like the client has already encrypted the email, so just email whatever we have out
        if(out_msg.get_content_type() == 'multipart/encrypted' or out_msg.get_content_type() == 'application/pkcs7-mime'):
            mail_out(recipient, orig_message)
            return

        ciphertext, result, sign_result = c.encrypt(out_msg.as_string().encode(), recipients=keyid, sign=False, always_trust=True)
        
        out_msg.set_type("multipart/encrypted");
        out_msg.set_param("protocol", "application/pgp-encrypted");
        out_msg.preamble = "This is an OpenPGP/MIME encrypted message (RFC 4880 and 3156)"
        set_header(out_msg, "Content-Transfer-Encoding", None)
        out_msg.set_payload(None)
        
        pgp_encrypt = MIMEApplication("Version: 1", "pgp-encrypted", email.encoders.encode_7or8bit)
        set_header(pgp_encrypt, "MIME-Version", None)
        out_msg.attach(pgp_encrypt)
        
        octet_stream = MIMEApplication(ciphertext, "octet-stream", email.encoders.encode_7or8bit)
        set_header(octet_stream, "Content-Type", "application/octet-stream;", name="encrypted.asc")
        set_header(octet_stream, "Content-Disposition", "inline", filename="encrypted.asc")
        set_header(octet_stream, "MIME-Version", None)
        out_msg.attach(octet_stream)
        
    else:
        body = out_msg.as_string().split("\n\n", 1)[1].strip()
        
        # It looks like the client has already encrypted the email (inline), so just email whatever we have out
        if re.search("-----BEGIN PGP MESSAGE-----", body, flags = re.MULTILINE) is not None:
            mail_out(recipient, orig_message)
            return
            
        ciphertext, result, sign_result = c.encrypt(body.encode(), recipients=keyid, sign=False, always_trust=True)

        out_msg.set_payload(None)
        out_msg.set_payload(ciphertext)
           

    mail_out(recipient, out_msg)


def mail_out(recipient, out_msg):
    smtp = smtplib.SMTP('127.0.0.1', '10026')
    smtp.sendmail(sender, recipient, out_msg.as_string())
    smtp.quit()
    

for recipient in recipients:
    keys = list(c.keylist(recipient, False, gpg.constants.keylist.mode.LOCATE))
    if(keys):
        for key in keys:
            if(key.subkeys[0].keyid):
                process_email(recipient, keys)
    else:
        mail_out(recipient, orig_message)
