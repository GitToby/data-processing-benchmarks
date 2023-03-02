import logging
from pathlib import Path

_data_root = Path(__file__).parent.parent.parent / "data"
crime_path = _data_root / "Crime_Data_from_2020_to_Present.csv"
reddit_path = _data_root / "reddit_account_data.csv"
out_path = _data_root / "output"
log = logging.getLogger(__name__)

if not out_path.exists():
    out_path.mkdir(parents=True)

log.info(crime_path)
log.info(reddit_path)
