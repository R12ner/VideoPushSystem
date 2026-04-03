import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib import error, request

import cv2


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
        self.vision_model = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")

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
        frame_descriptions = self._describe_video_frames(api_key, video.url)

        prompt_payload = self._build_summary_prompt(
            video=video,
            transcript=transcript,
            frame_descriptions=frame_descriptions,
        )
        summary = self._call_chat_completion(api_key, prompt_payload)

        sources = ["metadata"]
        if transcript:
            sources.insert(0, "subtitle")
        if frame_descriptions:
            sources.insert(0, "frames")

        result = {
            "summary": summary,
            "source": "+".join(sources),
            "model": self.model,
            "vision_model": self.vision_model if frame_descriptions else "",
            "frame_descriptions": frame_descriptions,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "cached": False,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def _build_summary_prompt(self, video, transcript, frame_descriptions):
        meta_lines = [
            f"标题：{video.title}",
            f"分类：{video.category or '未分类'}",
            f"标签：{video.tags or '无'}",
            f"简介：{video.description or '无'}",
            f"时长：{video.duration or 0} 秒",
        ]

        blocks = ["视频基础信息：", *meta_lines]

        if transcript:
            blocks.extend(
                [
                    "",
                    "字幕内容（可能已截断，请优先参考）：",
                    transcript[:6000],
                ]
            )
        else:
            blocks.extend(
                [
                    "",
                    "字幕内容：",
                    "无可用字幕，请不要编造字幕细节。",
                ]
            )

        if frame_descriptions:
            frame_lines = [
                f"第 {item['index']} 帧：{item['description']}"
                for item in frame_descriptions
            ]
            blocks.extend(["", "视频抽帧视觉分析：", *frame_lines])
        else:
            blocks.extend(["", "视频抽帧视觉分析：", "未能获取有效帧分析结果。"])

        user_prompt = (
            "请你根据给定的视频标题、简介、标签、字幕和抽帧分析结果，输出一个中文 AI 总结。\n"
            "要求如下：\n"
            "1. 只输出纯文本，不要使用 Markdown 代码块。\n"
            "2. 输出三部分，并保留以下小标题：核心内容、关键要点、观看建议。\n"
            "3. 核心内容写 2-3 句；关键要点写 3 条，每条单独一行；观看建议写 1-2 句。\n"
            "4. 优先使用字幕和视觉分析信息；如果信息不足，必须明确说明依据有限，不要编造事实。\n"
            "5. 如果抽帧分析与标题简介存在差异，以更稳妥、更不夸张的表述为准。\n\n"
            + "\n".join(blocks)
        )

        return {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个严谨的视频内容总结助手，擅长输出准确、克制、适合直接展示给用户的中文总结。",
                },
                {"role": "user", "content": user_prompt},
            ],
        }

    def _describe_video_frames(self, api_key, video_url):
        encoded_frames = self._extract_keyframes(video_url)
        if not encoded_frames:
            return []

        results = []
        for idx, encoded in enumerate(encoded_frames, start=1):
            try:
                description = self._call_vision_completion(api_key, encoded)
            except Exception:
                continue

            if description:
                results.append({"index": idx, "description": description})

        return results

    def _extract_keyframes(self, video_url, max_frames=3):
        video_path = self._resolve_static_path(video_url)
        if not video_path or not video_path.exists():
            return []

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return []

        ratios = [0.15, 0.5, 0.85][:max_frames]
        encoded_frames = []

        try:
            for ratio in ratios:
                target_frame = min(max(int(total_frames * ratio), 0), max(total_frames - 1, 0))
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                success, frame = cap.read()
                if not success or frame is None:
                    continue

                success, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 75],
                )
                if not success:
                    continue

                encoded_frames.append(base64.b64encode(buffer.tobytes()).decode("utf-8"))
        finally:
            cap.release()

        return encoded_frames

    def _call_vision_completion(self, api_key, encoded_image):
        payload = {
            "model": self.vision_model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个视频画面分析助手，负责客观描述单帧画面中可明确观察到的内容。",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "请用中文简要描述这张视频抽帧画面中可以明确看出的主体、场景、动作和氛围。"
                                "只描述能直接观察到的内容，不要猜测剧情。控制在 2 句内。"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            },
                        },
                    ],
                },
            ],
        }
        return self._call_chat_completion(api_key, payload).strip()

    def _call_chat_completion(self, api_key, payload):
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
        subtitle_path = self._resolve_static_path(subtitle_url)
        if not subtitle_path or not subtitle_path.exists():
            return ""

        with open(subtitle_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if subtitle_path.suffix.lower() == ".json":
            return self._parse_json_subtitle(content)

        return self._clean_subtitle(content)

    def _resolve_static_path(self, media_url):
        if not media_url:
            return None

        relative_path = media_url.split("?", 1)[0].lstrip("/")
        if not relative_path.startswith("static/"):
            return None

        base_dir = Path(__file__).resolve().parents[1]
        return base_dir / relative_path.replace("/", os.sep)

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

    def _parse_json_subtitle(self, raw_text):
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return self._clean_subtitle(raw_text)

        texts = []
        self._collect_subtitle_texts(data, texts)
        cleaned = " ".join(texts)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _collect_subtitle_texts(self, value, texts):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                texts.append(stripped)
            return

        if isinstance(value, list):
            for item in value:
                self._collect_subtitle_texts(item, texts)
            return

        if not isinstance(value, dict):
            return

        preferred_keys = [
            "text",
            "content",
            "subtitle",
            "transcript",
            "sentence",
            "line",
            "words",
            "caption",
            "value",
        ]

        for key in preferred_keys:
            if key in value:
                self._collect_subtitle_texts(value[key], texts)

        for nested_key, nested_value in value.items():
            if nested_key in preferred_keys:
                continue
            if isinstance(nested_value, (dict, list)):
                self._collect_subtitle_texts(nested_value, texts)


ai_summary_service = AISummaryService()
