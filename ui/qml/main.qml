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
                Item {
                    Layout.fillWidth: true
                }
            }            
        }
        RowLayout {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Rectangle {
                width: 120
                Layout.fillHeight: true
                clip: true
                ColumnLayout {
                    CheckBox { text: "1. Choose content (Asana?)" }
                    CheckBox { text: "2. Find a title"; id: cbTitle }
                    CheckBox { text: "3. Write the content"; id: cbContent  }
                    CheckBox { text: "4. Start an image generation (or find it)" }
                    CheckBox { text: "5. Proofread" }
                    CheckBox { text: "6. Translate (And proofread\nin french if the translation is bad)"; id: cbTranslate }
                    CheckBox { text: "7. Find/write tags" }
                    
                    Label { text: "<a href='https://medium.com/new-story'>Medium</a>"; onLinkActivated: Qt.openUrlExternally(link) }
                    CheckBox { text: "8.1. Publish to Medium" }
                    CheckBox { text: "8.2. Paste the link MEDIUM here" }
                    CheckBox { text: "8.3. Share to X (EVENTUALLY/IF APPLICABLE: Adapt it for X)" }
                    CheckBox { text: "8.3.2. COPY LINK of X here" }
                    CheckBox { text: "8.4. Share in facebook if relevant?" }
                    CheckBox { text: "8.4.2. COPY LINK of Facebook here" }
                    
                    Label { text: "<a href='https://typeshare.co/martingamsby'>Typeshare</a>"; onLinkActivated: Qt.openUrlExternally(link) }
                    CheckBox { text: "9.1. Publish to Typeshare" }
                    CheckBox { text: "9.2. COPY LINK of Typeshare here" }
                    CheckBox { text: "9.3. COPY IMAGE URL of Typeshare here" }
                    
                    CheckBox { text: "10. GITHUB: Upload the article!" }
                }
            }
            ArticleMeta {
                Layout.fillWidth: false
                width: 320
                clip: true
                hl: "fr"
            }
            ArticleContent {
                Layout.fillWidth: false
                width: 520
                clip: true
                hl: "fr"
            }
            ArticleContent {
                Layout.fillWidth: false
                width: 520
                clip: true
                hl: "en"
            }      
            ArticleMeta {
                Layout.fillWidth: false
                width: 320
                clip: true
                hl: "en"
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