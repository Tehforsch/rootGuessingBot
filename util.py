def tryConvertToInt(content):
    try:
        return int(content)
    except (ValueError, TypeError) as e:
        return None
