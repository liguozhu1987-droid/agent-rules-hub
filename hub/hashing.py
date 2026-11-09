"""校验值：全部 SHA-256，统一 LF + UTF-8 无 BOM + NFC。"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path


def normalize_bytes(text: str) -> bytes:
    """把文本规范化为 LF + NFC + 无 BOM 的 UTF-8 字节。"""
    value = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    return unicodedata.normalize("NFC", value).encode("utf-8")


def bytes_sha256(data: bytes) -> str:
    """计算字节串的 SHA-256。"""
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    """计算文件**实际字节**的 SHA-256，用于漂移检测。"""
    return bytes_sha256(Path(path).read_bytes())


def content_hash(body: str) -> str:
    """规范化规则正文后取 SHA-256，用于跨文件查重。

    规范化步骤：剥离首尾空白、统一 LF、去行尾空格、Unicode NFC。
    """
    value = unicodedata.normalize("NFC", body.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff"))
    lines = [line.rstrip() for line in value.strip().split("\n")]
    return bytes_sha256(normalize_bytes("\n".join(lines)))


def core_sha256(core_block: str) -> str:
    """唯一常驻正文块的 SHA-256，跨常驻视图必须相等。"""
    return bytes_sha256(normalize_bytes(core_block))


def chain_sha256(prev_snapshot_sha256: str, snapshot_bytes: bytes) -> str:
    """审计哈希链：sha256(上一快照哈希 + 本快照规范化字节)。"""
    payload = prev_snapshot_sha256.encode("utf-8") + snapshot_bytes
    return bytes_sha256(payload)
