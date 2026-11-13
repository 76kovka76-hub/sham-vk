"""Original short current-life jokes paired to rights-cleared Soviet film frames.

Not original movie dialogue. No verbatim copy of contemporary internet memes.
Use one Soviet still or a two-still collage; keep mobile readable and coherent.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Joke:
    key:str
    format:str
    source_ids:tuple[str,...]
    top:str
    bottom:str
    caption:str
    theme:str

def j(key,fmt,sources,top,bottom,caption,theme):
    assert fmt in ("single","collage")
    assert len(sources)==(1 if fmt=="single" else 2)
    assert top and bottom and len(bottom)<120
    return Joke(key,fmt,tuple(sources),top,bottom,caption,theme)


JOKES=[
    j("price_shock","single",("aelita_face",),
      "ЗАШЁЛ ЗА ХЛЕБОМ","В ЧЕКЕ ОБНАРУЖИЛ ИПОТЕКУ.",
      "С такими ценами скоро в магазин будут пускать только с поручителем.","деньги"),
    j("bank_suspects","single",("aelita_batalov",),
      "ОТКРЫЛ ПРИЛОЖЕНИЕ БАНКА","БАНК СПРОСИЛ, ВСЁ ЛИ СО МНОЙ ХОРОШО.",
      "Баланс увидел — и сам хотел спросить.","деньги"),
    j("boss_friday","single",("potemkin_2",),
      "ПЯТНИЦА. 17:59.","НАЧАЛЬНИК: «ЕСТЬ МАЛЕНЬКАЯ ЗАДАЧКА».",
      "Мои выходные уже собрали чемоданы.","работа"),
    j("monday_attacks","single",("potemkin_5",),
      "КОГДА НАСТУПИЛ ПОНЕДЕЛЬНИК","А У ТЕБЯ ЕЩЁ СУББОТА НЕ ЗАКОНЧИЛАСЬ.",
      "Понедельник, бл***ь, откуда ты взялся?","жизнь"),
    j("alarm_ambush","single",("potemkin_6",),
      "БУДИЛЬНИК В 06:00","Я: МЫ ЖЕ ВЧЕРА ДОГОВОРИЛИСЬ!",
      "Операция «встать с кровати» снова провалена.","сон"),
    j("group_chat","single",("potemkin_soldati",),
      "ЗАШЁЛ В СЕМЕЙНЫЙ ЧАТ","ЗА 5 МИНУТ УЖЕ ПЕРЕРУГАЛИСЬ ВСЕ.",
      "Я просто хотел узнать рецепт салата.","общение"),
    j("salary_and_bills","collage",("aelita_batalov","aelita_face"),
      "КОГДА ПРИШЛА ЗАРПЛАТА","КОГДА ПРИШЛИ КОММУНАЛЬНЫЕ.",
      "Порадовался деньгам ровно до второго уведомления.","деньги"),
    j("discount_battle","single",("potemkin_ship",),
      "УВИДЕЛ СКИДКУ 90%","НАЧАЛАСЬ БИТВА ЗА ПОСЛЕДНЮЮ СКОВОРОДКУ.",
      "Сходил в магазин. Вернулся ветераном распродажи.","покупки"),
    j("workday_march","collage",("potemkin_2","potemkin_soldati"),
      "УТРОМ: Я ВСЁ УСПЕЮ.","ВЕЧЕРОМ: КТО МЫ? ГДЕ МЫ?",
      "На работе прошёл весь квест, а зарплата всё ещё на первом уровне.","работа"),
    j("sleepy_math","single",("potemkin_5",),
      "ЛЯГУ СПАТЬ ПОРАНЬШЕ","03:47. ЧИТАЮ, КАК СПЯТ МУРАВЬИ.",
      "По уровню знаний я профессор. По уровню сна — ноль.","сон"),
    j("delivery_nerves","single",("potemkin_6",),
      "КУРЬЕР: «УЖЕ ПОДЪЕЗЖАЮ».","НА КАРТЕ ОН ЕЩЁ В ДРУГОЙ ЭПОХЕ.",
      "Наблюдаю маршрут курьера как исторический сериал.","еда"),
    j("social_typing","single",("aelita_face",),
      "ОН ПЕЧАТАЕТ УЖЕ 40 МИНУТ.","ОТВЕТ: «ОК».",
      "Такое напряжение даже кино не выдержит.","общение"),
    j("utility_bill","single",("aelita_batalov",),
      "ПОЛУЧИЛ СЧЁТ ЗА СВЕТ.","ТЕПЕРЬ БОЮСЬ ВКЛЮЧАТЬ МЫСЛИ.",
      "Экономия дошла до режима внутренней подсветки.","деньги"),
    j("wifi_family","collage",("aelita_batalov","potemkin_2"),
      "ОТКЛЮЧИЛСЯ ИНТЕРНЕТ.","ПРИШЛОСЬ ЗНАКОМИТЬСЯ С СОСЕДЯМИ.",
      "Оказывается, люди рядом тоже существуют.","жизнь"),
]
assert len({x.key for x in JOKES})==len(JOKES)
