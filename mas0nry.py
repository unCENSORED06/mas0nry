import sys
import threading
import logging
import hashlib
import os
from flask import Flask, request, Response
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit,
                             QPushButton, QTabWidget, QAction, QMenuBar, QDialog, QFormLayout, QLabel, QMessageBox)
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote, unquote

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Flask app for proxy server
app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    url = request.args.get('url', path)
    
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # Decode the URL to handle any encoded characters
    url = unquote(url)

    logging.info(f"Proxying request to {url}")

    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers, stream=True, verify=False)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, data=request.data, verify=False)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, data=request.data, verify=False)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers, verify=False)
        else:
            return "Method Not Allowed", 405

        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        proxy_response = Response(
            response.content,
            status=response.status_code,
            headers={'Content-Type': content_type}
        )
        
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']:
                proxy_response.headers[header] = value
        
        return proxy_response
    except requests.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        return str(e), 500

# Utility functions for password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_password_hash(password_hash):
    with open('password_hash.txt', 'w') as f:
        f.write(password_hash)

def load_password_hash():
    if os.path.exists('password_hash.txt'):
        with open('password_hash.txt', 'r') as f:
            return f.read().strip()
    return None

# Global password hash variable
password_hash = load_password_hash()

# PyQt5 Browser Class
class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('mas0nry')
        self.setGeometry(100, 100, 1200, 800)

        self.browser_tabs = QTabWidget()
        self.setCentralWidget(self.browser_tabs)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Enter URL and press Enter...')
        self.url_input.returnPressed.connect(self.load_url)

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_current_tab)

        self.loading_label = QLabel('Loading...')
        self.loading_label.setStyleSheet("color: blue; font-size: 16px;")
        self.loading_label.setVisible(False)

        self.menu_bar = self.menuBar()
        self.settings_menu = self.menu_bar.addMenu('Settings')

        self.settings_action = QAction('Settings', self)
        self.settings_action.triggered.connect(self.open_settings)
        self.settings_menu.addAction(self.settings_action)

        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.settings_menu.addAction(self.about_action)

        layout = QVBoxLayout()
        layout.addWidget(self.url_input)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.browser_tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.add_new_tab()

    def add_new_tab(self, url='https://www.google.com'):
        browser = QWebEngineView()
        browser.page().loadFinished.connect(self.on_load_finished)
        self.browser_tabs.addTab(browser, 'New Tab')
        self.browser_tabs.setCurrentWidget(browser)
        self.load_url_in_tab(browser, url)

    def load_url(self):
        url = self.url_input.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.load_url_in_tab(self.browser_tabs.currentWidget(), url)

    def load_url_in_tab(self, browser, url):
        encoded_url = quote(url, safe=':/?=&')
        proxy_url = f'http://localhost:5000/?url={encoded_url}'
        logging.debug(f"Proxy URL: {proxy_url}")
        self.loading_label.setVisible(True)
        browser.setUrl(QUrl(proxy_url))

    def refresh_current_tab(self):
        current_browser = self.browser_tabs.currentWidget()
        if current_browser:
            current_browser.reload()

    def on_load_finished(self, ok):
        if ok:
            self.loading_label.setVisible(False)
        else:
            self.loading_label.setText('Failed to load page.')
            self.loading_label.setVisible(True)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            global password_hash
            new_password = dialog.password_input.text()
            password_hash = hash_password(new_password)
            save_password_hash(password_hash)
            logging.info("Password has been set.")

    def show_about_dialog(self):
        QMessageBox.information(self, 'About', 'mas0nry\nVersion 0.7.0\n\nUSE THIS AT YOUR OWN RISK! IF YOU GET IN TROUBLE I AM NOT RESPONSIBLE (don’t do illegal stuff basically)')

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Settings')

        self.form_layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.form_layout.addRow(QLabel('Set Password:'), self.password_input)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.accept)
        self.form_layout.addWidget(self.save_button)

        self.setLayout(self.form_layout)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Login')

        self.form_layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.form_layout.addRow(QLabel('Enter Password:'), self.password_input)

        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.check_password)
        self.form_layout.addWidget(self.login_button)

        self.setLayout(self.form_layout)

    def check_password(self):
        global password_hash
        entered_password = self.password_input.text()
        if password_hash is None:
            self.accept()
        elif hash_password(entered_password) == password_hash:
            self.accept()
        else:
            self.password_input.clear()
            self.password_input.setPlaceholderText('Incorrect Password')

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    qt_app = QApplication(sys.argv)

    while True:
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            window = SimpleBrowser()
            window.show()
            sys.exit(qt_app.exec_())
            break
        else:
            QMessageBox.warning(None, 'Access Denied', 'Incorrect password. Please try again.')
