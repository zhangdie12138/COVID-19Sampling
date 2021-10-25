# Mobility-based spatial sampling for city-level mass testing to contain COVID-19
 
This repository contains code and information regarding data access for "Mobility-based spatial sampling for city-level mass testing to contain COVID-19".

Code within the InfectionRisk folder includes the calculations of regional infection risk derived from four spatial sampling approaches:

- **RunHCI**: contains main code obtaining POI-based diversity index at communities.
- **RunHFI**: contains main code used to get the number of inflow and outflow populations at 500-meter grids.
- **RunCFI**: contains main code computing the hourly counts of initial confirmed cases at 500-meter grids.
- **RunCTI**: contains main code used to estimate the transmission events caused by inter- and intra- regional movement of initial confirmed cases.




## Data availablity
### Demographics and COVID-19 data
Population data access can be requested [here](www.worldpop.org). WorldPop-aggregated population at the community level in Beijing is showed in the EXCEL file (CommunityAttr.xlsx).
COVID-19 data used in the study have been detailed in Supplementary Information and can be seen in CommunityAttr.xlsx.

### Mobile phone signaling data
It is restricted for the origin mobile phone signaling data (June 11 to 12, 2020) access because it is purchased from the service provider (China Mobile Ltd.). The data purchase agreement with China Mobile prohibits us from sharing these data with third parties. Interested parties can contact China Mobile to make the same data purchase. However, the aggregated staying populations and travelers (HFI) at communities based on mobile phone signaling data were detailed in CommunityAttr.xlsx.

### Point-of-interest Data
Publicly availability is restricted for the origin POI data owing to data restrictions from Gaode Map Services. Readers interested in the data can contact AutoNavi Software Co., Ltd. However, the number of POIs in the communities was showed in CommunityAttr.xlsx.
