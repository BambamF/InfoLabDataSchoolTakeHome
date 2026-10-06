# InfoLabDataSchoolTakeHome Gabi Fabiyi

## Project purpose

The purpose of this project was to demonstrate the full data pipeline, from acquisition, to cleaning, to enrichment and analysis.

The project utilises concurrent programming to acquire the required data via a public API while keeping credentials such as the API key out of the remote repository via the use of a environment file.

Upon completion of the data pipeline demonstration, once data quality had been ensured, the project transformed the insights gleamed from the resulting data transformations to create a product intended to be of use to end users, this product took the form of a games company locator with company locations visualised on an interactive map embedded in a webpage. The end user demographic I believe this product could be of use to is game developers looking to apply to companies and studios near them and gaming journalists looking to find information on companies to aid their writing.

## About me

My name is Gabi Fabiyi, I'm a current MSc Computer Science student (2026) with a study focus on Big Data Analytics and Machine Learning. 

I am currently attending Birkbeck College, University of London and have recently submitted my thesis project Harness Engineering for Agentic Code Generation. I am interested in Data Science/Engineering, Machine Learning and Robotics and I am currently conducting personal research into World Modelling and Gait Phase analysis for Geospacial Data/Intent Generation.

I have internship experience as a full stack developer and as a systems and data developer (current employment), and personal project experience of web development, model training and desktop application development.

I am interested in this role as a consultant with the Information Lab as I believe it would be a great opportunity to deepen my knowledge by learning directly from industry professionals and experts. I believe that learning industry practices from seasoned professionals and senior developers, along with the mentorship I would receive, would set me up for an ideal start to my career. I would relish the opportunity to provide tangible insights and benefits for clients through the application of the knowledge I gain from the Information Lab.

## End to end data pipeline and visualisation

For this project, I built a games companies locator for job candidates and game journalists to be able to easily locate game companies in the UK.

The project utilises the Companies House company profile api to find the company details.

I built the pipeline using python and pandas, the companies house api enforces a limit of 600 calls within a five minute period. To handle this, I built a custom blocking deque with increasing sleep times on each retry.

The pipeline uses a threadpool executor with a maximum worker count of 6 and a mutex locking strategy to download the rows of data, the initial data was acquired using the gamesmap csv from gamesmap.uk with over 3000 entries.

Dates and sic codes were formatted to be stored appropriately, the sic codes in this case were transformed into a semi colon delmitted string and addresses were also formatted from the nested dictionaries into a single string.

The cleaning step involved getting rid of duplicates and dropping completely null columns, turning company numbers into numerics was avoided as some company numbers contain character strings.

The analysis stage prints a number of statistics about the dataset to the terminal including the number of companies established since two global turning point years: 2008 and 2019. Displaying the rate of establishment of new gaming companies after major world events.

Bash
----

The code can be run by first activating a python virtual environment:

`python -m venv .venv`

Then activate the virtual environment:

`source .venv/bin/activate`

Download the dependencies:

`pip install -r requirements.txt`

Then initialise the database:

`PYTHONPATH=. python3 backend/init_db.py`

Then run the server:

`uvicorn backend.main:app --reload`

Split your terminal

In the second terminal console, run:

`cd frontend`

then 

`npm install`

and 

`npm update`

Then run the frontend in your local developer environment:

`npm run dev`

The frontend page should be active, visit [http://localhost:5173/] to view it.

When done you can stop the servers using `crtl + C` and deactivate the virtual environment using `deactivate`

To run the fetching code you will need a Companies House API Key

Place it in your `root/.env`

To run the query code you will need a Geocoding API Key and a Routing API key from GeoApify

Place the Geocoding API key in your `root/.env`

Place the Routing API key in your `frontend/.env`

## Future improvements

If I were to further develop this idea, I would likely work on improving the simple frontend to be much more responsive and pleasant to look at.

I would include a feedback for when the postcode search is loading as there is currently no feedback implemented.

I would also make the company list link to the company websites to make the application more useful for users, and implement input sanitisation to protect the database from SQL injections and other potential malicious input attacks.

Also, I would further enrich the dataset with persons of significant control as this could be useful for journalists and candidates to know. Further, more analytics could be gained from the dataset e.g. using the sic codes to find out which companies could be eligible for BICS discounts and which are not currently being taken advantage of, and where the concentration of companies are in the UK, an interesting find was the number of gaming companies that share the same building.

## AI use

I used AI to help with duckdb as this db is new to me so I queried AI at certain times e.g. To do the radius calculations I was looking up how to use lat and lon coordinate values to locate a certain area then calculate the companies that fall within that area as queried by the user, but claude suggested that that would be overengineered and duckdb actually supplies S_Distance_Spere and S_Point facilities that would do that calculation for me. This saved me a headache.

I also initially wrote a threadpool executor/ lock strategy script for enriching the lat lon values within the analysis.csv version of the data but with the 5 calls per second limitation of the GeoApify Geocoding endpoint, it was just taking far too long for over 3000 entries, watching the calls constantly sleeping was mind numbing. I noticed there was a batching option and used AI to make sense of the documentation quickly so I could use it as soon as possible. Using the batching strategy, it still took a while but it was much quicker. This also saved a lot of frustration.

Finally I used AI to help with using the Leaflet embedded map, this is a tool I havent used before and I queried AI on the react-leaflet syntax while also reading GeeksforGeeks to make sure I was using it correctly.