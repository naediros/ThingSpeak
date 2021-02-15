# ThingSpeak

Little repository for getting data from ThingSpeak API and displaying it in Jupyter Notebook with plotly library. 
What we personally have on ThingSpeak is currently data from Arduino (in fact, two Arduinos) gathering: 
- temperature inside a greenhouse
- temperature outside a greenhouse
- atmospheric pressure
- illumination
- humidity (inside a greenhouse)
- dew point (do not ask me why)
- battery current
- battery voltage

Libraries: 
- dotenv
- requests
- matplotlib
- pandas 
- plotly (graph_objects for now)

## TODO's: 
- check how the data download can be done in a better than 'append into csv' way. Maybe sqLite?
- finish all the plots
- think about what else can be displayed/defined from the data
- maybe create some sort of min/max digest would be nice :-) or historical... trends... etc.
