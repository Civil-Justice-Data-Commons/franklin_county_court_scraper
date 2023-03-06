# Franklin Co. Court Scraper

A tool for scraping limited court records from Franklin Co., Ohio.

## Use
This scraper is only intended for use with full permission of the Franklin Co. Court.

Even with permission from the court, overzealous requests will likely result in an IP block from their systems. Unfortunately, the ideal timing for use of the scraper still needs to be worked out for sustained use.

### From the Command Prompt
```shell 
python scraper.py --year 2001 --range_start 0 --range_end 100
```

#### Flags:
```python
--data_file # String, Not Required, Default is "defaults.json", the json file to pull options from
--case_year # Int, Not Required, Default is 1998, pulled from "defaults.json", case year to scrape
--case_code # String, Not Required, Default is "CVI", pulled from "defaults.json", case type to scrape
--range_start # Int, Mot Required, Default is 3000, pulled from "defaults.json", case number range to start scraping from
--range_end # Int, Not Required, Default is 6000, pulled from "defaults.json", case number to stop scraping on
--pause_time # Int, Not Required, Default is 2, pulled from "defaults.json", number of seconds to pause between scraping records
--jitter # Boolean, Not Required, Default is True, pulled from "defaults.json", to use the jitter function to add a random number to pause time
--jitter_time # Float, Not Required, Default is 5.0, pulled from "defaults.json", max time to add to pause time if jitter enabled
--web_driver_wait_time # Int, Not Required, Default is 10, pulled from "defaults.json", max time for the web drive to wait between scraping actions
--headless # Boolean, Not Required, Default is False, pulled from "defaults.json", should selenium run headless or not
--results_dir # String, Not Required, Default is "/results", pulled from "defaults.json", place to spit out results to
```

#### Default Behavior
The scraper takes command line arguments (or arguments from a defaults.json file or another json file specified), scrapes records from the `range_start` to `range_end` for the specified `year` and `case_code` (almost always CVI for civil cases), and then spits those results out into a json file in the `results` directory.

#### Results
The resulting json looks like this:
```json
{
	"<CASE NUMBER>": {
		"parties" : {
			"plaintiffs" : {
				"<PARTY NAME>" : {
					"address" : "",
					"city" : "",
					"state" : "",
					"zip" : ""
				}
			},
			"defendants" : {
				"<PARTY NAME>" : {
					"address" : "",
					"city" : "",
					"state" : "",
					"zip" : ""
				}
			},
		"attorneys" : {
			"<PARTY NAME>" : {
				"name" : "",
				"address" : "",
				"city" : "",
				"state" : "",
				"zip" : ""
			}
		},
		"dispositions" : {
			"<DISPOSITION>" : {
				"disposition_date" : "",
				"status" : "",
				"status_date" : ""
			}
		},
		"docket" : {
			"<DATE>" :{
				"event" : "",
				"amount" : "",
				"balance" : "",
				"details" : ""
			}
		}
	}
}
```

### Calling Methods
The internal methods of the scraper can also be called. `single_scrape()` in particular may be useful.
```python
scrape_record(webdriver driver, int year, str code, int case_num, int wait_time) # Used to scrape a record, returns dict
```
```python
bulk_scrape(webdriver driver, int year, str code, int start, int end, int pause, bool jitter, float jitter_time, int wait_time,) # Used to bulk scrape everything between start and end, returns a dict of dicts by case number
```
```python
single_scrape(int case_year=1998, str case_code='CVI', int case_num=3001, int web_driver_wait_time=10, bool headless=False) # Used mainly for testing, prints and returns a dict
```

## As a Model Scraper
This scraper is also intended to be a code resource for developing other court scrapers. As such, it is hopefully well commented. When adapting to scrape other court sites, *please* follow ethical scraping guidelines and scrape in such a way that is not burdensome on court resources and does not run foul of any guidelines or laws in that particular jurisdiction.

This scraper uses the Python Selenium library to scrape through search pages of a court case site, and then "prints" the cases it finds to get HTML results that are easier to use the BeautifulSoup library to parse into a dictionary, which is then spat out as a json file.

To adapt to a different site, the main changes are likely going to be the particularities of this final "printed" html. Careful examination of the html compared to the html for Franklin Co. (contained in the reference dir of this repo) is likely to be helpful.

---

Developed by James Carey for the Civil Justice Data Commons, a joint project between the Georgetown University Law Center and the Georgetown McCourt School Massive Data Institute.