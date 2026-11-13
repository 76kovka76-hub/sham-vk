"""SHAM: оригинальные мемы -> картинка -> VK. Секреты только из окружения."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import ImageFont
from hashtags import create_tags, add_hashtags

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "state" / "history.json"
OUT = ROOT / "output"
GROUP_ID = 243230846
VK_API = "https://api.vk.com/method/"
VK_VERSION = "5.199"

def get_state():
    if not STATE_PATH.exists():
        return {"posts": [], "slots": []}
    value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("History format error; publishing is stopped")
    value.setdefault("posts", [])
    value.setdefault("slots", [])
    return value


def identity(post):
    from quality_guard import joke_id
    return joke_id(post)


def current_slot():
    now = datetime.now(timezone.utc)
    # График каждые 15 минут, 96 слотов в UTC за сутки.
    return f"{now.date().isoformat()}-{now.hour:02d}-{now.minute // 15:02d}"


def generate_post(state, slot):
    """Return an explicitly approved, coherent meme; never mix random jokes."""
    from quality_guard import select_post
    if os.getenv("SHAM_LIVE_TEXT", "").strip().lower() in ("1", "true", "yes"):
        try:
            from live_jokes import generate_live_post
            return generate_live_post(state, slot)
        except (requests.RequestException, ValueError, RuntimeError, KeyError, TypeError) as exc:
            print("::warning::SHAM free live-text generator unavailable or failed QA; "
                  "falling back to curated original jokes: " + str(exc)[:160], flush=True)
    return select_post(state, slot)


def font(size):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(path, size)


def lines_for(draw, content, face, max_width):
    words, lines, line = content.split(), [], ""
    for word in words:
        new = (line + " " + word).strip()
        if draw.textbbox((0, 0), new, font=face)[2] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = new
    if line:
        lines.append(line)
    return lines


def centered_text(draw, text, y0, y1, color, max_size):
    for s in range(max_size, 25, -2):
        face = font(s)
        lines = lines_for(draw, text, face, 960)
        advance = s * 1.25
        if len(lines) * advance <= (y1 - y0) - 14 and len(lines) <= 4:
            break
    y = y0 + ((y1 - y0) - len(lines) * advance) / 2
    for line in lines:
        box = draw.textbbox((0, 0), line, font=face, stroke_width=3)
        w = box[2] - box[0]
        draw.text(((1080 - w) / 2, y), line, font=face, fill=color,
                  stroke_width=4, stroke_fill=(0, 0, 0))
        y += advance


def make_image(post, slot, state=None, style_override=None):
    visual_style = os.getenv("SHAM_VISUAL_STYLE", "horde").strip().lower()
    if visual_style != "horde":
        raise RuntimeError("SHAM only supports AI Horde realism/anime; Openverse/cartoon disabled")
    from horde_style import make_horde_image
    return make_horde_image(post, slot, OUT, font, centered_text,
                            style_override=style_override, state=state)


def vk_call(method, token, **fields):
    r = requests.post(VK_API + method, data={**fields, "access_token": token, "v": VK_VERSION}, timeout=35)
    r.raise_for_status()
    result = r.json()
    if "error" in result:
        err = result["error"]
        raise RuntimeError(f"VK API {method}: {err.get('error_code')} {err.get('error_msg')}")
    return result["response"]


def publish_vk(image_path, caption, slot):
    # В 2026 загрузка фотографий стены НЕ работает с токеном сообщества.
    # Нужен токен пользователя-администратора с разрешениями wall/photos.
    user_token = os.environ["VK_USER_TOKEN"].strip()
    if not user_token:
        raise RuntimeError("VK_USER_TOKEN is empty")
    upload = vk_call("photos.getWallUploadServer", user_token, group_id=GROUP_ID)
    with image_path.open("rb") as image:
        response = requests.post(upload["upload_url"], files={"photo": ("sham.png", image, "image/png")}, timeout=70)
    response.raise_for_status()
    saved_payload = response.json()
    saved = vk_call("photos.saveWallPhoto", user_token, group_id=GROUP_ID,
                    photo=saved_payload["photo"], server=saved_payload["server"],
                    hash=saved_payload["hash"])
    if not saved:
        raise RuntimeError("VK photo was not saved; post cancelled")
    photo = saved[0]
    attachment = f"photo{photo['owner_id']}_{photo['id']}"
    token = os.getenv("VK_GROUP_TOKEN", "").strip() or user_token
    # Фото обязательно: никогда не публикуем один лишь текст вместо изображения.
    dedup_guid = hashlib.sha256(f"SHAM:{GROUP_ID}:{slot}".encode("utf-8")).hexdigest()[:16]
    result = vk_call("wall.post", token, owner_id=-GROUP_ID, from_group=1,
                     message=caption, attachments=attachment, guid=dedup_guid)
    return result["post_id"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Сделать мем без публикации")
    parser.add_argument("--publish", action="store_true", help="Опубликовать немедленно")
    parser.add_argument("--enqueue", action="store_true", help="Пополнить отложенную очередь ВедиSMM")
    parser.add_argument("--health", action="store_true", help="Проверить выход отложенных записей")
    parser.add_argument("--clean-queue", action="store_true", help="Снять с очереди старые некачественные мемы")
    args = parser.parse_args()
    if sum((args.preview, args.publish, args.enqueue, args.health, args.clean_queue)) != 1:
        parser.error("Выберите один режим: --preview / --publish / --enqueue / --health / --clean-queue")
    state = get_state()
    if args.clean_queue:
        from queue_cleanup import clean_legacy_queue
        result = clean_legacy_queue(state)
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Старые отложенные мемы сняты: {result['unscheduled']}; пропущены: {result['skipped']}")
        for error in result["errors"]:
            print("::error::" + error)
        if result["errors"]:
            raise RuntimeError("Not all legacy queued memes could be safely unscheduled")
        return
    if args.health:
        from queue_health import reconcile_scheduled
        result = reconcile_scheduled(state)
        if result["updated"]:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Отложенные посты проверены: {result['checked']}, обновлены: {result['updated']}.")
        for warning in result["warnings"]:
            print("::warning::SHAM: " + warning)
        if os.getenv("GITHUB_STEP_SUMMARY"):
            summary = [f"### SHAM: проверка отложенных публикаций",
                       f"Проверено: {result['checked']}; обновлено: {result['updated']}."]
            summary.extend("- ⚠️ " + w for w in result["warnings"])
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
                out.write("\n".join(summary) + "\n")
        return
    slot = current_slot()
    scheduled_time = None
    posting = args.publish or args.enqueue
    if posting and os.getenv("SHAM_PAUSED", "").strip().lower() == "true":
        print("SHAM_PAUSED=true: автоматические публикации отключены.")
        return
    if posting and os.getenv("PUBLISH_ENABLED", "").strip().lower() != "true":
        print("PUBLISH_ENABLED != true: публикация отключена.")
        return
    if args.publish and slot in state["slots"]:
        print(f"Слот {slot} уже обработан; пропуск.")
        return
    if args.enqueue:
        from queue_planner import next_missing_slot
        slot, scheduled_time = next_missing_slot(state)
        if slot is None:
            print("Очередь ВедиSMM заполнена на ближайшие 12 часов, пропуск генерации.")
            return
    backend = os.getenv("SHAM_BACKEND", "vk").strip().lower()
    if backend not in ("vk", "vedismm"):
        raise RuntimeError("SHAM_BACKEND должен быть vk или vedismm")
    if args.enqueue and backend != "vedismm":
        raise RuntimeError("Отложенная очередь требует SHAM_BACKEND=vedismm")
    if posting and backend == "vk" and not os.getenv("VK_USER_TOKEN", "").strip():
        raise RuntimeError("Нужен VK_USER_TOKEN или переключите SHAM_BACKEND=vedismm; стена не изменена")
    if posting and backend == "vedismm" and not os.getenv("VEDISMM_TOKEN", "").strip():
        raise RuntimeError("Нужен VEDISMM_TOKEN (GitHub Actions Secret); стена не изменена")
    post = generate_post(state, slot)
    from quality_guard import validate
    validate(post, state["posts"])
    tags = create_tags(post["scene"], state, slot)
    message = add_hashtags(post["caption"], tags)
    qa_style = os.getenv("SHAM_PREVIEW_STYLE", "").strip().lower() if args.preview else ""
    if qa_style == "auto":
        qa_style = ""
    from style_catalog import STYLE_PROMPTS
    if qa_style and qa_style not in STYLE_PROMPTS:
        raise ValueError("SHAM_PREVIEW_STYLE must name a supported visual genre or auto")
    image = make_image(post, slot, state, style_override=qa_style or None)
    source_file = OUT / "image_source.json"
    image_source = json.loads(source_file.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "preview.json").write_text(
        json.dumps({**post, "hashtags": tags, "message": message,
                    "image_source": image_source}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("Мем:", post["top"], "—", post["bottom"])
    print("Подпись:", message)
    print("Картинка:", image)
    if args.preview:
        print("Режим предпросмотра: в VK ничего не отправлено.")
        return
    if args.enqueue:
        from vedismm_publisher import schedule_vedismm
        result = schedule_vedismm(image, message, slot, scheduled_time)
        publication = {"vedismm_post_id": result["post_id"],
                       "scheduled_at": result["scheduled_at"],
                       "publication_status": "scheduled",
                       "vk_url": ""}
    elif backend == "vedismm":
        from vedismm_publisher import publish_vedismm
        result = publish_vedismm(image, message, slot)
        publication = {"vedismm_post_id": result["post_id"],
                       "vedismm_job_id": result["job_id"],
                       "publication_status": result["status"],
                       "vk_url": result["url"]}
    else:
        post_id = publish_vk(image, message, slot)
        publication = {"vk_post_id": post_id, "publication_status": "published",
                       "vk_url": f"https://vk.com/wall-{GROUP_ID}_{post_id}"}
    state["slots"].append(slot)
    state["posts"].append({**post, "id": identity(post), "hashtags": tags,
                           "slot": slot, "quality_version": 3,
                           "image_source": image_source, **publication})
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if publication["publication_status"] == "scheduled":
        print(f"Запланировано в ВедиSMM на {publication['scheduled_at']}: post {publication['vedismm_post_id']}.")
        print("Пост пока НЕ опубликован в ВК: публикация выполнится позднее.")
    elif publication["publication_status"] == "published":
        print(f"Опубликовано: {publication['vk_url']}")
    else:
        print(f"Поставлено в очередь ВедиSMM (НЕ подтверждено ВК): {publication['vedismm_job_id']}")


if __name__ == "__main__":
    main()
