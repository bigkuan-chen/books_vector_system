import re


CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_RUN = re.compile(r"[ \t\r\f\v]+")


def normalize_query(query: str) -> str:
    text = CONTROL_CHARS.sub("", query)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(WHITESPACE_RUN.sub(" ", line).strip() for line in text.split("\n"))
    return text.strip()
