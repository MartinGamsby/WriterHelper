import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls
import "."

import QtQuick.Controls.Material 2.12

Window {
    // Just some window configuration
    id: root
    visible: true
    width: 1800
    height: 1024
    
    title: qsTr("Writer Helper")
    
    color: "lightgray"
    Material.accent: Material.Teal
    
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
                CheckBox {
                    id: cbFR
                    text: "<font color=\"white\">French</font>"
                    checked: true
                }
                CheckBox {
                    id: cbEN
                    text: "<font color=\"white\">English</font>"
                    checked: true
                }
                Item {
                    Layout.fillWidth: true
                }
            }            
        }
        RowLayout {
            Layout.fillHeight: true
            Layout.fillWidth: true
            CheckList {
                width: 160
                Layout.fillHeight: true            
            }
            Row {
                Layout.fillHeight: true
                Layout.fillWidth: true
                spacing: 3
                
                component Separator: Rectangle {
                    width: 1
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    color: "#3b513c"
                }
                
                Separator{}
                ArticleMeta {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: cbEN.checked ? 220 : 320
                    clip: true
                    
                    visible: cbFR.checked
                    
                    hl: "fr"
                }
                Separator{}
                ArticleContent {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: cbEN.checked ? 640 : 1024            
                    clip: true
                    
                    visible: cbFR.checked
                    
                    hl: "fr"
                }
                Separator{visible: cbFR.checked && cbEN.checked }
                ArticleContent {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: cbFR.checked ? 640 : 1024
                    clip: true
                    
                    visible: cbEN.checked
                    
                    hl: "en"
                }    
                Separator{}  
                ArticleMeta {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: cbFR.checked ? 220 : 320
                    clip: true
                    
                    visible: cbEN.checked
                    
                    hl: "en"
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