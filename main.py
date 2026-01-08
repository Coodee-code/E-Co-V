import requests
import base64
import re
import os
import json

SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'sub.txt'
OUTPUT_B64 = 'sub_b64.txt'

# هدر برای اینکه گیت‌هاب مسدود نکنه
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def robust_decode(text):
    """
    تلاش سنگین برای دیکد کردن Base64 حتی اگر خراب باشه
    """
    if not text: return ""
    text = text.strip()
    
    # اگر متن خودش کانفیگ خام هست، دست نزن
    if text.startswith('vless://') or text.startswith('vmess://') or text.startswith('trojan://'):
        return text

    # تلاش برای دیکد
    try:
        # اضافه کردن پدینگ تا جایی که ضریب 4 بشه
        missing_padding = len(text) % 4
        if missing_padding:
            text += '=' * (4 - missing_padding)
        
        decoded_bytes = base64.b64decode(text, validate=False)
        return decoded_bytes.decode('utf-8', errors='ignore')
    except:
        return text # اگه نشد، خود متن رو برگردون شاید خام باشه

def fetch_and_parse():
    if not os.path.exists(SOURCE_FILE):
        print("❌ فایل sources.txt پیدا نشد!")
        return []

    with open(SOURCE_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    collected_configs = []
    print(f"🔥 شروع استخراج از {len(urls)} منبع...")

    for url in urls:
        try:
            print(f"⚡ در حال دریافت: {url}")
            response = requests.get(url, headers=HEADERS, timeout=15)
            content = response.text.strip()
            
            # مرحله 1: دیکد اولیه
            decoded_content = robust_decode(content)
            
            # مرحله 2: پیدا کردن کانفیگ‌ها با Regex
            # این الگو تمام پروتکل‌ها رو میکشه بیرون
            found = re.findall(r'(vmess|vless|trojan|ss|ssr)://[a-zA-Z0-9\-_@.:?=&%#]*', decoded_content)
            
            # اگر با دیکد چیزی پیدا نشد، شاید فایل خام بوده، روی خود کانتنت اصلی تست میکنیم
            if not found:
                found = re.findall(r'(vmess|vless|trojan|ss|ssr)://[a-zA-Z0-9\-_@.:?=&%#]*', content)

            if found:
                collected_configs.extend(found)
                print(f"   ✅ {len(found)} کانفیگ پیدا شد.")
            else:
                print("   ⚠️ کانفیگی در این لینک پیدا نشد (شاید فرمت ناشناخته).")

        except Exception as e:
            print(f"   ❌ خطا: {e}")

    # حذف تکراری‌ها
    return list(set(collected_configs))

def rename_configs(configs):
    renamed_list = []
    counter = 1
    
    for conf in configs:
        try:
            # تشخیص پروتکل
            protocol = conf.split("://")[0]
            body = conf.split("://")[1]
            
            new_conf = conf # پیش‌فرض
            new_name = f"E-Config-{counter}"

            if protocol in ['vless', 'trojan', 'ss']:
                # برای این پروتکل‌ها، هر چی بعد از # هست رو پاک میکنیم و اسم جدید میذاریم
                if '#' in body:
                    clean_body = body.split('#')[0]
                    new_conf = f"{protocol}://{clean_body}#{new_name}"
                else:
                    new_conf = f"{conf}#{new_name}"
            
            # نکته: vmess رو تغییر نمیدیم چون ساختار JSON داره و ممکنه خراب شه
            # مگر اینکه بخوایم دیکد و انکد کنیم که پیچیده‌ست.
            
            renamed_list.append(new_conf)
            counter += 1
        except:
            renamed_list.append(conf)

    return renamed_list

def save_to_file(configs):
    if not configs:
        print("❌ هیچ کانفیگی جمع نشد!")
        return

    # ذخیره فایل متنی
    final_text = '\n'.join(configs)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_text)

    # ذخیره فایل Base64 (برای ایمپورت راحت‌تر)
    encoded_b64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open(OUTPUT_B64, 'w', encoding='utf-8') as f:
        f.write(encoded_b64)

    print(f"\n🎉 تمام! {len(configs)} کانفیگ جمع‌آوری و ذخیره شد.")
    print(f"📂 فایل‌ها: {OUTPUT_FILE} و {OUTPUT_B64}")

if __name__ == "__main__":
    raw_configs = fetch_and_parse()
    final_configs = rename_configs(raw_configs)
    save_to_file(final_configs)
