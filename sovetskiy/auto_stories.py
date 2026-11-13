"""SOVETSKIY: 96 distinct original short visual jokes; one per 15-minute slot.

Each visual description depicts the EXACT gag written on its image, not an
arbitrary attractive portrait or unrelated Soviet movie shot. Creative text
is original, not verbatim copyrighted film dialogue or internet jokes.
The target of 96 posts/day still depends on free image availability and VK.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Story:
    id:str
    top:str
    bottom:str
    visual:str
    theme:str

# The delimiter is safe: prompts and jokes in this bank do not contain '|'.
DATA = r"""salary_wallet|ПОЛУЧИЛ ЗАРПЛАТУ|КОММУНАЛКА УЖЕ ЖДЁТ У ДВЕРИ.|Shocked Soviet era man in modest shirt opens wallet while huge stack of utility bills under apartment door waits like a mob, panicked face|money
bread_reciept|КУПИЛ ОДИН БАТОН|ЧЕК ДОТЯНУЛСЯ ДО ПОТОЛКА.|Soviet grocery shop customer in coat holds one loaf of bread and absurdly long paper receipt unrolling from cash register to ceiling, cashier amazed|money
bankbook|ОТКРЫЛ СБЕРКНИЖКУ|ДЕНЬГИ ВЗЯЛИ ВЫХОДНОЙ.|Worried man with Soviet savings book open on table watches tiny banknotes with legs running away across table, astonished expression|money
rent_keys|ПРИШЁЛ ПЛАТИТЬ ЗА КВАРТИРУ|ХОЗЯИН ВЫДАЛ КЛЮЧ ОТ КЛАДОВКИ.|Furious Soviet-era tenant holds giant key to ridiculously tiny closet apartment, landlord grins, narrow corridor full of shoes|money
coinjar|РЕШИЛ КОПИТЬ НА ОТПУСК|КОПИЛКА ПОПРОСИЛА ПОЕСТЬ.|Man in 1970s home shows nearly empty piggy bank with sad eyes and tiny mouth; only one coin lies on wooden table|money
utility_bill|ПРИСЛАЛИ СЧЁТ ЗА СВЕТ|ТЕПЕРЬ УЖИНАЮ ПРИ СВЕЧКЕ.|Shocked man at Soviet kitchen table holds enormous bill under single tiny candle in otherwise dark kitchen, dramatic face|money
price_tag|ПОСМОТРЕЛ НА ЦЕННИК|ПОСЕДЕЛ ПРЯМО У ПРИЛАВКА.|Middle aged shopper in Soviet grocery stares at tiny price tag and comically grows a long white beard, cashier watching|money
payment_queue|ОПЛАТИЛ ВСЁ НЕОБХОДИМОЕ|ОСТАЛОСЬ КУПИТЬ ВОЗДУХ.|Man counting last coins at Soviet wooden table while giant stack of bills sits beside empty metal cup, desperate face|money
sofa_sale|УВИДЕЛ СКИДКУ НА ДИВАН|ПРИШЛОСЬ ПРОДАТЬ СТАРЫЙ ДИВАН.|Soviet furniture shop: man stunned by giant price tag tied to sofa while carrying broken old couch on back|money
borrow_neighbor|ЗАНЯЛ СОСЕДУ ДО ПЯТНИЦЫ|СОСЕД УЕХАЛ В ДРУГОЙ ГОРОД.|Soviet apartment stairwell: confused man holds empty hand while neighbor running away with suitcase and few banknotes|money
wallet_echo|ЗАГЛЯНУЛ В КОШЕЛЁК|ОТТУДА ОТВЕТИЛО ЭХО.|Close-up funny Soviet film still: shocked man holds open empty leather wallet by ear as if hearing echo, sparse room|money
bonus_crumb|НА РАБОТЕ ДАЛИ ПРЕМИЮ|НА НЕЁ ХВАТИЛО ПЕЧЕНЬЯ.|Tired man in old-fashioned Soviet suit solemnly holding one tiny biscuit like an award in front of huge empty office desk|money
boss_file|НАЧАЛЬНИК СКАЗАЛ: ПЯТЬ МИНУТ|ПРИНЁС ПЯТЬ ЧЕМОДАНОВ БУМАГ.|Soviet office boss with grin dragging five huge suitcases of documents toward horrified clerk at typewriter|work
friday_end|ПЯТНИЦА. УЖЕ СОБРАЛСЯ ДОМОЙ|СЛЫШУ: А ТЫ НЕ ЗАНЯТ?|Exhausted worker wearing coat reaches office door; stern smiling boss reaches after him holding pile of documents|work
meeting_age|СОВЕЩАНИЕ НА ПОЛЧАСА|К КОНЦУ У МЕНЯ ПОЯВИЛАСЬ СЕДИНА.|1970s Soviet office meeting: tired man with exaggerated sudden white hair surrounded by endless coffee mugs and wall clock|work
secretary_phones|ОТВЕТИЛ НА ОДИН ЗВОНОК|ЗАЗВОНИЛО ВСЁ БЮРО.|Stunned Soviet secretary between a dozen ringing black rotary telephones on office table, arms tangled in cords|work
paper_mountain|НАЧАЛ С ОДНОГО ОТЧЁТА|ВЕЧЕРОМ ОТКОПАЛИ ЛОПАТОЙ.|Soviet clerk buried neck deep in absurd mountain of paperwork at wooden desk, coworkers holding shovels|work
lunch_break|ВЫШЕЛ НА ОБЕД|ВОЗВРАЩАЮСЬ УЖЕ НА УЖИН.|Soviet factory worker in work overalls returns with tin lunch box as evening moon shines outside industrial window|work
new_job|ПЕРВЫЙ ДЕНЬ НА НОВОЙ РАБОТЕ|УЖЕ ОБЪЯСНЯЮ, КАК ТУТ ВСЁ ЧИНИТЬ.|Young employee in Soviet workshop surrounded by broken machinery while older coworkers hand him absurd pile of tools|work
printer_revolt|ПОПРОСИЛ МАШИНКУ НЕ ЗАЕДАТЬ|ОНА ВЫДАЛА ТРИ КИЛО БУМАГИ.|Vintage Soviet typewriter spits out a giant avalanche of tangled paper at shocked office clerk, funny physical action|work
salary_delay|ЗАРПЛАТУ ЗАДЕРЖАЛИ НА ДЕНЬ|МОЙ ХОЛОДИЛЬНИК УЖЕ В КУРСЕ.|Soviet factory worker in worn jacket sadly shakes nearly empty lunch tin beside empty kitchen fridge, exaggerated hunger|work
boss_smile|НАЧАЛЬНИК ЗАШЁЛ С УЛЫБКОЙ|МЫ СРАЗУ ПОНЯЛИ: БЕДА.|Soviet office workers at rows of desks stare terrified at unusually smiling boss entering doorway with huge stack of folders|work
holiday_call|ВЗЯЛ ОТГУЛ НА ОДИН ДЕНЬ|РАБОТА ПРИШЛА КО МНЕ ДОМОЙ.|Man in Soviet pajamas opening apartment door to a giant delivery cart full of office files and desk phone, shocked|work
last_report|СКАЗАЛ: ЭТО ПОСЛЕДНИЙ ОТЧЁТ|ПОЯВИЛСЯ ЕГО СТАРШИЙ БРАТ.|Clerk at typewriter looks horrified as second absurdly huge file rises behind small finished report on desk|work
fridge_sentinel|ОТКРЫЛ ХОЛОДИЛЬНИК ПЯТЫЙ РАЗ|КОЛБАСА ВСЁ ЕЩЁ НЕ ВЫРОСЛА.|1970s Soviet kitchenette: hungry adult opens nearly empty retro refrigerator repeatedly, one lonely sausage under light|home
dust_kingdom|НАЧАЛ ГЕНЕРАЛЬНУЮ УБОРКУ|НАШЁЛ ЧЕМОДАН 1962 ГОДА.|Soviet home man with broom discovers enormous dusty old suitcase hiding under bed, surprised face, cobwebs|home
dishes_army|ПОМЫЛ ОДНУ ТАРЕЛКУ|ОСТАЛЬНЫЕ ВЫСТРОИЛИСЬ В ОЧЕРЕДЬ.|Soviet kitchen: exhausted person holding sponge while tall towers of dirty ceramic plates line up on sink|home
curtain_change|РЕШИЛ ПОВЕСИТЬ ШТОРЫ|ТЕПЕРЬ РЕМОНТИРУЮ ПОТОЛОК.|Soviet apartment: man hanging curtains on ladder while cracked ceiling collapses, comically horrified|home
sofa_squeak|ПОЧИНИЛ СКРИПУЧИЙ ДИВАН|ТЕПЕРЬ СКРИПИТ ВЕСЬ ПОЛ.|Soviet living room: man holding tools by old sofa while wooden floor boards rise and squeak comically beneath him|home
neighbor_drill|СОСЕД ВОСКРЕСЕНЬЕМ НАЧАЛ РЕМОНТ|МОЙ БУДИЛЬНИК УШЁЛ В ОТПУСК.|Soviet apartment block: exhausted person in bed covers ears while giant electric drill protrudes through shared wall|home
family_tea|СЕЛ ПОПИТЬ ЧАЙ В ТИШИНЕ|ПРИШЛИ ВСЕ РОДСТВЕННИКИ СРАЗУ.|1970s Soviet tiny kitchen filled with a sudden crowd of relatives all reaching for tea cups, surprised host|home
washing_sock|ПОСТИРАЛ ДВА НОСКА|МАШИНКА ВЕРНУЛА ОДИН.|Soviet laundry: angry man holds one sock and looks accusingly at vintage washing machine with a sock sticking out|home
sugar_spill|РАССЫПАЛ ЛОЖКУ САХАРА|УБИРАЛ ПО ВСЕЙ КВАРТИРЕ.|Soviet apartment kitchenette: man sweeps enormous mountain of scattered sugar with tiny broom, shocked expression|home
cat_meeting|ПОСАДИЛ КОТА РЯДОМ|ОН УЖЕ ХОЗЯИН КВАРТИРЫ.|Soviet sitting room fat tabby cat in armchair like boss while adult owner stands nervously offering saucer of milk|home
cabbage_soup|РЕШИЛ СВАРИТЬ ЩИ|ПОЛУЧИЛ ОКЕАН В КАСТРЮЛЕ.|Soviet kitchen: cook in apron shocked as oversized stockpot bubbles over sending vegetable soup across stove|home
window_frost|ЗАКРЫЛ ОКНО НА ЗИМУ|ВЕСНОЙ ОТКРОЮ С ЛОМОМ.|Soviet apartment winter man struggles with heavily frozen old window while holding small crowbar and huge icicles|home
alarm_wrestle|БУДИЛЬНИК ЗАЗВОНИЛ В ШЕСТЬ|Я ВЫЗВАЛ ЕГО НА ДУЭЛЬ.|1970s Soviet bedroom: disheveled sleepy man in pajamas challenges huge ringing metal alarm clock like boxing opponent|sleep
snooze_year|НАЖАЛ ЕЩЁ ПЯТЬ МИНУТ|ПРОСНУЛСЯ В ДРУГОМ СЕЗОНЕ.|Soviet bedroom: bewildered man wakes under old duvet while window shows snow outside and torn calendar sheets everywhere|sleep
midnight_tea|ВЫПИЛ ЧАЙ ПЕРЕД СНОМ|В ТРИ НОЧИ СЧИТАЮ ТРЕЩИНЫ В ПОТОЛКЕ.|Soviet apartment night: sleepless wide eyed man staring at cracks in ceiling, empty tea cup at bedside, clock 3am|sleep
pillow_lawyer|ПЫТАЛСЯ ВСТАТЬ ПОРАНЬШЕ|ПОДУШКА ПОДАЛА АПЕЛЛЯЦИЮ.|Old Soviet bedroom: sleepy man being physically held down by giant fluffy pillow that seems to protest, morning sunlight|sleep
night_radio|ЛЁГ СПАТЬ С РАДИО|ПРОСНУЛСЯ ЭКСПЕРТОМ ПО УРОЖАЮ.|Soviet man in pajamas in bed with big old radio receiver blaring; he holds a wheat stalk and looks confused at sunrise|sleep
clock_race|СМОТРЮ: ЕЩЁ МНОГО ВРЕМЕНИ|ПОЧЕМУ ЧАСЫ УЖЕ НА РАБОТЕ?|Soviet bedroom: shocked sleeper reaching for wall clock that has tiny legs and is running away out the door|sleep
dream_rent|ВО СНЕ БЫЛ МИЛЛИОНЕРОМ|ПРОСНУЛСЯ — ПРИШЁЛ КВИТОК ЗА СВЕТ.|Soviet man awakening in pajamas from golden dream to giant utility bill on nightstand, worried face|sleep
blanket_grip|РЕШИЛ ВСТАТЬ ПО ДОБРОЙ ВОЛЕ|ОДЕЯЛО МЕНЯ НЕ ОТПУСТИЛО.|1970s bedroom: man crawling off bed while heavy blanket wraps around his legs like a rope, comic struggle|sleep
rooster_late|ПОСТАВИЛ ТРИ БУДИЛЬНИКА|ПРОСПАЛИ ВСЕ ЧЕТВЕРО.|Soviet bedroom: man oversleeping as three antique alarm clocks lie tipped over sleeping like him, sun through curtains|sleep
night_snack|ВСТАЛ НОЧЬЮ ЗА ВОДОЙ|ОЧНУЛСЯ У ХОЛОДИЛЬНИКА С КОЛБАСОЙ.|Soviet dark kitchen night: surprised man in pajamas holding entire sausage next to open vintage fridge, caught in act|sleep
bed_warm|СОБРАЛСЯ НА РАБОТУ|КРОВАТЬ СКАЗАЛА: НЕ ПРЕДАВАЙ.|Soviet bedroom: adult man wearing coat struggles to leave warm bed while huge pillows drag his coat sleeve back|sleep
monday_ghost|В ВОСКРЕСЕНЬЕ РЕШИЛ РАНЬШЕ ЛЕЧЬ|ПОНЕДЕЛЬНИК УЖЕ СИДЕЛ НА СТУЛЕ.|Retro Soviet bedroom: man in bed stares in horror at giant calendar page marked Monday sitting on chair beside him|sleep
family_chat|ЗАШЁЛ НА ПЯТЬ МИНУТ К РОДНЕ|ВЫШЕЛ С ПЛАНОМ НА ПЯТЬ ЛЕТ.|1970s Soviet dining table: exhausted man surrounded by relatives pointing at enormous life plan on paper, expression horrified|social
neighbor_salt|ЗАШЁЛ К СОСЕДКЕ ЗА СОЛЬЮ|УЗНАЛ НОВОСТИ СО ВСЕГО ДВОРА.|Soviet stairwell: stunned man with tiny salt shaker listens to elderly neighbor gesturing animatedly with stack of newspapers|social
first_date|НА ПЕРВОМ СВИДАНИИ ХОТЕЛ БЫТЬ ТАИНСТВЕННЫМ|ВЕСЬ ВЕЧЕР ГОВОРИЛ ПРО ЦЕНЫ НА ГРЕЧКУ.|Retro 1970s Soviet cafe: nervous man passionately shows buckwheat package to bored date across table|social
gift_pot|ПРИШЁЛ В ГОСТИ С ТОРТОМ|УШЁЛ С ТРЁХЛИТРОВОЙ БАНКОЙ ЩЕЙ.|Soviet apartment door: guest with empty cake box awkwardly carrying giant three liter jar of soup from smiling hostess|social
phone_gossip|ПОЗВОНИЛ СПРОСИТЬ КАК ДЕЛА|ЧЕРЕЗ ЧАС ЗАБЫЛ, ЗАЧЕМ ЗВОНИЛ.|Retro Soviet hallway: exhausted man entangled in long rotary telephone cord, wall clock showing an hour later|social
bad_news|СКАЗАЛ РОДНЕ: ВСЁ НОРМАЛЬНО|ОНИ СОЗВАЛИ СОВЕТ.|Soviet family dining room: surprised young man seated at table surrounded by serious older relatives like a formal commission|social
friend_debt|ОДОЛЖИЛ ДРУГУ ПЯТЬ РУБЛЕЙ|ОН ВДРУГ СТАЛ ПРИЗРАКОМ.|Soviet street: man with palm outstretched looks shocked as friend with banknote disappears in cartoon dust cloud|social
birthday_toast|ПРОСИЛ ТИХИЙ ДЕНЬ РОЖДЕНИЯ|СОСЕДИ УЖЕ ПОЮТ В ХОРЕ.|1970s Soviet small living room: birthday host shocked as huge group of neighbors squeeze through door holding tea cups and cake|social
train_compartment|ПОЗНАКОМИЛСЯ С ПОПУТЧИКОМ|УЖЕ ЗНАЮ ВСЮ ЕГО РОДОСЛОВНУЮ.|Soviet sleeper train compartment: stunned passenger buried in family photo albums while talkative stranger smiles across table|social
late_visitors|СКАЗАЛ ГОСТЯМ: Я РАНО ВСТАЮ|ГОСТИ ДОСТАЛИ ЕЩЁ ОДИН ЧАЙНИК.|Soviet home late night: exhausted host in robe stares at guests cheerfully bringing a second enormous samovar to table|social
mother_help|ПОПРОСИЛ МАМУ НЕ ВОЛНОВАТЬСЯ|ОНА ПРИВЕЗЛА ЧЕМОДАН ЕДЫ.|1970s Soviet apartment: stunned adult son opens door as mother drags giant overstuffed suitcase filled with jars and bread|social
greeting_card|НАПИСАЛ КОРОТКОЕ ПОЗДРАВЛЕНИЕ|РОДНЯ ВЫДАЛА МНЕ МЕТОДИЧКУ.|Soviet apartment: man with tiny postcard looks baffled as relatives hand him huge thick volume about proper greetings|social
bread_line|ЗАШЁЛ ЗА МОЛОКОМ|ОЧЕРЕДЬ УЖЕ ПОЛУЧИЛА ИМЯ.|Soviet dairy shop: worried man holding empty glass milk bottle stands before impossibly long queue going out onto the street|shopping
hat_choice|ВЫБИРАЛ ШАПКУ НА ЗИМУ|ПОКА ВЫБИРАЛ — НАСТУПИЛА ВЕСНА.|1970s Soviet clothing shop: stunned customer in wool hat sees spring blossoms outside window while shop assistant holds more hats|shopping
sausage_queue|ЗАНЯЛ ОЧЕРЕДЬ ЗА КОЛБАСОЙ|ПОСЛЕ МЕНЯ ВСТАЛА ЦЕЛАЯ ЭПОХА.|Soviet grocery meat counter: man with basket surprised by long enormous line of people stretching around store, humorous exaggeration|shopping
umbrella_sale|КУПИЛ ЗОНТ ОТ ДОЖДЯ|ПРОВЕРИЛ — В НЁМ ДЫРКА.|Soviet street in the rain: shocked man under umbrella with gigantic hole, water pouring through, shop bag in hand|shopping
shoe_repair|ПОНЁС БОТИНКИ В РЕМОНТ|ОТДАЛИ ПОСЛЕ ДВУХ ЗИМ.|Soviet cobbler workshop: worried man holds repaired winter shoes while outside window spring blossoms and calendar pages fall|shopping
discount_oath|ПРИШЁЛ ТОЛЬКО ПОСМОТРЕТЬ|УШЁЛ С ТРЕМЯ КОВРАМИ.|Soviet carpet store: overwhelmed man bent under three giant rolled rugs, shocked expression, smiling shop assistant|shopping
market_potatoes|НА РЫНКЕ ВЗЯЛ ДВЕ КАРТОШКИ|ДАЛИ МЕШОК ПОЛЕЗНЫХ СОВЕТОВ.|Soviet outdoor market: man holds two potatoes and giant bag of handwritten advice papers from energetic vendor|shopping
butter_receipt|СПРОСИЛ СКОЛЬКО СТОИТ МАСЛО|ПРОДАВЕЦ СРАЗУ ПРИНЁС ВОДЫ.|Soviet grocery counter: stunned man facing a price tag for butter, shop assistant offers him a glass of water, comedy|shopping
shopping_list|СОСТАВИЛ СПИСОК ИЗ ДВУХ ПУНКТОВ|С МАГАЗИНА ПРИНЁС СЕМЬ ПАКЕТОВ.|Soviet grocery checkout: confused shopper with tiny shopping list stands among huge pile of seven overstuffed string bags|shopping
bread_choice|ЗАШЁЛ В ГАСТРОНОМ ЗА БАТОНОМ|ВЫБИРАЮ УЖЕ ТРЕТЬЮ ПЯТИЛЕТКУ.|Fictional vintage Soviet grocery photo: adult man carefully inspecting one loaf of bread with serious expression at wooden counter|shopping
glass_jar|СДАВАЛ ПУСТЫЕ БАНКИ|ВЕРНУЛСЯ С НОВЫМИ БАНКАМИ.|Soviet store bottle return counter: man carrying pile of empty glass jars trades for another comically taller pile of glass jars|shopping
meat_scale|ПОПРОСИЛ ПОЛКИЛО МЯСА|ВЕСЫ ПОКАЗАЛИ МОИ ПЕРЕЖИВАНИЯ.|Soviet butcher counter: shocked customer and stern butcher stare at huge mechanical scale overloaded with one tiny piece of meat|shopping
rotary_dial|НАБИРАЛ НОМЕР НА ДИСКОВОМ ТЕЛЕФОНЕ|ЗАБЫЛ ЗАЧЕМ ЗВОНИЛ.|Soviet home man exhausted spinning rotary phone dial with finger while staring blankly at wall, clock ticks|phone
wrong_number|ПОЗВОНИЛ ПО ОШИБКЕ|МЕНЯ УЖЕ ПОЗВАЛИ НА УЖИН.|Old fashioned Soviet living room: man on black rotary telephone looks stunned while friendly stranger at other end imagined inviting him to tea|phone
long_call|СКАЗАЛ: МЫ НА МИНУТОЧКУ|ТЕЛЕФОННЫЙ ПРОВОД УСПЕЛ СОСТАРИТЬСЯ.|Soviet apartment: adult man with gray beard trapped in tangled giant old telephone cord during interminable conversation|phone
busy_signal|ЗВОНИЛ ДРУГУ ТРИДЦАТЬ РАЗ|ЗНАКОМЫ УЖЕ С ГУДКАМИ.|Soviet home man holds old phone receiver with exhausted expression surrounded by many spinning vintage alarm clocks|phone
telegram_panic|ПРИШЛА ТЕЛЕГРАММА: СРОЧНО|ОКАЗАЛОСЬ, ПРОСТО ПРИВЕТ.|Soviet post office: nervous man opening tiny telegram with panicked expression while smiling postwoman waits nearby|phone
postcard_wait|ОТПРАВИЛ ОТКРЫТКУ В ПОНЕДЕЛЬНИК|ОТВЕТ ПРИШЁЛ КОГДА ПРОШЛА ЗИМА.|Soviet apartment: man with long beard and snow at window excitedly holds a postcard delivered by smiling postman|phone
radio_static|ХОТЕЛ ПОСЛУШАТЬ МУЗЫКУ|РАДИО ВЫДАЛО ПРОГНОЗ НА УРОЖАЙ.|Soviet kitchen: man holding radio receiver looks bewildered as wheat stalks appear around radio on table|phone
phonebooth_rain|ЗАШЁЛ В ТЕЛЕФОННУЮ БУДКУ|СНАРУЖИ УЖЕ ВЫРОС ЛЕС.|Soviet outdoor phone booth: man holding old receiver looks out at absurd dense young trees that grew around booth|phone
telephone_cord|ПОЛЧАСА ГОВОРИЛ ПО ТЕЛЕФОНУ|ТЕПЕРЬ ПРОВОД — МОЙ РЕМЕНЬ.|Soviet apartment hallway: dizzy man entangled from waist to shoulders in twisted rotary telephone cord, funny expression|phone
silent_line|ПОДНЯЛ ТРУБКУ: ТИШИНА|НАВЕРНОЕ, РАЗГОВАРИВАЮ С СОВЕСТЬЮ.|Soviet room man looks suspiciously at old black phone receiver while his reflection in mirror stares back|phone
operator_busy|ПОПРОСИЛ СОЕДИНИТЬ С ДРУГОМ|АТС УСТРОИЛА СОБРАНИЕ.|Fictional 1970s Soviet telephone switchboard: weary operator surrounded by dozens of tangled wires and buzzing lights, funny chaos|phone
phone_list|НАШЁЛ СТАРУЮ ЗАПИСНУЮ КНИЖКУ|ТАМ ТЕЛЕФОНЫ ВСЕХ, КТО МНЕ ДОЛЖЕН.|Soviet apartment at kitchen table: man holds a giant old handwritten address book of phone numbers with vengeful amused expression|phone
weekend_calendar|ЖДАЛ ВЫХОДНЫЕ ВСЮ НЕДЕЛЮ|МОРГНУЛ — СНОВА ПОНЕДЕЛЬНИК.|Soviet man on worn sofa grabs calendar pages for Saturday and Sunday as the big Monday page tumbles down above him|life
gym_dumbbell|КУПИЛ ГАНТЕЛЮ ДЛЯ ЗАРЯДКИ|ПОДНИМАЮ ЕЁ ВЗГЛЯДОМ.|Soviet apartment man sprawled exhausted on carpet staring at tiny metal dumbbell just out of reach, funny laziness|life
new_year_tree|СОБРАЛСЯ НАРЯЖАТЬ ЁЛКУ|КОТ УЖЕ СНЯЛ ПОЛОВИНУ ИГРУШЕК.|Soviet living room: fat cat climbing festive fir tree with ornaments dropping, stunned man holding holiday decorations|life
picnic_rain|СОБРАЛИСЬ НА ПИКНИК|ТУЧА УЖЕ ЗАБРОНИРОВАЛА МЕСТО.|1970s Soviet picnic: group with food and checkered blanket looks up as giant gray rain cloud hangs directly over them|life
bus_last|ДОБЕЖАЛ ДО ОСТАНОВКИ|АВТОБУС РЕШИЛ ПОИГРАТЬ В ДОГОНЯЛКИ.|Soviet city street: breathless man in coat running after departing old bus with scarf flying, exaggerated panic|life
tram_crowd|ЗАШЁЛ В ТРАМВАЙ СВОБОДНО|ВЫШЕЛ С ТРЕМЯ ЧУЖИМИ СУМКАМИ.|Crowded Soviet tram: stunned man near doors holds three unrelated string shopping bags, surrounded by puzzled passengers|life
umbrella_wind|КУПИЛ БОЛЬШОЙ ЗОНТ|ВЕТЕР СДЕЛАЛ ИЗ МЕНЯ ПАРУС.|Soviet street: man holding oversized umbrella turned inside out by gust, lifted slightly off ground, hilarious surprise|life
communal_kitchen|ПОШЁЛ ГОТОВИТЬ ЗАВТРАК|НА КУХНЕ УЖЕ СОВЕЩАНИЕ.|Soviet communal apartment kitchen: stunned man with skillet faces group of neighbors seated seriously around tiny stove|life
lost_keys|ПОЛЧАСА ИСКАЛ КЛЮЧИ|ОНИ ВСЁ ВРЕМЯ БЫЛИ В РУКЕ.|Soviet apartment hallway: exhausted adult searching under cushions while visible bunch of keys clutched in own hand|life
clock_advance|ПЕРЕВЁЛ ЧАСЫ НА ЧАС ВПЕРЁД|РАБОТА ОБРАДОВАЛАСЬ ПЕРВОЙ.|Soviet desk with two vintage alarm clocks showing different times as confused office worker stares and grabs overcoat|life
holiday_photo|ПОПРОСИЛ СДЕЛАТЬ ОДНО ФОТО|ПОЛЧАСА СТОЯЛ КАК ПАМЯТНИК.|Soviet family photographer with vintage camera takes ages; stiff adult man stands frozen posing in park, tired expression|life
weather_hat|ПОСМОТРЕЛ ПРОГНОЗ ПОГОДЫ|НАВСЯКИЙ СЛУЧАЙ НАДЕЛ ВСЁ.|Soviet apartment: man wearing absurd layers of coats, scarf and fur hat in front of window with sunshine, embarrassed|life"""

STORIES = []
for n,raw in enumerate(DATA.splitlines()):
    fields=raw.split("|")
    if len(fields)!=5:
        raise ValueError(f"Malformed SOVETSKIY story at line {n+1}")
    key,top,bottom,visual,theme=fields
    if not (4<len(key)<70 and top and bottom and len(top)<=92
            and len(bottom)<=97 and len(visual)>65):
        raise ValueError(f"Insufficient detail at SOVETSKIY story {key}")
    STORIES.append(Story(key,top,bottom,visual,theme))
assert len(STORIES)==96, f"Expected 96 original short stories, got {len(STORIES)}"
assert len(set(s.id for s in STORIES))==96


def choose_story(state,slot):
    """Never reuse published/scheduled caption; diversify nearby themes.

    Once the finite reviewed writing bank is exhausted, stop rather than
    repeat the same status under a new picture.
    """
    used={e.get("story_id") for e in state.get("entries",[])}
    recent=[e.get("theme") for e in state.get("entries",[])[-6:]]
    choices=[s for s in STORIES if s.id not in used]
    if not choices:
        return None
    # Deterministic preference for variety, not uncontrolled random text.
    import hashlib
    choices.sort(key=lambda s:(
        s.theme in recent,
        int(hashlib.sha256((slot+":"+s.id).encode()).hexdigest()[:12],16)
    ))
    return choices[0]
