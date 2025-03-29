import sys

from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QComboBox, QScrollArea, QFrame, QTextEdit,
                               QDoubleSpinBox, QSpinBox, QCheckBox, QMessageBox,
                               QListWidget, QListWidgetItem, QSplitter, QGroupBox,
                               QTabWidget, QInputDialog)

from task_data_handler import TaskDataHandler
from task_display import TaskDisplayIntegration

class CustomCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                 margin-left: -10px;
            }
            QCheckBox::indicator {
                width: 30px;
                height: 30px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取复选框的矩形区域
        rect = QRect(0, 0, 20, 20)
        rect.moveCenter(QPoint(10, self.height() // 2))

        # 绘制边框
        if self.isChecked():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#4a86e8"))
        else:
            painter.setPen(QPen(QColor("#4a86e8"), 2))
            painter.setBrush(QColor("white"))

        painter.drawRoundedRect(rect, 4, 4)

        # 如果选中，绘制对钩
        if self.isChecked():
            painter.setPen(QPen(QColor("white"), 2))
            # 绘制对钩路径
            path = QPainterPath()
            path.moveTo(rect.left() + 5, rect.top() + 10)
            path.lineTo(rect.left() + 8, rect.bottom() - 6)
            path.lineTo(rect.right() - 5, rect.top() + 6)
            painter.drawPath(path)

        # 绘制文本 - 修改这一部分
        text = self.text()
        if text:  # 使用Python的方式检查字符串是否为空
            textRect = self.rect()
            textRect.setLeft(rect.right() + 5)
            painter.setPen(QColor("#2c3e50"))
            painter.drawText(textRect, Qt.AlignLeft | Qt.AlignVCenter, text)


class TaskListApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务管理系统")
        self.setMinimumSize(900, 700)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        # 左侧输入面板
        input_panel = self.setup_input_panel()

        # 右侧显示面板 - 使用选项卡
        display_panel = QTabWidget()

        # 第一个选项卡 - 原始列表视图
        list_view_tab = self.setup_list_view_tab()

        # 第二个选项卡 - 新的卡片视图
        card_view_tab, self.task_card_display = TaskDisplayIntegration.create_display_tab()

        # 添加选项卡
        display_panel.addTab(list_view_tab, "列表视图")
        display_panel.addTab(card_view_tab, "卡片视图")

        # 添加面板到分割器
        main_splitter.addWidget(input_panel)
        main_splitter.addWidget(display_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)

        # 初始化任务列表
        self.tasks = []
        self.filtered_tasks = []

        # 设置样式
        self.apply_styles()

        # 连接信号
        display_panel.currentChanged.connect(self.on_tab_changed)

        # 尝试自动加载任务
        self.auto_load_tasks()

    def update_filtered_tasks(self):
        """更新筛选后的任务列表"""
        filter_type = self.filter_combo.currentText()
        search_text = self.search_input.text().strip()

        # 先按类型筛选
        filtered = TaskDataHandler.filter_tasks_by_type(self.tasks, filter_type)

        # 再按搜索关键词筛选
        if search_text:
            filtered = TaskDataHandler.search_tasks(filtered, search_text)

        self.filtered_tasks = filtered

    def filter_tasks(self):
        """按类型筛选任务"""
        self.update_filtered_tasks()
        self.update_task_display()

    def search_tasks(self):
        """搜索任务"""
        self.update_filtered_tasks()
        self.update_task_display()


    def setup_input_panel(self):
        """设置输入面板"""
        input_panel = QWidget()
        input_layout = QVBoxLayout(input_panel)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)

        # 输入区域分组
        input_group = QGroupBox("添加新任务")
        input_group_layout = QVBoxLayout(input_group)

        # 总任务类型和标题
        main_task_frame = QFrame()
        main_task_layout = QVBoxLayout(main_task_frame)
        main_task_layout.setSpacing(8)

        # 类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("任务类型:"))
        self.main_task_type_combo = QComboBox()
        self.main_task_type_combo.setEditable(True)
        self.main_task_type_combo.addItems(["工作", "学习", "生活", "其他"])
        type_layout.addWidget(self.main_task_type_combo)
        main_task_layout.addLayout(type_layout)

        # 任务总标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("任务总标题:"))
        self.main_task_input = QLineEdit()
        self.main_task_input.setPlaceholderText("输入总任务名称")
        title_layout.addWidget(self.main_task_input)
        main_task_layout.addLayout(title_layout)

        input_group_layout.addWidget(main_task_frame)

        # 子任务信息
        subtask_frame = QFrame()
        subtask_layout = QVBoxLayout(subtask_frame)
        subtask_layout.setSpacing(8)

        # 子任务标题
        sub_title_layout = QHBoxLayout()
        sub_title_layout.addWidget(QLabel("子任务标题:"))
        self.sub_task_input = QLineEdit()
        self.sub_task_input.setPlaceholderText("输入子任务名称")
        sub_title_layout.addWidget(self.sub_task_input)
        subtask_layout.addLayout(sub_title_layout)

        # 细节描述
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(QLabel("细节描述:"))
        self.detail_input = QTextEdit()
        self.detail_input.setMaximumHeight(80)
        self.detail_input.setPlaceholderText("输入任务详细描述")
        detail_layout.addWidget(self.detail_input)
        subtask_layout.addLayout(detail_layout)

        # 时间和序号
        time_branch_layout = QHBoxLayout()

        time_layout = QVBoxLayout()
        time_header = QHBoxLayout()
        time_header.addWidget(QLabel("预计耗时:"))
        time_layout.addLayout(time_header)

        time_inputs = QHBoxLayout()
        time_inputs.addWidget(QLabel("小时:"))
        self.hours_input = QSpinBox()
        self.hours_input.setMinimum(0)
        time_inputs.addWidget(self.hours_input)

        time_inputs.addWidget(QLabel("分钟:"))
        self.minutes_input = QSpinBox()
        self.minutes_input.setMinimum(0)
        self.minutes_input.setMaximum(59)
        time_inputs.addWidget(self.minutes_input)
        time_layout.addLayout(time_inputs)

        time_branch_layout.addLayout(time_layout)

        branch_layout = QVBoxLayout()
        branch_layout.addWidget(QLabel("分支序号:"))
        self.branch_number_input = QSpinBox()
        self.branch_number_input.setMinimum(1)
        branch_layout.addWidget(self.branch_number_input)
        time_branch_layout.addLayout(branch_layout)

        subtask_layout.addLayout(time_branch_layout)

        # 权重设置
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("任务权重:"))
        self.weight_input = QSpinBox()
        self.weight_input.setMinimum(1)
        self.weight_input.setMaximum(100)
        self.weight_input.setValue(10)  # 默认权重为10
        weight_layout.addWidget(self.weight_input)
        subtask_layout.addLayout(weight_layout)

        # 子任务列表
        subtasks_group = QGroupBox("子任务列表")
        subtasks_layout = QVBoxLayout(subtasks_group)

        self.subtasks_list = QListWidget()
        subtasks_layout.addWidget(self.subtasks_list)

        subtasks_btn_layout = QHBoxLayout()
        self.add_subtask_btn = QPushButton("添加子任务")
        self.add_subtask_btn.clicked.connect(self.add_subtask)
        self.remove_subtask_btn = QPushButton("删除子任务")
        self.remove_subtask_btn.clicked.connect(self.remove_subtask)
        subtasks_btn_layout.addWidget(self.add_subtask_btn)
        subtasks_btn_layout.addWidget(self.remove_subtask_btn)
        subtasks_layout.addLayout(subtasks_btn_layout)

        subtask_layout.addWidget(subtasks_group)

        input_group_layout.addWidget(subtask_frame)

        # 添加任务按钮
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加任务")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_task)
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        input_group_layout.addLayout(btn_layout)

        input_layout.addWidget(input_group)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存任务")
        self.save_btn.clicked.connect(self.save_tasks)
        self.load_btn = QPushButton("加载任务")
        self.load_btn.clicked.connect(self.load_tasks)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.load_btn)
        input_layout.addLayout(bottom_layout)

        input_layout.addStretch()

        return input_panel


    def setup_list_view_tab(self):
        """设置列表视图标签页"""
        list_view_tab = QWidget()
        list_view_layout = QVBoxLayout(list_view_tab)

        # 搜索和筛选
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)

        filter_layout.addWidget(QLabel("筛选类型:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("全部")
        self.filter_combo.addItems(["工作", "学习", "生活", "其他"])
        self.filter_combo.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索")
        self.search_input.textChanged.connect(self.search_tasks)
        filter_layout.addWidget(self.search_input)

        list_view_layout.addWidget(filter_frame)

        # 任务显示区域
        tasks_group = QGroupBox("任务列表")
        tasks_layout = QVBoxLayout(tasks_group)

        self.task_display = QScrollArea()
        self.task_display.setWidgetResizable(True)
        self.task_content = QWidget()
        self.task_layout = QVBoxLayout(self.task_content)
        self.task_layout.setSpacing(10)
        self.task_display.setWidget(self.task_content)
        tasks_layout.addWidget(self.task_display)

        list_view_layout.addWidget(tasks_group)

        return list_view_tab


    def add_subtask(self):
        """添加子任务到列表"""
        subtask_text, ok = QInputDialog.getText(self, "添加子任务", "输入子任务名称:")
        if ok and subtask_text.strip():
            self.subtasks_list.addItem(subtask_text.strip())


    def remove_subtask(self):
        """从列表中删除选中的子任务"""
        selected_items = self.subtasks_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "删除子任务", "请先选择要删除的子任务")
            return

        for item in selected_items:
            row = self.subtasks_list.row(item)
            self.subtasks_list.takeItem(row)

    def apply_styles(self):
        """应用自定义样式"""
        # 设置字体
        app_font = QFont("Arial", 10)
        QApplication.setFont(app_font)

        # 设置样式表
        self.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        margin-top: 1ex;
                        padding-top: 10px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                    }
                    QFrame {
                        border-radius: 4px;
                    }
                    QPushButton {
                        background-color: #4a86e8;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background-color: #3a76d8;
                    }
                    QPushButton:pressed {
                        background-color: #2a66c8;
                    }
                    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        padding: 4px;
                    }
                    QScrollArea {
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                    }
                """)

    def add_task(self):
        """添加新任务到列表"""
        main_task = self.main_task_input.text().strip()
        main_task_type = self.main_task_type_combo.currentText().strip()
        sub_task = self.sub_task_input.text().strip()
        details = self.detail_input.toPlainText().strip()
        hours = self.hours_input.value()
        minutes = self.minutes_input.value()
        branch_number = self.branch_number_input.value()
        weight = self.weight_input.value()

        # 验证必填字段
        if not all([main_task, main_task_type, sub_task]):
            QMessageBox.warning(self, "输入错误", "请填写任务总标题、任务类型和子任务标题")
            return

        # 计算总时间（小时为单位）
        estimated_time = hours + (minutes / 60)

        # 获取子任务列表
        sub_task_tasks = {}
        for i in range(self.subtasks_list.count()):
            sub_task_tasks[self.subtasks_list.item(i).text()] = False

        # 创建任务对象
        task = {
            "main_task": main_task,
            "main_task_type": main_task_type,
            "sub_task": sub_task,
            "details": details,
            "estimated_time": estimated_time,
            "branch_number": branch_number,
            "completed": False,
            "weight": weight,
            "sub_task_tasks": sub_task_tasks
        }

        # 添加到任务列表
        self.tasks.append(task)

        # 清空输入框
        self.sub_task_input.clear()
        self.detail_input.clear()
        self.hours_input.setValue(0)
        self.minutes_input.setValue(0)
        self.branch_number_input.setValue(self.branch_number_input.value() + 1)
        self.subtasks_list.clear()

        # 更新显示
        self.update_filtered_tasks()
        self.update_task_display()
        self.update_card_display()

        # 提示成功
        QMessageBox.information(self, "添加成功", "任务已成功添加到列表")


    def update_card_display(self):
        """更新卡片视图任务显示"""
        if hasattr(self, 'task_card_display'):
            converted_data = TaskDisplayIntegration.convert_task_format(self.filtered_tasks)
            self.task_card_display.set_task_data(converted_data)


    def toggle_task_complete(self, task, state):
        """切换任务完成状态"""
        task["completed"] = (state == Qt.CheckState.Checked.value)
        # 更新卡片视图
        self.update_card_display()


    def on_tab_changed(self, index):
        """处理标签页切换事件"""
        # 如果切换到卡片视图标签页，刷新其内容
        if index == 1:  # 卡片视图是第二个标签页
            self.update_card_display()


    def save_tasks(self):
        """保存任务到文件"""
        if not self.tasks:
            QMessageBox.warning(self, "保存失败", "没有任务可以保存")
            return

        try:
            success = TaskDataHandler.save_tasks_to_json(self.tasks, "tasks.json")
            if success:
                QMessageBox.information(self, "保存成功", "任务已成功保存到文件")
            else:
                QMessageBox.critical(self, "保存失败", "保存任务时发生错误")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存任务时发生错误: {str(e)}")


    def load_tasks(self):
        """从文件加载任务"""
        try:
            loaded_tasks = TaskDataHandler.load_tasks_from_json("tasks.json")
            if loaded_tasks:
                self.tasks = loaded_tasks
                self.update_filtered_tasks()
                self.update_task_display()
                self.update_card_display()
                QMessageBox.information(self, "加载成功", "任务已成功从文件加载")
            else:
                QMessageBox.warning(self, "加载失败", "加载任务时发生错误或文件不存在")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载任务时发生错误: {str(e)}")


    def auto_load_tasks(self):
        """程序启动时尝试自动加载任务"""
        try:
            loaded_tasks = TaskDataHandler.load_tasks_from_json("tasks.json")
            if loaded_tasks:
                self.tasks = loaded_tasks
                self.update_filtered_tasks()
                self.update_task_display()
                self.update_card_display()
                print("已自动加载任务数据")
            else:
                print("未找到任务数据文件或文件为空")
        except Exception as e:
            print(f"自动加载任务数据失败: {e}")


    def delete_task(self, task):
        """删除指定任务"""
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除任务 '{task['main_task']} - {task['sub_task']}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 从任务列表中移除
            self.tasks.remove(task)
            # 更新显示
            self.update_filtered_tasks()
            self.update_task_display()
            self.update_card_display()
            QMessageBox.information(self, "删除成功", "任务已成功删除")


    def update_task_display(self):
        """更新任务显示区域"""
        # 清空现有内容
        for i in reversed(range(self.task_layout.count())):
            widget = self.task_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 如果没有任务，显示提示信息
        if not self.filtered_tasks:
            no_tasks_label = QLabel("没有任务可显示")
            no_tasks_label.setAlignment(Qt.AlignCenter)
            no_tasks_label.setStyleSheet("color: #7f8c8d; font-size: 16px; padding: 20px;")
            self.task_layout.addWidget(no_tasks_label)
            self.task_layout.addStretch()
            return

        # 按主任务分组显示
        task_groups = {}

        for task in self.filtered_tasks:
            main_task = task["main_task"]
            if main_task not in task_groups:
                task_groups[main_task] = []
            task_groups[main_task].append(task)

        # 为每个主任务创建一个分组
        for main_task, tasks in task_groups.items():
            # 获取第一个任务的类型作为主任务类型
            main_task_type = tasks[0]["main_task_type"]

            # 创建主任务框架
            main_frame = QFrame()
            main_frame.setFrameShape(QFrame.Shape.StyledPanel)
            main_frame.setStyleSheet("""
                background-color: #f5f7fa; 
                padding: 12px; 
                margin: 6px;
                border-radius: 8px;
                border: 1px solid #e0e6ed;
            """)
            main_layout = QVBoxLayout(main_frame)
            main_layout.setSpacing(10)

            # 主任务标题
            title_label = QLabel(
                f"<h3 style='color: #2c3e50;'>{main_task} <small style='color: #7f8c8d;'>({main_task_type})</small></h3>")
            main_layout.addWidget(title_label)

            # 按分支序号排序子任务
            sorted_tasks = sorted(tasks, key=lambda x: x["branch_number"])

            # 添加子任务
            for task in sorted_tasks:
                sub_frame = QFrame()
                sub_frame.setFrameShape(QFrame.Shape.StyledPanel)
                sub_frame.setStyleSheet("""
                    background-color: white; 
                    padding: 10px; 
                    margin: 4px;
                    border-radius: 6px;
                    border: 1px solid #eaeef2;
                """)
                sub_layout = QVBoxLayout(sub_frame)
                sub_layout.setSpacing(8)

                # 子任务标题和完成状态
                task_header = QHBoxLayout()

                # 复选框
                complete_checkbox = CustomCheckBox()
                complete_checkbox.setChecked(task["completed"])
                complete_checkbox.stateChanged.connect(lambda state, t=task: self.toggle_task_complete(t, state))
                task_header.addWidget(complete_checkbox)

                # 显示子任务标题
                sub_task_title = QLabel(
                    f"<span style='font-size: 14px; font-weight: bold; color: #34495e;'>{task['sub_task']}</span>")
                task_header.addWidget(sub_task_title)

                # 分支序号标签
                branch_label = QLabel(
                    f"<span style='font-size: 12px; color: white; background-color: #4a86e8; padding: 2px 6px; border-radius: 10px;'>分支 {task['branch_number']}</span>")
                task_header.addWidget(branch_label)

                task_header.addStretch()

                # 显示预计时间
                hours = int(task["estimated_time"])
                minutes = int((task["estimated_time"] - hours) * 60)
                time_str = ""
                if hours > 0:
                    time_str += f"{hours}小时"
                if minutes > 0 or hours == 0:
                    time_str += f"{minutes}分钟"

                time_label = QLabel(f"<span style='color: #7f8c8d;'>预计: {time_str}</span>")
                task_header.addWidget(time_label)

                # 删除按钮
                delete_btn = QPushButton("删除")
                delete_btn.setStyleSheet("""
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-size: 12px;
                    max-height: 24px;
                """)
                delete_btn.clicked.connect(lambda checked, t=task: self.delete_task(t))
                task_header.addWidget(delete_btn)

                sub_layout.addLayout(task_header)

                # 任务详情
                if task["details"]:
                    details_frame = QFrame()
                    details_frame.setStyleSheet("""
                        background-color: #f8f9fa;
                        border-radius: 4px;
                        padding: 8px;
                        margin-left: 25px;
                    """)
                    details_layout = QVBoxLayout(details_frame)
                    details_layout.setContentsMargins(10, 8, 10, 8)

                    details_label = QLabel(task["details"])
                    details_label.setWordWrap(True)
                    details_label.setStyleSheet("color: #5d6d7e;")
                    details_layout.addWidget(details_label)

                    sub_layout.addWidget(details_frame)

                # 子任务列表
                if task["sub_task_tasks"] and len(task["sub_task_tasks"]) > 0:
                    subtasks_frame = QFrame()
                    subtasks_frame.setStyleSheet("""
                        background-color: #f8f9fa;
                        border-radius: 4px;
                        padding: 8px;
                        margin-left: 25px;
                    """)
                    subtasks_layout = QVBoxLayout(subtasks_frame)
                    subtasks_layout.setContentsMargins(10, 8, 10, 8)

                    subtasks_label = QLabel("<b>子任务:</b>")
                    subtasks_layout.addWidget(subtasks_label)

                    # 显示子任务
                    if isinstance(task["sub_task_tasks"], dict):
                        for sub_task_name, completed in task["sub_task_tasks"].items():
                            subtask_layout = QHBoxLayout()

                            # 子任务复选框
                            subtask_checkbox = CustomCheckBox()
                            subtask_checkbox.setChecked(completed)
                            subtask_checkbox.stateChanged.connect(
                                lambda state, t=task, stn=sub_task_name: self.toggle_subtask_complete(t, stn, state)
                            )
                            subtask_layout.addWidget(subtask_checkbox)

                            # 子任务名称
                            subtask_name_label = QLabel(sub_task_name)
                            if completed:
                                subtask_name_label.setStyleSheet("text-decoration: line-through; color: #95a5a6;")
                            subtask_layout.addWidget(subtask_name_label)

                            subtask_layout.addStretch()

                            subtasks_layout.addLayout(subtask_layout)
                    elif isinstance(task["sub_task_tasks"], list):
                        for sub_task_name in task["sub_task_tasks"]:
                            subtask_layout = QHBoxLayout()

                            # 子任务复选框
                            subtask_checkbox = CustomCheckBox()
                            subtask_checkbox.stateChanged.connect(
                                lambda state, t=task, stn=sub_task_name: self.toggle_subtask_complete(t, stn, state)
                            )
                            subtask_layout.addWidget(subtask_checkbox)

                            # 子任务名称
                            subtask_name_label = QLabel(sub_task_name)
                            subtask_layout.addWidget(subtask_name_label)

                            subtask_layout.addStretch()

                            subtasks_layout.addLayout(subtask_layout)

                    sub_layout.addWidget(subtasks_frame)

                main_layout.addWidget(sub_frame)

            self.task_layout.addWidget(main_frame)

        # 添加弹性空间
        self.task_layout.addStretch()


    def toggle_subtask_complete(self, task, sub_task_name, state):
        """切换子任务完成状态"""
        is_completed = (state == Qt.CheckState.Checked.value)

        # 更新数据模型
        if isinstance(task["sub_task_tasks"], dict):
            task["sub_task_tasks"][sub_task_name] = is_completed
        elif isinstance(task["sub_task_tasks"], list):
            # 如果是列表，转换为字典
            sub_tasks_dict = {}
            for st in task["sub_task_tasks"]:
                sub_tasks_dict[st] = False
            sub_tasks_dict[sub_task_name] = is_completed
            task["sub_task_tasks"] = sub_tasks_dict

        # 更新视图
        self.update_task_display()
        self.update_card_display()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskListApp()
    window.show()
    sys.exit(app.exec())