from OpenSSL import crypto

def generate_self_signed_cert(cert_file, key_file):
    # Create a self-signed certificate using OpenSSL
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().CN = "localhost"  # You can set this to your domain or IP address
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)  # Valid for 10 years
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Write certificate and key to files
    with open(cert_file, "wb") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(key_file, "wb") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

# Generate the cert and key
generate_self_signed_cert("server.crt", "server.key")
print("Self-signed certificate and key generated!")
