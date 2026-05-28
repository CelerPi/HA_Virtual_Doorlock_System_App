# 国内用户如果 Docker Hub 访问失败，可改用以下镜像之一：
# 默认使用阿里云镜像的 latest 版本（当前为 Python 3.13+）
FROM registry.cn-hangzhou.aliyuncs.com/library/python:alpine
# 备选镜像源：
# FROM docker.mirrors.sjtug.sjtu.edu.cn/library/python:alpine
# FROM docker.mirrors.ustc.edu.cn/library/python:alpine
# 官方源（国内可能无法访问）：
# FROM python:alpine

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
