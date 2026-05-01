import random
import string
#generates access code
def generate_access_code(length=8):
    return ''.join(random.choices(string.digits, k=length))