# Usage
## opentripplanner index builder + tooling

on an aws box you'll probably need to do
     
     sudo apt install python2.7 python3-pip zip
     pip3 install -r requirements.txt
     
## Adding a new GTFS feed
Feeds are currently backed by http://transitfeeds.com/ with the tiniest start of support for http://transit.land

To add a feed, run `add-feed.py` with either a location URL like https://openmobilitydata.org/l/106-philadelphia-pa-usa or a specific provider feed like http://transitfeeds.com/p/mta/80 (either domain is fine). This will add an entry to `feeds.json`

`build.py` looks at `feeds.json` to determine what gtfs data to include in its index build. Before building the index, it 

- checks the transitfeeds api for new data from any of the configured providers, downloads them if the file is missing or the wrong size
- checks for errors in each feed with the google GTFS validator (this is what requires python2). Looks back up to five versions for valid GTFS, if not, doesn't include the feed
- Ten copies the latest valid GTFS files to an input directory (currently `./input`) for the OpenTripPlanner (OTP) build.

## Building an index

Just run `./build.py` - this will output a new inded at graphs/TIMESTAMP/ which will also be symlinked to graphs/current. There will also be an import log file in the current directory with more information about validation and whatnot.

build.py requires an [api key from transitfeeds.com](http://transitfeeds.com/api/keys). To run build.py, either specify TRANSITFEEDS_API_KEY as an environment variable or put TRANSITFEEDS_API_KEY=YOUR_KEY in a file called .env

     TRANSITFEEDS_API_KEY=YOUR_KEY ./build.py 

You can run & test this index on your local machine or in AWS.


# Notes on Data

There is no easy way to say "build me an index of every single GTFS feed in the world" For one thing, every transit agency maintains their own download page for the most part, as well as their own licensing terms, so we need to rely on aggregators for that. The two big aggregators are [http://transitfeeds.com/](http://transitfeeds.com/) and [https://transit.land/](https://transit.land/) (mapzen/interline).

This script current only supports [transitfeeds.com](http://transitfeeds.com). Support for transit.land is forcoming.

Some GTFS feeds seem not to work with OTP. There are two reasons for this that I've found - one is that the GTFS feed is invalid and OTP chokes on it. We try to prevent this by checking the [err field in the transitfeeds API](https://api.transitfeeds.com/v1/getFeedVersions?key=381c5d8f-a999-4bb3-a2e7-ad4bd4dbaefe&feed=suffolk-county-transit/1121&page=1&limit=10&err=1&warn=1) as well as running the feeds through the [incredibly out of date python2 google "official" gtfs validator.](https://github.com/google/transitfeed/wiki/FeedValidator) The other is that [OTP lags behind the official GTFS spec](https://github.com/mbta/OpenTripPlanner/commit/a704bb594539b7c80f1c8089879997cb621027ed#commitcomment-36591815) (as does the "official" gtfs validator). The official MBTA (boston) feed currently doesn't work in OTP even though it is valid with the current GTFS spec and works with google maps.

And, sometimes, even all this validation fails to catch feeds that OTP can't process. I tried to import all the paris feeds from [transitfeeds.com](http://transitfeeds.com) and hit some bus feed in Paris that caused the OTP build process to crash.

# Internals

## Configuration

The tool reads from a [feeds.json](https://github.com/radarlabs/otp-builder/blob/master/builder/feeds.json) file that can more easily be populated by [add-feed.py](https://github.com/radarlabs/otp-builder/blob/master/builder/add-feed.py) script. It understands GTFS feed urls from transitfeeds.com such as [http://transitfeeds.com/p/mta/86](http://transitfeeds.com/p/mta/86) as well as location urls such as  [http://transitfeeds.com/l/91-new-york-ny-usa](http://transitfeeds.com/l/91-new-york-ny-usa) (which is primarily what we are using to target entire metro areas).

The [build.py](https://github.com/radarlabs/otp-builder/blob/master/builder/build.py) tool does a few things

- Reads feeds.json, talks to transitfeeds' API to get GTFS download urls. Agencies and locations will likely yield multiple GTFS feeds (like, SF will include BART and MUNI, even NYC-MTA will include separate feeds for Queens, Brooklyn, etc)
- For each feed, tries to find the most recent valid version. A feed is valid if transitfeeds doesn't report any errors, and the (outdated) google validator doesn't report any errors. If the most recent feed has errors, goes back up to five releases to find one that's valid
- Copies the most recent valid versions the GTFS .zip files to one directory which is what OTP needs to build it
- Kicks off OTP build