
# istex2csv

* Parse row result from istex api. 
  http://demo.istex.fr/

* Convert json data to csv

* Export/append csv to ethercalc ( PUT, POST )

* @see https://github.com/padagraph/botapadd 



## requirements

  pip install -r requirements.txt


## convert istex data to %csv

  python istex2csv.py --port 5004 
  
## Notes

  # POST PUT to ethercalc with curl.
  curl -i -X PUT --data-binary @~/bidon.csv https://ethercalc.org/_/htkuiuytp8dj
  
