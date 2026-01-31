from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()

def get_hf_client():
    token = os.getenv("HF_TOKEN")
    if token is None:
        raise RuntimeError("環境変数 HF_TOKEN が設定されていません")
    return InferenceClient(token=token)
