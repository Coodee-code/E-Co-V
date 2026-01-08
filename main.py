import requests
import base64
import re
import os
import json

SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'sub.txt'
OUTPUT_B64 = 'sub_b64.txt'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def robust_decode(text):
    if not text: return ""
    text = text.strip()
    if text.startswith('vless://') or text.startswith('vmess://') or text.startswith('trojan://') or text.startswith('ss://'):
        return text
    try:
        missing_padding = len(text) % 4
        if missing_padding:
            text += '=' * (4 - missing_padding)
        return base64.b64decode(text, validate=False).decode('utf-8', errors='ignore')
    except:
        return text

def rename_vmess(link, new_name):
    """
    تابع مخصوص برای تغییر نام کانفیگ‌های VMess
    """
    try:
        # حذف vmess://
        b64_part = link[8:]
        # دیکد کردن کانفیگ
        missing_padding = len(b64_part) % 4
        if missing_padding:
            b64_part += '=' * (4 - missing_padding)
        
        json_str = base64.b64decode(b64_part).decode('utf-8')
        config = json.loads(json_str)
        
        # تغییر نام (ps)
        config['ps'] = new_name
        
        # دوباره انکد کردن
        new_json = json.dumps(config)
        new_b64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
        return f"vmess://{new_b64}"
    except:
        return link # اگه خراب بود دست نزن

def fetch_and_parse():
    if not os.path.exists(SOURCE_FILE):
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
            
            decoded_content = robust_decode(content)
            
            # --- فیکس اصلی اینجاست (?: اضافه شد که گروه کپچر نشه) ---
            pattern = r'(?:vmess|vless|trojan|ss|ssr)://[a-zA-Z0-9\-_@.:?=&%#]*'
            
            found = re.findall(pattern, decoded_content)
            if not found:
                found = re.findall(pattern, content)

            if found:
                collected_configs.extend(found)
                print(f"   ✅ {len(found)} کانفیگ پیدا شد.")
            else:
                print("   ⚠️ فرمت لینک شناسایی نشد (احتمالا YAML یا Clash است).")

        except Exception as e:
            print(f"   ❌ خطا: {e}")

    return list(set(collected_configs))

def rename_configs(configs):
    renamed_list = []
    counter = 1
    
    print(f"\n🔄 در حال تغییر نام {len(configs)} کانفیگ...")
    
    for conf in configs:
        try:
            new_name = f"E-Config-{counter}"
            
            if conf.startswith("vmess://"):
                # هندل کردن VMess
                new_conf = rename_vmess(conf, new_name)
                renamed_list.append(new_conf)
                
            elif conf.startswith("ss://") or conf.startswith("vless://") or conf.startswith("trojan://"):
                # هندل کردن بقیه
                if '#' in conf:
                    base_part = conf.split('#')[0]
                    renamed_list.append(f"{base_part}#{new_name}")
                else:
                    renamed_list.append(f"{conf}#{new_name}")
            else:
                renamed_list.append(conf)
                
            counter += 1
        except:
            renamed_list.append(conf)

    return renamed_list

def save_to_file(configs):
    if not configs:
        print("❌ هیچ کانفیگی جمع نشد!")
        return

    final_text = '\n'.join(configs)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_text)

    encoded_b64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open(OUTPUT_B64, 'w', encoding='utf-8') as f:
        f.write(encoded_b64)

    print(f"\n🎉 تمام! {len(configs)} کانفیگ با نام E-Config ذخیره شد.")

if __name__ == "__main__":
    raw_configs = fetch_and_parse()
    final_configs = rename_configs(raw_configs)
    save_to_file(final_configs)
