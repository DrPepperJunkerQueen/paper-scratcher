SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SPLASH_IMAGE_PATH = "resources/splash.png"
SPLASH_SOUND_PATH = "resources/splash.mp3"
TITLE_FONT_PATH = "resources/chlorinar/CHLORINR.TTF"
SKIN_IMAGE_PATHS = [
    "resources/skins/skin1.png",
    "resources/skins/skin2.png",
    "resources/skins/skin3.png",
]
SELECTED_SKIN_INDEX = 0  # Indeks wybranego skina
SKIN_SIZE = 15  # Rozmiar skina na planszy

# NOWE: Ustawienia otoczki
USE_CONCAVE_HULL = True  # True = otoczka wklęsła (bardziej realistyczna), False = otoczka wypukła
CONCAVE_ALPHA = 2.0  # Parametr alpha dla algorytmu alpha shapes (im mniejszy, tym bardziej szczegółowa otoczka)