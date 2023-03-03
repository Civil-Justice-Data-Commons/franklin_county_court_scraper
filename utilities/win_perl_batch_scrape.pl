# A simple Windows perl script for testing batch scraping records in smaller quantities/batches


$start = 0;
$end = 5000;
$unit = 100;

$count = $start;

while($count < $end){
	$count_block = $count + $unit;
	system("python scraper.py --range_start $count --range_end $count_block");
	$count = $count_block + 1;
}