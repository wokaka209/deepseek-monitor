from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .deepseek_api import BALANCE_URL, Balance, fetch_balance
from .desktop_integration import (
    config_dir,
    format_refresh_notification,
    installed_app_dir,
    launch_uninstaller,
    set_startup_enabled,
)
from .storage import AppConfig, load_config, save_config


API_DOCS_URL = "https://api-docs.deepseek.com/zh-cn/api/get-user-balance"


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, accent: str, subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("smallText")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.value_label.setStyleSheet(f"color: {accent};")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("smallText")
        self.subtitle_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_values(self, value: str, subtitle: str = "", subtitle_color: str = "#b8c0bb") -> None:
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setStyleSheet(f"color: {subtitle_color};")


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))))
        self.setMinimumWidth(460)

        self.api_key_input = QLineEdit(config.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        self.notifications_input = QCheckBox("启用 Windows 通知")
        self.notifications_input.setChecked(config.notifications_enabled)
        self.auto_refresh_input = QCheckBox("启动后自动刷新余额，并按间隔更新")
        self.auto_refresh_input.setChecked(config.auto_refresh_enabled)
        self.startup_input = QCheckBox("开机启动并最小化到托盘")
        self.startup_input.setChecked(config.startup_enabled)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(5, 1440)
        self.interval_input.setSuffix(" 分钟")
        self.interval_input.setValue(config.refresh_interval_minutes)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("DeepSeek 余额查询")
        title.setObjectName("dialogTitle")
        key_label = QLabel("DeepSeek API Key")
        key_label.setObjectName("smallText")
        endpoint = QLabel(f"余额查询接口：{BALANCE_URL}")
        endpoint.setObjectName("smallText")
        api_docs = QLabel(f'<a href="{API_DOCS_URL}">DeepSeek 官方余额 API 文档</a>')
        api_docs.setObjectName("linkText")
        api_docs.setOpenExternalLinks(True)
        api_docs.setTextInteractionFlags(Qt.TextBrowserInteraction)
        hint = QLabel("API Key 将保存到 Windows 用户目录的本应用配置文件中。")
        hint.setObjectName("smallText")
        hint.setWordWrap(True)

        buttons = QHBoxLayout()
        uninstall_btn = QPushButton("卸载程序")
        cancel_btn = QPushButton("取消")
        save_btn = QPushButton("保存")
        uninstall_btn.clicked.connect(self.request_uninstall)
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(uninstall_btn)
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout.addWidget(title)
        layout.addWidget(key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(endpoint)
        layout.addWidget(api_docs)
        layout.addWidget(self.notifications_input)
        layout.addWidget(self.auto_refresh_input)
        layout.addWidget(self.startup_input)
        layout.addWidget(QLabel("自动刷新间隔"))
        layout.addWidget(self.interval_input)
        layout.addWidget(hint)
        layout.addLayout(buttons)
        self.setStyleSheet(
            """
            QDialog {
                background: #151c1a;
                color: #f4f1e8;
                font-family: "Microsoft YaHei";
            }
            QLabel#dialogTitle {
                color: #f4f1e8;
                font-size: 22px;
                font-weight: 800;
            }
            QLabel#smallText {
                color: #aeb8b3;
                font-size: 12px;
            }
            QLabel#linkText {
                color: #7ac7ff;
                font-size: 12px;
            }
            QCheckBox {
                color: #f4f1e8;
                font-size: 13px;
                spacing: 8px;
            }
            QLineEdit, QSpinBox {
                background: #0b100e;
                color: #f4f1e8;
                border: 1px solid #3a4642;
                border-radius: 8px;
                padding: 9px;
            }
            QPushButton {
                background: rgba(255, 255, 255, 26);
                color: #f4f1e8;
                border: 1px solid rgba(255, 255, 255, 35);
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(121, 108, 255, 95);
            }
            """
        )

    @property
    def api_key(self) -> str:
        return self.api_key_input.text().strip()

    @property
    def notifications_enabled(self) -> bool:
        return self.notifications_input.isChecked()

    @property
    def auto_refresh_enabled(self) -> bool:
        return self.auto_refresh_input.isChecked()

    @property
    def startup_enabled(self) -> bool:
        return self.startup_input.isChecked()

    @property
    def refresh_interval_minutes(self) -> int:
        return self.interval_input.value()

    def request_uninstall(self) -> None:
        reply = QMessageBox.question(
            self,
            "卸载程序",
            f"将启动安装版卸载器，并删除配置目录：\n{config_dir()}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if not launch_uninstaller(installed_app_dir()):
            QMessageBox.information(self, "无法卸载", "当前不是安装版，未找到 unins000.exe。")
            return
        QApplication.instance().quit()


class BalanceRefreshWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, api_key: str) -> None:
        super().__init__()
        self.api_key = api_key

    def run(self) -> None:
        try:
            balance = fetch_balance(self.api_key)
        except Exception as exc:
            self.failed.emit(exc)
        else:
            self.succeeded.emit(balance)
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.balance = Balance(False, "CNY", 0.0)
        self.balance_refresh_thread: Optional[QThread] = None
        self.balance_refresh_worker: Optional[BalanceRefreshWorker] = None
        self.tray = self._create_tray()
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)

        self.setWindowTitle("DeepSeek Monitor")
        self.setWindowIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))))
        self.resize(820, 460)
        self.setMinimumSize(720, 420)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(22, 18, 22, 22)
        main.setSpacing(18)
        main.addLayout(self._build_header())
        main.addWidget(self._build_panel(), 1)

        self.status_label = QLabel("就绪：未配置 API Key 时余额显示 0。")
        self.status_label.setObjectName("smallText")
        main.addWidget(self.status_label)

        self._apply_style()
        self.refresh_view()
        self._schedule_auto_refresh()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title = QLabel("DeepSeek Monitor")
        title.setObjectName("title")
        self.refresh_btn = QPushButton("刷新余额")
        settings_btn = QPushButton("设置")
        self.refresh_btn.clicked.connect(self.refresh_balance)
        settings_btn.clicked.connect(self.open_settings)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        header.addWidget(settings_btn)
        return header

    def _build_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        top = QGridLayout()
        top.setSpacing(14)
        self.balance_card = MetricCard("账户余额", "¥0.00", "#796cff", "未连接 API")
        self.endpoint_card = MetricCard("查询方式", "官方 API", "#82b8ff", BALANCE_URL)
        top.addWidget(self.balance_card, 0, 0)
        top.addWidget(self.endpoint_card, 0, 1)
        layout.addLayout(top)

        help_card = QFrame()
        help_card.setObjectName("card")
        help_layout = QVBoxLayout(help_card)
        help_layout.setContentsMargins(22, 18, 22, 18)
        help_layout.setSpacing(10)
        help_title = QLabel("余额查询")
        help_title.setObjectName("cardTitle")
        help_text = QLabel("在设置中填写 DeepSeek API Key 后，点击刷新余额即可读取官方余额接口。")
        help_text.setObjectName("smallText")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        layout.addWidget(help_card, 1)
        return panel

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))), self)
        menu = QMenu(self)
        show_action = QAction("打开面板", self)
        refresh_action = QAction("刷新余额", self)
        quit_action = QAction("退出", self)
        show_action.triggered.connect(self.showNormal)
        refresh_action.triggered.connect(self.auto_refresh)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(show_action)
        menu.addAction(refresh_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.show()
        return tray

    def _schedule_auto_refresh(self) -> None:
        self.auto_refresh_timer.stop()
        if not self.config.auto_refresh_enabled:
            return
        QTimer.singleShot(1500, self.auto_refresh)
        self.auto_refresh_timer.start(self.config.refresh_interval_minutes * 60 * 1000)

    def refresh_view(self) -> None:
        subtitle, subtitle_color = balance_api_state(self.config.api_key, self.balance)
        self.balance_card.set_values(f"¥{self.balance.total:.2f}", subtitle, subtitle_color)

    def refresh_balance(self) -> None:
        self._start_balance_refresh(show_dialog=True, notify_on_success=False)

    def auto_refresh(self) -> None:
        self._start_balance_refresh(show_dialog=False, notify_on_success=True)

    def _start_balance_refresh(self, show_dialog: bool, notify_on_success: bool) -> None:
        if self.balance_refresh_thread is not None:
            self.status_label.setText("余额正在刷新，请稍候。")
            return
        if not self.config.api_key:
            self.balance = Balance(False, "CNY", 0.0)
            self.status_label.setText("未设置 API Key，余额显示 0。")
            self.refresh_view()
            return

        thread = QThread(self)
        worker = BalanceRefreshWorker(self.config.api_key)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(lambda balance: self._balance_refresh_succeeded(balance, notify_on_success))
        worker.failed.connect(lambda exc: self._balance_refresh_failed(exc, show_dialog))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._balance_refresh_finished)

        self.balance_refresh_thread = thread
        self.balance_refresh_worker = worker
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("余额刷新中。")
        thread.start()

    def _balance_refresh_succeeded(self, balance: Balance, notify_on_success: bool) -> None:
        self.balance = balance
        self.status_label.setText("余额已刷新。")
        self.refresh_view()
        if notify_on_success:
            title, body = format_refresh_notification(self.balance.total)
            self._notify(title, body)

    def _balance_refresh_failed(self, exc: object, show_dialog: bool) -> None:
        message = f"无法获取 DeepSeek 余额：\n{exc}"
        if show_dialog:
            QMessageBox.warning(self, "刷新失败", message)
        else:
            self._notify("DeepSeek Monitor 余额刷新失败", str(exc))
        self.status_label.setText("余额刷新失败，请检查 API Key 或网络。")

    def _balance_refresh_finished(self) -> None:
        self.refresh_btn.setEnabled(True)
        self.balance_refresh_thread = None
        self.balance_refresh_worker = None

    def _notify(self, title: str, body: str) -> None:
        if not self.config.notifications_enabled:
            return
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.showMessage(title, body, QSystemTrayIcon.Information, 8000)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() != QDialog.Accepted:
            return
        self.config.api_key = dialog.api_key
        self.config.notifications_enabled = dialog.notifications_enabled
        self.config.auto_refresh_enabled = dialog.auto_refresh_enabled
        self.config.refresh_interval_minutes = dialog.refresh_interval_minutes
        self.config.startup_enabled = dialog.startup_enabled
        save_config(self.config)
        set_startup_enabled(self.config.startup_enabled)
        self._schedule_auto_refresh()
        self.status_label.setText("设置已保存。")

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #273038, stop:0.45 #18201d, stop:1 #363b40);
                color: #f4f1e8;
                font-family: "Microsoft YaHei";
            }
            QFrame#panel {
                background: rgba(22, 27, 25, 210);
                border: 1px solid rgba(200, 230, 220, 70);
                border-radius: 24px;
            }
            QFrame#card {
                background: rgba(14, 18, 16, 235);
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 16px;
            }
            QLabel#title {
                color: #f4f1e8;
                font-size: 25px;
                font-weight: 800;
            }
            QLabel#smallText {
                color: #b8c0bb;
                font-size: 12px;
            }
            QLabel#metricValue {
                font-size: 34px;
                font-weight: 900;
            }
            QLabel#cardTitle {
                color: #f4f1e8;
                font-size: 18px;
                font-weight: 800;
            }
            QPushButton {
                background: rgba(255, 255, 255, 26);
                color: #f4f1e8;
                border: 1px solid rgba(255, 255, 255, 35);
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(121, 108, 255, 95);
            }
            """
        )


def resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base_path / relative_path


def balance_api_state(api_key: str, balance: Balance) -> tuple[str, str]:
    if not api_key:
        return "未使用 API", "#ff5c5c"
    if balance.is_available:
        return "账户可用", "#49e86f"
    return "已配置 API", "#49e86f"


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))))
    window = MainWindow()
    if "--minimized" not in sys.argv:
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
