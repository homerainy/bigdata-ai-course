# -*- coding: utf-8 -*-
"""
大数据与人工智能 —— 层层递进式刷题 Skill
==========================================

功能说明：
    这是一个可以交互做题的刷题程序，题目按难度「层层递进」设计，
    从 Python 基础一路到机器学习与人工智能核心概念。

    共 5 个关卡，顺序闯关：
        第 1 关  Python 入门         (基础语法)
        第 2 关  流程控制            (条件 / 循环)
        第 3 关  数据结构            (列表 / 字典 / 元组)
        第 4 关  数据分析            (pandas / numpy)
        第 5 关  机器学习与 AI       (核心概念)

    每题答完立即判断对错并给出解析，全部完成后统计总成绩。

运行方式：
    python skill.py

作者：homerainy
"""

import sys

# =====================================================================
# 题库数据：层层递进设计
# 每个关卡是一个字典，questions 里每题包含：
#   question : 题目
#   options  : 选项列表（判断题只有 "正确" / "错误"）
#   answer   : 正确答案（填写选项里的内容）
#   explain  : 解析（答完后展示，帮助理解）
# =====================================================================

LEVELS = [
    {
        "title": "第 1 关 · Python 入门",
        "desc": "基础语法：变量、数据类型、输入输出",
        "questions": [
            {
                "question": "Python 中用于向控制台输出内容的函数是？",
                "options": ["print()", "input()", "echo()", "output()"],
                "answer": "print()",
                "explain": "print() 用于输出，input() 用于接收用户输入。",
            },
            {
                "question": "在 Python 中，单行注释使用什么符号开头？",
                "options": ["//", "#", "--", "/*"],
                "answer": "#",
                "explain": "Python 单行注释用 #，多行注释用三个引号 ''' 或 \"\"\"。",
            },
            {
                "question": "以下哪个是合法的 Python 变量名？",
                "options": ["2name", "my-name", "_name", "class"],
                "answer": "_name",
                "explain": "变量名不能以数字开头、不能含连字符、不能是关键字，但可以以下划线开头。",
            },
            {
                "question": "字符串 \"hello\" 的长度是多少？",
                "options": ["4", "5", "6", "7"],
                "answer": "5",
                "explain": "len(\"hello\") 返回 5，共 h-e-l-l-o 五个字符。",
            },
        ],
    },
    {
        "title": "第 2 关 · 流程控制",
        "desc": "条件判断与循环结构",
        "questions": [
            {
                "question": "Python 中实现条件判断的关键字是？",
                "options": ["if", "for", "while", "switch"],
                "answer": "if",
                "explain": "if 用于条件判断，for/while 用于循环。",
            },
            {
                "question": "要依次遍历 0、1、2、3、4 这 5 个数，应使用？",
                "options": ["range(5)", "range(4)", "range(1,5)", "range(0,4)"],
                "answer": "range(5)",
                "explain": "range(5) 生成 0~4 共 5 个数；range(1,5) 是 1~4。",
            },
            {
                "question": "关于 while 循环，下列说法正确的是？",
                "options": ["条件为真时循环体才执行", "条件为假时循环体才执行", "无论如何都会执行", "只能执行一次"],
                "answer": "条件为真时循环体才执行",
                "explain": "while 在条件为 True 时反复执行循环体，直到条件变为 False。",
            },
            {
                "question": "以下代码会输出几次 Hello？for i in range(3): print('Hello')",
                "options": ["2 次", "3 次", "4 次", "无数次"],
                "answer": "3 次",
                "explain": "range(3) 产生 0、1、2 共 3 次迭代，所以输出 3 次。",
            },
        ],
    },
    {
        "title": "第 3 关 · 数据结构",
        "desc": "列表、字典、元组等常用容器",
        "questions": [
            {
                "question": "以下哪个是 Python 中可以修改（可变）的序列？",
                "options": ["元组 tuple", "列表 list", "字符串 str", "集合 set（无序）"],
                "answer": "列表 list",
                "explain": "列表可增删改；元组和字符串是不可变的。",
            },
            {
                "question": "字典 dict 是通过什么来访问对应的值的？",
                "options": ["下标数字", "键 key", "位置索引", "函数"],
                "answer": "键 key",
                "explain": "字典是「键-值」对结构，通过键来访问值，如 d['name']。",
            },
            {
                "question": "以下说法正确的是？",
                "options": ["元组可以修改元素", "列表元素可以增删改", "字符串可以改中间某个字符", "字典的键可以重复"],
                "answer": "列表元素可以增删改",
                "explain": "列表可变；元组、字符串不可变；字典的键必须唯一。",
            },
            {
                "question": "list.append(x) 的作用是？",
                "options": ["在列表头部插入 x", "在列表末尾添加 x", "删除 x", "对列表排序"],
                "answer": "在列表末尾添加 x",
                "explain": "append() 在末尾追加一个元素；insert() 才是在指定位置插入。",
            },
        ],
    },
    {
        "title": "第 4 关 · 数据分析",
        "desc": "pandas / numpy 数据处理基础",
        "questions": [
            {
                "question": "常用于数据分析和科学计算的第三方库是？",
                "options": ["pandas", "requests", "flask", "pygame"],
                "answer": "pandas",
                "explain": "pandas 是数据分析核心库，requests 是网络请求，flask 是 Web 框架。",
            },
            {
                "question": "pandas 中用于读取 CSV 文件的函数是？",
                "options": ["pd.read_csv()", "pd.read_excel()", "pd.to_csv()", "pd.open()"],
                "answer": "pd.read_csv()",
                "explain": "read_csv 读 CSV，read_excel 读 Excel，to_csv 是写出。",
            },
            {
                "question": "numpy 的 ndarray 数组中的元素类型，下列说法正确的是？",
                "options": ["可以各不相同", "必须完全相同", "只能是整数", "只能是浮点数"],
                "answer": "必须完全相同",
                "explain": "ndarray 要求所有元素类型一致（同质数组），这是它与列表的重要区别。",
            },
            {
                "question": "pandas 的 DataFrame 是几维的数据结构？",
                "options": ["一维", "二维", "三维", "四维"],
                "answer": "二维",
                "explain": "DataFrame 是带行列标签的二维表；Series 才是一维的。",
            },
        ],
    },
    {
        "title": "第 5 关 · 机器学习与 AI",
        "desc": "监督学习、模型评估与人工智能概念",
        "questions": [
            {
                "question": "使用「带标签」的数据进行训练的学习方式叫？",
                "options": ["监督学习", "无监督学习", "强化学习", "迁移学习"],
                "answer": "监督学习",
                "explain": "监督学习有输入和对应标签；无监督学习没有标签。",
            },
            {
                "question": "评估分类模型时，最常用的基础指标是？",
                "options": ["准确率 accuracy", "方差 variance", "标准差 std", "中位数 median"],
                "answer": "准确率 accuracy",
                "explain": "准确率 = 预测正确的样本数 / 总样本数，是最直观的分类指标。",
            },
            {
                "question": "关于「过拟合」，下列说法正确的是？",
                "options": [
                    "训练集表现好但测试集表现差",
                    "训练集和测试集表现都差",
                    "模型过于简单",
                    "数据量过大",
                ],
                "answer": "训练集表现好但测试集表现差",
                "explain": "过拟合指模型记住了训练数据细节，泛化到新数据（测试集）时表现差。",
            },
            {
                "question": "由 Google 开发的著名深度学习框架是？",
                "options": ["TensorFlow", "Flask", "Django", "Requests"],
                "answer": "TensorFlow",
                "explain": "TensorFlow 是 Google 的深度学习框架，另 PyTorch 由 Meta 主导。",
            },
        ],
    },
]

