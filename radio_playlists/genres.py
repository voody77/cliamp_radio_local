"""Genre definitions shared by the build scripts."""

# (display name, exact Radio Browser tag)
GENRES: list[tuple[str, str]] = [
    ("Pop", "pop"), ("News", "news"), ("Rock", "rock"), ("Talk", "talk"),
    ("Dance", "dance"), ("Oldies", "oldies"), ("Classical", "classical"),
    ("Jazz", "jazz"), ("80s", "80s"), ("Electronic", "electronic"),
    ("Christian", "christian"), ("Public Radio", "public radio"),
    ("Top 40", "top 40"), ("90s", "90s"), ("Community Radio", "community radio"),
    ("Classic Rock", "classic rock"), ("Adult Contemporary", "adult contemporary"),
    ("House", "house"), ("Local News", "local news"), ("Country", "country"),
    ("Folk", "folk"), ("Alternative", "alternative"), ("Pop Rock", "pop rock"),
    ("70s", "70s"), ("Soul", "soul"), ("Indie", "indie"),
    ("Chillout", "chillout"), ("Gospel", "gospel"), ("Metal", "metal"),
    ("Techno", "techno"), ("News Talk", "news talk"), ("Religious", "religious"),
    ("Ambient", "ambient"), ("Sports", "sports"), ("Easy Listening", "easy listening"),
    ("Lounge", "lounge"), ("Entertainment", "entertainment"), ("Rap", "rap"),
    ("Disco", "disco"), ("Blues", "blues"), ("Funk", "funk"), ("Salsa", "salsa"),
    ("Hip Hop", "hiphop"), ("EDM", "edm"), ("Reggae", "reggae"),
    ("Trance", "trance"), ("Electro", "electro"), ("Smooth Jazz", "smooth jazz"),
    ("World Music", "world music"), ("R&B", "rnb"), ("Deep House", "deep house"),
    ("Hard Rock", "hard rock"), ("Cumbia", "cumbia"), ("Reggaeton", "reggaeton"),
    ("Instrumental", "instrumental"), ("Latin", "latin"), ("Chill", "chill"),
    ("Heavy Metal", "heavy metal"), ("Punk", "punk"), ("Acoustic", "acoustic"),
]

# Hand-picked streams that belong in a genre regardless of catalog votes.
ACOUSTIC_EXTRAS: list[tuple[str, str]] = [
    ("OUI FM Acoustic", "https://ouifmacoustic.ice.infomaniak.ch/ouifmacoustic.mp3"),
    ("Spoon Radio - Acoustic Rock", "https://spoonradioacousticrock.ice.infomaniak.ch/spoon-acousticrock-hd.aac"),
    ("Radio Art - Acoustic Blues", "https://live.radioart.com/fAcoustic_blues.mp3"),
]

RUSSIA_POP_EXTRAS: list[tuple[str, str]] = [
    ("Радио Шоколад", "http://choco.hostingradio.ru:10010/fm"),
    ("Радио Шоколад Нижний Новгород 96.4 FM", "http://online2.gkvr.ru:8000/chocolate_nno_64.aac"),
]
