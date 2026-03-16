from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import requests
# CSS 美化模板
TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>任务清单-带AI鼓励</title>
    <style>
        body {
            font-family: "微软雅黑", Arial, sans-serif;
            background: linear-gradient(120deg,#f8fafc 60%,#dbeafe 100%);
            min-height:100vh;
            padding:0;
            margin:0;
        }
        .container {
            max-width: 500px;
            margin: 40px auto 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.07), 0 1.5px 6px rgba(80,98,168,0.13);
            padding: 2.5rem 2.5rem 1.6rem 2.5rem;
        }
        h1 {
            text-align: center;
            color: #2563eb;
            font-size: 1.95rem;
            letter-spacing: .05em;
            margin-bottom: 1.2rem;
        }
        form {
            display: flex;
            margin-bottom: 1.2rem;
            gap: .6rem;
        }
        input[type="text"] {
            flex: 1;
            padding: .6rem .9rem;
            border: 1.5px solid #aecbfa;
            border-radius: 8px;
            font-size: 1rem;
            outline: none;
            transition: border-color .2s;
            background: #f1f5fd;
        }
        input[type="text"]:focus {
            border-color: #2563eb;
            background: #e8eefd;
        }
        button, .delete-btn, .sum-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: .5rem 1.2rem;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            box-shadow: 0 1px 4px rgba(37,99,235,0.11);
            transition: background 0.15s;
        }
        button:hover, .sum-btn:hover {
            background: #1743a2;
        }
        .delete-btn {
            background: #ef4444;
            padding: .24rem .52rem;
            font-size: .97rem;
        }
        .delete-btn:hover {
            background: #c91c1c;
        }
        ul {
            list-style: none;
            padding: 0 0 .2rem 0;
            margin-bottom: .3rem;
        }
        li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: .58rem .3rem .58rem .18rem;
            font-size: 1.08rem;
            border-bottom: 1px dashed #e7e9fa;
        }
        li:last-child {
            border-bottom: none;
        }
        .summary-card {
            margin-top: 2rem;
            background: linear-gradient(90deg,#e0e7ff 65%,#f1f5f9 100%);
            padding: 1.5rem 1.1rem .55rem 1.2rem;
            border-radius: 12px;
            box-shadow: 0 1px 6px rgba(37,99,235,0.09);
            color: #2563eb;
            font-size: 1.18rem;
            letter-spacing: .03em;
            border-left: 5px solid #2563eb;
            margin-bottom: 1.5rem;
            font-weight: 500;
        }
        .flash {
            background: #fbf5c4;
            padding: .4rem .9rem;
            border-radius: 7px;
            color: #6c5200;
            margin-bottom: .88rem;
            border: 1.2px solid #ffe066;
            text-align: center;
        }
        .sum-btn {
            display: block;
            margin: 1.1rem auto 0 auto;
            background: #14b8a6;
            color: white;
            padding: .53rem 1.35rem;
            font-weight: 500;
            font-size: 1.06rem;
            border-radius: 28px;
            border: none;
            box-shadow: 0 1px 7px rgba(20,184,166,0.09);
            transition: background .13s;
        }
        .sum-btn:hover {
            background: #0f766e;
        }
        @media (max-width: 600px) {
            .container {
                padding: 1.1rem .77rem 1.2rem .77rem;
            }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>📋 任务清单</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash">
          {% for message in messages %}
            {{ message }}<br>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    <form method="POST" action="{{ url_for('index') }}">
        <input type="text" name="task" placeholder="输入今日任务，例如 复习单词">
        <button type="submit">添加</button>
    </form>
    <ul>
        {% for task in tasks %}
            <li>
                <span>{{ task }}</span>
                <a class="delete-btn" href="{{ url_for('index', delete=loop.index0) }}">✗ 删除</a>
            </li>
        {% else %}
            <li style="color:#a7adc6;text-align:center;">暂无任务，快来添加吧！</li>
        {% endfor %}
    </ul>
    <form method="POST" action="{{ url_for('summarize') }}">
        <button class="sum-btn" type="submit">AI 总结鼓励 💡</button>
    </form>
    {% if ai_summary %}
        <div class="summary-card">
            <b>AI鼓励✨：</b><br>
            {{ ai_summary | safe }}
        </div>
    {% endif %}
</div>
</body>
</html>
"""

app = Flask(__name__)
app.secret_key = 'random_secret_key_for_session'

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = "sk-5492c6a27d6d41f3aa8331bac6c76e71"  # 替换为你的真实Key

# 首页和处理添加/删除任务
@app.route('/', methods=['GET', 'POST'])
def index():
    if "tasks" not in session:
        session["tasks"] = []

    # 添加新任务
    if request.method == 'POST' and "task" in request.form:
        task = request.form.get("task", "").strip()
        if task:
            tasks = session["tasks"]
            tasks.append(task)
            session["tasks"] = tasks
            flash("添加成功~")
        return redirect(url_for('index'))

    # 删除任务
    if request.args.get("delete"):
        try:
            idx = int(request.args.get("delete"))
            tasks = session["tasks"]
            if 0 <= idx < len(tasks):
                tasks.pop(idx)
                session["tasks"] = tasks
                flash("已删除")
        except Exception:
            flash("删除失败")
        return redirect(url_for('index'))

    summary = session.pop("ai_summary", None)
    return render_template_string(TEMPLATE, tasks=session["tasks"], ai_summary=summary)

# 触发AI总结
@app.route('/summarize', methods=['POST'])
def summarize():
    tasks = session.get('tasks', [])
    task_list = "\n".join([f"[{t}]" for t in tasks]) if tasks else "[无任务]"
    prompt = f"以下是我的今日任务列表：{task_list}\n请用一句话中文总结我的今天计划，并给出鼓励。"
    data = {
        "model": "deepseek-chat",  # 请确认使用的模型名称
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(DEEPSEEK_API_URL, json=data, headers=headers, timeout=20)
        r.raise_for_status()
        res = r.json()
        # DeepSeek 返回格式可能为 res['choices'][0]['message']['content']
        summary = res.get('choices', [{}])[0].get('message', {}).get('content', 'AI总结失败')
    except Exception as e:
        summary = f"AI 总结失败: {e}"
    session["ai_summary"] = summary
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
