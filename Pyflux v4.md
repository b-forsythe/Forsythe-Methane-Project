### Pyflux v4

Device measures CO2, water vapor, methane

Greenhouse gas analyzer

based in instrument time, 2-5 minute intervals

linear change of gases

local environment -> move to cloud based?

CSV Files

- Systime, Time, [CH4] ppm, interested in derivative ch4 



Collar 'monitiring'.py

- error handling
- self-correcting diagnostics
- r^2 values (between 0.91 and 0.999)



Interested in flux - linear rate of change of ch4



#### MVP

1. Play around with the min_section_original

2. Implement length of time for successful test (time inside spreadsheet)



#### Stretch Goals

1. Graph shows observation data and the accepted line of best fit
2. Take top 3(?) accepted R-values and graph on same graph





* Add a column that shows amount of time to get result (number of seconds)
* Columns O, P, Q, R unnecessary
* if no data, make graph anyway? 
* 'use data column?' find and change threshold to 0.9







## Questions

1. June 2019 data skewing results? Why does it pull from that file?