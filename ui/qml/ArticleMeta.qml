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
            
        GridLayout {
            columns: 2
            Button {
                text: "New"
                onClicked: { 
                    hl_model.new_article()
                }
            }
            Button {
                text: "Translate"
                //enabled: !cbTranslate.checked
                onClicked: { 
                    root.backend.translate(menu.hl)
                }
            }
            Button {
                text: "Open"
                onClicked: { 
                    hl_model.open_article()
                }
            }
            Button {
                text: "Make V2"
                onClicked: { 
                    hl_model.new_both_articles(true)
                }
                Layout.columnSpan: 1
            }
            Button {
                text: "Open Prev"
                onClicked: { 
                    hl_model.open_prev_article()
                }
            }
            Button {
                text: "Open Next"
                onClicked: { 
                    hl_model.open_next_article()
                }
            }
            Button {
                text: "New both articles"
                onClicked: { 
                    hl_model.new_both_articles(false)
                }
                Layout.columnSpan: 1
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
            name: "Links"
            
            GridLayout {
                columns: 2
                //Label { text: "<a href='https://medium.com/new-story'>Medium</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) }; visible: menu.hl == "fr" }
                Label { text: "Medium"; visible: menu.hl == "fr" }
                TextField {
                    Layout.fillWidth: true; visible: menu.hl == "fr"
                    text: hl_model ? hl_model.p_link_medium : "..."
                    onEditingFinished: {
                        hl_model.set_link("Medium", text)
                    }
                }
                //Label { text: "<a href='https://typeshare.co/martingamsby'>Typeshare</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) }; visible: menu.hl == "en" }
                Label { text: "Typeshare"; visible: menu.hl == "en" }
                TextField {
                    Layout.fillWidth: true; visible: menu.hl == "en"
                    text: hl_model ? hl_model.p_link_typeshare : "..."
                    onEditingFinished: {
                        hl_model.set_link("Typeshare", text)
                    }
                }
                Label { text: "<a href='https://x.com/'>X/Twitter</a>"; onLinkActivated: function(link) { hl_model.post_x() } }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_x : "..."
                    onEditingFinished: {
                        hl_model.set_link("X/Twitter", text)
                    }
                }
                //Label { text: "<a href='https://linkedin.com/'>LinkedIn</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) }; visible: menu.hl == "en" }
                Label { text: "LinkedIn"; visible: menu.hl == "en" }
                TextField {
                    Layout.fillWidth: true; visible: menu.hl == "en"
                    text: hl_model ? hl_model.p_link_linkedin : "..."
                    onEditingFinished: {
                        hl_model.set_link("LinkedIn", text)
                    }
                }
                //Label { text: "<a href='https://facebook.com/'>Facebook</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) }; visible: menu.hl == "fr"     }
                Label { text: "Facebook"; visible: menu.hl == "fr" }
                TextField {
                    Layout.fillWidth: true ; visible: menu.hl == "fr"    
                    text: hl_model ? hl_model.p_link_facebook : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link("Facebook", text)
                    }
                }
                Label { text: "<a href='https://bsky.app/profile/martin-gamsby.bsky.social'>Bluesky</a>"; onLinkActivated: function(link) { hl_model.post_bluesky() } }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_bluesky : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link("Bluesky", text)
                    }
                }
                //Label { text: "<a href='https://studio.youtube.com'>YouTube</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
                Label { text: "YouTube" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_YouTube : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link("YouTube", text)
                    }
                }
                //Label { text: "<a href='https://studio.youtube.com'>YouTube Shorts</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
                Label { text: "YouTube Shorts" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_YouTubeShorts : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link("YouTube Shorts", text)
                    }
                }
                Label { text: "Source" }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_source : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link("Source", text)
                    }
                }
                Label { text: hl_model ? hl_model.get_based_on_text() : "..." } // TODO: real translate with Qt...
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_link_based_on : "..."                                   
                    onEditingFinished: {
                        hl_model.set_link(basedOnTxt.text, text)
                    }
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
        Button {
            text: "Generate Tags"
            onClicked: { 
                hl_model.generate_tags()
            }
        }

        Label {
                Layout.fillHeight: true            
        }
    }
}