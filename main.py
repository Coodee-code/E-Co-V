import requests
import base64
import re
import os

# اسم فایلی که لینک‌ها توشه
SOURCE_FILE = 'sources.txt'
# اسم فایلی که خروجی توش ذخیره میشه
OUTPUT_FILE = 'sub.txt'

def decode_base64(text):
    # سعی میکنه متن رو دیکد کنه، اگه نشد خود متن رو برمیگردونه
    try:
        # اضافه کردن پدینگ در صورت نیاز
        padding = len(text) % 4
        if padding > 0:
            text += '=' * (4 - padding)
        return base64.b64decode(text).decode('utf-8', errors='ignore')
    except:
        return text

def get_configs():
    if not os.path.exists(SOURCE_FILE):
        print("فایل sources.txt پیدا نشد!")
        return []

    with open(SOURCE_FILE, 'r') as f:
        urls = f.read().splitlines()

    all_configs = []
    
    print(f"--- شروع جمع‌آوری از {len(urls)} منبع ---")

    for url in urls:
        if not url.strip() or url.startswith('#'): continue
        try:
            print(f"در حال دریافت: {url}")
            resp = requests.get(url.strip(), timeout=10)
            content = resp.text.strip()
            
            # اگه محتوا Base64 بود اول بازش میکنیم
            if "vmess://" not in content and "vless://" not in content:
                 content = decode_base64(content)

            # پیدا کردن کانفیگ‌ها با Regex
            # این الگو پروتکل‌های رایج رو پیدا میکنه
            configs = re.findall(r'(vmess|vless|trojan|ss|ssr)://[a-zA-Z0-9\-_@.:?=&%#]*', content)
            
            for conf in configs:
                all_configs.append(conf)
                
        except Exception as e:
            print(f"خطا در لینک {url}: {e}")

    return list(set(all_configs)) # حذف تکراری‌ها

def rename_and_save(configs):
    final_list = []
    counter = 1
    
    for conf in configs:
        try:
            # جدا کردن پروتکل و بقیه ماجرا
            protocol = conf.split("://")[0]
            rest = conf.split("://")[1]
            
            new_conf = ""
            
            # تغییر نام برای Vless / Trojan / SS
            if '#' in rest:
                # حذف اسم قبلی و گذاشتن اسم جدید
                base_part = rest.split('#')[0]
                new_conf = f"{protocol}://{base_part}#E-Config-{counter}"
            else:
                # اگه اسم نداشت، اسم رو اضافه کن
                new_conf = f"{protocol}://{rest}#E-Config-{counter}"
            
            final_list.append(new_conf)
            counter += 1
        except:
            continue

    # ذخیره به صورت متن ساده (خط به خط)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_list))
    
    # اگه میخوای خروجی Base64 هم داشته باشی (برای ایمپورت راحت‌تر)
    with open('sub_b64.txt', 'w', encoding='utf-8') as f:
        encoded = base64.b64encode('\n'.join(final_list).encode('utf-8')).decode('utf-8')
        f.write(encoded)

    print(f"--- تمام! {len(final_list)} کانفیگ با نام E-Config ذخیره شد ---")

if __name__ == "__main__":
    configs = get_configs()
    rename_and_save(configs)
