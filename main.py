"""SHAM: оригинальные мемы -> картинка -> VK. Секреты только из окружения."""
import argparse
import hashlib
import json
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
from meme_bank import PACKS
from hashtags import create_tags, add_hashtags

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "state" / "history.json"
OUT = ROOT / "output"
GROUP_ID = 243230846
VK_API = "https://api.vk.com/method/"
VK_VERSION = "5.199"

# Авторские офлайн-шутки на случай отсутствия AI API. Использованные не повторяем.
JOKES = [
    ("Я: с понедельника новая жизнь", "Понедельник: а меня кто-нибудь спрашивал?", "Ну и ладно, попробуем со вторника.", "life"),
    ("Зарплата пришла", "И сразу ушла. Нормальные отношения на расстоянии.", "Деньги хотя бы попрощались бы.", "wallet"),
    ("Лёг спать пораньше", "В 03:17 мозг открыл архив позора.", "Спасибо за воспоминания, урод.", "phone"),
    ("Сказал на работе: «это быстро»", "Поздравляю, теперь это твоя должность.", "Нельзя показывать, что ты умеешь работать.", "work"),
    ("Когда открыл холодильник в третий раз", "Еда всё ещё не заспавнилась.", "Патч для холодильника где?", "home"),
    ("Решил копить деньги", "Банковское приложение посмеялось первым.", "Новая цель: дожить до пятницы.", "wallet"),
    ("Написал: «я уже выхожу»", "Начал искать второй носок.", "Транспорт, подожди, я в процессе.", "life"),
    ("Скачал приложение для продуктивности", "Три часа выбирал красивую тему.", "Теперь официально продуктивный.", "work"),
    ("Когда попросили быть самим собой", "А потом сказали: «нет, не настолько».", "Сами определитесь уже.", "social"),
    ("Планы на выходные: отдыхать", "Реальность: восстанавливаться после отдыха.", "Я устал от концепции понедельника.", "life"),
    ("Взял телефон на минутку", "На улице уже другая историческая эпоха.", "Скоро буду. Ещё один видос.", "phone"),
    ("Купил продукты на неделю", "Съел вкусное за два часа.", "Осталась гречка и самоуважение.", "home"),
    ("Мотивация в 02:00", "Утром даже зарядку от телефона не нашёл.", "Ночью я гений. Утром — мебель.", "life"),
    ("Меня спросили, как дела", "Я открыл приложение банка.", "Ответ получился документальным.", "wallet"),
    ("Решил меньше сидеть в соцсетях", "Соцсети: а кто наши уведомления прочитает?", "Цифровой детокс длился 4 минуты.", "social"),
    ("Рабочий созвон: «буквально пять минут»", "Дети уже выросли, а он всё идёт.", "Я теперь член этой конференции по наследству.", "work"),
    ("Пришёл за одной вещью в магазин", "Вышел с пакетом и вопросами к себе.", "Куда ушли деньги — отдельное расследование.", "wallet"),
    ("Я хотел быть загадочным", "Получилось просто не отвечать на сообщения.", "Гениальная стратегия общения.", "social"),
    ("Понял, что стал взрослым", "Обрадовался новой губке для посуды.", "Какой же я теперь опасный тип.", "home"),
    ("Отключил будильник", "И открыл портал в параллельный рабочий день.", "Ещё пять минут — заклинание хаоса.", "life"),
    ("Написал в чат «понял»", "Не понял вообще ничего.", "Главное — уверенная пунктуация.", "work"),
    ("Заказал еду и решил не смотреть доставку", "Обновил карту уже сорок раз.", "Курьер, брат, я верю в тебя.", "phone"),
    ("Включил режим экономии", "Но не для денег. Для нервной системы.", "Батарейка личности — 3%.", "life"),
    ("Пришёл на кухню за чем-то", "Забыл зачем. Зато открыл холодильник.", "Мозг: квест без маркера.", "home"),
    ("Новый месяц — новый я", "Старый я: дай хотя бы кофе допить.", "Перерождение откладывается.", "life"),
    ("Попросили скинуть резюме", "Скинул список пережитых понедельников.", "Стрессоустойчивость подтверждена.", "work"),
    ("Когда кто-то пишет «надо поговорить»", "Мозг уже нанял адвоката.", "Сообщение из пяти слов — паника на три сезона.", "social"),
    ("Увидел скидку 70%", "Купил то, что не хотел даже бесплатно.", "Экономика меня боится.", "wallet"),
    ("Я не ленивый", "Я в энергосберегающем режиме без зарядки.", "Производитель не положил адаптер.", "life"),
    ("Сделал уборку на столе", "Нашёл квитанцию из прошлой жизни.", "Археология за бесплатно.", "home"),
    ("На созвоне сказали: «есть один вопрос»", "Открыли презентацию на 86 слайдов.", "Отложите мою старость на полчаса.", "work"),
    ("Решил не проверять сообщения", "Открыл мессенджер проверить, не проверял ли.", "Вот и весь мой самоконтроль.", "phone"),
    ("Был уверен, что сегодня пятница", "Календарь: милый, сегодня вторник.", "Самое жестокое кино года.", "life"),
    ("Список дел на день", "1. Выжить. 2. Не обсуждается.", "Галочку за первый пункт вечером поставлю.", "work"),
    ("Купил дорогой кофе для бодрости", "Теперь бодрый и без денег.", "Баланс восстановлен.", "wallet"),
    ("Когда Wi-Fi завис на секунду", "Почувствовал дыхание каменного века.", "Так вот как жили предки.", "phone"),
]

