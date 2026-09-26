import json

# Read fixture with binary or latin-1 / cp1252 fallback to capture all characters cleanly
with open('datadump.json', 'rb') as f:
    raw_bytes = f.read()

try:
    text = raw_bytes.decode('utf-8')
except UnicodeDecodeError:
    print("Found non-utf8 characters, decoding with cp1252/latin-1 fallback...")
    text = raw_bytes.decode('cp1252', errors='replace')

data = json.loads(text)

# Write back strictly as clean UTF-8
with open('datadump.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("datadump.json successfully converted to clean UTF-8 JSON!")
