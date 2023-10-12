# A simple Windows perl script for testing batch scraping records in smaller quantities/batches

use strict;
use warnings;

my $start = 2000;
my $end = 10000;
my $year = 2021;
my $unit = 1000;

my $count = $start;

while($count < $end){
	my $count_block = $count + $unit - 1;
	system("python scraper.py --range_start $count --range_end $count_block --case_year $year --headless True --jitter_time 1.5 --web_driver_wait_time 2");
	my $count = $count_block;
}
