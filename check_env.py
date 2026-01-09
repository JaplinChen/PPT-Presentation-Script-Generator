import pkg_resources
import sys

# Agent 必須先跑這個腳本確認庫是否存在
required = {'flask', 'requests', 'sqlalchemy'} # 將你的核心庫填入此處
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    print(f"CRITICAL: Missing libraries: {missing}")
    print("ACTION: Stop coding. Run pip install first.")
    sys.exit(1)
else:
    print("Environment verified. Proceed.")