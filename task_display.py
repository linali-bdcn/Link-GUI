import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QFrame, QSplitter, QGroupBox)
from PySide6.QtCore import Qt, Signal, Slot, QObject
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel


class TaskDisplayBridge(QObject):
    """JavaScript和Python之间的通信桥接"""
    # 定义信号
    taskStatusChanged = Signal(str, int, bool)
    subTaskStatusChanged = Signal(str, int, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str, int, bool)
    def updateTaskStatus(self, subject, branch_number, completed):
        """更新任务状态"""
        self.taskStatusChanged.emit(subject, branch_number, completed)

    @Slot(str, int, str, bool)
    def updateSubTaskStatus(self, subject, branch_number, sub_task_name, completed):
        """更新子任务状态"""
        self.subTaskStatusChanged.emit(subject, branch_number, sub_task_name, completed)


class TaskDisplayPanel(QWidget):
    """任务显示面板"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 初始化数据
        self.task_data = {}

        # 创建通信桥接
        self.bridge = TaskDisplayBridge(self)

        # 设置UI
        self.setup_ui()

        # 连接信号
        self.bridge.taskStatusChanged.connect(self.on_task_status_changed)
        self.bridge.subTaskStatusChanged.connect(self.on_subtask_status_changed)

    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建Web视图 - 增加比例
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view, 95)  # 设置更大的伸缩因子，例如95%

        # 设置Web通道
        self.web_channel = QWebChannel()
        self.web_channel.registerObject("taskBridge", self.bridge)
        self.web_view.page().setWebChannel(self.web_channel)

        # 创建控制按钮区域 - 减少比例
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 5, 10, 5)

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新视图")
        self.refresh_btn.clicked.connect(self.refresh_display)
        control_layout.addWidget(self.refresh_btn)

        # 展开全部按钮
        self.expand_all_btn = QPushButton("展开全部")
        self.expand_all_btn.clicked.connect(self.expand_all_tasks)
        control_layout.addWidget(self.expand_all_btn)

        # 折叠全部按钮
        self.collapse_all_btn = QPushButton("折叠全部")
        self.collapse_all_btn.clicked.connect(self.collapse_all_tasks)
        control_layout.addWidget(self.collapse_all_btn)

        layout.addWidget(control_frame, 5)  # 设置较小的伸缩因子，例如5%

    def set_task_data(self, data):
        """设置任务数据并更新显示"""
        self.task_data = data
        self.refresh_display()

    def refresh_display(self):
        """刷新任务显示"""
        html_content = self.generate_html()
        self.web_view.setHtml(html_content)


    def generate_html(self):
        """生成HTML内容"""
        # 开始HTML文档
        html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>任务管理系统</title>
            <style>
                /* 基本样式 */
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }
    
                body {
                    font-family: 'Microsoft YaHei', 'Arial', sans-serif;
                    background-color: #f5f7fa;
                    color: #2c3e50;
                    padding: 15px;
                    line-height: 1.2;
                }
    
                /* 容器 */
                .container {
                    max-width: 100%;
                    margin: 0 auto;
                     min-height: 800px;
                }
    
                /* 任务卡片 */
                .task-card {
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 25px;
                    overflow: hidden;
                }
    
                /* 任务卡片标题区 */
                .task-header {
                    background: linear-gradient(135deg, #4a86e8, #3a76d8);
                    color: white;
                    padding: 15px 20px;
                    position: relative;
                }
    
                .task-title {
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }
    
                .task-meta {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                    font-size: 14px;
                }
    
                .task-meta-item {
                    display: flex;
                    align-items: center;
                }
    
                .task-meta-label {
                    font-weight: 500;
                    margin-right: 5px;
                }
    
                .task-type-badge {
                    display: inline-block;
                    padding: 3px 8px;
                    background-color: rgba(255,255,255,0.2);
                    border-radius: 4px;
                    font-size: 12px;
                    margin-right: 8px;
                }
    
                .task-stats {
                    position: absolute;
                    top: 15px;
                    right: 20px;
                    display: flex;
                    align-items: center;
                }
    
                .stat-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    background-color: rgba(255,255,255,0.15);
                    padding: 5px 10px;
                    border-radius: 6px;
                }
    
                .stat-value {
                    font-size: 16px;
                    font-weight: bold;
                }
    
                .stat-label {
                    font-size: 11px;
                    opacity: 0.85;
                }
    
                /* 任务内容区 */
                .task-content {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 15px;
                    padding: 20px;
                }
    
                /* 分支任务 */
                .branch-task {
                    background-color: #f8fafc;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                    overflow: hidden;
                    transition: all 0.2s;
                }
    
                .branch-task:hover {
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                    transform: translateY(-2px);
                }
    
                .branch-header {
                    padding: 10px 12px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 1px solid #e2e8f0;
                    background-color: white;
                }
    
                .branch-left {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex: 1;
                }
    
                .branch-checkbox {
                    width: 22px;
                    height: 22px;
                    border: 2px solid #4a86e8;
                    border-radius: 4px;
                    background-color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    flex-shrink: 0;
                }
    
                .branch-checkbox.checked {
                    background-color: #4a86e8;
                }
    
                .checkmark {
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    visibility: hidden;
                }
    
                .branch-checkbox.checked .checkmark {
                    visibility: visible;
                }
    
                .branch-name {
                    font-weight: 500;
                    font-size: 15px;
                    flex: 1;
                }
    
                .branch-name.completed {
                    text-decoration: line-through;
                    color: #94a3b8;
                }
    
                .branch-number {
                    background-color: #4a86e8;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }
    
                .branch-toggle {
                    width: 28px;
                    height: 28px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: #e2e8f0;
                    border-radius: 50%;
                    cursor: pointer;
                    margin-left: 8px;
                    transition: all 0.2s;
                }
    
                .branch-toggle:hover {
                    background-color: #cbd5e1;
                }
    
                .branch-toggle.expanded {
                    transform: rotate(180deg);
                    background-color: #cbd5e1;
                }
    
                /* 详情区域 */
                .branch-details {
                    padding: 0;
                    max-height: 0;
                    overflow: hidden;
                    transition: all 0.3s;
                }
    
                .branch-details.visible {
                    padding: 15px;
                    max-height: 500px;
                }
    
                .detail-item {
                    margin-bottom: 10px;
                    display: flex;
                    align-items: flex-start;
                }
    
                .detail-icon {
                    margin-right: 8px;
                    color: #64748b;
                }
    
                .detail-label {
                    font-weight: 500;
                    color: #64748b;
                    margin-right: 5px;
                    width: 70px;
                    flex-shrink: 0;
                }
    
                .detail-value {
                    color: #334155;
                    flex: 1;
                }
    
                /* 子任务列表 */
                .subtasks-list {
                    margin-top: 12px;
                    border-top: 1px solid #e2e8f0;
                    padding-top: 12px;
                }
    
                .subtasks-header {
                    font-weight: 500;
                    color: #64748b;
                    margin-bottom: 8px;
                }
                /* 子任务列表 */
                .subtasks-list {
                    margin-top: 12px;
                    border-top: 1px solid #e2e8f0;
                    padding-top: 12px;
                }
                
                .subtasks-header {
                    font-weight: 500;
                    color: #64748b;
                    margin-bottom: 8px;
                }
                
                .subtask-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin: 8px 0;
                    padding: 6px 8px;
                    border-radius: 4px;
                    transition: background-color 0.2s;
                }
                
                .subtask-item:hover {
                    background-color: #f1f5f9;
                }
                
                .subtask-checkbox {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #4a86e8;
                    border-radius: 3px;
                    background-color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                }
                
                .subtask-checkbox.checked {
                    background-color: #4a86e8;
                }
                
                .subtask-name {
                    font-size: 14px;
                }
                
                .subtask-name.completed {
                    text-decoration: line-through;
                    color: #94a3b8;
                }
                
                /* 无任务提示 */
                .no-tasks {
                    text-align: center;
                    padding: 40px;
                    color: #94a3b8;
                    font-size: 18px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
            </style>
        </head>
        <body>
            <div class="container">
        """

        # 检查是否有任务数据
        if not self.task_data:
            html += """
                <div class="no-tasks">
                    <p>没有任务数据可显示</p>
                    <p>请添加新任务或加载任务</p>
                </div>
                """
        else:
            # 遍历并生成每个主题的卡片
            for subject, subject_data in self.task_data.items():
                # 获取主题信息
                types = subject_data.get("Types", [])
                sub_task_number = subject_data.get("sub_task_number", 0)
                tasks = subject_data.get("tasks", [])

                # 计算已完成任务数
                completed_tasks = sum(1 for task in tasks if task.get("completed", False))

                # 生成主题卡片头部
                html += f"""
                    <div class="task-card">
                        <div class="task-header">
                            <div>
                                <div class="task-title">{subject}</div>
                                <div class="task-meta">
                    """

                # 添加类型标签
                for task_type in types:
                    html += f'            <span class="task-type-badge">{task_type}</span>\n'

                # 添加子任务数量信息
                html += f"""
                                <div class="task-meta-item">
                                    <span class="task-meta-label">分支任务总数:</span>
                                    <span>{sub_task_number}</span>
                                </div>
                            </div>
                        </div>
                        <div class="task-stats">
                            <div class="stat-item">
                                <span class="stat-value">{completed_tasks}/{sub_task_number}</span>
                                <span class="stat-label">已完成</span>
                            </div>
                        </div>
                    </div>
                    <div class="task-content">
                    """

                # 按分支号排序任务
                sorted_tasks = sorted(tasks, key=lambda x: x.get("branch_number", 0))

                # 生成每个分支任务的HTML
                for task in sorted_tasks:
                    # 获取分支任务信息
                    branch_number = task.get("branch_number", 0)
                    sub_task_name = task.get("sub_task_name", "")
                    details = task.get("details", "")
                    estimated_hours = task.get("estimated_time_hours", 0)
                    estimated_minutes = task.get("estimated_time_minutes", 0)
                    completed = task.get("completed", False)
                    weight = task.get("weight", 0)
                    sub_tasks = task.get("sub_task_tasks", {})

                    # 设置样式类
                    completed_class = "completed" if completed else ""
                    checked_class = "checked" if completed else ""

                    # 格式化时间显示
                    time_str = ""
                    if estimated_hours > 0:
                        time_str += f"{estimated_hours}小时"
                    if estimated_minutes > 0 or (estimated_hours == 0 and estimated_minutes == 0):
                        if time_str:
                            time_str += " "
                        time_str += f"{estimated_minutes}分钟"
                    if not time_str:
                        time_str = "无预计时间"

                    # 生成分支任务HTML
                    html += f"""
                        <div class="branch-task" data-subject="{subject}" data-branch="{branch_number}">
                            <div class="branch-header">
                                <div class="branch-left">
                                    <div class="branch-checkbox {checked_class}" onclick="toggleTaskCompleted(event, '{subject}', {branch_number})">
                                        <span class="checkmark">✓</span>
                                    </div>
                                    <span class="branch-name {completed_class}">{sub_task_name}</span>
                                </div>
                                <span class="branch-number">#{branch_number}</span>
                                <div class="branch-toggle" onclick="toggleBranchDetails(this)">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M6 9L12 15L18 9" stroke="#4A5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                </div>
                            </div>
                            <div class="branch-details">
                        """

                    # 添加详情内容
                    if details:
                        html += f"""
                                <div class="detail-item">
                                    <span class="detail-icon">📝</span>
                                    <span class="detail-label">详情:</span>
                                    <span class="detail-value">{details}</span>
                                </div>
                            """

                    # 添加时间和权重信息
                    html += f"""
                                <div class="detail-item">
                                    <span class="detail-icon">⏱️</span>
                                    <span class="detail-label">预计时间:</span>
                                    <span class="detail-value">{time_str}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-icon">⚖️</span>
                                    <span class="detail-label">权重:</span>
                                    <span class="detail-value">{weight}</span>
                                </div>
                        """

                    # 添加子任务列表
                    if sub_tasks and ((isinstance(sub_tasks, dict) and len(sub_tasks) > 0) or
                                      (isinstance(sub_tasks, list) and len(sub_tasks) > 0)):
                        html += """
                                    <div class="subtasks-list">
                                        <div class="subtasks-header">子任务列表:</div>
                            """

                        # 处理子任务 - 字典形式
                        if isinstance(sub_tasks, dict):
                            for sub_task_name, sub_task_completed in sub_tasks.items():
                                sub_completed_class = "completed" if sub_task_completed else ""
                                sub_checked_class = "checked" if sub_task_completed else ""

                                html += f"""
                                        <div class="subtask-item">
                                            <div class="subtask-checkbox {sub_checked_class}" 
                                                 onclick="toggleSubTaskCompleted(event, '{subject}', {branch_number}, '{sub_task_name}')">
                                                <span class="checkmark">✓</span>
                                            </div>
                                            <span class="subtask-name {sub_completed_class}">{sub_task_name}</span>
                                        </div>
                                    """
                        # 处理子任务 - 列表形式
                        elif isinstance(sub_tasks, list):
                            for sub_task_name in sub_tasks:
                                html += f"""
                                        <div class="subtask-item">
                                            <div class="subtask-checkbox" 
                                                 onclick="toggleSubTaskCompleted(event, '{subject}', {branch_number}, '{sub_task_name}')">
                                                <span class="checkmark">✓</span>
                                            </div>
                                            <span class="subtask-name">{sub_task_name}</span>
                                        </div>
                                    """

                        html += """
                                    </div>
                            """

                    # 关闭分支任务详情和分支任务div
                    html += """
                                </div>
                            </div>
                        """

                # 关闭当前主题的task-content和task-card
                html += """
                        </div>
                    </div>
                    """

        # 所有主题循环结束后，再添加JavaScript代码
        html += """
                </div>

                <script>
                    // 初始化与Python的通信
                    function initializeChannel() {
                        if (typeof window.taskBridge !== 'undefined') {
                            console.log("Web channel already initialized");
                            return;
                        }

                        if (typeof QWebChannel !== 'undefined') {
                            new QWebChannel(qt.webChannelTransport, function(channel) {
                                window.taskBridge = channel.objects.taskBridge;
                                console.log("Web channel initialized");
                            });
                        } else {
                            console.error("QWebChannel not found");
                        }
                    }

                    // 切换分支任务详情显示/隐藏
                    function toggleBranchDetails(element) {
                        const branchTask = element.closest('.branch-task');
                        const detailsElement = branchTask.querySelector('.branch-details');

                        if (detailsElement.classList.contains('visible')) {
                            detailsElement.classList.remove('visible');
                            element.classList.remove('expanded');
                        } else {
                            detailsElement.classList.add('visible');
                            element.classList.add('expanded');
                        }
                    }

                    // 切换任务完成状态
                    function toggleTaskCompleted(event, subject, branchNumber) {
                        event.stopPropagation();  // 防止触发详情展开

                        const branchTask = event.target.closest('.branch-task');
                        const checkbox = branchTask.querySelector('.branch-checkbox');
                        const taskName = branchTask.querySelector('.branch-name');

                        const isCompleted = checkbox.classList.contains('checked');

                        if (isCompleted) {
                            checkbox.classList.remove('checked');
                            taskName.classList.remove('completed');
                        } else {
                            checkbox.classList.add('checked');
                            taskName.classList.add('completed');
                        }

                        // 通知Python
                        if (window.taskBridge) {
                            window.taskBridge.updateTaskStatus(subject, branchNumber, !isCompleted);
                        }
                    }

                    // 切换子任务完成状态
                    function toggleSubTaskCompleted(event, subject, branchNumber, subTaskName) {
                        event.stopPropagation();

                        const subTaskItem = event.target.closest('.subtask-item');
                        const checkbox = subTaskItem.querySelector('.subtask-checkbox');
                        const taskName = subTaskItem.querySelector('.subtask-name');

                        const isCompleted = checkbox.classList.contains('checked');

                        if (isCompleted) {
                            checkbox.classList.remove('checked');
                            taskName.classList.remove('completed');
                        } else {
                            checkbox.classList.add('checked');
                            taskName.classList.add('completed');
                        }

                        // 通知Python
                        if (window.taskBridge) {
                            window.taskBridge.updateSubTaskStatus(subject, branchNumber, subTaskName, !isCompleted);
                        }
                    }

                    // 展开所有分支任务详情
                    function expandAllTasks() {
                        const details = document.querySelectorAll('.branch-details');
                        const toggles = document.querySelectorAll('.branch-toggle');

                        details.forEach(detail => {
                            detail.classList.add('visible');
                        });

                        toggles.forEach(toggle => {
                            toggle.classList.add('expanded');
                        });
                    }

                    // 折叠所有分支任务详情
                    function collapseAllTasks() {
                        const details = document.querySelectorAll('.branch-details');
                        const toggles = document.querySelectorAll('.branch-toggle');

                        details.forEach(detail => {
                            detail.classList.remove('visible');
                        });

                        toggles.forEach(toggle => {
                            toggle.classList.remove('expanded');
                        });
                    }

                    // 页面加载完成后初始化
                    document.addEventListener('DOMContentLoaded', function() {
                        initializeChannel();
                    });
                </script>
            </body>
            </html>
            """

        return html

    def on_task_status_changed(self, subject, branch_number, completed):
        """处理任务状态变更"""
        # 更新数据模型
        if subject in self.task_data:
            for task in self.task_data[subject]["tasks"]:
                if task.get("branch_number") == branch_number:
                    task["completed"] = completed
                    print(
                        f"任务 '{subject}:{task['sub_task_name']}' 状态已更新为: {'已完成' if completed else '未完成'}")
                    # 可能需要刷新显示
                    # self.refresh_display()  # 取消注释如果需要刷新整个视图
                    break

    def on_subtask_status_changed(self, subject, branch_number, sub_task_name, completed):
        """处理子任务状态变更"""
        # 更新数据模型
        if subject in self.task_data:
            for task in self.task_data[subject]["tasks"]:
                if task.get("branch_number") == branch_number:
                    # 检查子任务存储格式
                    if isinstance(task.get("sub_task_tasks"), dict):
                        task["sub_task_tasks"][sub_task_name] = completed
                    elif isinstance(task.get("sub_task_tasks"), list):
                        # 如果是列表，转换为字典
                        sub_tasks_dict = {}
                        for st in task["sub_task_tasks"]:
                            sub_tasks_dict[st] = False
                        sub_tasks_dict[sub_task_name] = completed
                        task["sub_task_tasks"] = sub_tasks_dict

                    print(
                        f"子任务 '{subject}:{task['sub_task_name']}:{sub_task_name}' 状态已更新为: {'已完成' if completed else '未完成'}")
                    # 可能需要刷新显示
                    # self.refresh_display()  # 取消注释如果需要刷新整个视图
                    break

    def expand_all_tasks(self):
        """展开所有任务详情"""
        self.web_view.page().runJavaScript("expandAllTasks();")

    def collapse_all_tasks(self):
        """折叠所有任务详情"""
        self.web_view.page().runJavaScript("collapseAllTasks();")

    def load_from_json(self, file_path):
        """从JSON文件加载任务数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.set_task_data(data)
                return True
        except Exception as e:
            print(f"加载JSON数据失败: {e}")
            return False

class TaskViewerApp(QMainWindow):
    """任务查看器应用"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务查看器")
        self.setGeometry(100, 100, 1000, 700)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)

        # 创建任务显示面板
        self.task_display = TaskDisplayPanel()
        layout.addWidget(self.task_display)

        # 创建控制按钮区域
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)

        self.load_btn = QPushButton("加载任务数据")
        self.load_btn.clicked.connect(self.load_task_data)
        control_layout.addWidget(self.load_btn)

        layout.addWidget(control_frame)

        # 加载示例数据
        self.load_sample_data()

    def load_sample_data(self):
        """加载示例数据"""
        sample_data = {
            "英语": {
                "Types": [
                    "工作"
                ],
                "describe": "",
                "tasks": [
                    {
                        "branch_number": 1,
                        "sub_task_name": "背单词",
                        "details": "每天20个",
                        "sub_task_tasks": {
                            "课内10个": False,
                            "课外10个": False
                        },
                        "estimated_time_hours": 0,
                        "estimated_time_minutes": 11,
                        "completed": False,
                        "weight": 11
                    },
                    {
                        "branch_number": 2,
                        "sub_task_name": "默写单词",
                        "details": "默写课内单词",
                        "sub_task_tasks": {},
                        "estimated_time_hours": 0,
                        "estimated_time_minutes": 10,
                        "completed": False,
                        "weight": 12
                    }
                ],
                "sub_task_number": 2
            },
            "语文": {
                "Types": [
                    "工作"
                ],
                "describe": "",
                "tasks": [
                    {
                        "branch_number": 1,
                        "sub_task_name": "默写古诗",
                        "details": "八年级上册全部",
                        "sub_task_tasks": {
                            "1-9篇   周6完成": False,
                            "10-18篇 周日完成": False
                        },
                        "estimated_time_hours": 1,
                        "estimated_time_minutes": 30,
                        "completed": False,
                        "weight": 13
                    }
                ],
                "sub_task_number": 1
            }
        }
        self.task_display.set_task_data(sample_data)

    def load_task_data(self):
        """从文件加载任务数据"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择任务数据文件", "", "JSON文件 (*.json)")

        if file_path:
            success = self.task_display.load_from_json(file_path)
            if success:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "加载成功", "任务数据已成功加载")

# 集成到现有程序的辅助类
class TaskDisplayIntegration:
    """任务显示集成类"""

    @staticmethod
    def create_display_tab(parent=None):
        """创建任务显示标签页"""
        display_widget = QWidget(parent)
        layout = QVBoxLayout(display_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        task_display = TaskDisplayPanel(display_widget)
        layout.addWidget(task_display)

        return display_widget, task_display

    @staticmethod
    def convert_task_format(tasks):
        """将TaskListApp格式的任务转换为TaskDisplayPanel格式"""
        # 按主任务分组
        task_groups = {}

        for task in tasks:
            main_task = task["main_task"]
            if main_task not in task_groups:
                task_groups[main_task] = {
                    "Types": [task["main_task_type"]],
                    "describe": "",
                    "tasks": [],
                    "sub_task_number": 0
                }

            # 转换任务格式
            formatted_task = {
                "branch_number": task["branch_number"],
                "sub_task_name": task["sub_task"],
                "details": task["details"],
                "sub_task_tasks": task.get("sub_task_tasks", {}),
                "estimated_time_hours": int(task["estimated_time"]),
                "estimated_time_minutes": int((task["estimated_time"] - int(task["estimated_time"])) * 60),
                "completed": task["completed"],
                "weight": task["weight"]
            }

            task_groups[main_task]["tasks"].append(formatted_task)
            task_groups[main_task]["sub_task_number"] += 1

        return task_groups


# 如果直接运行此文件
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskViewerApp()
    window.show()
    sys.exit(app.exec())