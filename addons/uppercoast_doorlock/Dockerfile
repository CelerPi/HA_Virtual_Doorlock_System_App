# 官方 Docker Hub 镜像（自动使用 latest Python 版本，当前为 3.13+）
FROM python:alpine

# 如果 Docker Hub 访问失败，可改用以下国内镜像之一（注释掉上面那行，去掉下面某行的 #）：
# FROM registry.cn-hangzhou.aliyuncs.com/library/python:alpine
# FROM docker.mirrors.sjtug.sjtu.edu.cn/library/python:alpine
# FROM docker.mirrors.ustc.edu.cn/library/python:alpine

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

COPY run.sh /
COPY app /app

RUN chmod a+x /run.sh

ENV PYTHONPATH=/app \
  PYTHONUNBUFFERED=1

CMD [ "/run.sh" ]
