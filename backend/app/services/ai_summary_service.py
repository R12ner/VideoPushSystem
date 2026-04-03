import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib import error, request


class AISummaryService:
    def __init__(self):
        app_dir = Path(__file__).resolve().parents[1]
        self.cache_dir = app_dir / "static" / "ai_summaries"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = os.getenv(
            "ZHIPU_API_URL",
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        )
        self.model = os.getenv("ZHIPU_MODEL", "glm-4-flash-250414")

    def summarize_video(self, video, force_refresh=False):
        cache_path = self.cache_dir / f"{video.id}.json"
        if cache_path.exists() and not force_refresh:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            cached["cached"] = True
            return cached

        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("未配置 ZHIPU_API_KEY")

        transcript = self._load_transcript(video.subtitle_url)
        prompt_payload = self._build_prompt(video, transcript)

        summary = self._call_zhipu(api_key, prompt_payload)
        result = {
            "summary": summary,
            "source": "subtitle" if transcript else "metadata",
            "model": self.model,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "cached": False,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def _build_prompt(self, video, transcript):
        meta_lines = [
            f"标题：{video.title}",
            f"分类：{video.category or '未分类'}",
            f"标签：{video.tags or '无'}",
            f"简介：{video.description or '无'}",
            f"时长：{video.duration or 0} 秒",
        ]

        if transcript:
            transcript = transcript[:6000]
            source_hint = "以下是视频字幕内容，请以字幕为主进行总结。"
            content_block = f"字幕内容：\n{transcript}"
        else:
            source_hint = "该视频没有可用字幕，请严格基于元数据进行总结，并明确说明总结依据有限。"
            content_block = "无字幕内容。"

        user_prompt = (
            "请你为一个视频页面生成中文 AI 总结，要求：\n"
            "1. 只输出纯文本，不要使用 Markdown 标题符号。\n"
            "2. 总结分为三部分，每部分都要保留小标题：\n"
            "   核心内容：2-3 句。\n"
            "   关键要点：3 条，每条一行。\n"
            "   观看建议：1-2 句。\n"
            "3. 如果信息不足，不要编造事实，要明确说明依据来自标题、简介、标签或字幕。\n\n"
            f"{source_hint}\n\n"
            + "\n".join(meta_lines)
            + "\n\n"
            + content_block
        )

        return {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个严谨的视频内容总结助手，擅长输出简洁、准确、可直接展示给用户的中文总结。",
                },
                {"role": "user", "content": user_prompt},
            ],
        }

    def _call_zhipu(self, api_key, payload):
        req = request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=90) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"智谱接口调用失败：{detail}") from exc
        except Exception as exc:
            raise ValueError(f"智谱接口调用失败：{exc}") from exc

        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("智谱接口返回格式异常") from exc

    def _load_transcript(self, subtitle_url):
        if not subtitle_url:
            return ""

        relative_path = subtitle_url.split("?", 1)[0].lstrip("/").replace("/", os.sep)
        base_dir = Path(__file__).resolve().parents[1]
        subtitle_path = base_dir / relative_path.replace("static" + os.sep, "static" + os.sep, 1)

        if not subtitle_path.exists():
            return ""

        with open(subtitle_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return self._clean_subtitle(content)

    def _clean_subtitle(self, raw_text):
        lines = []
        for line in raw_text.splitlines():
            text = line.strip()
            if not text:
                continue
            if text.upper() == "WEBVTT":
                continue
            if re.match(r"^\d+$", text):
                continue
            if "-->" in text:
                continue
            if text.startswith("NOTE"):
                continue
            lines.append(text)

        cleaned = " ".join(lines)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned


ai_summary_service = AISummaryService()
