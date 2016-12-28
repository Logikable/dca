from datetime import datetime

datefmts = ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M')
def toepoch(date):
    if isinstance(date, datetime):
        return date.timestamp()
    if date == "never":
        return -1
    for fmt in datefmts:
        try:
            date = datetime.strptime(date, fmt)
            break
        except ValueError:
            pass
    return date.timestamp()
