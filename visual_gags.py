"""Visual jokes for SHAM: a scene should be funny before anyone reads text.

Each action is original visual adaptation of classic short everyday joke themes;
no scraped photos or third-party comic images, no Openverse.
"""
VISUAL_GAGS = {
    # Work
    "five_minute_meeting": "An exhausted employee stuck on a laptop video meeting, completely covered in cobwebs as an enormous wall clock spins and coffee fossilizes on the desk, ridiculous time-lapse gag",
    "boss_friday": "An office employee trying to sneak out at 17:59 Friday while a giant grinning boss blocks the door with a tower of papers higher than the employee",
    "excel": "A shocked employee trying to fix one spreadsheet cell, hundreds of glowing spreadsheet cells burst out of laptop like angry little ghosts in the office",
    "deadline": "A terrified office worker running from a huge angry anthropomorphic wall clock with teeth, carrying a stack of work documents, funny panic",
    "after_vacation": "A returning office worker drowning under a gigantic ridiculous waterfall of paper emails from laptop, tiny tourist suitcase in one hand",
    # Money
    "salary": "A shocked adult staring at phone bank balance while a giant cartoonish vacuum cleaner made of utility bills sucks the entire salary out of a wallet",
    "grocery_total": "A stunned shopper holding three tiny groceries while a ridiculously long supermarket receipt snakes around the whole person and coils into the ceiling",
    "discount": "A confused shopper buried under huge sale signs and useless shopping bags, empty wallet crawling away, ridiculous sale trap",
    "rent": "A panicked tenant next to a tiny apartment door with enormous teeth eating a wallet, absurd rent monster in an ordinary apartment hallway",
    "subscriptions": "A surprised man being chased by many tiny human-shaped subscription bills jumping out of smartphone, coins raining from torn wallet",
    # Phone
    "scrolling": "A sleepy adult in bed under a blanket checking phone, huge clock indicates sunrise, tiny comic raccoons from videos climbing around pillow",
    "battery": "A desperate adult on a street holding dying phone while a tiny dead phone battery lies in a cartoon coffin and giant power cord runs away",
    "screen_time": "A horrified adult looking at enormous smartphone screen time chart that grows out of phone into a towering building, tiny person crushed by scrolling hours",
    "photo_gallery": "An adult cringing in shock at awkward old photographs emerging out of phone like a messy parade of younger embarrassing selves",
    "notifications": "An overwhelmed adult surrounded by hundreds of angry notification bubbles jumping from smartphone and tugging at clothes",
    # Home
    "fridge": "A hungry adult opening empty refrigerator again; lonely ketchup bottle sits on a tiny throne inside fridge with a crown, frustrated human holding empty plate",
    "dishes": "A tired person fighting a huge army of living dirty plates and forks with one tiny sponge, ridiculous battlefield in messy kitchen",
    "cleaning": "An exhausted cleaner trapped in a mountain of bizarre forgotten gadgets and dusty old cables after starting to tidy the living room",
    "socks": "A bewildered person holding one lonely sock in front of washing machine that suspiciously hides other socks behind its back like a thief",
    "delivery": "A starving adult looking at phone delivery map with binoculars while tiny courier circles around one block in the rain for hours",
    # Social
    "need_talk": "Terrified adult staring at phone message, their tiny imaginary lawyer and judge pop up over shoulders as if facing a trial in their own apartment",
    "typing": "An extremely nervous adult handcuffed to a giant smartphone with three mysterious typing dots, surrounding clocks spin and coffee mugs stack up",
    "date": "A nervous adult at a cafe first date presenting a supermarket discount coupon like a romantic bouquet, date looks confused, exaggerated awkwardness",
    "voice_messages": "An aging adult with long cobweb-covered beard listening to enormous eight-minute voice message on phone while a mountain of used coffee cups grows around",
    "groupchat": "A shocked person in front of giant phone as hundreds of tiny arguing chat bubbles with funny expressions fly out like a noisy flock",
    # Everyday life
    "alarm": "A sleepy adult wrestling a giant angry alarm clock with boxing gloves while the duvet pulls them back into bed",
    "weekend": "A man on a sofa being chased by huge hungry Monday calendar page that eats tiny Saturday and Sunday calendar pages",
    "adult_bills": "An overwhelmed adult sitting at kitchen table as giant utility bills grow arms and legs and form an angry queue waiting to collect coins",
    "fitness": "An exhausted adult lying next to tiny pink dumbbell as the dumbbell poses triumphantly with muscles and a coach applauds the weight",
    "to_do": "A baffled adult buried under a mile-long to-do checklist wrapping the room, only one giant tick next to 'write to-do list'",
}
assert len(VISUAL_GAGS)==30

def get_visual_gag(post):
    return post.get("visual_gag") or VISUAL_GAGS.get(post.get("topic")) or post.get("visual")
