
def get_circleci_pipelines(api_token):
    headers = {
        'Circle-Token': api_token,
    }
    url = 'https://circleci.com/api/v2/pipeline'
    params = {
        'org-slug': 'gh/codecov',
        'mine': False
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception if the request was not successful
        return response.json()
    except httpx.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None