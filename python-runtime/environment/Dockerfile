# 示例环境定义：一个只含 Python 标准库的最小运行时
# 仅用于声明可复现环境，不要求构建（本地无需 docker 即可完成自检）
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace

# 本环境刻意不安装任何第三方包：所有示例资产都只用标准库
RUN python3 -c "import sys; assert sys.version_info >= (3, 10), 'need python>=3.10'"

COPY . /workspace/environment/
