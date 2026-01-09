import os
from dotenv import load_dotenv

load_dotenv()
pw = os.getenv('DB_PASSWORD')
print(f'Password: {pw}')
print(f'Length: {len(pw)}')
print(f'Has spaces: {" " in pw}')
print(f'Repr: {repr(pw)}')
