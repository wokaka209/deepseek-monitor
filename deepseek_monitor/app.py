from __future__ import annotations

import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QLineF, QRectF, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
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

from .deepseek_api import Balance, fetch_balance
from .deepseek_api import BALANCE_URL
from .desktop_integration import (
    config_dir,
    format_refresh_notification,
    installed_app_dir,
    launch_uninstaller,
    remaining_cooldown_seconds,
    set_startup_enabled,
)
from .platform_usage import PlatformRateLimitError, fetch_platform_balance, fetch_platform_usage
from .storage import AppConfig, load_config, load_usage_csv, save_config, save_usage_csv
from .usage import UsageMetric, UsageSummary, aggregate_usage, parse_usage_csv, sample_usage

API_DOCS_URL = "https://api-docs.deepseek.com/zh-cn/api/get-user-balance"
PLATFORM_USAGE_URL = "https://platform.deepseek.com/usage"


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, accent: str, subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(7)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("smallText")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.value_label.setStyleSheet(f"color: {accent};")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("smallText")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_values(self, value: str, subtitle: str = "") -> None:
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)


def create_model_row(model: str, metric: UsageMetric, max_tokens: int, accent: str) -> QFrame:
    row = QFrame()
    row.setObjectName("modelRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(14)

    badge = QLabel("◆")
    badge.setAlignment(Qt.AlignCenter)
    badge.setFixedSize(42, 42)
    badge.setObjectName("badge")
    badge.setStyleSheet(f"color: {accent};")

    text_box = QVBoxLayout()
    text_box.setSpacing(3)
    name = QLabel(model)
    name.setObjectName("modelName")
    tokens = QLabel(f"{format_number(metric.tokens)} Tokens")
    tokens.setObjectName("smallText")
    text_box.addWidget(name)
    text_box.addWidget(tokens)

    right_box = QVBoxLayout()
    right_box.setSpacing(3)
    cost = QLabel(f"¥{metric.cost:.2f}")
    cost.setObjectName("modelCost")
    reqs = QLabel(f"{metric.requests:,} 次")
    reqs.setObjectName("smallText")
    cost.setAlignment(Qt.AlignRight)
    reqs.setAlignment(Qt.AlignRight)
    right_box.addWidget(cost)
    right_box.addWidget(reqs)

    layout.addWidget(badge)
    layout.addLayout(text_box, 2)
    layout.addWidget(MiniBar(metric.tokens / max(1, max_tokens), accent), 3)
    layout.addLayout(right_box, 1)
    return row


class MiniBar(QWidget):
    def __init__(self, ratio: float, accent: str) -> None:
        super().__init__()
        self.ratio = max(0.04, min(1.0, ratio))
        self.accent = QColor(accent)
        self.setMinimumHeight(14)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, self.height() / 2 - 3, self.width(), 6)
        painter.setBrush(QColor("#252a28"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 3, 3)

        fill = QRectF(rect.left(), rect.top(), rect.width() * self.ratio, rect.height())
        gradient = QLinearGradient(fill.topLeft(), fill.topRight())
        gradient.setColorAt(0, self.accent.lighter(125))
        gradient.setColorAt(1, QColor("#82d7ff"))
        painter.setBrush(gradient)
        painter.drawRoundedRect(fill, 3, 3)


class TokenChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.points: List[Tuple[date, UsageMetric]] = []
        self.setMinimumHeight(260)

    def set_summary(self, summary: UsageSummary) -> None:
        self.points = sorted(summary.by_day.items())[-7:]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(22, 18, -22, -22)
        max_tokens = max([metric.tokens for _, metric in self.points] or [1])
        count = max(1, len(self.points))
        slot = rect.width() / count
        bar_width = min(34, slot * 0.42)

        painter.setPen(QPen(QColor("#26302d"), 1))
        for i in range(4):
            y = rect.bottom() - rect.height() * i / 3
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))

        for index, (day, metric) in enumerate(self.points):
            ratio = metric.tokens / max_tokens if max_tokens else 0
            height = max(8, rect.height() * 0.78 * ratio)
            left = rect.left() + slot * index + (slot - bar_width) / 2
            bar = QRectF(left, rect.bottom() - height - 26, bar_width, height)

            gradient = QLinearGradient(bar.topLeft(), bar.bottomLeft())
            gradient.setColorAt(0, QColor("#6fe1ff"))
            gradient.setColorAt(1, QColor("#6b5cff"))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar, 8, 8)

            painter.setPen(QColor("#d7d5ca"))
            painter.setFont(QFont("Microsoft YaHei", 8, QFont.Bold))
            painter.drawText(QRectF(left - 24, bar.top() - 24, bar_width + 48, 18), Qt.AlignCenter, compact_number(metric.tokens))
            painter.setPen(QColor("#8f9691"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(QRectF(left - 12, rect.bottom() - 18, bar_width + 24, 18), Qt.AlignCenter, f"{day.month}/{day.day}")


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))))
        self.setMinimumWidth(460)
        self.api_key_input = QLineEdit(config.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        self.platform_token_input = QLineEdit(config.platform_token)
        self.platform_token_input.setEchoMode(QLineEdit.Password)
        self.platform_token_input.setPlaceholderText("platform userToken")
        self.notifications_input = QCheckBox("启用 Windows 通知")
        self.notifications_input.setChecked(config.notifications_enabled)
        self.auto_refresh_input = QCheckBox("启动后自动刷新，并按间隔更新")
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
        title = QLabel("连接 DeepSeek")
        title.setObjectName("dialogTitle")
        label = QLabel("DeepSeek API Key")
        label.setObjectName("smallText")
        platform_label = QLabel("DeepSeek Platform userToken")
        platform_label.setObjectName("smallText")
        endpoint = QLabel(f"余额查询：{BALANCE_URL}")
        endpoint.setObjectName("smallText")
        api_docs = QLabel(f'<a href="{API_DOCS_URL}">DeepSeek 官方余额 API 文档</a>')
        api_docs.setObjectName("linkText")
        api_docs.setOpenExternalLinks(True)
        api_docs.setTextInteractionFlags(Qt.TextBrowserInteraction)
        platform_hint = QLabel(
            "userToken 获取方法：\n"
            "1. 点击下方平台用量页并登录 DeepSeek。\n"
            "2. 按 F12 打开开发者工具，进入 Application / 应用程序。\n"
            "3. 打开 Local storage -> https://platform.deepseek.com。\n"
            "4. 复制 key 为 userToken 的 value，粘贴到上方输入框。"
        )
        platform_hint.setObjectName("smallText")
        platform_hint.setWordWrap(True)
        platform_link = QLabel(f'<a href="{PLATFORM_USAGE_URL}">打开 DeepSeek Platform Usage 页面</a>')
        platform_link.setObjectName("linkText")
        platform_link.setOpenExternalLinks(True)
        platform_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        hint = QLabel("API Key 将保存到 Windows 用户目录的本应用配置文件中。")
        hint.setObjectName("smallText")
        hint.setWordWrap(True)
        buttons = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        uninstall_btn = QPushButton("卸载程序")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        uninstall_btn.clicked.connect(self.request_uninstall)
        buttons.addWidget(uninstall_btn)
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout.addWidget(title)
        layout.addWidget(label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(endpoint)
        layout.addWidget(api_docs)
        layout.addWidget(platform_label)
        layout.addWidget(self.platform_token_input)
        layout.addWidget(platform_link)
        layout.addWidget(platform_hint)
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
            QLabel#linkText a {
                color: #7ac7ff;
                text-decoration: underline;
            }
            QCheckBox {
                color: #f4f1e8;
                font-size: 13px;
                spacing: 8px;
            }
            QLineEdit {
                background: #0b100e;
                color: #f4f1e8;
                border: 1px solid #3a4642;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #796cff;
            }
            QSpinBox {
                background: #0b100e;
                color: #f4f1e8;
                border: 1px solid #3a4642;
                border-radius: 8px;
                padding: 8px;
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
    def platform_token(self) -> str:
        return self.platform_token_input.text().strip()

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


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.balance = Balance(False, "CNY", 25.75)
        self.summary = self._load_summary()
        self.tray = self._create_tray()
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.platform_refresh_started_at = 0.0
        self.platform_refresh_cooldown_seconds = 300

        self.setWindowTitle("DeepSeek Monitor")
        self.setWindowIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))))
        self.resize(1120, 700)
        self.setMinimumSize(960, 620)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(22, 18, 22, 22)
        main.setSpacing(18)

        main.addLayout(self._build_header())

        content = QHBoxLayout()
        content.setSpacing(18)
        self.left_panel = self._build_left_panel()
        self.right_panel = self._build_right_panel()
        content.addWidget(self.left_panel, 1)
        content.addWidget(self.right_panel, 1)
        main.addLayout(content, 1)

        self.status_label = QLabel("就绪：无 API Key 时显示示例余额；导入 CSV 或刷新平台用量后显示真实用量。")
        self.status_label.setObjectName("smallText")
        main.addWidget(self.status_label)

        self._apply_style()
        self.refresh_view()
        self._schedule_auto_refresh()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title = QLabel("DeepSeek Monitor")
        title.setObjectName("title")
        refresh_btn = QPushButton("刷新余额")
        usage_btn = QPushButton("刷新用量")
        import_btn = QPushButton("导入 Usage CSV")
        settings_btn = QPushButton("设置")
        refresh_btn.clicked.connect(self.refresh_balance)
        usage_btn.clicked.connect(self.refresh_platform_usage)
        import_btn.clicked.connect(self.import_csv)
        settings_btn.clicked.connect(self.open_settings)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        header.addWidget(usage_btn)
        header.addWidget(import_btn)
        header.addWidget(settings_btn)
        return header

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("deepseek_monitor/assets/app.ico"))), self)
        menu = QMenu(self)
        show_action = QAction("打开面板", self)
        refresh_action = QAction("刷新余额和用量", self)
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

    def _build_left_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        top = QGridLayout()
        top.setSpacing(14)
        self.balance_card = MetricCard("账户余额", "¥25.75", "#796cff", "账户可用")
        self.cost_card = MetricCard("本月消费", "¥0.00", "#ffb33c", "CSV / 示例数据")
        top.addWidget(self.balance_card, 0, 0)
        top.addWidget(self.cost_card, 0, 1)
        layout.addLayout(top)

        self.model_container = QVBoxLayout()
        self.model_container.setSpacing(12)
        layout.addLayout(self.model_container)

        trend_card = QFrame()
        trend_card.setObjectName("card")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(18, 16, 18, 14)
        label = QLabel("消耗趋势")
        label.setObjectName("cardTitle")
        self.small_chart = TokenChart()
        self.small_chart.setMinimumHeight(180)
        trend_layout.addWidget(label)
        trend_layout.addWidget(self.small_chart)
        layout.addWidget(trend_card, 1)
        return panel

    def _build_right_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        top = QGridLayout()
        top.setSpacing(14)
        self.requests_card = MetricCard("API 请求次数", "0", "#82b8ff")
        self.tokens_card = MetricCard("Tokens", "0", "#82b8ff")
        top.addWidget(self.requests_card, 0, 0)
        top.addWidget(self.tokens_card, 0, 1)
        layout.addLayout(top)

        chart_card = QFrame()
        chart_card.setObjectName("card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(22, 18, 22, 18)
        chart_header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("按日 Token 消耗")
        title.setObjectName("cardTitle")
        self.range_label = QLabel("")
        self.range_label.setObjectName("smallText")
        self.chart_total_label = QLabel("")
        self.chart_total_label.setObjectName("smallText")
        self.chart_total_label.setAlignment(Qt.AlignRight)
        title_box.addWidget(title)
        title_box.addWidget(self.range_label)
        chart_header.addLayout(title_box)
        chart_header.addStretch()
        chart_header.addWidget(self.chart_total_label)
        self.large_chart = TokenChart()
        chart_layout.addLayout(chart_header)
        chart_layout.addWidget(self.large_chart, 1)
        layout.addWidget(chart_card, 1)
        return panel

    def _load_summary(self) -> UsageSummary:
        csv_text = load_usage_csv()
        if not csv_text.strip():
            return sample_usage()
        try:
            return aggregate_usage(parse_usage_csv(csv_text))
        except Exception:
            return sample_usage()

    def refresh_view(self) -> None:
        balance_text = f"¥{self.balance.total:.2f}" if self.balance.is_available else "示例 ¥25.75"
        balance_subtitle = "账户可用" if self.balance.is_available else "未连接 API"
        self.balance_card.set_values(balance_text, balance_subtitle)
        self.cost_card.set_values(f"¥{self.summary.total_cost:.2f}", "本月消费")
        self.requests_card.set_values(f"{self.summary.total_requests:,}")
        self.tokens_card.set_values(format_number(self.summary.total_tokens))
        self.small_chart.set_summary(self.summary)
        self.large_chart.set_summary(self.summary)
        self._refresh_model_rows()
        self._refresh_chart_labels()

    def _refresh_model_rows(self) -> None:
        clear_layout(self.model_container)
        max_tokens = max([metric.tokens for metric in self.summary.by_model.values()] or [1])
        accents = ["#75d8ff", "#b15cff", "#796cff", "#ffb33c"]
        for index, (model, metric) in enumerate(sorted(self.summary.by_model.items(), key=lambda item: item[1].tokens, reverse=True)[:4]):
            self.model_container.addWidget(create_model_row(model, metric, max_tokens, accents[index % len(accents)]))

    def _refresh_chart_labels(self) -> None:
        days = sorted(self.summary.by_day)
        if days:
            self.range_label.setText(f"{days[0].month}/{days[0].day} - {days[-1].month}/{days[-1].day}")
        self.chart_total_label.setText(compact_number(self.summary.total_tokens))

    def refresh_balance(self) -> None:
        if not self.config.api_key and not self.config.platform_token:
            self.status_label.setText("未设置 API Key 或 Platform userToken，继续显示示例余额。")
            return
        try:
            if self.config.api_key:
                self.balance = fetch_balance(self.config.api_key)
                source = "API Key"
            else:
                self.balance = fetch_platform_balance(self.config.platform_token)
                source = "Platform userToken"
        except Exception as exc:
            if self.config.api_key and self.config.platform_token:
                try:
                    self.balance = fetch_platform_balance(self.config.platform_token)
                except Exception:
                    pass
                else:
                    self.status_label.setText("余额已通过 Platform userToken 刷新。")
                    self.refresh_view()
                    return
            QMessageBox.warning(self, "刷新失败", f"无法获取 DeepSeek 余额：\n{exc}")
            self.status_label.setText("余额刷新失败，请检查 API Key、Platform userToken 或网络。")
            return
        self.status_label.setText(f"余额已通过 {source} 刷新。")
        self.refresh_view()

    def refresh_platform_usage(self) -> None:
        if self._skip_platform_refresh_if_cooling_down(show_dialog=True):
            return
        if not self.config.platform_token:
            self.status_label.setText("未设置 Platform userToken，无法刷新平台用量。")
            return
        now = datetime.now(timezone.utc)
        try:
            self.platform_refresh_started_at = time.monotonic()
            self.balance = fetch_platform_balance(self.config.platform_token)
            self.summary = fetch_platform_usage(self.config.platform_token, now.year, now.month)
        except PlatformRateLimitError as exc:
            QMessageBox.information(self, "刷新太频繁", str(exc))
            self.status_label.setText(str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "刷新失败", f"无法获取 DeepSeek 平台用量：\n{exc}")
            self.status_label.setText("平台用量刷新失败，请检查 userToken 或网络。")
            return
        self.status_label.setText(f"平台余额和用量已刷新：UTC {now.year}-{now.month:02d}")
        self.refresh_view()

    def auto_refresh(self) -> None:
        if self._skip_platform_refresh_if_cooling_down(show_dialog=False):
            return
        if not self.config.platform_token:
            self._notify("DeepSeek Monitor", "未设置 Platform userToken，无法自动刷新用量。")
            return
        now = datetime.now(timezone.utc)
        try:
            self.platform_refresh_started_at = time.monotonic()
            self.balance = fetch_platform_balance(self.config.platform_token)
            self.summary = fetch_platform_usage(self.config.platform_token, now.year, now.month)
        except PlatformRateLimitError as exc:
            self.status_label.setText(str(exc))
            self._notify("DeepSeek Monitor 刷新太频繁", str(exc))
            return
        except Exception as exc:
            self.status_label.setText("自动刷新失败。")
            self._notify("DeepSeek Monitor 自动刷新失败", str(exc))
            return
        self.status_label.setText(f"自动刷新完成：UTC {now.year}-{now.month:02d}")
        self.refresh_view()
        title, body = format_refresh_notification(self.balance.total, self.summary)
        self._notify(title, body)

    def _skip_platform_refresh_if_cooling_down(self, show_dialog: bool) -> bool:
        remaining = remaining_cooldown_seconds(
            self.platform_refresh_started_at,
            time.monotonic(),
            self.platform_refresh_cooldown_seconds,
        )
        if remaining <= 0:
            return False
        message = f"平台接口刚刷新过，请等待约 {remaining} 秒后再试。"
        self.status_label.setText(message)
        if show_dialog:
            QMessageBox.information(self, "刷新太频繁", message)
        return True

    def _notify(self, title: str, body: str) -> None:
        if not self.config.notifications_enabled:
            return
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.showMessage(title, body, QSystemTrayIcon.Information, 8000)

    def import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "导入 DeepSeek Usage CSV", str(Path.home()), "CSV Files (*.csv);;All Files (*.*)")
        if not path:
            return
        csv_text = read_text_file(Path(path))
        try:
            summary = aggregate_usage(parse_usage_csv(csv_text))
        except Exception as exc:
            QMessageBox.warning(self, "导入失败", f"CSV 无法解析：\n{exc}")
            return
        save_usage_csv(csv_text)
        self.summary = summary
        self.status_label.setText(f"已导入：{path}")
        self.refresh_view()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() != QDialog.Accepted:
            return
        self.config.api_key = dialog.api_key
        self.config.platform_token = dialog.platform_token
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
            QFrame#card, QFrame#modelRow {
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
                font-size: 38px;
                font-weight: 900;
            }
            QLabel#cardTitle, QLabel#modelName {
                color: #f4f1e8;
                font-size: 18px;
                font-weight: 800;
            }
            QLabel#modelCost {
                color: #f4f1e8;
                font-size: 15px;
                font-weight: 800;
            }
            QLabel#badge {
                background: rgba(70, 92, 105, 95);
                border-radius: 21px;
                font-size: 18px;
                font-weight: 900;
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
            QLineEdit {
                background: #111512;
                color: #f4f1e8;
                border: 1px solid #343d39;
                border-radius: 8px;
                padding: 9px;
            }
            """
        )


def clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M".rstrip("0").rstrip(".")
    if value >= 1_000:
        return f"{value / 1_000:.1f}K".rstrip("0").rstrip(".")
    return str(value)


def format_number(value: int) -> str:
    return f"{value:,}"


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            pass
    return path.read_text()


def resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base_path / relative_path


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
