"""SKRBL: brief original takes on recognizable short joke/folk-anecdote themes.

No verbatim copies of posts, stand-up material, authored comics or user comments.
Short ideas are rewritten as our own absurd visual gags, designed as one to four
panels instead of forcing a four-panel grid for every joke.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Scene:
    top: str
    visual: str


@dataclass(frozen=True)
class Story:
    id: str
    topic: str
    caption: str
    scenes: tuple[Scene, ...]


def s(title, topic, caption, *panels):
    assert 1 <= len(panels) <= 4
    assert len(caption) >= 20
    return Story(title, topic, caption, tuple(Scene(*p) for p in panels))


STORIES = [
    s("salary_vacuum","money","Зарплата увидела счета и сама полезла обратно в банкомат. Бл***ь. #SKRBL #юмор #карандашныемемы",
      ("ЗАРПЛАТА ПРИШЛА.","Exhausted man in crooked pajamas reaching joyfully to grab a flying bundle of cash while a gigantic vacuum cleaner made from utility bills sucks money straight out of his hands, ridiculous panic in cluttered apartment, comically bulging eyes")),
    s("supermarket_receipt","money","На кассе купил хлеб. В чеке почему-то появилась однушка в ипотеку. #SKRBL #юмор #карандашныемемы",
      ("ЗАШЁЛ ЗА ХЛЕБОМ.","Shocked scruffy customer holding tiny bread and an absurdly long paper receipt that wraps around his body and reaches ceiling, cashier laughing, tiny grocery checkout filled with details")),
    s("rent_monster","money","Хозяин повысил аренду. Теперь у меня не квартира, а платная подписка на стены. #SKRBL #юмор #карандашныемемы",
      ("АРЕНДА ПОДРОСЛА.","A tiny cramped rental apartment literally eating the tenant's wallet, door with sharp teeth and landlord peeking behind it, scared adult man clutching a few coins")),
    s("discount_trap","money","Скидка 80%. Сэкономил всё, что осталось от зарплаты. #SKRBL #юмор #карандашныемемы",
      ("УВИДЕЛ СКИДКУ 80%.","Confused adult man pinned beneath gigantic red price tag like under a trap, shopping bags overflowing useless things, empty wallet hanging upside down, absurd department store")),
    s("bank_notifications","money","Банк прислал пуш: «У вас всё хорошо?» Нет, бл***ь, я просто открыл приложение. #SKRBL #юмор #карандашныемемы",
      ("ЗАГЛЯНУЛ В БАНК.","A shocked man holding a huge smartphone while a gigantic bank app notification bubble grows arms and pats him sadly on the shoulder, tiny empty piggy bank crying on table")),
    s("alarm_boxer","sleep","Бой века: я против будильника. По очкам проиграл матрасу. #SKRBL #юмор #карандашныемемы",
      ("ПОНЕДЕЛЬНИК. 07:00.","Sleepy man in pajamas boxing against giant angry ringing alarm clock with red boxing gloves, pillow on corner of boxing ring, cartoon morning sun as referee")),
    s("sleep_scroll","sleep","Собирался лечь пораньше. Очнулся в 04:38, эксперт по жизни енотов. #SKRBL #юмор #карандашныемемы",
      ("ЛЯГУ НА ПЯТЬ МИНУТ.","Messy hair tired adult at 4am in bed clutching phone while dozens of cartoon raccoons on screen crawl out around his pillow, enormous wall clock and black circles under eyes")),
    s("duvet_trap","sleep","Наконец проснулся. Одеяло подало апелляцию. #SKRBL #юмор #карандашныемемы",
      ("УТРО ПОШЛО НЕ ПО ПЛАНУ.","A huge grumpy blanket with tiny cartoon hands dragging man back into bed while alarm clock rings, messy apartment, man's eyes comically wide")),
    s("office_friday","work","Пятница, 17:59. Пришёл начальник с «маленькой задачкой». П***ец, выходные. #SKRBL #юмор #карандашныемемы",
      ("ПЯТНИЦА. 17:59.","Office employee trying to crawl out office door, giant smiling boss holding a tiny sticky note attached to enormous tower of documents, wall clock showing one minute before six")),
    s("email_raid","work","Открыл почту. Письма залезли на стол и начали требовать отчёты. #SKRBL #юмор #карандашныемемы",
      ("ПОЧТУ ПРОВЕРЮ ЗА МИНУТУ.","Tiny frantic office worker at cluttered desk surrounded by living furious paper envelopes with teeth and small arms emerging from laptop, coffee splashed everywhere")),
    s("excel_mage","work","Сказал, что умею Excel. Теперь меня вызывают, когда пропадает интернет. #SKRBL #юмор #карандашныемемы",
      ("НЕМНОГО ЗНАЮ EXCEL.","Tired office man wearing a wizard hat with cells of spreadsheet projected everywhere as coworkers kneel before him, laptop overflowing magical green grids")),
    s("work_call","work","Созвон на пять минут. Успел состариться и получить пенсию. #SKRBL #юмор #карандашныемемы",
      ("БЫСТРЫЙ СОЗВОН.","Old grey-bearded employee with cobwebs and huge headphones staring at video call on laptop, coffee mug fossilized, calendar pages flying all around office")),
    s("office_plant","work","Взял отпуск на два дня. На работе меня заменили фикусом. Он уже тимлид. #SKRBL #юмор #карандашныемемы",
      ("УШЁЛ В ОТПУСК.","Confused tired man returns to office where smiling potted plant wears tie and sits in his office chair leading an important meeting, coworkers applaud")),
    s("passwords","phone","Пароль должен быть сложным. Теперь я для собственного телефона подозрительный тип. #SKRBL #юмор #карандашныемемы",
      ("ЗАБЫЛ ПАРОЛЬ.","Angry smartphone wearing police cap interrogates a confused man with handcuffs in front of his own apartment door, small keypad and confused face")),
    s("typing_message","phone","Три точки «печатает…» висели полчаса. Ответ: «ок». Серьёзно, бл***ь? #SKRBL #юмор #карандашныемемы",
      ("ПЕЧАТАЕТ УЖЕ ПОЛЧАСА.","Panicking adult man staring at giant smartphone showing three simple dots, clock hands spinning wildly, sweat flying off his face, abandoned coffee and eaten nails")),
    s("battery_funeral","phone","Телефон сел на улице. Я впервые заметил, что у города есть деревья. #SKRBL #юмор #карандашныемемы",
      ("1% БАТАРЕИ.","Worried adult man holding nearly dead giant smartphone while tiny cartoon battery lies in coffin beside him, lively city street and pigeons watching")),
    s("food_delivery","home","Заказал ужин, смотрю на курьера по карте уже час. Знаю его лучше родственников. #SKRBL #юмор #карандашныемемы",
      ("КУРЬЕР В СОСЕДНЕМ ДВОРЕ.","Hungry skinny man with bulging eyes stares through binoculars at smartphone map tracking a tiny delivery cyclist wandering a ridiculous maze across the street")),
    s("empty_fridge","home","Смотрел в холодильник шестой раз. Кетчуп предложил съесть лёд. #SKRBL #юмор #карандашныемемы",
      ("НУ, ЧТО ТАМ ПОЕСТЬ?","A deeply tired man opening nearly empty gigantic refrigerator; tiny ketchup bottle wearing top hat bows on otherwise empty shelf, lonely ice cube and crumbs")),
    s("dishes_kingdom","home","Помыл одну тарелку. Остальные устроили восстание. Бл***ь, кухня не сдаётся. #SKRBL #юмор #карандашныемемы",
      ("РЕШИЛ ПОМЫТЬ ПОСУДУ.","Disheveled adult man waving tiny sponge against huge mountain of angry plates and cups advancing on him like an army in chaotic kitchen")),
    s("cat_manager","home","Кот сел на ноутбук. Через час получил повышение. Меня попросили освободить кресло. #SKRBL #юмор #карандашныемемы",
      ("КОТ СЕЛ НА КЛАВИАТУРУ.","Fat smug tabby cat in office suit sitting in plush executive chair with laptop and fancy coffee, horrified owner holding cardboard box of his belongings, messy home office")),
    s("wifi_router","home","Пропал Wi-Fi. Семья познакомилась друг с другом. Оказались нормальными, бл***ь. #SKRBL #юмор #карандашныемемы",
      ("ОТРУБИЛСЯ WI-FI.","Giant exhausted Wi-Fi router lying on couch while four people around dinner table stare at each other like strangers, shocked exaggerated faces, lots of household clutter")),
    s("vacuum_battle","home","Робот-пылесос третий день ездит по одной комнате. Я ему уже зарплату должен. #SKRBL #юмор #карандашныемемы",
      ("УБОРКУ ДОВЕРИЛ РОБОТУ.","A tiny robot vacuum dressed as a union worker angrily holds a handwritten bill in front of confused man, messy living room with socks and cat toys")),
    s("dating_weather","social","На свидании хотел быть загадочным. Десять минут рассказывал о скидках на гречку. #SKRBL #юмор #карандашныемемы",
      ("ПЕРВОЕ СВИДАНИЕ.","Nervous man in wrinkled shirt with giant sweat drops pointing passionately at tiny buckwheat packet on cafe table, unimpressed date watching, awkward rose in vase")),
    s("groupchat_chaos","social","Открыл семейный чат. За 300 сообщений успели поссориться и помириться без меня. #SKRBL #юмор #карандашныемемы",
      ("ЗАШЁЛ В СЕМЕЙНЫЙ ЧАТ.","Shocked man holding huge smartphone while angry chat bubbles spill out like hundreds of noisy tiny shouting relatives, slippers and tea cups scattered on floor")),
    s("voice_message","social","Голосовое на 8 минут. На шестой минуте человек только поздоровался. #SKRBL #юмор #карандашныемемы",
      ("ДРУГ ПРИСЛАЛ ГОЛОСОВОЕ.","Older adult man with long grown beard and cobwebs listening to extremely long audio message on smartphone, a mountain of coffee cups and tiny calendar pages")),
    s("friend_loan","social","Друг одолжил 500 рублей. Исчез быстрее, чем я успел произнести «когда вернёшь». #SKRBL #юмор #карандашныемемы",
      ("ДАЛ ДРУГУ В ДОЛГ.","Man in shocked expression watches friend run away holding banknote and dissolving into dust cloud, street cafe table with two coffee mugs")),
    s("gym_entrance","life","Купил абонемент в спортзал. На третий день устал от уведомлений клуба. #SKRBL #юмор #карандашныемемы",
      ("ПОШЁЛ В ЗАЛ.","Athletic trainer carries exhausted man like a carpet out of gym while tiny dumbbell smiles smugly and other gym machines watch, dramatic goofy sweat")),
    s("todo_scroll","life","Составил список из 20 дел. Выполнил первое: «написать список». #SKRBL #юмор #карандашныемемы",
      ("СЕГОДНЯ Я ПРОДУКТИВНЫЙ.","Proud sleepy man wearing small award ribbon holds impossibly long to-do list wrapping around entire apartment, the first checkmark huge and all other boxes blank")),
    s("adult_life","life","Взрослая жизнь: купил новую губку для посуды и почувствовал себя счастливым. #SKRBL #юмор #карандашныемемы",
      ("ВЗРОСЛАЯ ЖИЗНЬ.","Tired adult man in kitchen holds a brand new dish sponge above his head like a royal crown, imaginary fireworks and confetti while dirty dishes surround him")),
    s("weekend_eaten","life","Суббота началась. Моргнул — понедельник. Кто сожрал воскресенье, бл***ь? #SKRBL #юмор #карандашныемемы",
      ("ГДЕ МОИ ВЫХОДНЫЕ?","Man in pajamas fighting a giant angry wall calendar monster who is literally chewing on Sunday page, living room full of empty coffee mugs")),
    s("haircut_tragedy","life","Попросил убрать пару сантиметров. Теперь меня узнаёт только паспорт. #SKRBL #юмор #карандашныемемы",
      ("ЧУТЬ-ЧУТЬ ПОДРОВНЯТЬ.","Terrified man in barber cape with ridiculous almost-bald haircut holds up a passport photo with lush hair while cheerful barber poses with oversized scissors")),
    # Short progression stories: two panels are ideal for a setup/punchline.
    s("boss_small_fix","work","Начальник сказал, что правка маленькая. Проект не пережил знакомства. #SKRBL #юмор #карандашныемемы",
      ("НУЖНА МЕЛКАЯ ПРАВКА.","At office boss in suit hands employee a very tiny sticky note, employee smiles relieved, cluttered desk and laptop"),
      ("...НА 74 СТРАНИЦАХ.","Same employee buried alive beneath giant toppling tower of documents, boss smiles and gives thumbs up, comical eyes bulging from pile")),
    s("salary_vs_bills","money","Не успел получить зарплату, а коммуналка уже стоит под дверью с вилкой. #SKRBL #юмор #карандашныемемы",
      ("ДИНЬ! ЗАРПЛАТА.","Tired man excited looking at glowing mobile bank notification while sitting in tiny cluttered living room, hopeful eyes"),
      ("БЛ***Ь. ВСЁ.","Same man panicking as gigantic utility bill with teeth and fork eats a stack of cash on his kitchen table, dramatic visual gag")),
    s("sleep_just_one","sleep","Последний ролик в ленте оказался на шесть часов длиннее сна. #SKRBL #юмор #карандашныемемы",
      ("ЕЩЁ ОДИН РОЛИК.","Sleepy adult in dark bedroom scrolling phone under duvet, wall clock shows around midnight, slightly tired eyes"),
      ("УЖЕ РАССВЕТ, БЛ***Ь.","Same adult wide-eyed with messy hair still staring at glowing phone, sunrise through window, birds holding tiny alarm clocks laugh")),
    s("shop_tiny_basket","money","В магазин за двумя продуктами. На выходе пришлось брать кредит на пакет. #SKRBL #юмор #карандашныемемы",
      ("ВОЗЬМУ ТОЛЬКО ДВА.","Smiling customer at grocery store holding two tiny vegetables in small basket, bright cashier nearby"),
      ("ЧЕК ДО ЛУНЫ.","Shocked customer surrounded by absurd mountain of receipt paper snaking through shop like a dragon, two groceries on checkout")),
    s("room_cleaning","home","Начал убираться в десять утра. Вечером нашёл одну старую флешку и все воспоминания. #SKRBL #юмор #карандашныемемы",
      ("НАЧНУ УБОРКУ.","Adult with mop and garbage bag enters messy living room full of clothes, optimistic face and clock on wall"),
      ("ПРОШЛО ВОСЕМЬ ЧАСОВ.","Same adult sitting crosslegged on floor smiling nostalgically at old gadgets and printed photos, room even messier, sunset outside")),
    s("dating_last_message","social","Написал «привет». Через час мысленно уже развёлся. #SKRBL #юмор #карандашныемемы",
      ("НАПИСАЛ «ПРИВЕТ».","Nervous smiling man holding phone and typing a greeting at cafe table, heart stickers drawn on notebook, clean small table"),
      ("ОТВЕТА НЕТ.","Same man with panicked giant bloodshot eyes surrounded by old calendars and coffee cups, waits forever holding phone, rain outside cafe")),
    s("wifi_connection","home","Выключили интернет. Отец спросил, кто эти люди на кухне. #SKRBL #юмор #карандашныемемы",
      ("ИНТЕРНЕТ ПРОПАЛ.","A family of four in separate corners each staring at mobile phone with sad Wi-Fi symbol, tidy dining room"),
      ("О! У МЕНЯ ЕСТЬ СЕМЬЯ.","Same four family members squint suspiciously at each other across table as if first meeting, one person holding a plate in surprise")),
    s("cat_keyboard","home","Кот помог с работой. Теперь у него премия, а у меня собеседование. #SKRBL #юмор #карандашныемемы",
      ("КОТ ОТВЕТИЛ НА ПИСЬМО.","Fat lazy striped cat accidentally walking across laptop keyboard at cluttered work desk, sleepy owner in pajamas"),
      ("КОТ ТЕПЕРЬ НАЧАЛЬНИК.","Same fat cat now wearing dark suit in big boss armchair, sad owner in pajamas holding box with houseplant, comedic office scene")),
    s("alarm_snooze","sleep","Нажал «ещё 5 минут». Проснулся в другом времени года. #SKRBL #юмор #карандашныемемы",
      ("ЕЩЁ ПЯТЬ МИНУТ.","Sleepy scruffy man in messy bed pushing alarm clock snooze button with tired finger, night sky outside window"),
      ("ОЙ, БЛ***Ь.","Same sleepy man wakes in bed now covered by snow as seasons changed, gigantic calendar flying past, eyes comically wide")),
    s("phone_charge","phone","Искал зарядку так отчаянно, будто от неё зависит моя пенсия. #SKRBL #юмор #карандашныемемы",
      ("1% ЗАРЯДА.","Adult man anxiously squints at smartphone with nearly empty battery in city street, no charger nearby"),
      ("РОЗЕТКА НАШЛАСЬ!","Same adult man hugging glowing wall power outlet like dear friend, kneeling on sidewalk with giant happy tears, startled strangers")),
    s("courier_tracker","home","Следил за курьером так долго, что у него в итоге появился мой адрес в завещании. #SKRBL #юмор #карандашныемемы",
      ("КУРЬЕР УЖЕ РЯДОМ.","Hungry man squints at smartphone with moving tiny map marker inside apartment kitchen, fast food plates empty"),
      ("УЖЕ ТРЕТИЙ ЧАС РЯДОМ.","Same starved man with beard and cobwebs watching smartphone map, cyclist appears to be riding in circles outside the window")),
    s("three_panels_contract","work","В договоре мелкий шрифт. Оказывается, я подписал соглашение быть счастливым по выходным. #SKRBL #юмор #карандашныемемы",
      ("ПОДПИШИ ЗДЕСЬ.","Smiling human resources officer pointing at tiny paper form, bewildered employee sitting across desk in office"),
      ("А ТУТ — МЕЛКИЙ ШРИФТ.","Same employee examines absurd giant magnifying glass above mile-long contract written in unreadable scribbles, nervous expression"),
      ("ПОДПИСАЛ ВСЮ ЖИЗНЬ.","Exhausted employee now wearing enormous chain made of paper contracts while office boss laughs from armchair, absurd visual comedy")),
    s("three_panels_fridge","home","Семь раз открывал холодильник. На восьмой холодильник спросил: «Чё надо, бл***ь?» #SKRBL #юмор #карандашныемемы",
      ("ЗАХОТЕЛ ПОЕСТЬ.","Hungry scruffy man peeks inside mostly empty refrigerator in messy kitchen, small ketchup bottle on shelf"),
      ("ЧЕРЕЗ ПЯТЬ МИНУТ.","Same hungry man opens the empty fridge again with sad face, only ketchup and ice visible, dim kitchen"),
      ("ХОЛОДИЛЬНИК НЕ ВЫДЕРЖАЛ.","Giant refrigerator now has big angry eyes and teeth, shouting at shocked man who drops his plate, kitchen full of scribbly details")),
    s("three_panels_vacation","work","Только приехал в отпуск. Начальник написал: «Быстрый вопросик». И всё, бл***ь, море высохло. #SKRBL #юмор #карандашныемемы",
      ("ОТПУСК! МОРЕ!","Happy exhausted office worker in shorts sunbathing on beach with cocktail and folded umbrella, wide grin"),
      ("СООБЩЕНИЕ ОТ БОССА.","Same man in shorts shocked as phone vibrates on sunny beach, ocean waves behind, bulging eyes"),
      ("МОРЕ ТОЖЕ УВОЛИЛОСЬ.","Same man surrounded by dried out seabed, giant laptop replacing palm tree, dramatic panic, crabs carrying office papers")),
    s("four_panels_birthday","life","Планировал тихий день рождения. Пришли родственники и устроили собрание жильцов. #SKRBL #юмор #карандашныемемы",
      ("ХОЧУ ТИХИЙ ДЕНЬ РОЖДЕНИЯ.","Adult man peacefully decorating a small cake in cozy home kitchen, calm smile"),
      ("ЗВОНОК В ДВЕРЬ.","Adult man startled as doorbell rings, tiny cake on table, balloons trembling"),
      ("РОДСТВЕННИКИ ПРИШЛИ.","Huge comically exaggerated crowd of relatives with dishes and balloons fills tiny apartment, man squeezed in corner"),
      ("КАК ЖЕ ТУТ ТИХО, БЛ***Ь.","Exhausted man sitting crushed beneath pile of party hats, loud relatives cheer, tiny birthday candle still lit on cake")),
    s("four_panels_boss_weekend","work","Пятница на работе: начальник появился с «идеей». Мои выходные уже подали на развод. #SKRBL #юмор #карандашныемемы",
      ("ПЯТНИЦА. ПОЧТИ ДОМОЙ.","Office worker folds laptop with joyful relief as wall clock nears evening"),
      ("ВОШЁЛ НАЧАЛЬНИК.","Boss leans into office doorway holding tiny notebook with evil smile, employee frozen"),
      ("ЕСТЬ КОЕ-КАКАЯ ИДЕЯ.","Giant tower of office paperwork emerges behind boss, employee's huge eyes bulge from shock"),
      ("ВЫХОДНЫЕ ПОКА, БЛ***Ь.","Depressed worker chained to office chair by telephone cords, sunset visible outside window, boss cheerfully waves goodbye")),
]
assert len({story.id for story in STORIES}) == len(STORIES)
assert len(STORIES) >= 40
assert all(1 <= len(story.scenes) <= 4 for story in STORIES)
