```
git clone  
cd pulse 
mv config.json.example config.json
```  
Fill out the config  
``` 
poetry install  
poetry env use python3  
poetry run python sitemap.py --base-url=a7.co --poll=5 --keyword=arnold
```
