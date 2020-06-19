# log_analyzer

```log_analyzer``` is a Python script for parsing nginx logs and creating an ```html``` report with the top-x longest queries.

The script processes the last one (with the most recent date in the name, not by mtime of the file!) log file in folder
The result of the work should be a report file like: ```report-2017.06.30.html```. 
In other words, the script reads the log, parses the necessary fields, counts the necessary information
statistics by ```url``` and render template ```report.html```. 
The situation that
there are no logs on the server-it is possible, this is not an error.
If the script successfully processed, it does not redo the work when it is restarted. 
Reports are stored in the reports folder. 
Report contain statistics for URLS with the highest total processing time (time_sum).

## Installation

you only need these files. 

```bash
log_analyzer.py 
report.html
log_analyzer.ini 
```

## Params
The script can be ordered to read the config file by passing its path through --config. All parameters must be located in the [CONFIG] section. If the file doesn't exist or isn't parsed, the script will end up with an error.

|param|value|meaning|
|------|------|--------|
|REPORT_SIZE| 1000| number of lines in report table|  
|REPORT_DIR"|./reports| folder with reports|
|LOG_DIR|./log| folder with source logs| 
|LOG_FILE_MASK|\*nginx-access-ui.log-????????*| file mask for log file
|MAX_ERROR_PERCENT|20| max possible percent of unparsed lines in log file 

