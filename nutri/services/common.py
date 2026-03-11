def parse_int_or_zero(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