PASS_SCORE = 60  # 每关过关分数线（百分制）


def clear_screen():
    """清屏（Windows 用 cls，其他用 clear）。"""
    import os
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    """打印程序标题。"""
    banner = r"""
  ============================================
   大数据与人工智能 · 层层递进刷题 Skill
  ============================================
   共 {n} 关，从易到难，闯关成功才算通关！
  """.format(n=len(LEVELS))
    print(banner)


def ask_question(level_idx, q_idx, q):
    """
    出题并返回该题是否正确。
    level_idx: 关卡序号（从 0 开始）
    q_idx    : 题序号（从 0 开始）
    q        : 题目字典
    """
    print("-" * 44)
    print(f"[{level_idx + 1}-{q_idx + 1}] {q['question']}")
    print()
    for i, opt in enumerate(q["options"], start=1):
        print(f"    {i}. {opt}")

    # 获取用户输入并校验
    while True:
        try:
            choice = input("\n请输入选项序号 (1-%d)： " % len(q["options"])).strip()
            idx = int(choice) - 1
            if 0 <= idx < len(q["options"]):
                break
            print(f"   ⚠ 请输入 1 到 {len(q['options'])} 之间的数字。")
        except ValueError:
            print("   ⚠ 输入无效，请输入数字。")

    user_answer = q["options"][idx]
    correct = (user_answer == q["answer"])

    if correct:
        print("   ✅ 回答正确！")
    else:
        print(f"   ❌ 回答错误，正确答案是：{q['answer']}")

    print(f"   💡 解析：{q['explain']}")
    print()
    return correct


def play_level(level_idx, level):
    """
    闯一关：逐题作答，返回本关得分（0~100）。
    """
    print("\n" + "=" * 44)
    print(f"  {level['title']}")
    print(f"  {level['desc']}")
    print("=" * 44 + "\n")

    total = len(level["questions"])
    correct_count = 0

    for q_idx, q in enumerate(level["questions"]):
        if ask_question(level_idx, q_idx, q):
            correct_count += 1

    score = round(correct_count / total * 100)
    print("-" * 44)
    print(f"  本关得分：{score} 分（答对 {correct_count}/{total} 题）")

    return score


def main():
    """主流程：顺序闯关 + 总分统计。"""
    clear_screen()
    print_banner()

    total_score = 0
    passed_all = True

    for level_idx, level in enumerate(LEVELS):
        input(f"\n按回车键开始「{level['title']}」...")
        score = play_level(level_idx, level)
        total_score += score

        if score >= PASS_SCORE:
            print(f"  🎉 恭喜过关！（≥{PASS_SCORE} 分）\n")
        else:
            print(f"  ⚠ 本关未达 {PASS_SCORE} 分，建议复习后再来挑战。\n")
            passed_all = False

    # 汇总
    avg_score = round(total_score / len(LEVELS))
    print("=" * 44)
    print("  全部关卡完成！成绩汇总：")
    print(f"    总成绩：{total_score} 分")
    print(f"    平均分：{avg_score} 分")
    if passed_all:
        print("    🏆 全部通关，太棒了！")
    else:
        print("    💪 继续加油，多多练习就能通关！")
    print("=" * 44)

    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已退出。")
        sys.exit(0)
