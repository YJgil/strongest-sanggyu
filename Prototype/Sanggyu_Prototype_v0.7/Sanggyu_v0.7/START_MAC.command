#!/bin/sh
# Finder/Terminal may use different PATHs. Select a Python with modern Tk.
cd "$(dirname "$0")" || exit 1

launch_game() {
    launcher_python=$1
    if ! "$launcher_python" -c 'import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 10) and tkinter.TkVersion >= 8.6 else 1)' >/dev/null 2>&1; then
        return 1
    fi
    launcher_log_dir="$HOME/Library/Logs/StrongestSanggyu"
    if ! mkdir -p "$launcher_log_dir"; then
        echo "실행 기록 폴더를 만들 수 없습니다: $launcher_log_dir"
        return 1
    fi
    launcher_log="$launcher_log_dir/launch.log"
    echo "상규 게임 실행 중: $launcher_python"
    echo "실행 기록: $launcher_log"
    "$launcher_python" main.pyw >>"$launcher_log" 2>&1
    launcher_status=$?
    if [ "$launcher_status" -ne 0 ]; then
        echo "게임 실행 중 오류가 발생했습니다 (종료 코드 $launcher_status)."
        tail -n 40 "$launcher_log"
        printf '\n이 창의 오류 문구를 알려 주세요. Enter를 누르면 닫힙니다. '
        read -r launcher_answer
    fi
    exit "$launcher_status"
}

for launcher_candidate in python3 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
    /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    launch_game "$launcher_candidate"
done

echo "게임 실행에는 Python 3.10 이상과 Tk 8.6 이상이 필요합니다."
echo "설치된 Python에서 tkinter를 찾지 못했습니다."
printf '이 문구를 알려 주세요. Enter를 누르면 닫힙니다. '
read -r launcher_answer
exit 1
