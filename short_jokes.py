"""Short, independently rewritten SHAM mini-jokes inspired by common online
anecdote genres. They are NOT verbatim copied internet jokes or existing memes.
Each has one tightly matching visual slapstick setup, not an unrelated portrait.
"""
def joke(key, scene, top, bottom, caption, visual):
    assert len(top)>=15 and len(bottom)>=20
    return dict(topic="mini_"+key,scene=scene,top=top,bottom=bottom,
                caption=caption,visual=visual)


SHORT_JOKES=[
    joke("salary_escape","wallet","Зарплата пришла утром.","К вечеру уже попросила не искать её.","Деньги умеют уходить без прощаний.","Shocked employee watches paper money sprout tiny legs and run out of an open wallet across messy kitchen table"),
    joke("bread_receipt","wallet","Пришёл в магазин за хлебом.","На кассе предложили оформить ипотеку.","Вроде хлеб, а чек как на квартиру.","A shocked shopper holding only one loaf of bread while cashier hands a ridiculously long paper receipt coiling around the whole checkout"),
    joke("alarm_court","life","Будильник поднял меня с кровати.","Подушка подала на него в суд.","С утра уже идёт заседание.","Groggy adult in pajamas watches angry pillow dressed as a judge interrogate tiny alarm clock on bedroom table, absurd morning scene"),
    joke("wifi_family","home","На час отключили интернет.","Узнал, что дома живут ещё трое.","Оказались вполне приличные люди.","Family of four sit around kitchen table staring at each other in surprise as dead wifi router lies on back like a broken robot"),
    joke("fridge_watchman","home","Открыл холодильник шестой раз.","Кетчуп спросил, не нужен ли пропуск.","Сменился охранник холодильника.","Hungry man staring into nearly empty fridge where a little ketchup bottle wears security guard cap and guards a single ice cube"),
    joke("boss_five","work","Начальник попросил пять минут.","К концу разговора я успел поседеть.","В офисе время течёт иначе.","Young employee ages into an old gray-bearded man with cobwebs while endless video call continues on laptop, office clock spinning"),
    joke("cat_promotion","work","Кот случайно нажал клавиатуру.","Ему сразу предложили повышение.","Я работал пять лет, между прочим.","Fat smug cat in suit sits in office boss chair behind a laptop while human employee holds cardboard box of office belongings"),
    joke("delivery_tour","home","Курьер уже десять минут рядом.","Кажется, он проводит экскурсию по району.","Знаю каждый поворот по карте.","Hungry adult studies gigantic phone courier map with binoculars; tiny delivery cyclist loops around same building while pizza sits far away"),
    joke("typing_marathon","social","В переписке полчаса пишут ответ.","Пришло одно торжественное «ок».","Очень содержательные переговоры.","Anxious adult glued to smartphone as giant three typing dots hold a dramatic award ceremony and wall clocks fall from ceiling"),
    joke("voice_podcast","social","Друг прислал голосовое сообщение.","На седьмой минуте закончил здороваться.","Похоже, я подписался на подкаст.","Tired person with long gray beard in an armchair listening to phone voice message while calendar sheets and used coffee cups pile up"),
    joke("gym_hurt","life","Первый раз пошёл в спортзал.","На выходе меня обогнала швабра.","Тело не поддержало инициативу.","Exhausted adult crawling out of gym, a cheerful mop overtakes him and tiny dumbbell flexes cartoon muscles, exaggerated physical comedy"),
    joke("wardrobe_clean","home","Решил разобрать шкаф за полчаса.","Откопал провода от телефона 2007 года.","Археологи мной гордятся.","Adult dressed like archaeologist finds an enormous mountain of tangled old phone wires spilling from small wardrobe in cluttered bedroom"),
    joke("subscription_family","wallet","Проверил свои платные подписки.","Оказалось, содержу целый сериал сервисов.","Не зря же у меня нет денег.","Man at kitchen table shocked as a parade of tiny smartphones wearing subscription service badges drains coins from wallet"),
    joke("weekend_time","life","Утром в субботу решил отдохнуть.","Моргнул — уже воскресенье вечер.","Хочется попросить перемотку назад.","Person sitting on couch while gigantic calendar monster swallows Saturday and Sunday pages, bewildered man holds remote control"),
    joke("rental_balcony","wallet","Посмотрел цену аренды комнаты.","По фотографии там помещается только чайник.","Зато вид на соседний чайник.","Shocked tenant looking at computer listing of absurdly tiny apartment where giant teapot occupies the entire room and a chair sticks out of window"),
    joke("mail_swarm","work","Проверил рабочую почту на минуту.","Теперь письма преследуют меня в лифте.","Всего лишь хотел посмотреть погоду.","Office employee fleeing a swarm of angry living paper envelopes with teeth and tiny arms down elevator hallway"),
    joke("phone_battery","phone","У телефона осталось 1% заряда.","Навигатор решил оставить меня в лесу.","Будем искать дорогу по звёздам.","Adult in city park holds dead phone while tiny GPS arrow sprouts legs and runs away, anxious expression, confusing winding paths"),
    joke("todo_one","life","Написал список дел на сегодня.","Выполнил только пункт «написать список».","Главное — начать с победы.","Proud exhausted adult celebrates one giant check mark on absurdly long to-do list wrapping around kitchen, other dozens of boxes empty"),
]
assert len(SHORT_JOKES)==18
assert len({x["topic"] for x in SHORT_JOKES})==len(SHORT_JOKES)