PALETTES = [
    ((20, 9, 42), (95, 28, 128), (218, 255, 59)),
    ((12, 20, 39), (16, 93, 112), (255, 215, 63)),
    ((42, 12, 29), (128, 37, 71), (150, 251, 250)),
    ((21, 13, 57), (98, 55, 193), (255, 223, 70)),
]


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
    text = re.sub(r"\s+", " ", post["top"].lower() + " " + post["bottom"].lower()).strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_slot():
    now = datetime.now(timezone.utc)
    # График каждые 15 минут, 96 слотов в UTC за сутки.
    return f"{now.date().isoformat()}-{now.hour:02d}-{now.minute // 15:02d}"


def generate_post(state, slot):
    """Бесплатная генерация — выбор новой комбинации из тематического банка."""
    used = {entry["id"] for entry in state.get("posts", []) if "id" in entry}
    rng = random.Random(slot + "-SHAM-free-v3")
    packs = list(PACKS)
    rng.shuffle(packs)
    for pack in packs:
        # Перемешиваем целые пары, исключаем уже публиковавшиеся.
        combinations = [(a, b) for a in pack["setups"] for b in pack["punchlines"]]
        rng.shuffle(combinations)
        for top, bottom in combinations:
            post = {"top": top, "bottom": bottom,
                    "caption": rng.choice(pack["captions"]),
                    "scene": pack["scene"]}
            if identity(post) not in used:
                return post

    # Дополнительный банк из полностью написанных шуток.
    standalone = list(JOKES)
    rng.shuffle(standalone)
    for top, bottom, caption, scene in standalone:
        post = {"top": top, "bottom": bottom, "caption": caption, "scene": scene}
        if identity(post) not in used:
            return post
    raise RuntimeError(
        "Банк оригинальных мемов исчерпан. Добавьте новые шаблоны в meme_bank.py. "
        "Повторы не публикуем."
    )


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


def local_background(post, seed):
    rng = random.Random(seed)
    a, b, acid = rng.choice(PALETTES)
    im = Image.new("RGB", (1080, 1080), a)
    d = ImageDraw.Draw(im)
    for y in range(1080):
        k = y / 1080
        d.line((0, y, 1080, y), fill=tuple(int(a[i] * (1-k) + b[i] * k) for i in range(3)))
    for i in range(44):
        x, y = rng.randrange(1080), rng.randrange(180, 900)
        r = rng.randrange(5, 65)
        d.ellipse((x-r, y-r, x+r, y+r), outline=rng.choice([(136, 72, 235), (246, 60, 153), acid]), width=rng.randrange(2, 8))
    # Оригинальная иллюстрация-реакция: лицо + тематический предмет.
    d.ellipse((245, 315, 835, 915), fill=acid, outline=(9, 9, 20), width=24)
    d.arc((341, 437, 506, 547), 190, 350, fill=(10, 10, 19), width=25)
    d.arc((557, 437, 724, 547), 190, 350, fill=(10, 10, 19), width=25)
    d.arc((355, 560, 725, 784), 15, 160, fill=(10, 10, 19), width=34)
    icon = post["scene"]
    if icon == "phone":
        d.rounded_rectangle((730, 493, 918, 762), radius=25, fill=(28, 32, 48), outline=(250, 249, 252), width=9)
        d.rounded_rectangle((758, 525, 891, 714), radius=12, fill=(123, 94, 248))
        d.ellipse((809, 728, 838, 750), fill=acid)
    elif icon == "wallet":
        d.rounded_rectangle((721, 598, 975, 769), radius=26, fill=(40, 26, 63), outline=(248, 247, 250), width=8)
        d.rounded_rectangle((816, 629, 965, 705), radius=18, fill=(250, 67, 141))
        d.ellipse((847, 653, 879, 686), fill=(255, 242, 70))
    elif icon == "work":
        d.rounded_rectangle((717, 579, 1006, 765), radius=15, fill=(23, 31, 57), outline=(251, 248, 255), width=10)
        d.line((734, 741, 990, 741), fill=(175, 110, 255), width=8)
        d.text((748, 629), "!!!", font=font(72), fill=(255, 65, 134))
    elif icon == "home":
        d.polygon([(749, 590), (858, 496), (977, 596)], fill=(250, 84, 161))
        d.rectangle((782, 590, 947, 767), fill=(35, 33, 64))
        d.rectangle((844, 647, 897, 767), fill=(255, 216, 64))
    elif icon == "social":
        d.rounded_rectangle((728, 528, 988, 728), radius=43, fill=(24, 22, 42), outline=(248, 248, 250), width=8)
        d.text((762, 575), "???", font=font(75), fill=(248, 85, 149))
    else:
        for j in range(3):
            x = 754 + j*76
            d.line([(x-22, 611), (x+16, 681), (x-18, 681), (x+30, 745)], fill=(252, 79, 145), width=14, joint="curve")
    return im



