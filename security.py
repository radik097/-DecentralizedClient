from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import pytz
from rich.console import Console
from rich.traceback import install
import os, json
install()
console=Console()

  
def generate_self_signed_cert(client_id):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    now = datetime.now(pytz.UTC)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        now + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256(), default_backend())

    keyfile = f"{client_id}_key.pem"
    certfile = f"{client_id}_cert.pem"
    
    if os.path.exists("known_users.json"):
        with open("known_users.json", "r") as f:
            known_users = json.load(f)
            if keyfile in known_users or certfile in known_users:
                return
    with open("known_users.json", "a") as f:
        json.dump([keyfile, certfile], f)
        f.write("\n")

    with open(keyfile, "wb") as f:
        f.write(key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=NoEncryption()
        ))

    with open(certfile, "wb") as f:
        f.write(cert.public_bytes(Encoding.PEM))

    return certfile, keyfile
