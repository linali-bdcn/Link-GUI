import json
import os
from datetime import datetime


class TaskDataHandler:
    """
    任务数据处理类，用于保存和读取任务数据
    """

    @staticmethod
    def filter_tasks_by_type(tasks, task_type):
        """按类型筛选任务"""
        if task_type == "全部":
            return tasks
        return [task for task in tasks if task["main_task_type"] == task_type]

    @staticmethod
    def save_tasks_to_json(tasks, filename):
        """
        保存任务，按总标题分类，按分支序号排序，包含完成状态和总任务类型。

        参数:
            tasks (list): 任务对象列表
            filename (str): 保存的文件名
        """
        # 创建备份
        TaskDataHandler.backup_tasks_file(filename)

        organized_tasks = {}

        for task in tasks:
            main_task = task['main_task']
            main_task_type = task['main_task_type']

            if main_task not in organized_tasks:
                organized_tasks[main_task] = {
                    "Types": [main_task_type] if main_task_type else [],
                    "describe": "",  # 可以从前端获取描述
                    "tasks": [],
                    "sub_task_number": 0
                }
            elif main_task_type and main_task_type not in organized_tasks[main_task]["Types"]:
                organized_tasks[main_task]["Types"].append(main_task_type)

            # 转换估计时间为小时和分钟
            estimated_time = task["estimated_time"]
            hours = int(estimated_time)
            minutes = round((estimated_time - hours) * 60)

            sub_task_data = {
                "branch_number": task["branch_number"],
                "sub_task_name": task["sub_task"],
                "details": task["details"],
                "sub_task_tasks": task.get("sub_task_tasks", {}),
                "estimated_time_hours": hours,
                "estimated_time_minutes": minutes,
                "completed": task.get("completed", False),
                "weight": task.get("weight", 10)
            }

            organized_tasks[main_task]["tasks"].append(sub_task_data)

        # 更新子任务数量并排序
        for main_task in organized_tasks:
            organized_tasks[main_task]["sub_task_number"] = len(organized_tasks[main_task]["tasks"])
            # 按branch_number排序子任务
            organized_tasks[main_task]["tasks"].sort(key=lambda x: x["branch_number"])

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(organized_tasks, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存任务时出错: {e}")
            return False

    @staticmethod
    def load_tasks_from_json(filename):
        """
        加载任务，恢复原始格式，包含完成状态和总任务类型。

        参数:
            filename (str): 文件名

        返回:
            list: 任务列表，如果加载失败则返回None
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                organized_tasks = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载任务时出错: {e}")
            return None

        tasks = []
        for main_task, data in organized_tasks.items():
            # 获取主任务类型，如果有多个则使用第一个
            main_task_type = data["Types"][0] if data["Types"] else ""

            for sub_task in data["tasks"]:
                # 计算小时和分钟为估计时间
                hours = sub_task.get("estimated_time_hours", 0)
                minutes = sub_task.get("estimated_time_minutes", 0)

                # 转换为小时为单位的浮点数
                estimated_time = hours + (minutes / 60)

                task = {
                    "main_task": main_task,
                    "main_task_type": main_task_type,
                    "sub_task": sub_task["sub_task_name"],
                    "details": sub_task["details"],
                    "estimated_time": estimated_time,
                    "branch_number": sub_task["branch_number"],
                    "completed": sub_task["completed"],
                    "weight": sub_task.get("weight", 10),
                    "sub_task_tasks": sub_task.get("sub_task_tasks", {})
                }
                tasks.append(task)

        return tasks

    @staticmethod
    def filter_tasks_by_type(tasks, task_type):
        """
        按类型筛选任务

        参数:
            tasks (list): 任务对象列表
            task_type (str): 任务类型

        返回:
            list: 筛选后的任务列表
        """
        if not task_type or task_type == "全部":
            return tasks

        return [task for task in tasks if task.get("main_task_type") == task_type]

    @staticmethod
    def search_tasks(tasks, query):
        """
        在任务中搜索关键词

        参数:
            tasks (list): 任务对象列表
            query (str): 搜索关键词

        返回:
            list: 匹配的任务列表
        """
        if not query:
            return tasks

        query = query.lower()
        results = []

        for task in tasks:
            if (query in task.get("main_task_type", "").lower() or
                    query in task.get("main_task", "").lower() or
                    query in task.get("sub_task", "").lower() or
                    query in task.get("details", "").lower()):
                results.append(task)

        return results

    @staticmethod
    def backup_tasks_file(filename):
        """
        创建任务文件的备份

        参数:
            filename (str): 要备份的文件名

        返回:
            str: 备份文件名，如果备份失败则返回None
        """
        if not os.path.exists(filename):
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.splitext(filename)[0]}_{timestamp}.bak"

            with open(filename, 'r', encoding='utf-8') as src:
                with open(backup_name, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

            return backup_name
        except Exception as e:
            print(f"备份任务文件时出错: {e}")
            return None