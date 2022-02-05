# Automatically encrypt emails using WKD and Postfix

See https://wgauthier.net/blog/automatically-encrypt-emails-using-wkd-and-postfix/

This is a small Python script that will automatically encrypt all outgoing emails to receipients that have published their public PGP keys in the Web Key Directory (WKD). The script will receive and process e-mails received from Postfix's pipe delivery agent and re-inject the e-mail back into Postfix for final delivery.

# Installation and configuration
## 1. Create a dedicated system user and setup the Python script

Create an unprivileged system account that the script will run under:


    adduser --system wkd-user

Download the script and place it under the system user's home folder and make it executable:


    wget https://raw.githubusercontent.com/wjgauthier/postfix-wkd/main/postfix-wkd.py -O /home/wkd-user/postfix-wkd.py
    chmod +x /home/wkd-user/postfix-wkd.py

Explicitly state that we only want to fetch keys over WKD in **/home/wkd-user/.gnupg/gpg.conf**


    auto-key-locate local,wkd

Install the required dependency:


    apt install python3-gpg


## 2. Configure Postfix Milter

In **/etc/postfix/master.cf**, make the following additions/changes: 


<pre># ==========================================================================
# service type  private unpriv  chroot  wakeup  maxproc command + args
#               (yes)   (yes)   (no)    (never) (100)
# ==========================================================================
<b>localhost:10026 inet  n       -       n       -       10      smtpd
    -o content_filter= 
    -o receive_override_options=no_unknown_recipient_checks,no_header_body_checks,no_milters
    -o smtpd_helo_restrictions=
    -o smtpd_client_restrictions=
    -o smtpd_sender_restrictions=
    # Postfix 2.10 and later: specify empty smtpd_relay_restrictions.
    -o smtpd_relay_restrictions=
    -o smtpd_recipient_restrictions=permit_mynetworks,reject
    -o mynetworks=127.0.0.0/8
	-o smtpd_authorized_xforward_hosts=127.0.0.0/8</b>b>
smtp      inet  n       -       y       -       -       smtpd
<b>    -o content_filter=filter:dummy</b>
	
[...]

<b>filter    unix  -       n       n       -       10      pipe
    flags=Rq user=wkd-user null_sender=
    argv=/home/wkd-user/wkd-postfix.py -f ${sender} -- ${recipient}</b></pre>

Restart Postfix

    systemctl restart postfix
