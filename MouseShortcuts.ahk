; Mouse Shortcut — AutoHotkey v2
; Double right-click = Win+Tab (Task View)
; Single right-click = normal context menu

#Requires AutoHotkey v2.0
#SingleInstance Force

RButton::{
    KeyWait "RButton"

    if KeyWait("RButton", "D T0.3") {
        KeyWait "RButton"
        Send "#tab"
    } else {
        Click "Right"
    }
}