
def calculate_grade(score):

    if score >= 80:
        return "เกรด A"
    elif score >= 70:
        return "เกรด B"
    elif score >= 60:
        return "เกรด C"
    elif score >= 50:
        return "เกรด D"
    else:
        return "เกรด F"


def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    print("=" * 40)
    print("     ระบบให้เกรดตามคะแนน")
    print("=" * 40)
    
    try:
        # กรอกคะแนน
        score = float(input("\nกรุณากรอกคะแนน (0-100): "))
        
        # ตรวจสอบความถูกต้องของคะแนน
        if score < 0 or score > 100:
            print("❌ กรุณากรอกคะแนนระหว่าง 0 ถึง 100")
            return
        
        # คำนวณเกรด
        grade = calculate_grade(score)
        
        # แสดงผลลัพธ์
        print("\n" + "=" * 40)
        print(f"คะแนน: {score}")
        print(f"ผลลัพธ์: {grade}")
        print("=" * 40)
        
    except ValueError:
        print("❌ กรุณากรอกตัวเลขให้ถูกต้อง")


if __name__ == "__main__":
    main()
