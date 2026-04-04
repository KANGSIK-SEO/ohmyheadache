set ver to ((word 1 of (do shell script "sw_vers -productVersion")) as integer)

if ver >= 13 then
    tell application "System Settings"
        activate
        delay 0.8
        reveal pane id "com.apple.preference.keyboard"
        delay 1.5
    end tell

    tell application "System Events"
        tell process "System Settings"
            set frontmost to true
            delay 0.5
            set waited to 0
            repeat until (exists window "Keyboard") or waited > 10
                delay 0.5
                set waited to waited + 0.5
            end repeat

            if not (exists window "Keyboard") then
                display dialog "⚠️ Keyboard 창을 열지 못했습니다." buttons {"확인"} default button "확인" with icon caution
                return
            end if

            tell window "Keyboard"
                set editFound to false
                repeat with grpIdx from 1 to 5
                    repeat with n in {"Edit…", "Edit...", "편집…", "편집..."}
                        try
                            click button (n as string) of group grpIdx
                            set editFound to true
                            exit repeat
                        end try
                    end repeat
                    if editFound then exit repeat
                end repeat

                if not editFound then
                    try
                        repeat with btn in (every button of window "Keyboard")
                            set bName to name of btn
                            if bName contains "Edit" or bName contains "편집" then
                                click btn
                                set editFound to true
                                exit repeat
                            end if
                        end repeat
                    end try
                end if

                if not editFound then
                    display dialog "⚠️ Edit 버튼을 찾지 못했습니다." buttons {"확인"} default button "확인" with icon caution
                    return
                end if

                delay 1.0

                set capsFound to false
                set capsNames to {"Use Caps Lock key to switch to and from ABC", "Use Caps Lock key to switch to and from", "Caps Lock 키로 전환", "Caps Lock 키를 사용하여 전환", "Caps Lock"}

                repeat with n in capsNames
                    try
                        set cb to checkbox (n as string) of sheet 1
                        if value of cb is 0 then
                            click cb
                        else
                            display dialog "ℹ️ 이미 활성화되어 있습니다." buttons {"확인"} default button "확인"
                        end if
                        set capsFound to true
                        exit repeat
                    end try
                end repeat

                if not capsFound then
                    try
                        repeat with cb in (every checkbox of sheet 1)
                            if name of cb contains "Caps Lock" then
                                if value of cb is 0 then click cb
                                set capsFound to true
                                exit repeat
                            end if
                        end repeat
                    end try
                end if

                if not capsFound then
                    display dialog "⚠️ 체크박스를 찾지 못했습니다." buttons {"확인"} default button "확인" with icon caution
                    return
                end if
            end tell
        end tell
    end tell

else
    tell application "System Preferences"
        activate
        delay 0.8
        set current pane to pane "com.apple.preference.keyboard"
        delay 1.2
    end tell

    tell application "System Events"
        tell process "System Preferences"
            tell window "Keyboard"
                set tabFound to false
                repeat with tabName in {"Input Sources", "입력 소스"}
                    try
                        click radio button (tabName as string) of tab group 1
                        set tabFound to true
                        exit repeat
                    end try
                end repeat
                if not tabFound then
                    display dialog "⚠️ Input Sources 탭을 찾지 못했습니다." buttons {"확인"} default button "확인" with icon caution
                    return
                end if
                delay 0.5

                set capsNames to {"Use Caps Lock key to switch to and from ABC", "Use Caps Lock key to switch to and from", "Caps Lock 키로 전환", "Caps Lock 키를 사용하여 전환"}
                set capsFound to false

                repeat with n in capsNames
                    try
                        set cb to checkbox (n as string) of scroll area 1 of tab group 1
                        if value of cb is 0 then click cb
                        set capsFound to true
                        exit repeat
                    end try
                    try
                        set cb to checkbox (n as string) of tab group 1
                        if value of cb is 0 then click cb
                        set capsFound to true
                        exit repeat
                    end try
                end repeat

                if not capsFound then
                    display dialog "⚠️ 체크박스를 찾지 못했습니다." buttons {"확인"} default button "확인" with icon caution
                    return
                end if
            end tell
        end tell
    end tell
end if

display dialog "✅ 완료! Caps Lock으로 한/영 전환이 가능합니다." buttons {"완료"} default button "완료"
