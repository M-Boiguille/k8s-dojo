#!/usr/bin/env python3
"""IA Lead Dev PR review (DeepSeek + GitHub)."""
import json
import os
import re
from pathlib import Path

import openai
import requests
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PR_NUMBER = os.getenv("PR_NUMBER")
REPO = os.getenv("REPO_NAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def load_prompt(prompt_name: str, **placeholders: str) -> str:
    path = Path(f"cli/prompts/{prompt_name}.txt")
    text = path.read_text(encoding="utf-8")
    for key, value in placeholders.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


def _github_headers() -> dict:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_pr_files() -> dict:
    """Récupère les fichiers modifiés et leurs contenus via l'API GitHub."""
    pr_url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
    pr_resp = requests.get(pr_url, headers=_github_headers(), timeout=20)
    pr_resp.raise_for_status()
    pr_info = pr_resp.json()
    head_sha = pr_info["head"]["sha"]

    files_url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    files_resp = requests.get(files_url, headers=_github_headers(), params={"per_page": 100}, timeout=20)
    files_resp.raise_for_status()
    files = files_resp.json()

    entries = []
    for f in files:
        filename = f.get("filename", "")
        if not filename.endswith((".yaml", ".yml")):
            continue
        download_url = f.get("download_url") or f.get("raw_url")
        if not download_url:
            continue
        try:
            content = requests.get(download_url, timeout=20).text
        except Exception:
            content = "<unreachable>"
        entries.append({"filename": filename, "content": content})

    return {"head_sha": head_sha, "files": entries}


def post_comment(body: str) -> None:
    if not GITHUB_TOKEN or not PR_NUMBER or not REPO:
        return
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    try:
        requests.post(url, headers=_github_headers(), json={"body": body}, timeout=20)
    except Exception as exc:
        print(f"⚠️ Impossible de poster le commentaire : {exc}")


def post_check_run(sha: str, score: int, conclusion: str = "neutral") -> None:
    if not GITHUB_TOKEN or not REPO:
        return
    url = f"https://api.github.com/repos/{REPO}/check-runs"
    try:
        requests.post(
            url,
            headers={**_github_headers(), "Accept": "application/vnd.github.antiope-preview+json"},
            json={
                "name": "IA Lead Review",
                "head_sha": sha,
                "status": "completed",
                "conclusion": conclusion,
                "output": {
                    "title": f"Score de confiance : {score}/100",
                    "summary": f"DeepSeek a attribué un score de confiance de **{score}/100**.",
                },
            },
            timeout=20,
        )
    except Exception as exc:
        print(f"⚠️ Impossible de poster le check_run : {exc}")


def main() -> None:
    try:
        files_context = get_pr_files()
    except Exception as exc:
        print(f"⚠️ Impossible de récupérer les fichiers PR: {exc}")
        return

    if not files_context["files"]:
        print("Aucun fichier YAML modifié. Rien à reviewer.")
        return

    system_prompt = load_prompt("system_leaddev", pr_files_content=json.dumps(files_context, indent=2))

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Génère la review au format JSON demandé."},
            ],
            temperature=0.3,
            max_tokens=600,
        )
        raw = response.choices[0].message.content or ""
        review_data = json.loads(_clean_json(raw))
    except Exception as exc:
        print(f"⚠️ IA Review indisponible pour le moment: {exc}")
        post_comment("⚠️ IA Review indisponible pour le moment.")
        return

    positive = review_data.get("positive", "")
    improvements = review_data.get("improvements", [])
    trap = review_data.get("trap_question", "")
    score = int(review_data.get("confidence_score", 0))

    comment = f"""### 🤖 IA Lead Review (Score: {score}/100)

**✅ Positif :** {positive}

**🔧 Améliorations :**
{"".join(f"- {imp}\n" for imp in improvements)}

**❓ Question piège :** {trap}
    """
    post_comment(comment)
    conclusion = "success" if score >= 80 else "neutral"
    post_check_run(files_context["head_sha"], score, conclusion)
    print(comment)


if __name__ == "__main__":
    main()
