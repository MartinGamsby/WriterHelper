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
            Button {
                text: "Translate"
                enabled: !cbTranslate.checked
                onClicked: { 
                    root.backend.translate(menu.hl)
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

        Label {
                Layout.fillHeight: true            
        }
    }
}