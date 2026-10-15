//<script>
(async () => {
    const pluginName = "Tailscale"
    let AP_ACCESS_ENABLED = false
    let Log_INTERVAL = null

    const oldDom = document.getElementById(`IFRAME_REX_${pluginName}`);
    if (oldDom) oldDom.remove();
    const checkWeakToken = () => {
        if (typeof SHA256 !== 'undefined') {
            let weakTokenList = ["admin", "password", "666", "6666", "12345", "123456", "1234567", "12345678", "123456789", "1234567890", "root"]
            for (let token of weakTokenList) {
                if (SHA256(token) == KANO_TOKEN.toUpperCase()) return true
            }
        }
        return false
    }

    const checkAdvanceFunc = async () => {
        const res = await runShellWithRoot('whoami')
        return !!(res.content && res.content.includes('root'))
    }

    const checkIsBootUp = async (installed) => {
        if (installed === undefined) installed = await isInstall()
        if (!installed) return false

        const bootScriptExists = await runShellWithRoot(`test -f /sdcard/ufi_tools_boot.sh && echo "exists" || echo "not_found"`)
        if (bootScriptExists.content && bootScriptExists.content.includes("not_found")) {
            return false
        }

        const res = await runShellWithRoot(`
        grep -q '/data/rex_Tailscale/service.sh start' /sdcard/ufi_tools_boot.sh 2>/dev/null
        echo $?
        `)
        return res.content.trim() == '0';
    }

    const checkApAccessEnabled = async () => {
        try {
            const res = await runShellWithRoot(`ls /data/rex_Tailscale/flag/enableHotspotAccess`)
            return res.content && res.content.includes('enableHotspotAccess')
        } catch { return false }
    }

    const updateNatBtnState = async (installed) => {
        const btn = document.querySelector('#tailscale_nat_btn')
        if (!btn) return
        if (installed === undefined) installed = await isInstall()
        if (!installed) {
            btn.style.display = 'none'
            return
        }
        btn.style.display = ''
        AP_ACCESS_ENABLED = await checkApAccessEnabled()
        if (AP_ACCESS_ENABLED) {
            btn.style.background = "var(--dark-btn-color-active)"
        } else {
            btn.style.background = ""
        }
    }

    const isInstall = async () => {
        const res = await runShellWithRoot(`test -f /data/rex_Tailscale/service.sh && echo "exists" || echo "not_found"`)
        return !!(res.content && res.content.includes("exists"))
    }

    const checkLoginStatus = async () => {
        const res = await runShellWithRoot(`/data/rex_Tailscale/service.sh status_json`)
        try {
            const status = JSON.parse(res.content || '{}')
            return status && status.BackendState === 'Running'
        } catch {
            return false
        }
    }

    const getUserInfo = async () => {
        try {
            const res = await runShellWithRoot(`/data/rex_Tailscale/service.sh status_json`)

            if (!res.success || !res.content || typeof res.content !== 'string') {
                console.error('[getUserInfo] Invalid response:', res)
                return { isLoggedIn: false, userName: '', hostName: '' }
            }

            try {
                const status = JSON.parse(res.content || '{}')

                if (status && status.Self) {
                    const userIdStr = String(status.Self.UserID)
                    const userProfile = (status.User && (status.User[userIdStr] || Object.values(status.User)[0])) || null
                    const hasUserProfile = userProfile && userProfile.LoginName
                    const isNotNeedingLogin = status.BackendState !== 'NeedsLogin' && status.BackendState !== 'NoState'

                    return {
                        isLoggedIn: !!(hasUserProfile && isNotNeedingLogin),
                        userName: userProfile?.DisplayName || userProfile?.LoginName || status.Self.DNSName || '未知用户',
                        hostName: status.Self.HostName || '',
                    }
                }
            } catch (e) {
                console.error('[getUserInfo] JSON parse error:', e)
                console.error('[getUserInfo] Raw content was:', res.content?.substring(0, 200))
            }
        } catch (error) {
            // Handle abort errors and other exceptions
            console.error('[getUserInfo] Command execution error:', error)
            if (error.name === 'AbortError' || (error.message && error.message.includes('abort'))) {
                console.error('[getUserInfo] Request was aborted (likely timeout)')
            }
        }
        return { isLoggedIn: false, userName: '', hostName: '' }
    }

    const updateBootBtnState = async (installed) => {
        const boot_on = document.querySelector('#tailscale_boot_on')
        if (!boot_on) return

        if (installed === undefined) installed = await isInstall()
        if (!installed) {
            boot_on.style.display = 'none'
            return
        }

        boot_on.style.display = ''
        const isBootUp = await checkIsBootUp(installed)
        if (isBootUp) {
            boot_on.style.background = "var(--dark-btn-color-active)"
            boot_on.textContent = "已开启自启"
        } else {
            boot_on.style.background = ""
            boot_on.textContent = "开机自启"
        }
    }

    const updateLoginBtnState = async (installed, isFreshInstall) => {
        const login_container = document.querySelector('#tailscale_login_container')
        if (!login_container) return

        if (installed === undefined) installed = await isInstall()
        if (!installed) {
            login_container.innerHTML = ''
            return
        }

        const userInfo = isFreshInstall ? { isLoggedIn: false, userName: '', hostName: '' } : await getUserInfo()

        if (userInfo.isLoggedIn) {
            login_container.innerHTML = `
                <button id="tailscale_username_btn" style="background:#1e3a1e;color:#4CAF50;margin-right:6px;cursor:pointer;" title="点击跳转到管理页面">
                    <span style="margin-right:4px;">✓</span>${userInfo.userName}
                </button>
                <button id="tailscale_logout_btn" style="background:#f44336;margin:0;">退出登录</button>
            `
            // 绑定用户名点击事件
            const usernameBtn = document.querySelector('#tailscale_username_btn')
            if (usernameBtn) {
                usernameBtn.onclick = () => {
                    window.open('https://login.tailscale.com/admin/machines', '_blank')
                }
            }
            // 绑定退出登录事件
            const logoutBtn = document.querySelector('#tailscale_logout_btn')
            if (logoutBtn) {
                let count = 0
                let timer = null
                logoutBtn.onclick = async () => {
                    if (! await checkAdvanceFunc()) return createToast("无Root权限！")
                    if (timer) clearTimeout(timer)
                    timer = setTimeout(() => { count = 0 }, 2000)
                    if (count++ < 2) return createToast(count === 1 ? "再点两次确认退出" : "再点一次确认退出")

                    createToast("正在退出登录...")
                    await runShellWithRoot(`/data/rex_Tailscale/service.sh logout`)
                    createToast("已退出登录", 'green')
                    genLog()
                    setTimeout(() => updateLoginBtnState(), 1000)
                }
            }
        } else {
            login_container.innerHTML = `<button id="tailscale_login_btn" style="background:#2196F3;margin:0;">登录</button>`
            // 绑定登录事件
            const loginBtn = document.querySelector('#tailscale_login_btn')
            if (loginBtn) {
                loginBtn.onclick = async () => {
                    if (! await checkAdvanceFunc()) return createToast("无Root权限！")
                    createToast("正在获取登录链接...")
                    const res = await runShellWithRoot(`/data/rex_Tailscale/service.sh get_login_url`)
                    const loginUrl = res.content ? res.content.trim() : ''

                    if (loginUrl && loginUrl.includes('https://')) {
                        createToast(`正在打开登录页面...`, 'green', 5000)
                        window.open(loginUrl, '_blank')
                        genLog()
                        // 轮询检查登录状态（每2秒检查一次，持续60秒）
                        let checkCount = 0
                        const maxChecks = 30 // 30 * 2s = 60s
                        const checkInterval = setInterval(async () => {
                            checkCount++
                            const info = await getUserInfo()
                            if (info.isLoggedIn) {
                                clearInterval(checkInterval)
                                updateLoginBtnState()
                                createToast("登录成功！", 'green')
                                genLog()
                            } else if (checkCount >= maxChecks) {
                                clearInterval(checkInterval)
                                createToast("登录检测超时，请手动刷新或重新登录", 'pink')
                                updateLoginBtnState() // 最后更新一次状态，以防万一
                            }
                        }, 2000)
                    } else {
                        createToast("未找到登录链接，请先重启服务生成新的登录链接", 'red', 6000)
                        genLog()
                    }
                }
            }
        }
    }

    const updateInstallBtnState = async (installed) => {
        const install_container = document.querySelector('#tailscale_install_container')
        if (!install_container) return

        if (installed === undefined) installed = await isInstall()

        if (installed) {
            install_container.style.display = 'none'
            return
        }

        install_container.style.cssText = 'display:flex; width: 100%; justify-content: center; padding: 20px 0;'
        install_container.innerHTML = `
            <div style="text-align: center; width: 100%;">
                <div style="margin-bottom: 12px; color: #888; font-size: 14px;">Tailscale 组网服务尚未安装，点击下方按钮一键部署</div>
                <button id="tailscale_install_btn" style="margin:0;background:#4CAF50;padding: 10px 32px; font-size: 15px; border-radius: 8px; border: none; font-weight: bold; box-shadow: 0 4px 12px green; cursor: pointer; color: white;">🚀 开始安装</button>
            </div>
        `

        // 绑定安装按钮事件
        const installBtn = document.querySelector('#tailscale_install_btn')
        if (installBtn) {
            installBtn.onclick = async () => {
                if (checkWeakToken()) { return createToast(`检测到弱口令，请先修改密码！`, "red", 8000) }
                if (! await checkAdvanceFunc()) return createToast("没有开启高级功能！", 'red')

                if (await isInstall()) return createToast("已安装，请勿重复安装！", 'red')

                createToast("开始下载安装包...")
                const res1 = await runShellWithRoot(`/data/data/com.minikano.f50_sms/files/curl -L "https://pan.rexe.cc/d/UFI-TOOLS-UPDATE/plugins/rex_Tailscale.zip" -o /data/rex_Tailscale.zip --output /data/rex_Tailscale.zip --write-out "DOWNLOAD_DONE\nTotal: %{size_download} bytes\nSpeed: %{speed_download} B/s\nTime: %{time_total} sec\n" > /data/tailscale_download.log 2>&1 &`, 100 * 1000)

                if (!res1.success) {
                    createToast("下载失败", 'red')
                    return
                }

                let log = ''
                const max_times = 600 // 最多等待10分钟
                let count_times = 0
                const { el, close } = createFixedToast("tailscale_download_toast", `<pre style="white-space: pre-wrap;min-width:300px;text-align: center;">等待日志中...</pre>`, '')

                const interval = setInterval(async () => {
                    const dlog = await runShellWithRoot("timeout 2s awk '{print}' /data/tailscale_download.log")
                    const lines = dlog.content.split('\n');
                    log = lines.slice(-6).join('\n');
                    el.innerHTML = `<pre style="white-space: pre-wrap;min-width:300px;text-align: center;">${log.replaceAll('\n', "<br>")}</pre>`
                    if (log.includes('DOWNLOAD_DONE')) {
                        setTimeout(() => {
                            close()
                        }, 2000);
                    }
                }, 1000)

                while (true) {
                    if (max_times <= count_times) {
                        clearInterval(interval)
                        close()
                        createToast("下载超时，请检查网络连接或稍后重试！", 'red')
                        return
                    }
                    if (log.includes('DOWNLOAD_DONE')) {
                        clearInterval(interval)
                        break
                    }
                    count_times++
                    await new Promise(resolve => setTimeout(resolve, 1000))
                }

                await runShellWithRoot("rm -f /data/tailscale_download.log")

                const checkDownload = await runShellWithRoot(`test -f /data/rex_Tailscale.zip && echo "exists" || echo "not_found"`)
                if (!checkDownload.content || checkDownload.content.includes("not_found")) {
                    createToast("下载文件不存在，安装失败", 'red')
                    return
                }

                createToast("解压中...")
                const res2 = await runShellWithRoot(`
                    cd /data && rm -rf rex_Tailscale_temp rex_Tailscale && 
                    mkdir -p rex_Tailscale_temp && 
                    unzip -o rex_Tailscale.zip -d rex_Tailscale_temp && 
                    if [ -d "rex_Tailscale_temp/rex_Tailscale" ]; then
                        mv rex_Tailscale_temp/rex_Tailscale rex_Tailscale
                        rm -rf rex_Tailscale_temp
                    else
                        mv rex_Tailscale_temp rex_Tailscale
                    fi
                    mkdir -p /data/rex_Tailscale/bin /data/rex_Tailscale/data /data/rex_Tailscale/flag
                    mv /data/rex_Tailscale/tailscale /data/rex_Tailscale/bin/ 2>/dev/null
                    mv /data/rex_Tailscale/tailscaled /data/rex_Tailscale/bin/ 2>/dev/null
                `)

                if (!res2.success) {
                    createToast("解压失败", 'red')
                    return
                }
                const checkFiles = await runShellWithRoot(`
                    test -f /data/rex_Tailscale/service.sh && 
                    test -f /data/rex_Tailscale/bin/tailscale && 
                    test -f /data/rex_Tailscale/bin/tailscaled && 
                    echo "exists" || echo "not_found"
                `)
                if (!checkFiles.content || checkFiles.content.includes("not_found")) {
                    createToast("关键文件缺失，安装失败", 'red')
                    await runShellWithRoot(`rm -rf /data/rex_Tailscale /data/rex_Tailscale.zip`)
                    return
                }

                createToast("设置权限...")
                await runShellWithRoot(`chmod 777 /data/rex_Tailscale/bin/tailscale /data/rex_Tailscale/bin/tailscaled /data/rex_Tailscale/service.sh || true`)

                createToast("设置自启动...")
                await runShellWithRoot(`grep -qxF '/data/rex_Tailscale/service.sh start' /sdcard/ufi_tools_boot.sh || echo '/data/rex_Tailscale/service.sh start' >> /sdcard/ufi_tools_boot.sh`)

                createToast("启动服务...")
                await runShellWithRoot(`nohup /data/rex_Tailscale/service.sh start >/dev/null 2>&1 &`)
                await runShellWithRoot(`rm -f /data/rex_Tailscale.zip /data/rex_Tailscale/Tailscale*.js`)

                createToast(`安装成功！`, 'green')
                await Promise.all([showConf(), updateAllStates(true, true)])
                startLogPolling()
            }
        }

    }

    const showConf = async () => {
        try {
            const Tailscale_config = document.querySelector('#Tailscale_config')
            if (Tailscale_config) {
                // 先检查文件是否存在
                const checkFile = await runShellWithRoot(`test -f /data/rex_Tailscale/config.txt && echo "exists" || echo "not_found"`)
                if (checkFile.content && checkFile.content.includes("not_found")) {
                    Tailscale_config.value = `# Tailscale 配置文件，请根据需要修改配置

# ============ 基础配置 ============
# 是否启用Tailscale服务（true/false）
ENABLED="true"

# Tailscaled监听端口（留空使用默认端口41641）
PORT=""

# ============ 网络配置 ============
# 是否接受路由（true/false）
ACCEPT_ROUTES="false"

# 主机名
HOSTNAME="REX"

# 是否使用MagicDNS（true/false）
ACCEPT_DNS="false"

# ============ 路由配置 ============
# 是否作为出口节点（true/false）
ADVERTISE_EXIT_NODE="false"

# 使用的出口节点（IP或主机名）
EXIT_NODE=""

# 广播路由（逗号或空格分隔，例如：192.168.0.0/24,10.0.0.0/8）
# 广播子网路由至 Tailscale
ADVERTISE_ROUTES=""

# 子网互通（true/false，禁用子网路由的源网络地址转换）
DISABLE_SNAT_SUBNET_ROUTES="false"

# 子网路由（逗号或空格分隔，例如：192.168.1.0/24,192.168.2.0/24）
# 通过本机访问的其他Tailscale节点的子网
SUBNET_ROUTES=""

# ============ 自建 Headscale 配置 ============
# 服务器地址
LOGIN_SERVER=""

# 认证密钥
AUTHKEY=""

# ============ 其他配置 ============
# 其他额外参数（空格分隔，例如：--exit-node=10.0.0.1 --exit-node-allow-lan-access）
# 更多参数请参考：https://tailscale.com/docs/reference/tailscale-cli/up
FLAGS=""
`
                } else {
                    const res = await runShellWithRoot(`timeout 2s awk '{print}' /data/rex_Tailscale/config.txt`)
                    Tailscale_config.value = res.content || ""
                }
            }
        } catch (e) {
            console.error("showConf error:", e)
        }
    }

    // 生成日志
    let pervLogText = ''

    const genLog = async () => {
        const Tailscale_textarea = document.querySelector("#Tailscale_textarea")
        if (Tailscale_textarea) {
            const res = await runShellWithRoot(`timeout 2s  awk '{print}' /dev/log/Tailscale_LOG.txt | tail -n 50`)
            if (res.content == pervLogText) return
            pervLogText = res.content

            // 将 UTC 时间转换为浏览器本地时区时间（自动适配用户时区）
            const convertedContent = res.content.replace(
                /(\d{4})\/(\d{2})\/(\d{2}) (\d{2}):(\d{2}):(\d{2})/g,
                (match, year, month, day, hour, minute, second) => {
                    const utcDate = new Date(Date.UTC(year, month - 1, day, hour, minute, second))
                    // sv-SE locale 输出 YYYY-MM-DD HH:MM:SS，替换 - 为 / 匹配原格式
                    return utcDate.toLocaleString('sv-SE').replace(/-/g, '/').replace('T', ' ')
                }
            )

            Tailscale_textarea.value = `${convertedContent}\n`
            Tailscale_textarea.scrollTop = Tailscale_textarea.scrollHeight
        }
    }

    // 保存配置文件
    const saveConfig = async (conf) => {
        try {
            const file = new File([conf], "config.txt", { type: "text/plain" });
            const formData = new FormData();
            formData.append("file", file);
            const res = await (await fetch(`${KANO_baseURL}/upload_img`, {
                method: "POST",
                headers: common_headers,
                body: formData,
            })).json()

            if (res.url) {
                let foundFile = await runShellWithRoot(`ls /data/data/com.minikano.f50_sms/files${res.url}`)
                if (!foundFile.content) throw "上传失败"

                let resShell = await runShellWithRoot(`mv /data/data/com.minikano.f50_sms/files${res.url} /data/rex_Tailscale/config.txt`)

                if (resShell.success) {
                    createToast(`配置保存成功！正在重启...`, 'green')
                    const restartBtn = document.getElementById('tailscale_restart_btn');
                    if (restartBtn) restartBtn.click();
                    await showConf()
                }
            } else throw res.error || ''
        }
        catch (e) {
            console.error(e);
            createToast(`保存失败!`, 'red')
        } finally {
            genLog()
        }
    }

    const stopBtn = document.createElement('button')
    stopBtn.textContent = "停止"
    stopBtn.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！")
        const res = await runShellWithRoot(`/data/rex_Tailscale/service.sh stop`)
        createToast(res.success ? "已停止" : "停止失败", res.success ? 'pink' : 'red')
        genLog()
    }

    const restartBtn = document.createElement('button')
    restartBtn.id = 'tailscale_restart_btn'
    restartBtn.textContent = "重启服务"
    restartBtn.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！")
        createToast("正在重启...")
        const res = await runShellWithRoot(`
        /data/rex_Tailscale/service.sh restart
        `)
        createToast("重启完成", 'green')
        genLog()
        updateBootBtnState()
    }

    const createRandomString = (length = 8) => {
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        return result;
    }

    const showDeviceDialog = (message, title = "设备列表") => {

        const containerId = "toast_" + createRandomString(4)
        const id = 'close_message_btn_' + createRandomString(4)
        const id_refresh = 'refresh_btn_' + createRandomString(4)
        const message1 = message.replaceAll('\n', "<br>")
        const { el, close } = createFixedToast(containerId, `
        <div style="pointer-events:all;width:80vw;max-width:800px">
            <div class="title" style="margin:0">${title}</div>
            <div class="content_message" style="margin:10px 0;max-height: 400px;overflow: auto;font-size: 12px;font-family:monospace;white-space:pre-wrap;">${message1}</div>
            <div style="text-align:right">
                <button style="font-size:12px" id="${id_refresh}">刷新</button>
                <button style="font-size:12px" id="${id}">关闭</button>
            </div>
        </div>
        `)
        const btn = el.querySelector(`#${id}`)
        const rBtn = el.querySelector(`#${id_refresh}`)
        if (!btn) {
            close()
            return
        }

        const refresh = async (flag = false) => {
            const msg_el = el.querySelector(`.content_message`)
            const res = await runShellWithRoot(`/data/rex_Tailscale/service.sh list_devices`)
            if (res.success && res.content) {
                msg_el.innerHTML = res.content.replaceAll('\n', "<br>")
                flag && createToast("设备列表已刷新", 'green')
            } else {
                flag && createToast("获取设备列表失败", 'red')
            }
        }

        if (rBtn) {
            rBtn.onclick = async () => {
                await refresh(true)
            }
        }

        btn.onclick = async () => {
            close()
        }
    }

    const statusBtn = document.createElement('button')
    statusBtn.textContent = "查看设备列表"
    statusBtn.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！")
        createToast("正在获取设备列表...")
        const res = await runShellWithRoot(`/data/rex_Tailscale/service.sh list_devices`)
        if (!res.success || !res.content) return createToast("获取设备列表失败", 'red')
        showDeviceDialog(res.content, "Tailscale 设备列表")
    }

    const showPingDialog = () => {

        const containerId = "toast_" + createRandomString(4)
        const id = 'close_ping_btn_' + createRandomString(4)
        const id_ping = 'exec_ping_btn_' + createRandomString(4)
        const id_netcheck = 'exec_netcheck_btn_' + createRandomString(4)
        const id_input = 'ping_input_' + createRandomString(4)
        const id_output = 'ping_output_' + createRandomString(4)

        const { el, close } = createFixedToast(containerId, `
        <div style="pointer-events:all;width:80vw;max-width:800px">
            <div class="title" style="margin:0">Tailscale 网络诊断</div>
            <div style="margin:10px 0;display:flex;gap:6px;align-items:center;">
                <input type="text" id="${id_input}" placeholder="输入Tailscale内网IP、主机名或域名" style="flex:1;padding:8px;border:1px solid #444;border-radius:5px;background:#1e1e1e;color:#d4d4d4;font-size:14px;" />
                <button style="font-size:14px;padding:8px 16px;" id="${id_ping}">Ping</button>
                <button style="font-size:14px;padding:8px 16px;background:#ff9800;" id="${id_netcheck}">Netcheck</button>
            </div>
            <div id="${id_output}" style="margin:10px 0;max-height:400px;overflow:auto;font-size:12px;font-family:monospace;background:#000;color:#0f0;padding:8px;border:1px solid #444;border-radius:5px;white-space:pre-wrap;word-break:break-all;min-height:100px;"></div>
            <div style="text-align:right">
                <button style="font-size:12px" id="${id}">关闭</button>
            </div>
        </div>
        `)

        const closeBtn = el.querySelector(`#${id}`)
        const pingBtn = el.querySelector(`#${id_ping}`)
        const netcheckBtn = el.querySelector(`#${id_netcheck}`)
        const inputEl = el.querySelector(`#${id_input}`)
        const outputEl = el.querySelector(`#${id_output}`)

        if (!closeBtn || !pingBtn || !netcheckBtn || !inputEl || !outputEl) {
            close()
            return
        }

        outputEl.textContent = '等待执行命令...'

        let currentInterval = null

        const clearCurrentInterval = () => {
            if (currentInterval) {
                clearInterval(currentInterval)
                currentInterval = null
            }
        }

        const executePing = async () => {
            const target = inputEl.value.trim()
            if (!target) {
                createToast("请输入目标地址", 'red')
                return
            }

            clearCurrentInterval()

            outputEl.textContent = `正在 ping ${target}...\n`
            createToast(`正在执行 ping ${target}...`)

            await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_ping.log`)

            const startRes = await runShellWithRoot(`/data/rex_Tailscale/service.sh ping ${target} > /data/rex_Tailscale/tailscale_ping.log 2>&1 & echo $!`, 500)

            if (!startRes.success) {
                outputEl.textContent = `启动 ping 命令失败`
                createToast("启动 ping 命令失败", 'red')
                return
            }

            const pid = startRes.content ? startRes.content.trim() : ''
            let count = 0
            const maxWaitTime = 60

            currentInterval = setInterval(async () => {
                const logRes = await runShellWithRoot(`timeout 2s awk '{print}' /data/rex_Tailscale/tailscale_ping.log 2>/dev/null || echo ""`)

                if (logRes.content) {
                    outputEl.textContent = logRes.content
                    outputEl.scrollTop = outputEl.scrollHeight
                }

                if (pid) {
                    const checkProcess = await runShellWithRoot(`ps | grep ${pid} | grep -v grep`)
                    const isRunning = checkProcess.content && checkProcess.content.includes(pid)

                    if (!isRunning || count >= maxWaitTime) {
                        clearCurrentInterval()

                        const finalRes = await runShellWithRoot(`timeout 2s awk '{print}' /data/rex_Tailscale/tailscale_ping.log 2>/dev/null || echo ""`)
                        if (finalRes.content) {
                            outputEl.textContent = finalRes.content
                            outputEl.scrollTop = outputEl.scrollHeight
                        }

                        if (count >= maxWaitTime) {
                            createToast("Ping 超时", 'red')
                        } else {
                            createToast("Ping 执行完成", 'green')
                        }

                        await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_ping.log`)
                    }
                }
                count++
            }, 1000)
        }

        const executeNetcheck = async () => {
            clearCurrentInterval()

            outputEl.textContent = `正在执行 Netcheck...\n`
            createToast(`正在执行 Netcheck...`)

            await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_netcheck.log`)

            const startRes = await runShellWithRoot(`cd /data/rex_Tailscale && /data/rex_Tailscale/service.sh netcheck > /data/rex_Tailscale/tailscale_netcheck.log 2>&1 & echo $!`, 500)

            if (!startRes.success) {
                outputEl.textContent = `启动 Netcheck 失败`
                createToast("启动 Netcheck 失败", 'red')
                return
            }

            const pid = startRes.content ? startRes.content.trim() : ''
            let count = 0
            const maxWaitTime = 30 // netcheck shouldn't take too long

            currentInterval = setInterval(async () => {
                const logRes = await runShellWithRoot(`timeout 2s awk '{print}' /data/rex_Tailscale/tailscale_netcheck.log 2>/dev/null || echo ""`)

                if (logRes.content) {
                    outputEl.textContent = logRes.content
                    outputEl.scrollTop = outputEl.scrollHeight
                }

                if (pid) {
                    const checkProcess = await runShellWithRoot(`ps | grep ${pid} | grep -v grep`)
                    const isRunning = checkProcess.content && checkProcess.content.includes(pid)

                    if (!isRunning || count >= maxWaitTime) {
                        clearCurrentInterval()

                        const finalRes = await runShellWithRoot(`timeout 2s awk '{print}' /data/rex_Tailscale/tailscale_netcheck.log 2>/dev/null || echo ""`)
                        if (finalRes.content) {
                            outputEl.textContent = finalRes.content
                            outputEl.scrollTop = outputEl.scrollHeight
                        }

                        createToast("Netcheck 执行完成", 'green')
                        await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_netcheck.log`)
                    }
                }
                count++
            }, 1000)
        }

        pingBtn.onclick = executePing
        netcheckBtn.onclick = executeNetcheck

        inputEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                executePing()
            }
        })

        closeBtn.onclick = () => {
            clearCurrentInterval()
            close()
        }
    }

    const networkBtn = document.createElement('button')
    networkBtn.textContent = "网络诊断"
    networkBtn.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！")
        showPingDialog()
    }

    const updateServiceBtnsState = async (installed) => {
        if (installed === undefined) installed = await isInstall()
        const display = installed ? '' : 'none'
        if (stopBtn) stopBtn.style.display = display
        if (restartBtn) restartBtn.style.display = display
        if (statusBtn) statusBtn.style.display = display
        if (networkBtn) networkBtn.style.display = display
        if (monitorBtn) monitorBtn.style.display = display
        if (natBtn) natBtn.style.display = display

        const configLogContainer = document.querySelector('#tailscale_config_log_container')
        if (configLogContainer) configLogContainer.style.display = display

        const hintContainer = document.querySelector('#tailscale_hint_container')
        if (hintContainer) hintContainer.style.display = display
    }

    const updateUpdateBtnState = async (installed) => {
        const container = document.querySelector('#tailscale_update_container')
        if (!container) return
        if (installed === undefined) installed = await isInstall()
        container.style.display = installed ? 'inline-flex' : 'none'
    }

    const boot_on = document.createElement('button')
    boot_on.id = "tailscale_boot_on"
    boot_on.textContent = "开机自启"
    boot_on.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！")
        if (! await isInstall()) return createToast("请先安装！", 'red')

        const isBootUp = await checkIsBootUp();
        if (isBootUp) {
            await runShellWithRoot(`sed -i '/rex_Tailscale/d' /sdcard/ufi_tools_boot.sh`)
            createToast("已取消开机自启", 'green')
        } else {
            await runShellWithRoot(`grep -qxF '/data/rex_Tailscale/service.sh start' /sdcard/ufi_tools_boot.sh || echo '/data/rex_Tailscale/service.sh start' >> /sdcard/ufi_tools_boot.sh`)
            createToast("已设置开机自启", 'green')
        }
        updateBootBtnState()
    }

    const natBtn = document.createElement('button')
    natBtn.id = "tailscale_nat_btn"
    natBtn.textContent = "热点转发"
    natBtn.title = "允许连接此设备热点的手机访问Tailscale内网"
    natBtn.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！", 'red')
        if (! await isInstall()) return createToast("请先安装Tailscale！", 'red')
        if (!AP_ACCESS_ENABLED) {
            const r = await runShellWithRoot("/data/rex_Tailscale/service.sh enable_ap_access")
            createToast(r.content || "已开启热点转发", 'pink', 5000)
            AP_ACCESS_ENABLED = true
            natBtn.style.background = "var(--dark-btn-color-active)"
        } else {
            const r = await runShellWithRoot("/data/rex_Tailscale/service.sh disable_ap_access")
            createToast(r.content || "已关闭热点转发", 'pink', 5000)
            AP_ACCESS_ENABLED = false
            natBtn.style.background = ""
        }
    }

    const monitorBtn = document.createElement('button')
    monitorBtn.id = "tailscale_monitor_btn"
    monitorBtn.textContent = "IPv6网络监测"
    monitorBtn.onclick = async () => {
        if (! await checkAdvanceFunc()) return createToast("无Root权限！")

        const checkDisabled = await runShellWithRoot(`test -f /data/rex_Tailscale/flag/ipv6_monitor_disable && echo "exists" || echo "not_found"`)

        if (checkDisabled.content && checkDisabled.content.includes("exists")) {
            const r = await runShellWithRoot(`/data/rex_Tailscale/service.sh enable_ipv6_monitor`)
            createToast(r.content || "IPv6网络监测已开启", 'green')
        } else {
            const r = await runShellWithRoot(`/data/rex_Tailscale/service.sh disable_ipv6_monitor`)
            createToast(r.content || "IPv6网络监测已关闭", 'pink')
        }

        setTimeout(updateMonitorBtnState, 500)
    }

    const updateMonitorBtnState = async () => {
        const btn = document.querySelector('#tailscale_monitor_btn')
        if (!btn) return

        const checkDisabled = await runShellWithRoot(`test -f /data/rex_Tailscale/flag/ipv6_monitor_disable && echo "exists" || echo "not_found"`)

        btn.textContent = "IPv6网络监测"

        if (checkDisabled.content && checkDisabled.content.includes("exists")) {
            btn.style.background = ""
        } else {
            btn.style.background = "var(--dark-btn-color-active)"
        }
    }

    // --- DOM 注入 ---

    const wait = (sec = 100) => new Promise((resolve) => setTimeout(resolve, sec))
    let mmContainer = null
    while (!(mmContainer = document.querySelector('.functions-container'))) {
        await wait(200)
    }

    const htmlTemplate = `
            <div id="IFRAME_REX_${pluginName}" style="width: 100%; margin-top: 10px;">
                <div class="title" style="margin: 6px 0 ;">
                    <strong>Tailscale</strong>
                    <div style="display: inline-block;" id="collapse_Tailscale_btn"></div>
                </div>
                <div class="collapse" id="collapse_Tailscale" data-name="close" style="height: 0px; overflow: hidden;">
                    <div class="collapse_box">
                        <div id="Tailscale_main_content">
                            <div id="Tailscale_action_box" style="margin-bottom:10px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
                                <div id="tailscale_login_container" style="display:inline-flex;align-items:center;"></div>
                            </div>
                            <ul class="deviceList" id="tailscale_config_log_container" style="display:none;">
                                <li style="padding:10px; display: flex; flex-wrap: wrap; gap: 10px;">
                                    <div style="flex: 1 1 300px;">
                                        <div class="title">
                                            <span>配置文件</span>
                                            <div>
                                                <button style="margin:0!important;padding:2px 8px;" onclick="rexSaveTailscaleConfig()">保存并重启</button>
                                                <button style="margin:0!important;padding:2px 8px;" onclick="rexReadTailscaleConfig()">读取</button>
                                            </div>
                                        </div>
                                        <textarea id="Tailscale_config" spellcheck="false" style="margin-top:4px;font-size:12px!important;font-family:monospace;border:1px solid #444;padding:8px;width:100%;height:300px;border-radius:5px;background:#1e1e1e;color:#d4d4d4;white-space:pre;"></textarea>
                                    </div>
                                    <div style="flex: 1 1 300px;">
                                        <div class="title">
                                            <span>运行日志</span>
                                            <button style="margin:0!important;padding:2px 8px;" onclick="rexReadTailscaleLog()">刷新</button>
                                        </div>
                                        <textarea id="Tailscale_textarea" disabled spellcheck="false" style="margin-top:4px;font-size:12px!important;font-family:monospace;border:1px solid #444;padding:8px;width:100%;height:300px;border-radius:5px;background:#000;color:#0f0;white-space:pre-wrap;word-break:break-all;"></textarea>
                                    </div>
                                </li>
                            </ul>
                            <div id="tailscale_hint_container" style="display:none;font-size:12px; color:#666; padding: 5px;">
                                提示: 首次启动后需要先登录
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            `
    mmContainer.insertAdjacentHTML("afterend", htmlTemplate)

    // --- 绑定按钮与事件 ---

    const mmBox = document.querySelector('#Tailscale_action_box')
    if (mmBox) {
        mmBox.appendChild(boot_on)
        mmBox.appendChild(natBtn)
        mmBox.appendChild(monitorBtn)
        mmBox.appendChild(statusBtn)
        mmBox.appendChild(networkBtn)
        mmBox.appendChild(restartBtn)
        mmBox.appendChild(stopBtn)

        const installContainer = document.createElement('div')
        installContainer.id = 'tailscale_install_container'
        installContainer.style.cssText = 'display:inline-flex;align-items:center;'
        mmBox.appendChild(installContainer)

        const updateContainer = document.createElement('div')
        updateContainer.id = 'tailscale_update_container'
        updateContainer.style.cssText = 'display:none;align-items:center;'
        const updateBtn = document.createElement('button')
        updateBtn.id = 'tailscale_update_btn'
        updateBtn.textContent = '更新'
        updateBtn.style.cssText = 'margin:0;background:#4CAF50;'
        updateBtn.onclick = async () => {
            if (! await checkAdvanceFunc()) return createToast('无Root权限！', 'red')
            if (! await isInstall()) return createToast('请先安装！', 'red')

            createToast('正在准备更新...')
            const logId = 'tailscale_update_log_' + createRandomString(4)
            const closeId = 'tailscale_update_close_' + createRandomString(4)
            const { el, close } = createFixedToast('tailscale_update_toast', `
                <div style="pointer-events:all;width:80vw;max-width:800px">
                    <div class="title" style="margin:0">Tailscale 更新</div>
                    <pre id="${logId}" style="white-space:pre-wrap;word-break:break-all;min-width:300px;max-height:400px;overflow:auto;background:#000;color:#0f0;padding:8px;border-radius:5px;font-size:12px;margin:10px 0;">正在更新，请稍候...</pre>
                    <div style="text-align:right"><button id="${closeId}" style="font-size:12px">关闭</button></div>
                </div>
            `)
            const logEl = el && el.querySelector(`#${logId}`)
            const closeBtn2 = el && el.querySelector(`#${closeId}`)
            if (closeBtn2) closeBtn2.onclick = () => close()

            await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_update.log`)
            await runShellWithRoot(`nohup sh -c '/data/rex_Tailscale/service.sh update > /data/rex_Tailscale/tailscale_update.log 2>&1' > /dev/null 2>&1 &`, 500)

            let done = false
            const maxWait = 600
            let waited = 0
            const iv = setInterval(async () => {
                const r = await runShellWithRoot(`timeout 2s awk '{print}' /data/rex_Tailscale/tailscale_update.log 2>/dev/null || echo ""`)
                if (logEl && r.content) {
                    const converted = r.content
                        .split('\n').filter(l => !l.startsWith('UPDATE_RESULT:')).join('\n')
                        .replace(
                            /(\d{4})\/(\d{2})\/(\d{2}) (\d{2}):(\d{2}):(\d{2})/g,
                            (m, Y, M, D, h, mi, s) => new Date(Date.UTC(Y, M - 1, D, h, mi, s))
                                .toLocaleString('sv-SE').replace(/-/g, '/').replace('T', ' ')
                        )
                    logEl.textContent = converted
                    logEl.scrollTop = logEl.scrollHeight
                }
                if (r.content && r.content.includes('UPDATE_RESULT:no_update_needed')) {
                    clearInterval(iv)
                    done = true
                    createToast('已是最新版本，无需更新', 'green')
                    await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_update.log`)
                } else if (r.content && r.content.includes('UPDATE_RESULT:updated')) {
                    clearInterval(iv)
                    done = true
                    createToast('更新成功！正在自动重启...', 'green')
                    await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_update.log`)
                    await runShellWithRoot(`/data/rex_Tailscale/service.sh restart`)
                    createToast('重启完成', 'green')
                    genLog()
                    updateBootBtnState()
                } else if (r.content && r.content.includes('UPDATE_RESULT:failed')) {
                    clearInterval(iv)
                    createToast('更新失败，服务返回了非0状态，请检查日志', 'red')
                    await runShellWithRoot(`rm -f /data/rex_Tailscale/tailscale_update.log`)
                } else if (waited >= maxWait) {
                    clearInterval(iv)
                    createToast('更新超时，请检查网络或手动更新', 'red')
                }
                waited++
            }, 1000)
        }
        updateContainer.appendChild(updateBtn)
        mmBox.appendChild(updateContainer)

        const uninstallContainer = document.createElement('div')
        uninstallContainer.id = 'tailscale_uninstall_container'
        uninstallContainer.style.cssText = 'display:inline-flex;align-items:center;'
        mmBox.appendChild(uninstallContainer)
    }

    const updateUninstallBtnState = async (installed) => {
        const uninstall_container = document.querySelector('#tailscale_uninstall_container')
        if (!uninstall_container) return

        if (installed === undefined) installed = await isInstall()
        if (!installed) {
            uninstall_container.style.display = 'none'
            return
        }

        uninstall_container.style.display = 'inline-flex'
        uninstall_container.innerHTML = `<button id="tailscale_uninstall_btn" style="margin:0;background:#f44336;">卸载</button>`

        const uninstallBtn = document.querySelector('#tailscale_uninstall_btn')
        if (uninstallBtn) {
            let count = 0
            let timer = null
            uninstallBtn.onclick = async () => {
                if (! await checkAdvanceFunc()) return createToast("无Root权限！", 'red')
                if (timer) clearTimeout(timer)
                timer = setTimeout(() => { count = 0 }, 2000)
                if (count++ < 2) return createToast(count === 1 ? "再点两次确认卸载" : "再点一次确认卸载")

                createToast("正在卸载...")
                await runShellWithRoot(`/data/rex_Tailscale/service.sh stop`)
                await runShellWithRoot(`
                    rm -f /dev/log/Tailscale_LOG.txt
                    rm -rf /data/rex_Tailscale
                    sed -i '/rex_Tailscale/d' /sdcard/ufi_tools_boot.sh
                `)

                createToast("卸载成功", 'green')
                document.querySelector('#Tailscale_config').value = ""
                document.querySelector('#Tailscale_textarea').value = ""
                await updateAllStates()
            }
        }
    }

    const updateAllStates = async (forceInstalled, isFreshInstall) => {
        const installed = (forceInstalled === true || forceInstalled === false) ? forceInstalled : await isInstall()
        await updateInstallBtnState(installed)
        await updateUninstallBtnState(installed)
        await Promise.all([
            updateBootBtnState(installed),
            updateLoginBtnState(installed, isFreshInstall),
            updateServiceBtnsState(installed),
            updateMonitorBtnState(),
            updateNatBtnState(installed),
            updateUpdateBtnState(installed)
        ])
    }

    updateAllStates()

    window.rexSaveTailscaleConfig = () => {
        const Tailscale_config = document.querySelector('#Tailscale_config')
        if (!Tailscale_config) return
        createToast('正在上传配置...')
        saveConfig(Tailscale_config.value)
    }

    window.rexReadTailscaleConfig = () => {
        showConf()
        createToast('配置已重新读取')
    }

    window.rexReadTailscaleLog = () => {
        genLog()
        createToast('日志已刷新')
    }

    const startLogPolling = () => {
        stopLogPolling()
        genLog()
        Log_INTERVAL = setInterval(() => genLog(), 2000)
    }

    const stopLogPolling = () => {
        if (Log_INTERVAL) {
            clearInterval(Log_INTERVAL)
            Log_INTERVAL = null
        }
    }

    if (typeof collapseGen === 'function') {
        collapseGen("#collapse_Tailscale_btn", "#collapse_Tailscale", "#collapse_Tailscale", (newVal) => {
            if (newVal == 'open') {
                isInstall().then(installed => {
                    if (installed) {
                        showConf()
                        startLogPolling()
                    }
                })
                updateAllStates()
            } else {
                stopLogPolling()
            }
        })
    }

    if (localStorage.getItem("#collapse_Tailscale") == 'open') {
        isInstall().then(installed => {
            if (installed) {
                showConf()
                startLogPolling()
            }
        })
    }

})()
//</script>