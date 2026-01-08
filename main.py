import requests
import base64
import re
import os
import json
# random رو حذف کردم چون دیگه لازم نیست

SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'sub.txt'
OUTPUT_B64 = 'sub_b64.txt'

# --- تنظیمات ---
APP_TITLE = "E-Config FULL"
TOTAL_TRAFFIC = 10737418240000000

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

def get_unique_fingerprint(config):
    """
    اثر انگشت برای شناسایی تکراری‌ها (آی‌پی + پورت)
    """
    try:
        protocol = config.split("://")[0]
        
        if protocol == "vmess":
            b64_part = config[8:]
            pad = len(b64_part) % 4
            if pad: b64_part += '=' * (4 - pad)
            data = json.loads(base64.b64decode(b64_part).decode('utf-8'))
            return f"vmess_{data['add']}_{data['port']}"
            
        elif protocol in ["vless", "trojan"]:
            # فرمت: vless://uuid@ip:port?query...
            main_part = config.split("@")[1].split("?")[0].split("#")[0]
            return f"{protocol}_{main_part}"
            
        elif protocol == "ss":
            if '@' in config:
                server_part = config.split('@')[1].split("#")[0]
                return f"ss_{server_part}"
                
        return config 
    except:
        return config

def rename_vmess(link, new_name):
    try:
        b64_part = link[8:]
        pad = len(b64_part) % 4
        if pad: b64_part += '=' * (4 - pad)
        config = json.loads(base64.b64decode(b64_part).decode('utf-8'))
        config['ps'] = new_name
        new_json = json.dumps(config)
        return f"vmess://{base64.b64encode(new_json.encode('utf-8')).decode('utf-8')}"
    except:
        return link

def fetch_and_parse():
    if not os.path.exists(SOURCE_FILE): return []
    with open(SOURCE_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    raw_configs = []
    print(f"🔥 شروع جمع‌آوری...")

    for url in urls:
        try:
            print(f"⚡ دریافت: {url}")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            content = robust_decode(resp.text.strip())
            
            pattern = r'(?:vmess|vless|trojan|ss|ssr)://[a-zA-Z0-9\-_@.:?=&%#]*'
            found = re.findall(pattern, content)
            if not found: found = re.findall(pattern, resp.text.strip())
            
            if found: raw_configs.extend(found)
        except: pass

    return list(set(raw_configs))

def process_configs(configs):
    unique_pool = {}
    
    print(f"\n🧹 تعداد کل خام: {len(configs)}")

    # 1. فقط حذف تکراری‌ها
    for conf in configs:
        fingerprint = get_unique_fingerprint(conf)
        
        # اگر کلید تکراری نبود، اضافه کن
        if fingerprint not in unique_pool:
            unique_pool[fingerprint] = conf

    # لیست نهایی = همه کانفیگ‌های یکتا (بدون هیچ فیلتر دیگه‌ای)
    final_list = list(unique_pool.values())
    print(f"✅ تعداد نهایی (یکتا): {len(final_list)}")

    # 2. تغییر نام همه
    renamed_list = []
    counter = 1
    for conf in final_list:
        name = f"E-Config-{counter}"
        if conf.startswith("vmess://"):
            renamed_list.append(rename_vmess(conf, name))
        elif '#' in conf:
            renamed_list.append(f"{conf.split('#')[0]}#{name}")
        else:
            renamed_list.append(f"{conf}#{name}")
        counter += 1

    return renamed_list

def save_to_file(configs):
    if not configs: return

    title_b64 = base64.b64encode(APP_TITLE.encode('utf-8')).decode('utf-8')
    header_info = [
        f"#profile-title: base64:{title_b64}",
        f"#subscription-userinfo: upload=0; download=0; total={TOTAL_TRAFFIC}; expire=0",
        "#profile-update-interval: 1",
        ""
    ]
    
    final_text = '\n'.join(header_info + configs)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f: f.write(final_text)
    
    encoded_b64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open(OUTPUT_B64, 'w', encoding='utf-8') as f: f.write(encoded_b64)

    print(f"\n🎉 فایل ذخیره شد. تعداد کل: {len(configs)}")

if __name__ == "__main__":
    raw = fetch_and_parse()
    final = process_configs(raw)
    save_to_file(final)
