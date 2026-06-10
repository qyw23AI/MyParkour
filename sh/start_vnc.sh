#!/usr/bin/env bash
set -euo pipefail

export DISPLAY=:1
export VGL_GLFLUSH=1
export VGL_VSYNC=1
export MUJOCO_GL=egl

# 检查 VNC 密码是否已设置
if [[ ! -f "${HOME}/.vnc/passwd" ]]; then
    echo "首次使用 VNC，请设置密码（至少6位）:"
    vncpasswd
fi

if ! pgrep -f "Xvfb :1" > /dev/null; then
    echo "启动 Xvfb :1..."
    Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    sleep 2
fi

echo "启动 TurboVNC server..."
vncserver :1 -geometry 1920x1080 -depth 24 -vsys 0

echo ""
echo "VNC 服务已启动"
echo "连接地址: <your_server_ip>:5901"
echo "如需停止 VNC: vncserver -kill :1"
