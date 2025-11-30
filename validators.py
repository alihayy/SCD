import re

# ✅ Password must include: uppercase, lowercase, digit, special character
def is_valid_password(password):
    return re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#]).{8,}$', password)

# ✅ Username must be alphanumeric only
def is_valid_username(username):
    return re.fullmatch(r'^[A-Za-z0-9]+$', username)

# ✅ Email format check
def is_valid_email(email):
    return re.fullmatch(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email)

# ✅ Name must contain alphabets only
def is_valid_name(name):
    return re.fullmatch(r'^[A-Za-z ]+$', name)
