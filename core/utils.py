def cast_bool(s: str):
    return True if s == "Yes" else False


def cast_list(s: str):
    return [row.strip() for row in s.split(",")]


def cast_int(s: str):
    s = s.strip()
    if s == "":
        return None
    else:
        return int(s)
