import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: root
    title: "TUIO Bridge"
    width: 1920
    height: 1080
    minimumWidth: 900
    minimumHeight: 600
    visible: true

    Material.theme: Material.Dark
    Material.accent: Material.Teal
    Material.primary: Material.BlueGrey

    // -----------------------------------------------------------------------
    // Main layout: three resizable panels
    // -----------------------------------------------------------------------
    SplitView {
        id: mainSplit
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            bottom: statusBar.top
        }
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 4
            color: SplitHandle.hovered || SplitHandle.pressed
                   ? Material.accentColor
                   : Qt.rgba(1, 1, 1, 0.08)
        }

        ConfigPanel {
            id: configPanel
            SplitView.preferredWidth: 480
            SplitView.minimumWidth: 380
        }

        MonitorPanel {
            id: monitorPanel
            SplitView.fillWidth: true
            SplitView.minimumWidth: 300
        }

        LogPanel {
            id: logPanel
            SplitView.preferredWidth: 360
            SplitView.minimumWidth: 240
        }
    }

    // -----------------------------------------------------------------------
    // Status bar
    // -----------------------------------------------------------------------
    StatusBar {
        id: statusBar
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
    }

    // -----------------------------------------------------------------------
    // Keyboard shortcut: Ctrl+S = save config
    // -----------------------------------------------------------------------
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: Bridge.saveConfig()
    }
}
