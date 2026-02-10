#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import os
from pathlib import Path
from typing import Optional


class SecureStorageError(Exception):
    pass


class SecureKeyStore:
    def __init__(self, service_name: str = "gui_intelligent_file_classifier"):
        self.service_name = service_name
        self._fallback_dir = Path.home() / ".file_classifier_ai"
        self._fallback_dir.mkdir(exist_ok=True)
        self._fallback_file = self._fallback_dir / "secret_store.json"

    def _try_get_keyring(self):
        try:
            import keyring  # type: ignore

            return keyring
        except Exception:
            return None

    def set_secret(self, key_name: str, secret: str) -> None:
        if not key_name:
            raise SecureStorageError("key_name is required")

        keyring = self._try_get_keyring()
        if keyring is not None:
            try:
                keyring.set_password(self.service_name, key_name, secret)
                return
            except Exception:
                pass

        self._set_secret_fallback(key_name, secret)

    def get_secret(self, key_name: str) -> Optional[str]:
        if not key_name:
            return None

        keyring = self._try_get_keyring()
        if keyring is not None:
            try:
                value = keyring.get_password(self.service_name, key_name)
                if value:
                    return value
            except Exception:
                pass

        return self._get_secret_fallback(key_name)

    def delete_secret(self, key_name: str) -> None:
        keyring = self._try_get_keyring()
        if keyring is not None:
            try:
                keyring.delete_password(self.service_name, key_name)
            except Exception:
                pass

        self._delete_secret_fallback(key_name)

    def clear_all_local_data(self) -> None:
        keyring = self._try_get_keyring()
        if keyring is not None:
            for name in ["ai_api_key"]:
                try:
                    keyring.delete_password(self.service_name, name)
                except Exception:
                    pass

        try:
            if self._fallback_file.exists():
                self._fallback_file.unlink()
        except Exception:
            pass

    def _get_machine_key(self) -> bytes:
        try:
            import hashlib
            import getpass
            import platform

            seed = f"{getpass.getuser()}|{platform.node()}|{self.service_name}".encode("utf-8")
            return hashlib.sha256(seed).digest()
        except Exception as e:
            raise SecureStorageError(str(e))

    def _dpapi_encrypt(self, plaintext: bytes) -> Optional[bytes]:
        if os.name != 'nt':
            return None

        try:
            import ctypes
            from ctypes import wintypes

            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

            crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

            def _blob_from_bytes(data: bytes) -> DATA_BLOB:
                buf = ctypes.create_string_buffer(data)
                return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

            in_blob = _blob_from_bytes(plaintext)
            out_blob = DATA_BLOB()

            if not crypt32.CryptProtectData(
                ctypes.byref(in_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(out_blob),
            ):
                return None

            try:
                out_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                return out_bytes
            finally:
                kernel32.LocalFree(out_blob.pbData)
        except Exception:
            return None

    def _dpapi_decrypt(self, ciphertext: bytes) -> Optional[bytes]:
        if os.name != 'nt':
            return None

        try:
            import ctypes
            from ctypes import wintypes

            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

            crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

            def _blob_from_bytes(data: bytes) -> DATA_BLOB:
                buf = ctypes.create_string_buffer(data)
                return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

            in_blob = _blob_from_bytes(ciphertext)
            out_blob = DATA_BLOB()

            if not crypt32.CryptUnprotectData(
                ctypes.byref(in_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(out_blob),
            ):
                return None

            try:
                out_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                return out_bytes
            finally:
                kernel32.LocalFree(out_blob.pbData)
        except Exception:
            return None

    def _xor_bytes(self, data: bytes, key: bytes) -> bytes:
        out = bytearray(len(data))
        for i, b in enumerate(data):
            out[i] = b ^ key[i % len(key)]
        return bytes(out)

    def _set_secret_fallback(self, key_name: str, secret: str) -> None:
        raw = secret.encode("utf-8")
        dpapi = self._dpapi_encrypt(raw)
        if dpapi is not None:
            enc = dpapi
            mode = "dpapi"
        else:
            key = self._get_machine_key()
            enc = self._xor_bytes(raw, key)
            mode = "xor"
        payload = {
            "v": 1,
            "mode": mode,
            "data": base64.b64encode(enc).decode("ascii"),
        }

        store = {}
        if self._fallback_file.exists():
            try:
                store = json.loads(self._fallback_file.read_text(encoding="utf-8"))
            except Exception:
                store = {}

        store[key_name] = payload
        self._fallback_file.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")

    def _get_secret_fallback(self, key_name: str) -> Optional[str]:
        if not self._fallback_file.exists():
            return None

        try:
            store = json.loads(self._fallback_file.read_text(encoding="utf-8"))
            payload = store.get(key_name)
            if not payload or "data" not in payload:
                return None

            enc = base64.b64decode(payload["data"].encode("ascii"))

            mode = payload.get("mode")
            if mode == "dpapi":
                raw = self._dpapi_decrypt(enc)
                if raw is None:
                    return None
            else:
                key = self._get_machine_key()
                raw = self._xor_bytes(enc, key)
            return raw.decode("utf-8")
        except Exception:
            return None

    def _delete_secret_fallback(self, key_name: str) -> None:
        if not self._fallback_file.exists():
            return

        try:
            store = json.loads(self._fallback_file.read_text(encoding="utf-8"))
            if key_name in store:
                del store[key_name]
                self._fallback_file.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
