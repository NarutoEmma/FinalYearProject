import random
import string
def generate_access_code(length=8):
    return ''.join(random.choices(string.digits, k=length))