"""
test_install.py - 验证量化环境安装
"""
import sys
print(f"Python 版本：{sys.version}")

# 测试 pandas
import pandas as pd
print(f"pandas 版本：{pd.__version__}")
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print("pandas 测试通过:")
print(df)

# 测试 numpy
import numpy as np
print(f"\nnumpy 版本：{np.__version__}")
arr = np.array([1, 2, 3, 4, 5])
print("numpy 测试通过:")
print(f"数组：{arr}, 均值：{np.mean(arr)}")

# 测试 matplotlib
import matplotlib
print(f"\nmatplotlib 版本：{matplotlib.__version__}")
import matplotlib.pyplot as plt
plt.figure(figsize=(6, 4))
plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
plt.title("Matplotlib 测试")
plt.savefig("test_plot.png")
print("matplotlib 测试通过，图表已保存为 test_plot.png")

print("\n✅ 所有库安装成功！")
