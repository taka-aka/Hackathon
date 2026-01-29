import subprocess
import sys
import os
import signal

# OS共通の文字化け対策
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "UTF-8"

def main():
    # 起動コマンドの設定
    backend_cmd = [sys.executable, "-m", "uvicorn", "hackathon_app.main:app", "--reload"]
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", "src/hackathon_app/frontend/UI.py"]

    print("🚀 開発環境を起動中...")

    processes = []
    try:
        # バックエンドとフロントエンドを並列で起動
        p_back = subprocess.Popen(backend_cmd)
        processes.append(p_back)
        
        p_front = subprocess.Popen(frontend_cmd)
        processes.append(p_front)

        print("✅ 両方のプロセスが起動しました。終了するには Ctrl+C を押してください。")
        
        # プロセスが終了するのを待機
        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\n🛑 終了リクエストを受け取りました。停止中...")
    finally:
        # Ctrl+Cが押されたら全てのプロセスを確実に殺す
        for p in processes:
            if p.poll() is None: # まだ動いていたら
                if os.name == 'nt': # Windowsの場合
                    p.terminate()
                else: # Mac/Linuxの場合
                    os.kill(p.pid, signal.SIGTERM)
        print("👋 全てのプロセスを安全に停止しました。")

if __name__ == "__main__":
    main()