def call_llm(history):
    last = history[-1]["content"]

    # explore first
    if "README" in last or "home" in last:
        return "ls /etc/app"

    if "No such file" in last:
        return "ls /etc/app"

    if "conf.bak" in last:
        return "mv /etc/app/conf.bak /etc/app/conf"

    if "moved" in last:
        return "systemctl restart app"

    return "ls"
