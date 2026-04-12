import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls

/*
  DoubleSpinBox — a SpinBox that works with floating-point values.
  Internally stores value * 1000 as integers (3 decimal places of precision).

  Usage:
    DoubleSpinBox {
        value: 1.0
        from: 0.0
        to: 10.0
        stepSize: 0.1
        onValueModified: doSomething(value)
    }
*/
SpinBox {
    id: control

    property real realFrom:     0.0
    property real realTo:       10.0
    property real realStep:     0.1
    property real realValue:    1.0

    readonly property int _scale: 1000

    from:     Math.round(realFrom  * _scale)
    to:       Math.round(realTo    * _scale)
    stepSize: Math.round(realStep  * _scale)
    value:    Math.round(realValue * _scale)

    editable: true
    font.pixelSize: 11
    implicitHeight: 32
    Component.onCompleted: {
        if (up.indicator)   up.indicator.implicitWidth   = 24
        if (down.indicator) down.indicator.implicitWidth = 24
    }

    validator: DoubleValidator {
        bottom: control.realFrom
        top:    control.realTo
        decimals: 3
        notation: DoubleValidator.StandardNotation
    }

    textFromValue: function(v, locale) {
        return (v / control._scale).toFixed(3)
    }

    valueFromText: function(text, locale) {
        return Math.round(parseFloat(text) * control._scale)
    }

    onValueModified: {
        control.realValue = control.value / control._scale
    }
}
