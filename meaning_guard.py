"""Fast, deterministic near-meaning guard for SHAM's Russian jokes.

This is not a language model: explicit premise groups catch rewritten versions
of the same gag, and conservative token similarity catches close paraphrases.
We prefer missing a slot over recycling a stale premise.
"""
import re

ALIASES = {
    "salary_escape": "salary_disappears",
    "salary_fugitive": "salary_disappears",
    "salary": "salary_disappears",
    "bread_receipt": "groceries_expensive",
    "grocery_total": "groceries_expensive",
    "alarm_court": "alarm_war",
    "alarm_boss": "alarm_war",
    "alarm": "alarm_war",
    "wifi_family": "offline_family",
    "internet_mummy": "offline_family",
    "fridge_watchman": "empty_fridge",
    "fridge_union": "empty_fridge",
    "fridge": "empty_fridge",
    "boss_five": "endless_meeting",
    "five_minute_meeting": "endless_meeting",
    "meeting_meteor": "endless_meeting",
    "delivery_tour": "delivery_delay",
    "delivery_space": "delivery_delay",
    "delivery": "delivery_delay",
    "typing_marathon": "typing_delay",
    "typing": "typing_delay",
    "voice_podcast": "long_voice_message",
    "voice_messages": "long_voice_message",
    "gym_hurt": "gym_exhaustion",
    "fitness": "gym_exhaustion",
    "subscription_family": "subscriptions",
    "subscription_zoo": "subscriptions",
    "subscriptions": "subscriptions",
    "weekend_time": "weekend_disappears",
    "weekend": "weekend_disappears",
    "rental_balcony": "ridiculous_rent",
    "rent_coffin": "ridiculous_rent",
    "rent": "ridiculous_rent",
    "mail_swarm": "email_overload",
    "after_vacation": "email_overload",
    "phone_battery": "dead_phone",
    "battery": "dead_phone",
    "todo_one": "todo_list",
    "to_do": "todo_list",
    "groupchat_apocalypse": "group_chat",
    "groupchat": "group_chat",
    "notifications": "group_chat",
    "ai_boss": "ai_manager",
    "robot_hr": "ai_manager",
    "bank_therapy": "bank_balance",
    "algorithm_funeral": "ads_algorithm",
    "ai_resume": "ai_resume",
    "smart_home": "smart_home",
    "toilet_ai": "smart_home",
    "neighbor_drill": "neighbor_noise",
    "printer_hell": "printer_hell",
    "pigeon_landlord": "pigeon_landlord",
    "vacation_robot": "work_robot",
    "monday_police": "monday",
    "career_ladder": "career",
}
STOP = frozenset((
    "сегодня вчера завтра опять теперь потом когда чтобы меня тебе ему она они нас"
    " меня моя мой мои меня этом этот того уже только даже просто очень вообще"
    " который которая почему потому потом было были будет есть вот как где что"
    " чего зачем сразу стал стала вроде почти если после перед между через"
    " сейчас меня тебя свой своё свою себе наши ваш еще ещё ну да ну а и в на"
    " не за по до от из у о с к для об это я ты вы мы он она оно без всё все"
    " или либо но то бы же ведь ли вот мой мне там тут так"
).split())
SFX = ("иями", "ящего", "ащего", "ением", "остями", "ость", "ение", "иями", 
       "ами", "ями", "ого", "ему", "ыми", "ими", "ать", "ять", "ить", "ый",
       "ий", "ая", "яя", "ое", "ее", "ов", "ев", "ах", "ях", "ам", "ям",
       "ые", "ие", "ой", "ей", "ом", "ем", "а", "я", "ы", "и", "у", "ю", "е", "о")


def _tokens(text):
    words = re.findall(r"[а-яёa-z0-9]{3,}", str(text).lower().replace("ё", "е"))
    out = set()
    for word in words:
        if word in STOP:
            continue
        for suffix in SFX:
            if len(word) - len(suffix) >= 4 and word.endswith(suffix):
                word = word[:-len(suffix)]
                break
        if len(word) >= 3:
            out.add(word)
    return out


def idea_group(post):
    topic = str(post.get("topic", ""))
    if topic.startswith("mini_"):
        topic = topic[5:]
    return ALIASES.get(topic, topic)


def lexical_overlap(a, b):
    """Conservative, short-joke-friendly overlap on meaningful words."""
    ta = _tokens(str(a.get("top", "")) + " " + str(a.get("bottom", "")))
    tb = _tokens(str(b.get("top", "")) + " " + str(b.get("bottom", "")))
    if min(len(ta), len(tb)) < 4:
        return 0.0
    common = len(ta & tb)
    return common / min(len(ta), len(tb))


def shares_premise(candidate, prior):
    group = idea_group(candidate)
    earlier = idea_group(prior)
    if group and earlier and group == earlier:
        return True
    return lexical_overlap(candidate, prior) >= 0.72


def recent_meaning_conflict(candidate, history, horizon=12):
    return any(shares_premise(candidate, past) for past in history[-horizon:])
