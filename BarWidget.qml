import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

Item {
  id: root
  implicitWidth: 32
  implicitHeight: 32

  Rectangle {
    anchors.centerIn: parent
    width: 28
    height: 28
    radius: 6
    color: mouseArea.containsMouse ? Qt.rgba(1, 1, 1, 0.15) : "transparent"

    Text {
      anchors.centerIn: parent
      text: "󱄄"
      font.pixelSize: 16
      color: "#ffffff"
    }

    MouseArea {
      id: mouseArea
      anchors.fill: parent
      hoverEnabled: true
      onClicked: function() {
        screensaverMenuProc.running = true
      }
    }
  }

  Process {
    id: screensaverMenuProc
    command: ["omarchy-menu-screensaver"]
  }
}
