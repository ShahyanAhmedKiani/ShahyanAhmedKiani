import os
import requests
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
USERNAME = os.getenv("USERNAME")
README_FILE = "README.md"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_all_repos():
    repos = []
    page = 1
    while True:
        res = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&type=public&affiliation=owner",
            headers=HEADERS
        )
        if res.status_code != 200:
            print(f"⚠️ Failed to fetch repos (status {res.status_code})")
            break
        data = res.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    print(f"✅ Fetched {len(repos)} repositories")
    return repos

def aggregate_languages(repos):
    lang_bytes = {}
    total_repos = len(repos)
    processed = 0
    
    for repo in repos:
        repo_name = repo.get("name")
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        
        res = requests.get(lang_url, headers=HEADERS)
        if res.status_code == 200:
            langs = res.json()
            if langs:
                for lang, size in langs.items():
                    lang_bytes[lang] = lang_bytes.get(lang, 0) + size
                processed += 1
                print(f"  📁 {repo_name}: {list(langs.keys())}")
    
    print(f"✅ Processed {processed}/{total_repos} repos with code")
    print(f"🌐 Found {len(lang_bytes)} unique languages")
    return lang_bytes

def generate_stats_md(lang_bytes):
    total = sum(lang_bytes.values())
    if total == 0:
        return "📊 No language data found."

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
    
    # Show ALL languages (remove the percentage filter)
    lines = ["## 📊 Language Stats", "", "```mermaid", "pie showData", "    title Code Language Distribution"]
    
    for lang, size in sorted_langs:
        pct = (size / total) * 100
        # Show ALL languages (even <1%)
        safe_lang = lang.replace('"', '\\"')
        lines.append(f'    "{safe_lang}" : {pct:.2f}')
    
    lines.extend(["```", ""])
    
    # Add detailed table below
    lines.extend(["### 📈 Detailed Breakdown", "", "| Language | Bytes | Percentage |", "|----------|-------|------------|"])
    
    for lang, size in sorted_langs:
        pct = (size / total) * 100
        lines.append(f"| {lang} | {size:,} | {pct:.2f}% |")
    
    # Add timestamp
    lines.append("")
    lines.append(f"*🔄 Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
    
    return "\n".join(lines)

def update_readme(new_content):
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    start, end = "<!-- language-stats-start -->", "<!-- language-stats-end -->"
    if start in content and end in content:
        content = content.split(start)[0] + start + "\n" + new_content + "\n" + end + content.split(end)[1]
    else:
        content += f"\n{start}\n{new_content}\n{end}\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    print("🔍 Fetching repositories...")
    repos = fetch_all_repos()
    print(f"📦 Total: {len(repos)} repositories")
    print("🌐 Calculating language stats...")
    lang_bytes = aggregate_languages(repos)
    md = generate_stats_md(lang_bytes)
    update_readme(md)
    print("✅ README updated successfully!")
