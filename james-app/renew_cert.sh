#!/bin/bash
# renew_cert.sh - Create or renew a self-signed SSL cert for local HTTPS

CERT_DAYS=366
CERT_PATH="/app"
cd "$CERT_PATH" || exit 1

# Only renew if cert doesn't exist or is within 30 days of expiry
if [ ! -f cert.pem ] || [ ! -f key.pem ]; then
    echo "SSL: No certificate found, generating new one..."
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days $CERT_DAYS -nodes -subj '/CN=JamesLocal'
else
    END_DATE=$(openssl x509 -enddate -noout -in cert.pem | cut -d= -f2)
    END_SECS=$(date -d "$END_DATE" +%s)
    NOW_SECS=$(date +%s)
    DIFF_DAYS=$(( (END_SECS - NOW_SECS) / 86400 ))
    if (( DIFF_DAYS < 30 )); then
        echo "SSL: Cert expiring in $DIFF_DAYS days, renewing..."
        openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days $CERT_DAYS -nodes -subj '/CN=JamesLocal'
    else
        echo "SSL: Cert is good for $DIFF_DAYS more days, no renewal needed."
    fi
fi
