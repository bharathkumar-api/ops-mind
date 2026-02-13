import bleach

ALLOWED_TAGS = ["p", "strong", "em", "ul", "ol", "li", "code", "pre", "a", "blockquote"]
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}


def sanitize_markdown(content: str) -> str:
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
