import binascii


def crc32(data: bytes, crc: int = 0) -> int:
    """Return unsigned CRC-32/ISO-HDLC (ADCCP/PKZIP)."""

    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")

    if type(crc) is not int or not 0 <= crc <= 0xFFFFFFFF:
        raise ValueError("crc must be an unsigned 32-bit integer")

    return binascii.crc32(data, crc) & 0xFFFFFFFF
