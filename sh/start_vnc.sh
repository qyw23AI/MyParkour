#!/usr/bin/env bash
# 架构: Xvfb :1 (虚拟 X 服务器) + x11vnc (将画面暴露为 VNC)
# 避免了 TurboVNC 与 Xvfb 争抢同一 display 的冲突
set -euo pipefail

DISPLAY_NUM=1
VNC_PORT=5901
DISPLAY=":${DISPLAY_NUM}"
RESOLUTION="1920x1080"
DEPTH=24
VNC_PASSWD_FILE="${HOME}/.vnc/passwd"
LOG_DIR="${HOME}/.vnc"
X11VNC_LOG="${LOG_DIR}/x11vnc.log"

export DISPLAY
export VGL_GLFLUSH=1
export VGL_VSYNC=1
export MUJOCO_GL=egl

mkdir -p "${LOG_DIR}"

# ── 工具函数 ───────────────────────────────────────────────
is_xvfb_running()  { pgrep -f "Xvfb ${DISPLAY}" > /dev/null 2>&1; }
is_vnc_listening() { ss -tlnp 2>/dev/null | grep -q ":${VNC_PORT}"; }
is_wm_running()    { pgrep -f "xfce4-session\|openbox\|fluxbox" > /dev/null 2>&1; }

die() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO]  $*"; }

# ── 1. 如果 VNC 端口已在监听，直接退出 ─────────────────────
if is_vnc_listening; then
    info "VNC server 已在运行，端口 ${VNC_PORT} 正常监听。"
    info "连接地址: $(hostname -I | awk '{print $1}'):${VNC_PORT}"
    exit 0
fi

# ── 2. VNC 密码 ─────────────────────────────────────────────
if [[ ! -f "${VNC_PASSWD_FILE}" ]]; then
    info "首次使用 VNC，请设置密码（至少 6 位）:"
    mkdir -p "$(dirname "${VNC_PASSWD_FILE}")"
    x11vnc -storepasswd "${VNC_PASSWD_FILE}" \
        || die "密码设置失败，请手动运行: x11vnc -storepasswd ${VNC_PASSWD_FILE}"
fi

# ── 3. 清理旧的 x11vnc 残留进程 ─────────────────────────────
if pgrep -f "x11vnc.*${DISPLAY}" > /dev/null 2>&1; then
    info "清理旧 x11vnc 进程..."
    pkill -f "x11vnc.*${DISPLAY}" || true
    sleep 1
fi

# ── 4. 启动 Xvfb（如果没在跑）──────────────────────────────
if is_xvfb_running; then
    info "Xvfb ${DISPLAY} 已在运行，跳过启动。"
else
    info "启动 Xvfb ${DISPLAY} (${RESOLUTION}x${DEPTH})..."
    # nohup + disown 确保 VS Code/SSH 断开后进程不被 SIGHUP 杀死
    nohup Xvfb "${DISPLAY}" -screen 0 "${RESOLUTION}x${DEPTH}" \
        -ac +extension GLX +render -noreset \
        &> "${LOG_DIR}/xvfb.log" &
    disown $!
    # 等待 Xvfb 就绪（最多 10 秒）
    for i in $(seq 1 10); do
        xdpyinfo -display "${DISPLAY}" > /dev/null 2>&1 && break
        sleep 1
        [[ $i -eq 10 ]] && die "Xvfb 启动超时，请检查系统日志。"
    done
    info "Xvfb 启动成功。"
fi

# ── 5. 启动窗口管理器（如果没在跑）────────────────────────
if is_wm_running; then
    info "窗口管理器已在运行，跳过启动。"
else
    info "启动 xfce4 桌面环境..."
    nohup bash -c "DISPLAY=${DISPLAY} xfce4-session" \
        &> "${LOG_DIR}/xfce4.log" &
    disown $!
    sleep 3
fi

# ── 6. 启动 x11vnc ─────────────────────────────────────────
info "启动 x11vnc，端口 ${VNC_PORT}..."
x11vnc \
    -display "${DISPLAY}" \
    -rfbport "${VNC_PORT}" \
    -rfbauth "${VNC_PASSWD_FILE}" \
    -forever \
    -shared \
    -noxrecord \
    -noxfixes \
    -noxdamage \
    -bg \
    -o "${X11VNC_LOG}"

# ── 7. 验证端口监听 ────────────────────────────────────────
for i in $(seq 1 5); do
    is_vnc_listening && break
    sleep 1
    [[ $i -eq 5 ]] && die "x11vnc 启动后端口 ${VNC_PORT} 未监听，查看日志: ${X11VNC_LOG}"
done

# ── 8. 完成 ────────────────────────────────────────────────
SERVER_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=============================================="
echo " VNC 服务已就绪"
echo " 连接地址 : ${SERVER_IP}:${VNC_PORT}"
echo " 日志文件 : ${X11VNC_LOG}"
echo " 停止命令 : pkill x11vnc"
echo "=============================================="
