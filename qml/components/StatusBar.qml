import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    height: 32
    color: Qt.rgba(0, 0, 0, 0.35)

    RowLayout {
        anchors {
            fill: parent
            leftMargin: 12
            rightMargin: 12
        }
        spacing: 16

        // Status indicator dot
        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: Bridge.isRunning ? "#4caf50" : "#f44336"

            SequentialAnimation on opacity {
                running: Bridge.isRunning
                loops: Animation.Infinite
                NumberAnimation { to: 0.3; duration: 800; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 800; easing.type: Easing.InOutSine }
            }
        }

        // Status text
        Label {
            text: Bridge.status
            font.pixelSize: 12
            color: Bridge.isRunning ? "#b2dfdb" : "#ef9a9a"
            Layout.fillWidth: false
        }

        // Separator
        Rectangle { width: 1; height: 16; color: Qt.rgba(1,1,1,0.15) }

        // Active objects
        Label {
            text: "Active: " + Bridge.activeCount
            font.pixelSize: 12
            color: "#90a4ae"
        }

        Rectangle { width: 1; height: 16; color: Qt.rgba(1,1,1,0.15) }

        // Messages per second
        Label {
            text: Bridge.msgPerSec.toFixed(0) + " msg/s"
            font.pixelSize: 12
            color: "#90a4ae"
        }

        Rectangle { width: 1; height: 16; color: Qt.rgba(1,1,1,0.15) }

        // Error count
        Label {
            visible: Bridge.errorCount > 0
            text: "⚠ " + Bridge.errorCount + " errors"
            font.pixelSize: 12
            color: "#ffb74d"
        }

        Item { Layout.fillWidth: true }

        // Version label
        Label {
            text: "TUIO Bridge 1.0"
            font.pixelSize: 11
            color: Qt.rgba(1,1,1,0.3)
        }
    }
}
