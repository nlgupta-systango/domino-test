from domino.base_piece import BasePiece
from .models import InputModel, OutputModel
from typing import List
import requests
import json

class InstagramGetMediaPiece(BasePiece):

    host_domain = 'https://graph.facebook.com/'
    graph_api_version = 'v15.0'
    endpoint_base_path = f'{host_domain}{graph_api_version}/'

    @staticmethod
    def make_api_call(url:str, endpoint_query_params:str, request_method='get'):
        if request_method == 'get':
            try:
                data = requests.get(url=url, params=endpoint_query_params)
            except Exception as e:
                print(e)
        elif request_method == 'post':
            try:
                data = requests.post(url=url, params=endpoint_query_params)
            except Exception as e:
                print(e)
        else:
            raise ValueError('request_method must be: "get" or "post"')

        response = {}
        response['url'] = url
        response['endpoint_query_params'] = endpoint_query_params
        response['json_content'] = json.loads(data.content)
    
        return response

    @classmethod
    def get_long_lived_access_token(cls, app_id:str, app_secret:str, access_token:str):
        url = cls.endpoint_base_path + 'oauth/access_token'
        endpoint_query_params = f'grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={access_token}'
        response = cls.make_api_call(url=url, endpoint_query_params=endpoint_query_params, request_method='get')
        return response['json_content']['access_token']

    @classmethod
    def get_page_id(cls, access_token:str, facebook_page_name:str):
        url = cls.endpoint_base_path + 'me/accounts'
        endpoint_query_params = f'access_token={access_token}'

        response = cls.make_api_call(url=url, endpoint_query_params=endpoint_query_params, request_method='get')

        for i in response['json_content']['data']:
            if i['name'] == facebook_page_name:
                return i['id']
        
        raise Exception(f'Page "{facebook_page_name}" not found')
    
    @classmethod
    def get_instagram_business_account(cls, access_token:str, page_id:str):
        url = f'{cls.endpoint_base_path}{page_id}'
        endpoint_query_params = f'access_token={access_token}&fields=instagram_business_account'

        response = cls.make_api_call(url=url, endpoint_query_params=endpoint_query_params, request_method='get')

        return response['json_content']['instagram_business_account']['id']

    @classmethod
    def get_media_list(cls, access_token:str, instagram_business_account:str, media_fields: List):
        url = f'{cls.endpoint_base_path}{instagram_business_account}/media'
        fields = [field.value for field in media_fields]
        str_fields = ','.join(fields)
        endpoint_query_params = f'access_token={access_token}&fields={str_fields}'

        response = cls.make_api_call(url=url, endpoint_query_params=endpoint_query_params, request_method='get')

        return response['json_content']['data']

    def piece_function(self, input_model: InputModel):
        
        app_id = self.secrets.APP_ID
        app_secret = self.secrets.APP_SECRET
        access_token = self.secrets.ACCESS_TOKEN

        long_lived_access_token = self.secrets.ACCESS_TOKEN = self.get_long_lived_access_token(app_id=app_id, app_secret=app_secret, access_token=access_token)

        page_id = self.get_page_id(access_token=long_lived_access_token, facebook_page_name=input_model.facebook_page_name)

        instagram_business_account = self.get_instagram_business_account(access_token=long_lived_access_token, page_id=page_id)

        media_list = self.get_media_list(access_token=long_lived_access_token, instagram_business_account=instagram_business_account, media_fields=input_model.instagram_media_fields)

        # Display result in the Domino GUI
        media_string = ""
        for i in media_list:
            media_string += '  \n'.join([f"{key}: {str(value)}" for key, value in i.items()])
            media_string += '  \n\n'
        self.format_display_result(input_model, media_string)

        if input_model.output_type == "string":
            return OutputModel(
                media_string=media_string
            )
    
        if input_model.output_type == "python_list":
            return OutputModel(
                media_list=media_list
            )

        if input_model.output_type == "json_string":
            json_string = "\n".join(json.dumps(i, indent=4) for i in media_list)
            return OutputModel(
                media_json_string=json_string
            )

    def format_display_result(self, input_model: InputModel, media_string: str):
        # json_media_list = '\n\n'.join(json.dumps(i, indent=4) for i in media_list)
        md_text = f"""
## Media list:

{media_string}

## Args
**facebook page name**: {input_model.facebook_page_name}

"""
        file_path = f"{self.results_path}/display_result.md"
        with open(file_path, "w") as f:
            f.write(md_text)
        self.display_result = {
            "file_type": "md",
            "file_path": file_path
        }
