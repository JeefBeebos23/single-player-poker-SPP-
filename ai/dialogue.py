import random
from ai.personality import Personality

_LINES: dict[str, dict[int, list[str]]] = {
    'bluff_attempt': {
        0: ["Hehe, what could I have?", "I definitely have something...", "Uh... I raise? Yeah."],
        1: ["Bold move on my part.", "Let's see if you're reading me.", "Worth a shot."],
        2: ["...", "Interesting spot.", "You should fold here."],
    },
    'bluff_success': {
        0: ["I WIN! Did you see that?!", "You fell for it! Ha!", "I always win!"],
        1: ["Nice.", "You'll get me next time.", "Good read... on my part."],
        2: ["Expected.", "I had you from the start.", "That was elementary."],
    },
    'win_pot': {
        0: ["YESSS! I'm amazing!", "Easy money!", "Did that just happen?"],
        1: ["Good hand.", "I'll take that.", "Felt that one."],
        2: ["Correct.", "As projected.", "You played that poorly."],
    },
    'lose_big': {
        0: ["What?! No fair!", "That was totally rigged.", "I was robbed!"],
        1: ["Ouch.", "I'll get it back.", "Didn't see that coming."],
        2: ["Suboptimal outcome.", "I'll adjust.", "You got lucky. Once."],
    },
    'player_raises': {
        0: ["Oooh scary...", "You're bluffing, right?", "I call! Probably."],
        1: ["You sure about that?", "Big bet.", "I see you."],
        2: ["I counted that.", "You've done this before. Twice.", "Noted."],
    },
    'player_folds': {
        0: ["Haha you're scared!", "Smart! I had the nuts!", "Bye bye!"],
        1: ["Good fold.", "Mm.", "Another time."],
        2: ["Correct decision.", "You're learning.", "..."],
    },
    'showdown': {
        0: ["Let's GOOO!", "Oh no oh no...", "I feel good about this!"],
        1: ["Here we go.", "Show 'em.", "Let's see it."],
        2: ["I know what you have.", "This ends here.", "..."],
    },
}


def get_line(trigger: str, difficulty: int, personality: Personality) -> str | None:
    """
    Return a dialogue line for the given trigger, or None if the bot stays silent.
    Respects talk_frequency from personality.
    """
    if random.random() > personality.talk_frequency:
        return None
    lines = _LINES.get(trigger, {}).get(difficulty, [])
    if not lines:
        return None
    return random.choice(lines)


def all_triggers() -> list[str]:
    return list(_LINES.keys())
