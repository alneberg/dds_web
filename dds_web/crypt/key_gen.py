""" Code for generating project related keys """

import os

from cryptography.hazmat import backends
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf import scrypt
from nacl import bindings
from flask import current_app


class project_keygen(object):
    """Class with methods to generate keys"""

    def __init__(self, project_id):
        """Needs a project id"""
        self.project_id = project_id
        self._set_project_id_bytes()
        self._set_salt_and_nonce()
        self._set_passphrase()
        self._set_private_and_public_keys()

    def get_key_info_dict(self):
        return dict(
            privkey_salt=self._salt.hex().upper(),
            privkey_nonce=self._nonce.hex().upper(),
            #                    passphrase=self._passphrase.hex().upper(),
            private_key=self._encrypted_private_key.hex().upper(),
            public_key=self._public_key_bytes.hex().upper(),
        )

    def _set_project_id_bytes(self):
        """Converts and set the project id in bytes"""
        self._project_id_bytes = bytes(self.project_id, "utf-8")

    def _set_salt_and_nonce(self):
        """Set salt and nonce i.e. random generated bit for encryption"""
        self._salt = os.urandom(16)
        self._nonce = os.urandom(12)

    def _set_passphrase(self):
        """Sets the private encryption passphrase using app secret key"""
        self._passphrase = (current_app.config.get("SECRET_KEY")).encode("utf-8")
        # self._passphrase = bytes.fromhex(current_app.config.get("SECRET_KEY"))

    def _set_private_and_public_keys(self):
        """Genrates salted, encrypted private and public key"""
        project_key_gen = x25519.X25519PrivateKey.generate()
        # generate private key bytes
        private_key_bytes = project_key_gen.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        # Massage the passphrase to be used for encryption using scrypt
        scrpyt_salt = scrypt.Scrypt(
            salt=self._salt,
            length=32,
            n=2 ** 14,
            r=8,
            p=1,
            backend=backends.default_backend(),
        )
        derived_passphrase_key = scrpyt_salt.derive(self._passphrase)
        # Encrypt the formatted private key with salted passphrase and nonce
        self._encrypted_private_key = bindings.crypto_aead_chacha20poly1305_ietf_encrypt(
            message=private_key_bytes,
            aad=None,
            nonce=self._nonce,
            key=derived_passphrase_key,
        )
        # Generate public key bytes
        self._public_key_bytes = project_key_gen.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
