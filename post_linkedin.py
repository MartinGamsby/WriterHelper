
        # https://github.com/FrancescoSaverioZuppichini/linkedin_python (Well it doesn`t work)
        # To generate a new token: https://www.linkedin.com/developers/tools/oauth
        
        # https://dotslashdata.com/linkedin-rest-api-python/
        
        image_path = os.path.join(os.path.realpath(__file__),"richTextArea_en1.png")
        
        
        ###TO ADD IN A CONFIG FILE OR WHATEVER
        ##os.environ["LINKEDIN_TOKEN"] = ""
        ##
        ##
        ##
        ##user = User()
        ##res = user.create_post(
        ##    self.title,
        ##    images=[
        ##        (image_path, self.title)
        ##    ],
        ##)
        ##print(res)
        #
        #######URL:
        client_id = "REDACTED"
        ######
        ######
        ######base_url = "https://www.linkedin.com/oauth/v2/authorization"
        redirect_uri = "https://www.linkedin.com/developers/tools/oauth/redirect"#"https://thedatascholar.com/auth/linkedin/callback&quot;
        ######scope = "w_member_social,profile,email,openid"#"w_member_social,r_liteprofile"
        ######
        ######url = f"{base_url}?response_type=code&client_id={client_id}&state=random&redirect_uri={redirect_uri}&scope={scope}"
        ######print(url)
        ######return url: "https://www.linkedin.com/developers/tools/oauth/redirect?code=REDACTED_ROTATE_THIS&state=random"
        
        #=#=#=#=#=#=##
        #=#=#=#=#=#=#url_access_token = "https://www.linkedin.com/oauth/v2/accessToken"
        #=#=#=#=#=#=#auth_code = "REDACTED_ROTATE_THIS"
        #=#=#=#=#=#=#client_secret = "REDACTED_ROTATE_THIS"
        #=#=#=#=#=#=#
        #=#=#=#=#=#=#
        #=#=#=#=#=#=#payload = {
        #=#=#=#=#=#=#    'grant_type' : 'authorization_code',
        #=#=#=#=#=#=#    'code' : auth_code,
        #=#=#=#=#=#=#    'redirect_uri' : redirect_uri,
        #=#=#=#=#=#=#    'client_id' : client_id,
        #=#=#=#=#=#=#    'client_secret' : client_secret
        #=#=#=#=#=#=#}
        #=#=#=#=#=#=#
        #=#=#=#=#=#=#response = requests.post(url=url_access_token, params=payload)
        #=#=#=#=#=#=#response_json = response.json()
        #=#=#=#=#=#=#print(response_json)
        #=#=#=#=#=#=## Extract the access_token from the response_json
        #=#=#=#=#=#=#access_token = response_json['access_token']
        
        ###
        
        #-#-#-#-#-## Get LinkedIn user ID
        #-#-#-#-#-#url = "https://api.linkedin.com/v2/me"
        #-#-#-#-#-#
        #-#-#-#-#-#header = {
        #-#-#-#-#-#    'Authorization' : f'Bearer {access_token}'
        #-#-#-#-#-#}
        #-#-#-#-#-#
        #-#-#-#-#-#response = requests.get(url=url, headers=header)
        #-#-#-#-#-#response_json_li_person = response.json()
        #-#-#-#-#-#
        #-#-#-#-#-#print(response_json_li_person)
        #-#-#-#-#-#person_id = response_json_li_person['id']
        person_id = "martingamsby"
        
        ############### 
        url = "https://api.linkedin.com/v2/shares"
        
        ###################manual:access_token="REDACTED_ROTATE_THIS"
        access_token = "REDACTED_ROTATE_THIS"
        
        headers = {
            'Authorization' : f'Bearer {access_token}',
            'Content-Type' : 'application/json'
        }
        
        payload = {
            "content": {
                "contentEntities": [
                    {
                        "entityLocation": self.get_website_url() + self.get_slug(),#"https://www.redhat.com/en/topics/api/what-is-a-rest-api",
                        "thumbnails": [
                            {
                                "url": image_path  #"resolvedUrl": "https://images.pexels.com/photos/2115217/pexels-photo-2115217.jpeg"
                            }
                        ]
                    }
                ],
                "title": self.title
            },
            'distribution': {
                'linkedInDistributionTarget': {}
            },
            'owner': f'urn:li:person:{person_id}'#,
            #'text': {
            #    'text': f'Learn more about REST APIs in details.  \n#restapi #api'
            #}
        }

        response = requests.post(url=url, headers=headers, json = payload)

        print(response.json())