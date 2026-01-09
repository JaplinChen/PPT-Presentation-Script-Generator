# 初始化 app 模組 - 最早的時機抑制警告
import warnings
import os

# 抑制所有煩人的棄用警告
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning,ignore::FutureWarning"
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*google.generativeai.*")
warnings.filterwarnings("ignore", message=".*on_event.*")
warnings.filterwarnings("ignore", message=".*deprecated.*")
