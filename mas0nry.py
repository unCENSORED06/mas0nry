import sys
import os
import bcrypt  # Import bcrypt for password hashing
from flask import Flask, request, Response
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTabWidget, QDialog, QFormLayout, QLabel, QMessageBox, QMenuBar, QMenu, QToolBar
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import QUrl, QThread
from PyQt6.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote, unquote
from PyQt6.QtMultimedia import QSoundEffect  # Use QSoundEffect for audio
import threading

# Flask app for proxy server
app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to allow cross-origin requests."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    """Proxy requests to external URLs."""
    url = request.args.get('url', path)

    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    url = unquote(url)

    try:
        # Forward request
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers.items() if key.lower() != 'host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True
        )

        # Filter and forward headers
        excluded_headers = ['content-length', 'transfer-encoding', 'connection']
        forwarded_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in excluded_headers
        }

        # Return response with forwarded content and headers
        proxy_response = Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            headers=forwarded_headers,
        )
        proxy_response.headers['Content-Type'] = response.headers.get('Content-Type', 'application/octet-stream')
        return proxy_response

    except requests.RequestException as e:
        return f"Error proxying the request: {e}", 500

# Password hashing utilities with bcrypt
def hash_password(password):
    """Generate a bcrypt hash of the password."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def save_password_hash(password_hash):
    """Save the password hash to a file."""
    with open('password_hash.txt', 'w') as f:
        f.write(password_hash)

def load_password_hash():
    """Load the password hash from a file, or initialize it if it doesn't exist."""
    if os.path.exists('password_hash.txt'):
        with open('password_hash.txt', 'r') as f:
            return f.read().strip()
    else:
        # If the file does not exist, initialize it with a default password hash
        default_password = "defaultpassword"  # You can change this
        hashed_password = hash_password(default_password)
        save_password_hash(hashed_password)
        return hashed_password

# Function to verify password
def verify_password(stored_hash, password):
    """Verify the entered password against the stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

# Global password hash
password_hash = load_password_hash()

# PyQt6 Web Browser
class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Ensure password is correct before starting the main app
        if not self.ask_for_password():
            sys.exit()  # Exit if the password is incorrect

        self.setWindowTitle('mas0nry')
        self.setGeometry(100, 100, 1200, 800)
        self.dark_mode = False

        # Layout for URL input and browser tabs
        self.main_layout = QVBoxLayout()

        # Browser Tab Setup
        self.browser_tabs = QTabWidget()
        self.browser_tabs.setTabsClosable(True)
        self.browser_tabs.tabCloseRequested.connect(self.close_tab)
        self.main_layout.addWidget(self.browser_tabs)

        # Set layout for the main window
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Menu Bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)

        # Settings Menu
        settings_menu = QMenu('Settings', self)
        self.menu_bar.addMenu(settings_menu)

        # Toggle Theme Action
        toggle_theme_action = QAction('Toggle Theme', self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(toggle_theme_action)

        # Change Password Action
        change_password_action = QAction('Change Password', self)
        change_password_action.triggered.connect(self.change_password)
        settings_menu.addAction(change_password_action)

        # About Action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        settings_menu.addAction(about_action)

        # Add new tab button to toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        new_tab_action = QAction('New Tab', self)
        new_tab_action.triggered.connect(self.add_new_tab)
        self.toolbar.addAction(new_tab_action)

        # Add initial tab
        self.add_new_tab()

    def add_new_tab(self):
        """Add a new browser tab."""
        browser = QWebEngineView()
        browser.setUrl(QUrl('https://www.google.com'))  # Open Google by default
        self.browser_tabs.addTab(browser, 'New Tab')
        self.browser_tabs.setCurrentWidget(browser)
        browser.urlChanged.connect(self.update_tab_title)

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.browser_tabs.count() > 1:
            self.browser_tabs.removeTab(index)
        else:
            self.add_new_tab()  # Prevent closing the last tab

    def update_tab_title(self, url):
        """Update the tab title to reflect the page title."""
        browser = self.browser_tabs.currentWidget()
        if browser:
            self.browser_tabs.setTabText(self.browser_tabs.indexOf(browser), browser.title())

    def load_url(self):
        """Load the URL from the input field into the current tab."""
        url = self.url_input.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.load_url_in_tab(self.browser_tabs.currentWidget(), url)

    def load_url_in_tab(self, browser, url):
        """Load the URL into the specific tab."""
        encoded_url = quote(url, safe=':/?=&')
        proxy_url = f'http://localhost:5000/?url={encoded_url}'
        browser.setUrl(QUrl(proxy_url))

    def toggle_theme(self):
        """Toggle between dark and light mode."""
        self.dark_mode = not self.dark_mode
        theme = """
        QMainWindow {
            background-color: #282C34;
            color: white;
        }
        QTabWidget::pane {
            border: 1px solid #444;
        }
        QTabBar::tab {
            background: #444;
            color: white;
            padding: 5px;
        }
        QTabBar::tab:selected {
            background: #282C34;
        }
        """ if self.dark_mode else """
        QMainWindow {
            background-color: white;
            color: black;
        }
        QTabWidget::pane {
            border: 1px solid #ddd;
        }
        QTabBar::tab {
            background: #fff;
            color: black;
            padding: 5px;
        }
        QTabBar::tab:selected {
            background: #f5f5f5;
        }
        """
        self.setStyleSheet(theme)

    def change_password(self):
        """Open the Change Password dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            global password_hash
            new_password = dialog.password_input.text()
            password_hash = hash_password(new_password)
            save_password_hash(password_hash)
            QMessageBox.information(self, 'Success', 'Password has been changed.')

    def show_about_dialog(self):
        """Show the About dialog with an image and audio using QSoundEffect."""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About mas0nry")

        layout = QVBoxLayout()

        # Add image to the about dialog
        image_label = QLabel()
        pixmap = QPixmap("mas0nry.png")  # Provide the correct path to your image file
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

        # Add description
        description_label = QLabel('mas0nry\nVersion 0.8.0 "Red Dwarf"\nUSE THIS AT YOUR OWN RISK!')
        layout.addWidget(description_label)

        # Play sound using QSoundEffect
        sound = QSoundEffect()
        sound.setSource(QUrl.fromLocalFile('about.wav'))  # Path to your WAV file
        sound.setVolume(1.0)  # Set volume (0.0 to 1.0)
        sound.play()  # Play the sound effect

        about_dialog.setLayout(layout)
        about_dialog.exec()

    def ask_for_password(self):
        """Ask user for password before proceeding."""
        password_dialog = PasswordDialog(self)
        if password_dialog.exec() == QDialog.DialogCode.Accepted:
            entered_password = password_dialog.password_input.text()
            if verify_password(password_hash, entered_password):
                return True
            else:
                QMessageBox.warning(self, 'Incorrect Password', 'The password you entered is incorrect.')
                return False
        return False

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Change Password')
        self.setGeometry(400, 300, 300, 150)

        self.form_layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow('New Password:', self.password_input)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.accept)
        self.form_layout.addWidget(self.save_button)

        self.setLayout(self.form_layout)

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Password Required')
        self.setGeometry(400, 300, 300, 150)

        self.form_layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow('Enter Password:', self.password_input)

        self.save_button = QPushButton('OK')
        self.save_button.clicked.connect(self.accept)
        self.form_layout.addWidget(self.save_button)

        self.setLayout(self.form_layout)

# Run Flask and PyQt6
def start_flask():
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start PyQt6 application
    app = QApplication(sys.argv)
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())
