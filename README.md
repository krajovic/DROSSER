# DROSSER Instructions:

1. Install Elasticsearch
    - It can be downloaded from [here](https://www.elastic.co/downloads/elasticsearch)
    - The version I used for this project was 7.12.0
    - Follow the instructions on the above page to run Elasticsearch
        - Specifically, navigate to Elasticsearch in your file system, for me it is a folder called elasticsearch-7.12.0
        - from there, run the command:
            - `$ bin/elasticsearch`


2. Create a virtual environment: 
    - `$ python3 -m venv <virtual_env_name>`

    - Then you can activate the environment using: `$ source <virtual_env_name>/bin/activate`

    - After this you can install all necessary packages with:
`$ pip install -r requirements.txt`


3. Use get_textbook_subsections.py to get the text content from Open Data Structures. 

    - `$ ./get_textbook_subsections <output_filename>`

    - I usually call this file textbook_subsections.jsonl. 
    - It contains all documents in the system. 


4. Use index_textbook.py to build the Elasticsearch index. 

    - `$ ./index_textbook.py <filename_from_previoust_step>`

    - Elasticsearch must be running during this step, and for all subsequent steps.


5. Start the app

    - `$ ./app.py`

    - You can then navigate to <http://127.0.0.1:5000/> to interact with the system. 


Note: Once you terminate the session, a metrics file will be produced called metrics.json. 
This is a simple JSON that contains the counts of all ratings made by the user during the session. 
The next time you use the app, that file will be loaded on startup so that those counts can be 
added to rather than starting again from zero. 