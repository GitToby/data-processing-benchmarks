from pathlib import Path

_data_root = Path("..", "data").resolve()
crime_path = _data_root / "Crime_Data_from_2020_to_Present.csv"
reddit_path = _data_root / "reddit_account_data.csv"
out_path = _data_root / "output"

if not out_path.exists():
    out_path.mkdir(parents=True)

print(crime_path)
print(reddit_path)
print(out_path)
