import QtQuick
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
    id: root
    moduleName: "daemon0.screensaver-studio"
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    BarIconButton {
        id: button; anchors.fill: parent; bar: root.bar
        text: "󱄄"; tooltipText: "Screensaver"
        onPressed: { if (!menu.running) menu.running = true; }
    }
    Process { id: menu; command: ["omarchy-menu-screensaver"] }
}
