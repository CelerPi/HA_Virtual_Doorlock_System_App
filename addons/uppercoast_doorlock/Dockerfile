# 如果 Docker Hub 访问失败，可改用以下国内镜像之一（去掉前面的 #）：
# FROM docker.mirrors.sjtug.sjtu.edu.cn/library/python:3.12-alpine
# FROM docker.mirrors.ustc.edu.cn/library/python:3.12-alpine
# FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.12-alpine
FROM python:3.12-alpine

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
