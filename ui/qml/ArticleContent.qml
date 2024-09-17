import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls

import QtQuick.Controls.Material 2.12

Flickable {
    id: menu
    Layout.fillWidth: true
    Layout.fillHeight: true
    
    boundsBehavior: Flickable.StopAtBounds
    contentHeight: 2000// I don't have time for this shit columnLayout.height
    
    required property string hl
    
    property QtObject hl_model: root.backend ? root.backend.article(hl) : null
    
    
    ColumnLayout
    {
        id: columnLayout
        anchors.fill: parent
        anchors.margins: 0
            
        RowLayout {
            Label {
                text: menu.hl + " Article"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 15
                padding: 5
            }
        
        //Setting { 
        //    name: "Mini (vs Court)"
            
            CheckBox {
                checked: false
                text: "Mini (vs Court)"
                                    
                onToggled: {
                    hl_model.set_mini(checked)
                }            
            }
        //}
        
            //Setting { 
            //    name: "Posts path"
            //    Layout.fillWidth: true
                
                TextField {
                    id: postsPathEdit
                    text: hl_model ? hl_model.p_posts_folder : "..."
                           
                    onEditingFinished: {
                        hl_model.set_posts_folder(text)
                    }
                }
                TextField {
                    text: hl_model ? hl_model.p_website_url : "..."                           
                    onEditingFinished: {
                        hl_model.set_website_url(text)
                    }
                }
            //}
            
        }
        Setting { 
            //name: "Title"
            desc: hl_model ? hl_model.p_slug : "..."
            enabled: !cbTitle.checked
            
            ColumnLayout {
                TextField {
                    id: titleEdit
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_title : "..."
                                        
                    onEditingFinished: {
                        hl_model.set_title(text)
                    }
                }
                RowLayout {
                    CheckBox {   
                        id: cbDate
                        checked: false
                        text: "Date override"
                    }
                    TextField {
                        Layout.fillWidth: true
                        enabled: cbDate.checked//TODO: visible instead of enabled
                        text: hl_model ? hl_model.p_date : "..."
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 320
            color: cbContent.checked ? "#aaa" : "white"
            Flickable {
              id: flickable
              flickableDirection: Flickable.VerticalFlick
              anchors.fill: parent

              TextArea.flickable: TextArea {
                  id: contentEdit
                  //textFormat: Qt.RichText
                  wrapMode: TextArea.Wrap
                  //focus: true
                  selectByMouse: true
                  persistentSelection: true
                  leftPadding: 6
                  rightPadding: 6
                  topPadding: 6
                  bottomPadding: 6
                  //background: null
                  
                  text: hl_model ? hl_model.p_content : "..."
            
                  onEditingFinished: {
                      hl_model.set_content(text)
                  }
                  //MouseArea {
                  //    acceptedButtons: Qt.RightButton
                  //    anchors.fill: parent
                  //    onClicked: contextMenu.open()
                  //}
              }

              ScrollBar.vertical: ScrollBar {}
            }
        }        
        
        Rectangle {
            width: parent.width
            height: 320
            color: "#333"
            Flickable {
              flickableDirection: Flickable.VerticalFlick
              anchors.fill: parent

              TextArea.flickable: TextArea {
                  color: "#aaa"
                  wrapMode: TextArea.Wrap
                  readOnly: true
                  selectByMouse: true
                  persistentSelection: true
                  textFormat: TextEdit.RichText
                  leftPadding: 6
                  rightPadding: 6
                  topPadding: 6
                  bottomPadding: 6
                  
                  text: hl_model ? hl_model.p_content_md_rich : "..."
              }
              ScrollBar.vertical: ScrollBar {}
            }
        }
        
        Flickable {
          width: parent.width
          height: 320
          flickableDirection: Flickable.VerticalFlick

          TextArea.flickable: TextArea {
              wrapMode: TextArea.Wrap
              readOnly: true
              
              text: hl_model ? hl_model.p_content_md : "..."
          }
          ScrollBar.vertical: ScrollBar {}
        }

        Label {
                Layout.fillHeight: true            
        }
        Timer {
            id: timer
            interval: 2000 // 3000
            running: true
            repeat: true
            onTriggered: {
                if( titleEdit.activeFocus )
                    hl_model.set_title(titleEdit.text)
                
                if( contentEdit.activeFocus )
                    hl_model.set_content(contentEdit.text)
            }
        }
    }
}