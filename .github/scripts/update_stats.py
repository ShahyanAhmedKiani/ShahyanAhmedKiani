import os
import requests

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
    return repos

def aggregate_languages(repos):
    lang_bytes = {}
    for repo in repos:
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        res = requests.get(lang_url, headers=HEADERS)
        if res.status_code == 200:
            for lang, size in res.json().items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + size
    return lang_bytes

def generate_stats_md(lang_bytes):
   def generate_stats_md(lang_bytes):
    total = sum(lang_bytes.values())
    if total == 0:
        return "📊 No language data found."

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
    
    # Mermaid pie chart syntax
    lines = ["## 📊 Language Stats", "", "```mermaid", "pie showData", "title Code Language Distribution"]
    
    for lang, size in sorted_langs:
        pct = (size / total) * 100
        if pct >= 1.0:  # Show languages with >=1% usage
            # Escape special chars in language names for Mermaid
            safe_lang = lang.replace('"', '\\"')
            lines.append(f'    "{safe_lang}" : {pct:.1f}')
    
    lines.extend(["```", ""])
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
    print(f"📦 Found {len(repos)} repositories.")
    print("🌐 Calculating language stats...")
    lang_bytes = aggregate_languages(repos)
    md = generate_stats_md(lang_bytes)
    update_readme(md)
    print("✅ README updated successfully!")
