def _google_search(self, query: str, max_results: int) -> List[Dict]:
    """
    Perform Google Custom Search using their API
    """
    try:
        from googleapiclient.discovery import build
        
        service = build('customsearch', 'v1', developerKey=self.api_keys['google'])
        result = service.cse().list(
            q=query,
            cx='YOUR_SEARCH_ENGINE_ID',  # Add your search engine ID
            num=max_results
        ).execute()

        search_results = []
        if 'items' in result:
            for item in result['items']:
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'google'
                })
                
        return search_results
    except Exception as e:
        print(f"Google search error: {str(e)}")
        return []

def _bing_search(self, query: str, max_results: int) -> List[Dict]:
    """
    Perform Bing Web Search using their API
    """
    try:
        import http.client
        import json
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_keys['bing']
        }
        
        conn = http.client.HTTPSConnection('api.bing.microsoft.com')
        conn.request("GET", f"/v7.0/search?q={query}&count={max_results}", headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        
        search_results = []
        if 'webPages' in data and 'value' in data['webPages']:
            for item in data['webPages']['value']:
                search_results.append({
                    'title': item.get('name', ''),
                    'link': item.get('url', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'bing'
                })
                
        return search_results
    except Exception as e:
        print(f"Bing search error: {str(e)}")
        return []

def _serpapi_search(self, query: str, max_results: int) -> List[Dict]:
    """
    Perform search using SerpAPI
    """
    try:
        from serpapi import GoogleSearch
        
        search = GoogleSearch({
            "q": query,
            "num": max_results,
            "api_key": self.api_keys['serpapi']
        })
        results = search.get_dict()
        
        search_results = []
        if 'organic_results' in results:
            for item in results['organic_results']:
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'serpapi'
                })
                
        return search_results
    except Exception as e:
        print(f"SerpAPI search error: {str(e)}")
        return []
