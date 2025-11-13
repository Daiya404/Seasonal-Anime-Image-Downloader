import datetime
import re


def get_current_season():
month = datetime.datetime.now().month
if month in [1, 2, 3]:
return "Winter"
if month in [4, 5, 6]:
return "Spring"
if month in [7, 8, 9]:
return "Summer"
return "Fall"




def sanitize_filename(name: str) -> str:
# Very conservative sanitization
name = name.strip()
name = re.sub(r"[<>:\\"/\\|?*]", "", name)
name = re.sub(r"\s+", " ", name)
return name