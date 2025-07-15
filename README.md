# Q_SNAKE

A modern take on the classic Snake game with enhanced graphics, physics, and gameplay features.

![Q_SNAKE Game](https://github.com/Egregius/AmazonBuildersChallenge_RetroGame
/pictures/screenshot.png)

## Features

- **Beautiful Graphics**: Smooth animations, particle effects, and visual enhancements
- **Multiple Difficulty Levels**: Choose from Easy, Normal, Hard, or Insane
- **Bonus Food System**: Special golden food appears periodically for extra points
- **High Score Tracking**: Your best scores are saved between sessions
- **Ornate Game Frame**: Decorative border enhances the visual experience
- **Procedural Environment**: Dynamic grass and rocks create a living game world

## Installation

### Prerequisites

- Python 3.6 or higher
- Pip package manager

### Required Libraries

```bash
pip install arcade pymunk opensimplex perlin-noise numpy scipy
```

### Running the Game

```bash
python Snake_game.py
```

## How to Play

### Controls

- **Arrow Keys**: Control snake direction
- **SPACE**: Start game / Pause game
- **ESC**: Return to menu (when paused or game over)
- **↑↓ Arrows**: Select difficulty level in menu

### Gameplay

1. **Objective**: Guide the snake to eat food and grow as long as possible without hitting walls or itself
2. **Regular Food**: Red apples worth 10 points
3. **Bonus Food**: Golden apples worth 50 points (disappear after 8 seconds)
4. **Game Over**: Occurs when snake hits a wall or itself

### Difficulty Levels

- **Easy**: Speed 5 - Relaxed gameplay
- **Normal**: Speed 8 - Standard challenge
- **Hard**: Speed 12 - Fast-paced action
- **Insane**: Speed 16 - Extreme reflexes required

## Development

This game was built using:
- **Arcade**: For graphics rendering and game loop
- **PyMunk**: For physics simulation
- **OpenSimplex/Perlin**: For procedural texture generation

## Credits

Developed as part of the Builder Challenge with Amazon Q.

## License

This project is open source and available under the MIT License.