def make_image(post, slot):
    seed = int(hashlib.sha256(slot.encode("utf-8")).hexdigest()[:8], 16)
    image = local_background(post, seed)
    d = ImageDraw.Draw(image, "RGBA")
    d.rectangle((0, 0, 1080, 300), fill=(5, 5, 12, 230))
    d.rectangle((0, 785, 1080, 1080), fill=(5, 5, 12, 237))
    d.rectangle((0, 295, 1080, 308), fill=(225, 255, 58, 255))
    d.text((51, 26), "SHAM / МЕМЫ БЕЗ ТОРМОЗОВ", font=font(27), fill=(219, 255, 74, 255))
    centered_text(d, post["top"], 74, 291, (255, 255, 255, 255), 68)
    centered_text(d, post["bottom"], 807, 1030, (220, 255, 63, 255), 71)
    d.text((1005, 1048), "@SHAM", font=font(22), anchor="ra", fill=(194, 187, 218, 255))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "sham_meme.png"
    image.save(path, "PNG", optimize=True)
    return path


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
    parser.add_argument("--publish", action="store_true", help="Публикация (при PUBLISH_ENABLED=true)")
    args = parser.parse_args()
    if args.preview == args.publish:
        parser.error("Выберите --preview или --publish")
    state = get_state()
    slot = current_slot()
    if args.publish and os.getenv("SHAM_PAUSED", "").strip().lower() == "true":
        print("SHAM_PAUSED=true: публикация отключена оператором.")
        return
    if args.publish and os.getenv("PUBLISH_ENABLED", "").strip().lower() != "true":
        print("PUBLISH_ENABLED != true: публикация отключена.")
        return
    if args.publish and slot in state["slots"]:
        print(f"Слот {slot} уже обработан; пропуск.")
        return
    backend = os.getenv("SHAM_BACKEND", "vk").strip().lower()
    if backend not in ("vk", "vedismm"):
        raise RuntimeError("SHAM_BACKEND должен быть vk или vedismm")
    if args.publish and backend == "vk" and not os.getenv("VK_USER_TOKEN", "").strip():
        raise RuntimeError("Нужен VK_USER_TOKEN или переключите SHAM_BACKEND=vedismm; стена не изменена")
    if args.publish and backend == "vedismm" and not os.getenv("VEDISMM_TOKEN", "").strip():
        raise RuntimeError("Нужен VEDISMM_TOKEN (GitHub Actions Secret); стена не изменена")
    post = generate_post(state, slot)
    tags = create_tags(post["scene"], state, slot)
    message = add_hashtags(post["caption"], tags)
    image = make_image(post, slot)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "preview.json").write_text(
        json.dumps({**post, "hashtags": tags, "message": message}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("Мем:", post["top"], "—", post["bottom"])
    print("Подпись:", message)
    print("Картинка:", image)
    if args.preview:
        print("Режим предпросмотра: в VK ничего не отправлено.")
        return
    if backend == "vedismm":
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
                           "slot": slot, **publication})
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if publication["publication_status"] == "published":
        print(f"Опубликовано: {publication['vk_url']}")
    else:
        print(f"Поставлено в очередь ВедиSMM (НЕ подтверждено ВК): {publication['vedismm_job_id']}")


if __name__ == "__main__":
    main()
