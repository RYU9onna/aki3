from flask import Flask, request, render_template, session
from flask_session import Session
import openai
import os
import random

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    playing = False
    message = ""
    session['image'] = session.get('image', 'top1.png')
    openai.api_key = session.get('openai_api_key', None)
    
    if request.method == 'POST':
        if "set_api_key" in request.form:
            api_key = request.form['api_key']
            session['openai_api_key'] = api_key
            openai.api_key = api_key
            message = "APIキーがセットされました。"
        elif "clear_api_key" in request.form:
            session.pop('openai_api_key', None)
            openai.api_key = None
            message = "APIキーが解除されました。"
        elif "play" in request.form:
            if openai.api_key:
                chat = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "system", "content": "あなたは私の20問ゲームの対戦相手です。今から1つの道具、家電、物体、食べ物、生き物、日本の芸能人などから名前だけを考えてください。その名前だけ返事してください。"}, {"role": "user", "content": "名前を１つ決めてください。その名前だけ返事してください。"}], temperature=1.2)
                session['topic'] = chat['choices'][0]['message']['content']
                message = "私が考えているのは何でしょう？質問して当ててみて"
                playing = True
                session['image'] = 'top2.png'
            else:
                message = "APIキーがセットされていません。"
        elif "surrender" in request.form:
            if 'topic' in session:
                message = "答えは" + session['topic'] + "でした"
                session.pop('topic', None)  # ゲームをリセット
                playing = False
                session['image'] = 'top4.png'
            else:
                message = "まずPlayを押してください"
        elif "question" in request.form:
            if 'topic' in session:
                question = request.form['question']
                # ユーザーが直接答えを推測した場合
                if question == session['topic']:
                    message = f"正解です！答えは {session['topic']} でした！"
                    session.pop('topic', None)  # ゲームをリセット
                    playing = False
                    session['image'] = 'top3.png'
                else:
                    # GPT-4に質問を評価させる
                    chat = openai.ChatCompletion.create(model="gpt-4", messages=[
                        {"role": "system", "content": "あなたは私の20問ゲームの対戦相手です。"},
                        {"role": "user", "content": f'"「{session["topic"]}"は、"{question}"？」と質問します。「はい」「少しそう」「どちらでもない」「違います」「少し違う」のいずれかだけで返事をします。'}
                    ])
                    answer = chat['choices'][0]['message']['content']
                    message = answer
                    playing = True
        else:
            message = "まずPlayを押してください"
    else:
        if not openai.api_key:
            message = "APIキーがセットされていません。"
    
    return render_template('index.html', message=message, playing=playing, image=session['image'])

if __name__ == '__main__':
    app.run(debug=True)
