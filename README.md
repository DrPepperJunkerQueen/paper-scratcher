# Paper-Scratcher

Paper-Scratcher is an arcade-style territory capture game built with Python and Pygame. Inspired by classic paper-capturing mechanics, the game challenges you to claim as much of the map as possible while competing against AI-driven bots. Draw trails outside your safe zone and return to expand your territory, but be careful—if an enemy crosses your trail, or if you cross your own trail, you lose!

## 👥 Authors

This project was developed by:

* [@DrPepperJunkerQueen](https://github.com/DrPepperJunkerQueen) - DrPepperJunkerQueen
* [@kaemiks](https://github.com/kaemiks) - Kaemiks
* [@Kokoszka2004](https://github.com/Kokoszka2004) - Kokoszka
* [@kacper207](https://github.com/kacper207) - kacperr

## 🌟 Features

* **Dynamic Territory Capture:** Venture outside your base to draw lines and enclose new areas. Connect back to your base to claim the territory and expand your polygon.
* **Smart AI Bots:** Compete against 3 distinct bots (colored orange, green, and lime) that randomly explore, hunt for power-ups, return to their base when vulnerable, and actively try to cut your trail.
* **Power-Ups:** Collect yellow speed items on the map that grant a temporary 2x speed boost for 300 ticks. The `PowerUpManager` ensures a maximum of 3 power-ups can spawn on the map at the same time.
* **Audiovisual Feedback:** Picking up a power-up plays a custom sound effect (`MyLifebelikememe.mp3`) and adds visual pulsing effects to your character and territory. Winning plays a victory sound (`awiwawiwados.mp3`), while losing triggers a defeat sound (`defeat.mp3`).
* **Advanced Polygon Algorithms:** Customize how captured areas are calculated directly from the settings menu.
* **Convex Hull Generation:** A simple and fast territory filling algorithm.
* **Concave Hull (Alpha Shapes):** Uses customizable alpha values for highly realistic and precise path tracing.
* **Delaunay Triangulation:** Employs an experimental, highly detailed territory expansion logic that creates mini-hulls per triangle.
* **Area Smoothing:** Interpolates points for visually appealing, rounded edges on all captured territories.
* **Skin System:** Choose and customize your character's appearance in the skins menu using local image files loaded from your resources folder.
* **Win Condition:** Dominate the game by capturing over 80% of the total map area.

## 🎮 Controls

* **Arrow Keys (Up, Down, Left, Right):** Move your character across the screen.
* **ESC:** Pause the game and return to the Main Menu.
* **R:** Restart the game, resetting the player, bots, and power-ups after a Game Over or Victory.

## 🛠️ Tech Stack

* **Language:** Python 3.
* **Framework:** Pygame.
* **Math & Geometry:** Custom algorithmic implementations of Cross Products, Circumcenters, Alpha Shapes, and Polygon Union/Difference.

## 📁 Project Structure

* `main.py` - Game entry point and Pygame scene loop initialization.
* `constants.py` - Global configuration including screen dimensions, colors, fonts, and power-up spawn rates.
* `scenes/` - Contains different game UI states such as `splash.py`, `main_menu.py`, `game.py`, `settings.py`, and `skin_selection.py`.
* `scenes/game_mechanics/` - Contains the core entity logic in `PaperBot.py`, `PaperPlayer.py`, and `PowerUp.py`.
* `resources/` - Assets folder including skins, menu fonts (`CHLORINR.TTF`), and game sound effects.
