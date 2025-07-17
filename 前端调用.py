import sys
import os
import pickle
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtGui import  QFont, QFontMetrics,QPixmap, QDragEnterEvent, QDropEvent,QIcon
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import QSize

#调用本地模型

from openai import OpenAI

# 配置信息
ragflow_address = "localhost"
ragflow_api_key = "..."
chat_id = "..."

# 创建OpenAI客户端
client = OpenAI(
    api_key=ragflow_api_key,
    base_url=f"http://{ragflow_address}/api/v1/chats_openai/{chat_id}"
)





class ChatBox(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_records = []   # 聊天记录存储为列表
        self.initUI()

        # 初始化与模型对话历史（包含系统角色设定）
        self.conversation_history = [
        {"role": "system", "content": "You are a helpful movie recommendation assistant."}
        ]

        # 如果聊天记录为空，则发送AI问候
        if not self.chat_records:
            self.send_ai_greeting()

    def initUI(self):
        self.setWindowTitle('AI-Movie_Assistant')
        self.setGeometry(100, 100, 1000, 600)  # 扩大窗口初始尺寸

        #加载窗口logo
        logo_path = os.path.join("bot_icon.png")
        if os.path.isfile(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        else:
            print(f"无法加载窗口logo: {logo_path}")

        # 主布局为垂直布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # 添加边距
        main_layout.setSpacing(10)

        # 聊天显示区域（可滚动）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setSpacing(10)  # 消息间距
        self.chat_container.setLayout(self.chat_layout)
        self.scroll_area.setWidget(self.chat_container)
        
        # 添加拉伸项使消息从顶部开始显示
        self.chat_layout.addStretch(1)
        
        main_layout.addWidget(self.scroll_area, 3)  # 聊天区域占3份空间

        # 输入区域
        input_layout = QVBoxLayout()
        
        # 输入框
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setMinimumHeight(80)
        self.input_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        input_layout.addWidget(self.input_box)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # 在按钮前添加弹簧
        
        # 发送按钮
        self.send_button = QPushButton('发送')
        self.send_button.setFixedSize(100, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)
        
        input_layout.addLayout(button_layout)
        
        main_layout.addLayout(input_layout, 1)  # 输入区域占1份空间

        self.setLayout(main_layout)

        # 显示加载的聊天记录
        self.display_chat_history()

    def display_chat_history(self):
        """显示所有聊天记录"""
        for msg in self.chat_records:
            self.add_message(msg["text"], msg["is_sender"], msg.get("file_path"))

 
    def send_message(self):
        message = self.input_box.toPlainText().strip()
        if message:
            # 添加到聊天记录
            self.chat_records.append({
                "text": message,
                "is_sender": True,
                "file_path": None
            })
            
            # 添加到界面
            self.add_message(message, is_sender=True)
            
            # 清空输入框
            self.input_box.clear()
            
            #调用模型
            self.invoke_model(message)
            

            
    # 发送AI问候
    def send_ai_greeting(self):
        
        reply = "您好！我是您的私人电影推荐助手，有什么可以帮您的吗？"
        self.chat_records.append({
            "text": reply,
            "is_sender": False,
            "file_path": None
        })
        self.add_message(reply, is_sender=False)

    #主调用
    def invoke_model(self,message):
        # 获取用户输入
        user_input = message
                    
        # 将用户输入加入对话历史
        self.conversation_history.append({"role": "user", "content": user_input})
                    
        # 获取并打印助手回复
        reply = self.get_assistant_response()
        #保存到聊天记录
        self.chat_records.append({
            "text": reply,
            "is_sender": False,
            "file_path": None
        })
        #在屏幕上打印
        self.add_message(reply, is_sender=False)



    #模型回复
    def get_assistant_response(self):
        """获取助手回复并更新对话历史"""
        response = client.chat.completions.create(
        model="model",  # 模型名称
        messages=self.conversation_history,
        stream=False
        )
        assistant_reply = response.choices[0].message.content
        # 将助手回复加入对话历史
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})
        
        return assistant_reply


    def add_message(self, message: str, is_sender: bool, file_path: str = None):
        # 计算当前聊天区域的宽度
        chat_width = self.scroll_area.viewport().width() if self.scroll_area.viewport() else 600
        max_bubble_width = min(int(chat_width * 0.75), 500)  # 最大宽度为聊天窗口的3/4，不超过500px
        
        # 创建消息容器
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(5, 5, 5, 5)

        # 气泡样式
        bubble_style = f"""
            QWidget#chatBubble {{
                background-color: {"#dcf8c6" if is_sender else "#e6e6e6"}; 
                border-radius: 15px;
                padding: 10px;
                max-width: {max_bubble_width}px;
            }}
        """

        # 内容部件
        content_widget = QWidget()
        content_widget.setObjectName("chatBubble")
        content_widget.setStyleSheet(bubble_style)
        
        # 文本标签设置为可选中
        content_label = QLabel(message)
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_label.setStyleSheet("background: transparent;")
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # 允许文本选中

        # 根据文本计算气泡宽度
        font = content_label.font()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(message)
        bubble_width = max(100, min(text_width + 40, max_bubble_width))  # 最小宽度100px，文本宽度 + 内边距

        # 设置气泡最小高度
        text_lines = message.count('\n') + 1
        bubble_height = max(40, fm.lineSpacing() * text_lines + 20)  # 最小高度40px，文本高度 + 内边距

        # 手动设置气泡大小
        content_widget.setFixedSize(bubble_width, bubble_height)
        content_label.setMaximumWidth(bubble_width - 20)  # 减去内边距

        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(content_label)

        message_layout.addWidget(content_widget)

        # 对齐方式
        message_layout.setAlignment(Qt.AlignmentFlag.AlignRight if is_sender else Qt.AlignmentFlag.AlignLeft)

        # 添加到聊天布局（在拉伸项之前）
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_widget)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动到底部"""
        scroll_bar = self.scroll_area.verticalScrollBar()
        QTimer.singleShot(100, lambda: scroll_bar.setValue(scroll_bar.maximum()))

    def closeEvent(self, event):
        """窗口关闭事件"""
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }
        QScrollArea {
            background-color: #f0f0f0;
            border-radius: 5px;
        }
        QTextEdit {
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
            font-size: 14px;
        }
    """)
    
    chat_box = ChatBox()
    chat_box.show()
    sys.exit(app.exec())





