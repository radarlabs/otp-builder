# opentripplanner index builder + tooling

on an aws box you'll probably need to do
     
     sudo apt install python2.7 python3-pip zip
     pip3 install -r requirements.txt
     
# Adding a new GTFS feed
Feeds are currently backed by http://transitfeeds.com/ with the tiniest start of support for http://transit.land

To add a feed, run `add-feed.py` with either a location URL like https://openmobilitydata.org/l/106-philadelphia-pa-usa or a specific provider feed like http://transitfeeds.com/p/mta/80 (either domain is fine). This will add an entry to `feeds.json`

`build.py` looks at `feeds.json` to determine what gtfs data to include in its index build. Before building the index, it 

- checks the transitfeeds api for new data from any of the configured providers, downloads them if the file is missing or the wrong size
- checks for errors in each feed with the google GTFS validator (this is what requires python2). Looks back up to five versions for valid GTFS, if not, doesn't include the feed
- Ten copies the latest valid GTFS files to an input directory (currently `./input`) for the OpenTripPlanner (OTP) build.

# Building an index

Just run `./build.py` - this will output a new inded at graphs/TIMESTAMP/ which will also be symlinked to graphs/current. There will also be an import log file in the current directory with more information about validation and whatnot.

build.py requires an [api key from transitfeeds.com](http://transitfeeds.com/api/keys). To run build.py, either specify TRANSITFEEDS_API_KEY as an environment variable or put TRANSITFEEDS_API_KEY=YOUR_KEY in a file called .env

     TRANSITFEEDS_API_KEY=YOUR_KEY ./build.py 

You can run & test this index on your local machine or in AWS.