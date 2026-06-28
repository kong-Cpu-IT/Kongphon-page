import argparse
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("daily_horoscope.json")


def load_horoscope_data(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def list_signs(horoscopes):
    return [entry["sign"] for entry in horoscopes]


def find_horoscope(horoscopes, sign_name):
    normalized = sign_name.strip().lower()
    for entry in horoscopes:
        if entry["sign"].strip().lower() == normalized:
            return entry
    return None


def format_horoscope(entry):
    return (
        f"ราศี: {entry['sign']}\n"
        f"คำทำนาย: {entry['prediction']}\n"
        f"เลขนำโชค: {entry['lucky_number']}\n"
        f"สีมงคล: {entry['lucky_color']}\n"
        f"คำแนะนำ: {entry['advice']}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="โปรแกรมทำนายดวงรายวันจากไฟล์ JSON"
    )
    parser.add_argument(
        "--sign",
        "-s",
        help="ระบุราศี เช่น 'ราศีเมษ' เพื่อดูคำทำนายของราศีนั้น"
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="แสดงคำทำนายของทุกราศี"
    )
    args = parser.parse_args()

    data = load_horoscope_data(DATA_FILE)
    horoscopes = data.get("horoscopes", [])

    print(f"วันที่: {data.get('date', 'ไม่ระบุ')}\nแหล่งข้อมูล: {data.get('source', 'ไม่ระบุ')}\n")

    if args.all:
        for entry in horoscopes:
            print(format_horoscope(entry))
            print("\n" + "-" * 40 + "\n")
        return

    if args.sign:
        entry = find_horoscope(horoscopes, args.sign)
        if entry:
            print(format_horoscope(entry))
            return
        print(f"ไม่พบข้อมูลราศี '{args.sign}'\n")

    print("ราศีที่รองรับ:")
    for sign in list_signs(horoscopes):
        print(f"- {sign}")
    print("\nเรียกใช้: python horoscope.py --sign 'ราศีเมษ' หรือ python horoscope.py --all")


if __name__ == "__main__":
    main()
