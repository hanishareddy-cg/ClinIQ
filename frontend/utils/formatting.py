from datetime import datetime


def fmt_datetime(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                value = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        else:
            return value
    return value.strftime("%b %d, %Y %H:%M") if isinstance(value, datetime) else str(value)


def fmt_date(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            value = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return value
    return value.strftime("%b %d, %Y") if isinstance(value, datetime) else str(value)


def flag_color(flag: str | None) -> str:
    if flag and "abnormal" in flag.lower():
        return "🔴"
    if flag and "delta" in flag.lower():
        return "🟡"
    return "🟢"


def source_type_icon(source_type: str) -> str:
    return {
        "lab":        "🧪",
        "medication": "💊",
        "vital":      "❤️",
        "diagnosis":  "📋",
        "note":       "📝",
    }.get(source_type, "•")
