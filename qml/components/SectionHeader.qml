import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls

Rectangle {
    property alias text: label.text
    width: parent ? parent.width : 200
    height: 32
    color: "#1a2228"

    Label {
        id: label
        anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
        font.pixelSize: 11
        font.weight: Font.Medium
        font.letterSpacing: 1.2
        color: "#4db6ac"
        text: ""
    }
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 1
        color: Qt.rgba(1, 1, 1, 0.06)
    }
}
