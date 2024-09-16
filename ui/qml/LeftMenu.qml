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
            Button {
                text: "New"
                onClicked: { 
                    hl_model.new_article()
                }
            }
            Button {
                text: "Open"
                onClicked: { 
                    hl_model.open_article()
                }
            }
        }
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
            height: 240
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
        Button {
            text: "Translate"
            enabled: !cbTranslate.checked
            onClicked: { 
                root.backend.translate(menu.hl)
            }
        }
        // TODO: Translate tags
        Setting { 
            name: "Tags"          
            desc: root.backend? root.backend.get_used_tags(menu.hl) : "Loading"
            TextField {
                id: tagsEdit
                Layout.fillWidth: true
                text: hl_model ? hl_model.p_tags : "..."
                onEditingFinished: {
                    hl_model.set_tags(text)
                }
            }
        }
        Setting { 
            name: "Links"
            
            GridLayout {
                columns: 2
                Label { text: "Medium" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_medium : "..."
                    onEditingFinished: {
                        hl_model.set_link("Medium", text)
                    }
                }
                Label { text: "X/Twitter" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_x : "..."
                    onEditingFinished: {
                        hl_model.set_link("X/Twitter", text)
                    }
                }
                Label { text: "Typeshare" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_typeshare : "..."
                    onEditingFinished: {
                        hl_model.set_link("Typeshare", text)
                    }
                }
                Label { text: "LinkedIn" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_linkedin : "..."
                    onEditingFinished: {
                        hl_model.set_link("LinkedIn", text)
                    }
                }
                Label { text: "Facebook" }
                TextField {
                    Layout.fillWidth: true     
                    text: hl_model ? hl_model.p_link_facebook : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link("Facebook", text)
                    }
                }
            }
        }
        Setting { 
            name: "Image"
            
            //desc: root.backend? hl_model.p_excerpt_img : "Loading"
            //Image{
            //    source : hl_model.excerpt_img_local()
            //}
            TextField {
                id: imageEdit
                Layout.fillWidth: true
                text: hl_model ? hl_model.p_excerpt_img : "..."
                onEditingFinished: {
                    hl_model.set_excerpt_img(text)
                }
            }
        }

        TextArea {
            text: hl_model ? hl_model.p_content_md : "..."
            wrapMode: Text.WrapAnywhere
            readOnly: true
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