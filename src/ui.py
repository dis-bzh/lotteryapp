import os
import sys
import random
import math

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QRectF, QElapsedTimer, QUrl
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from src.config import (
    WINDOW_TITLE, LABEL_INSTRUCTION, BUTTON_INITIALIZE_TEXT, BUTTON_DRAW_TEXT,
    CHECKBOX_TEXT, LABEL_RESULT_INITIAL, LABEL_WINNERS
)
from src.lottery_logic import parse_input
from src.resources import resource_path


class ScrollingSquaresWidget(QWidget):
    """
    Widget that displays scrolling squares with numbers cycling in a loop.
    The animation runs for a fixed duration and for a given number of cycles.
    The scroll stops when the winning square is aligned at target_alignment_x.
    """
    def __init__(self, numbers=None, parent=None):
        super().__init__(parent)
        self.numbers = numbers or []  # List of numbers to display
        self.offset = 0               # Horizontal offset (in pixels)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.square_size = 60         # Size (width and height) of each square
        self.spacing = 10             # Space between squares

        # Alignment position (in pixels) for the center of the winning square.
        self.target_alignment_x = 50

        self.result_callback = None   # Callback to be invoked at animation end
        self.winning_index = None     # Index of the winning square

        # Animation parameters
        self.animation_duration = 10000  # Duration in ms (default)
        self.animation_start_time = None
        self.start_offset = 0
        self.target_offset = 0
        self.initial_velocity = 0
        self.deceleration_value = 0

    def set_numbers(self, numbers):
        """Update the list of numbers to be displayed."""
        self.numbers = numbers
        print("Initialized number list:", self.numbers)
        self.update()

    def set_result_callback(self, callback):
        """
        Set the callback function to be called at the end of the animation.
        The function will receive the winning number as its argument.
        """
        self.result_callback = callback

    def start_scroll(self, winning_index, duration=2000, cycles=3):
        """
        Start the scrolling animation that runs for a given duration and cycles.
        The winning square (specified by winning_index) will be aligned with target_alignment_x.
        """
        if not self.numbers:
            return

        self.winning_index = winning_index
        step = self.square_size + self.spacing
        
        # Calculate target offset so that the winning square is centered at target_alignment_x.
        self.target_offset = self.target_alignment_x - (winning_index * step) - (self.square_size / 2)
        
        # Calculate the total width of one cycle (all numbers).
        cycle_width = len(self.numbers) * step
        
        # Start the animation at an offset that gives "cycles" extra loops before stopping.
        self.start_offset = self.target_offset - cycles * cycle_width
        self.offset = self.start_offset

        # Set the duration for the animation (in ms)
        self.animation_duration = duration
        T = duration / 1000.0  # Duration in seconds
        
        # Total distance S to travel
        S = self.target_offset - self.start_offset
        
        # Calculate initial velocity and deceleration for uniformly decelerated motion
        self.initial_velocity = 2 * S / T
        self.deceleration_value = 2 * S / (T ** 2)
        
        # Start the timer to measure elapsed time
        self.animation_start_time = QElapsedTimer()
        self.animation_start_time.start()
        
        self.timer.start(20)

    def animate(self):
        """Update the horizontal offset using uniformly decelerated motion."""
        elapsed_ms = self.animation_start_time.elapsed()  # in ms
        t = elapsed_ms / 1000.0  # Convert to seconds
        T = self.animation_duration / 1000.0

        if t >= T:
            self.offset = self.target_offset
            self.timer.stop()
            if self.result_callback:
                try:
                    winning_number = self.numbers[self.winning_index]
                except IndexError:
                    winning_number = None
                self.result_callback(winning_number)
            self.update()
            return

        # Equation of uniformly decelerated motion: offset = start_offset + v0*t - 0.5*a*t².
        self.offset = self.start_offset + self.initial_velocity * t - 0.5 * self.deceleration_value * t * t
        self.update()

    def paintEvent(self, event):
        """Draw the scrolling squares with numbers."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        step = self.square_size + self.spacing

        if not self.numbers:
            painter.drawText(10, 20, "Liste vide")
            return

        width = self.width()
        # Determine index bounds to cover the widget width.
        i_min = int(math.floor((-self.offset) / step)) - 1
        i_max = int(math.ceil((width - self.offset) / step)) + 1

        for i in range(i_min, i_max + 1):
            num = self.numbers[i % len(self.numbers)]
            x = self.offset + i * step
            y = (self.height() - self.square_size) / 2
            rect = QRectF(x, y, self.square_size, self.square_size)

            # Draw only if the square is (partially) visible.
            if rect.right() < 0 or rect.left() > width:
                continue

            color = QColor(200, 200, 255) if (i % 2 == 0) else QColor(180, 220, 180)
            painter.setBrush(color)
            painter.setPen(QPen(Qt.black, 2))
            painter.drawRect(rect)

            font = QFont("Arial", 14, QFont.Bold)
            painter.setFont(font)
            text = str(num)
            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(text)
            text_height = fm.height()
            text_x = x + (self.square_size - text_width) / 2
            text_y = y + (self.square_size + text_height) / 2 - fm.descent()
            painter.drawText(int(text_x), int(text_y), text)

        # Draw a dashed red line for alignment.
        painter.setPen(QPen(Qt.red, 3, Qt.DashLine))
        painter.drawLine(self.target_alignment_x, 0, self.target_alignment_x, self.height())


class TirageApp(QWidget):
    """
    Main widget for the lottery drawing application.
    Manages the number list input, animation, sound effects, and results.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.original_list = []  # Original list of numbers
        self.current_list = []   # List used for drawing (modifiable)
        self.winners = []        # List of previously drawn winning numbers

        # For deferred removal in case of "remise en jeu"
        self.last_winner = None

        self.setup_ui()

        # Prepare the sound lists from the "sounds/wheel" and "sounds/winner" directories.
        base_dir = resource_path("sounds")
        self.wheel_sounds = self.load_sounds(os.path.join(base_dir, "wheel"))
        self.winner_sounds = self.load_sounds(os.path.join(base_dir, "winner"))
        print("Loaded wheel sounds:", self.wheel_sounds)
        print("Loaded winner sounds:", self.winner_sounds)

        # Media players for sound playback
        self.wheel_player = None
        self.winner_player = None
        # Timer for fading out the wheel sound
        self.wheel_fade_timer = QTimer(self)

    def load_sounds(self, directory):
        """
        Load the full paths of all .mp3 files in a directory.
        """
        sounds = []
        if os.path.isdir(directory):
            for file in os.listdir(directory):
                if file.lower().endswith(".mp3"):
                    full_path = os.path.join(directory, file)
                    sounds.append(full_path)
        return sounds

    def setup_ui(self):
        """Arrange all UI elements."""
        layout = QVBoxLayout()

        self.label_instruction = QLabel(LABEL_INSTRUCTION)
        layout.addWidget(self.label_instruction)

        self.input_field = QLineEdit()
        layout.addWidget(self.input_field)

        self.checkbox_remise = QCheckBox(CHECKBOX_TEXT)
        self.checkbox_remise.setChecked(True)
        layout.addWidget(self.checkbox_remise)

        self.button_initialize = QPushButton(BUTTON_INITIALIZE_TEXT)
        self.button_initialize.clicked.connect(self.initialize_list)
        layout.addWidget(self.button_initialize)

        self.label_result = QLabel(LABEL_RESULT_INITIAL)
        self.label_result.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.label_result)

        # Label to show the list of previous winners.
        self.label_winners = QLabel(LABEL_WINNERS)
        self.label_winners.setFont(QFont("Arial", 12))
        layout.addWidget(self.label_winners)

        self.scrolling_widget = ScrollingSquaresWidget()
        self.scrolling_widget.set_result_callback(self.on_scroll_result)
        layout.addWidget(self.scrolling_widget)

        self.button_draw = QPushButton(BUTTON_DRAW_TEXT)
        self.button_draw.clicked.connect(self.lancer_tirage)
        self.button_draw.setEnabled(False)
        layout.addWidget(self.button_draw)

        self.setLayout(layout)

    def initialize_list(self):
        """
        Initialize the number list based on user input and shuffle it.
        """
        input_str = self.input_field.text()
        if not input_str.strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir une liste de nombres ou intervalles.")
            return

        self.original_list = parse_input(input_str)
        if not self.original_list:
            QMessageBox.warning(self, "Erreur", "La liste entrée est invalide ou vide.")
            return

        random.shuffle(self.original_list)
        self.current_list = self.original_list.copy()
        self.label_result.setText("Liste initialisée. Prêt pour le tirage !")
        self.scrolling_widget.set_numbers(self.current_list)
        self.button_draw.setEnabled(True)
        
        # Reset winners and last winner.
        self.winners = []
        self.label_winners.setText(LABEL_WINNERS)
        self.last_winner = None

    def lancer_tirage(self):
        """
        Launch the drawing process:
          - If the "remise en jeu" option is active and a previous winner exists,
            that number is removed from the available list.
          - Randomly select a winning index.
          - Start the scrolling animation.
          - Play a wheel sound during the animation.
        """
        if self.checkbox_remise.isChecked() and self.last_winner is not None:
            try:
                self.current_list.remove(self.last_winner)
                print(f"Deferred removal of number {self.last_winner} before next draw.")
            except ValueError:
                pass
            self.last_winner = None

        if not self.current_list:
            QMessageBox.information(self, "Information", "Plus aucun numéro disponible.")
            return

        winning_index = random.randrange(len(self.current_list))
        self.label_result.setText("Tirage en cours...")
        self.scrolling_widget.set_numbers(self.current_list)

        # Start playing the wheel sound.
        self.play_wheel_sound()

        # Start the scrolling animation: 10 seconds duration and 3 cycles.
        self.scrolling_widget.start_scroll(winning_index, duration=10000, cycles=3)

    def on_scroll_result(self, winning_number):
        """
        Callback invoked at the end of the scrolling animation.
          - Initiates fade-out of the wheel sound.
          - Plays a winner sound.
          - Displays the winning number and updates the winners list.
          - Depending on the "remise en jeu" option, the number is either removed immediately or deferred.
        """
        if self.wheel_player is not None:
            self.stop_wheel_sound()

        self.play_winner_sound()

        if winning_number is not None:
            self.label_result.setText(f"Le numéro gagnant est : {winning_number}")
            self.winners.append(winning_number)
            self.label_winners.setText(LABEL_WINNERS + " " + ", ".join(map(str, self.winners)))
            
            if self.checkbox_remise.isChecked():
                self.last_winner = winning_number
            else:
                try:
                    self.current_list.remove(winning_number)
                except ValueError:
                    pass
                if not self.current_list:
                    QMessageBox.information(self, "Information", "Tous les numéros ont été tirés.")
        else:
            self.label_result.setText("Erreur dans le tirage.")

    def play_wheel_sound(self):
        """
        Randomly select a sound from the 'sounds/wheel' folder and play it in a loop.
        If no sound is found, print a debug message.
        """
        if not self.wheel_sounds:
            print("No sound found in 'wheel' directory.")
            return

        sound_file = random.choice(self.wheel_sounds)
        print("Playing wheel sound:", sound_file)

        url = QUrl.fromLocalFile(sound_file)
        
        # Create the media player for the wheel sound.
        self.wheel_player = QMediaPlayer(self)
        self.wheel_player.setMedia(QMediaContent(url))
        self.wheel_player.setVolume(100)

        self.wheel_player.error.connect(lambda: print("Error wheel_player:", self.wheel_player.errorString()))
        self.wheel_player.stateChanged.connect(lambda state: print("wheel_player stateChanged:", state))
        self.wheel_player.mediaStatusChanged.connect(self.handle_wheel_media_status)

        self.wheel_player.play()
        print("wheel_player state:", self.wheel_player.state())

    def handle_wheel_media_status(self, status):
        from PyQt5.QtMultimedia import QMediaPlayer
        print("wheel_player mediaStatusChanged:", status)
        # Typically, status 2 corresponds to LoadedMedia.
        if status == QMediaPlayer.LoadedMedia:
            print("Media loaded, playing wheel sound...")
            self.wheel_player.play()

    def stop_wheel_sound(self):
        """
        Initiate fade-out of the wheel sound; gradually reduce the volume before stopping playback.
        """
        self.wheel_fade_timer.timeout.connect(self.fade_out_wheel)
        self.wheel_fade_timer.start(50)

    def fade_out_wheel(self):
        """
        Gradually decrease the volume of the wheel_player.
        When the volume reaches 0, stop the timer and then the playback.
        """
        if self.wheel_player is None:
            self.wheel_fade_timer.stop()
            return

        current_volume = self.wheel_player.volume()
        if current_volume > 0:
            new_volume = max(0, current_volume - 5)
            self.wheel_player.setVolume(new_volume)
            print("Fading wheel sound, volume:", new_volume)
        else:
            self.wheel_fade_timer.stop()
            self.wheel_player.stop()
            print("Wheel sound completely stopped.")

    def play_winner_sound(self):
        """
        Randomly select a sound from the 'sounds/winner' folder and play it once.
        If no sound is found, print a debug message.
        """
        if not self.winner_sounds:
            print("No sound found in 'winner' directory.")
            return

        sound_file = random.choice(self.winner_sounds)
        print("Playing winner sound:", sound_file)

        url = QUrl.fromLocalFile(sound_file)
        
        self.winner_player = QMediaPlayer(self)
        self.winner_player.setMedia(QMediaContent(url))
        self.winner_player.setVolume(100)

        self.winner_player.error.connect(lambda: print("Error winner_player:", self.winner_player.errorString()))
        self.winner_player.stateChanged.connect(lambda state: print("winner_player stateChanged:", state))
        self.winner_player.mediaStatusChanged.connect(self.handle_winner_media_status)

        self.winner_player.play()
        print("winner_player state:", self.winner_player.state())

    def handle_winner_media_status(self, status):
        from PyQt5.QtMultimedia import QMediaPlayer
        print("winner_player mediaStatusChanged:", status)
        if status == QMediaPlayer.LoadedMedia:
            print("Winner media loaded, playing sound...")
            self.winner_player.play()

# If you run ui.py directly (for debugging), uncomment the following block:
# if __name__ == "__main__":
#     from PyQt5.QtWidgets import QApplication
#     app = QApplication(sys.argv)
#     window = TirageApp()
#     window.resize(500, 600)
#     window.show()
#     sys.exit(app.exec_())
