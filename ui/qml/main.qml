import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls
import "."

import QtQuick.Controls.Material 2.12

Window {
    // Just some window configuration
    id: root
    visible: true
    width: 1024
    height: 768
    
    title: qsTr("Writer Helper")
    
    color: "lightgray"
    Material.accent: Material.Teal

    
    property string debugString: "Debug string from backend"
    property QtObject backend
    
    
    ColumnLayout
    {
        anchors.fill: parent
        Rectangle {
            color: "#3b513c"
            implicitHeight: lblTitle.height + 12*2//margins6*2
            implicitWidth: root.width
            RowLayout {
                anchors.fill: parent
                //Layout.margins: 6
                anchors.margins: 6 
                Label {
                    id: lblTitle
                    text: "Writer Helper"
                    font.pointSize: 20
                    Layout.leftMargin: 12
                    color: "white"
                }
                Item {
                    Layout.fillWidth: true
                }
            }            
        }
        RowLayout {
            Layout.fillWidth: true
            LeftMenu {
                Layout.fillWidth: false
                width: 300
                clip: true
            }
            
            Rectangle {
                    Layout.fillHeight: true
                    Layout.fillWidth: true

                Rectangle {
                    anchors.fill: parent
                    color: "transparent"


                    Text {
                        anchors {
                            bottom: parent.bottom
                            bottomMargin: 12
                            left: parent.left
                            leftMargin: 12
                        }
                        text: debugString
                        wrapMode: Text.WrapAnywhere
                    }

                }

            }

            Connections {
                target: backend

                function onUpdated(msg) {
                    debugString = msg;
                }
            }
            
        }
        Label {
            id: bottomPart
            //text: new Date().toLocaleString(Qt.locale("fr_CA"),Locale.ShortFormat)
            text: new Date().toLocaleString(Qt.locale("fr_CA"),Locale.LongFormat)
        }
        Timer {
            id: timer
            interval: 1000
            running: true
            repeat: true
            //onTriggered: bottomPart.text = new Date().toLocaleString(Qt.locale("fr_CA"),Locale.ShortFormat)
            onTriggered: bottomPart.text = new Date().toLocaleString(Qt.locale("fr_CA"),Locale.LongFormat)
        }
    }
}