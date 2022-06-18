# Mobility-based sampling improves detection of emerging infections in mass testing
 
This repository contains code and information regarding data access for "Mobility-based sampling improves detection of emerging infections in mass testing".
Provided codes and data were showed for the Beijing, while two metropolises, Beijing and Guangzhou, were tested in the study. 

Code within the Mobility-based folder includes the calculations of regional infection risk derived from four spatial sampling approaches:

- **RunHCI**: contains main code obtaining POI-based diversity index at communities.
- **RunHFI**: contains main code used to get the number of inflow and outflow populations at communities.
- **RunCFI**: contains main code computing the hourly counts of initial confirmed cases at communities.
- **RunCTI**: contains main code used to estimate the transmission events caused by intra-regional movement of initial cases.

Code within the SEIR folder includes the calculations of estimating epidemic transmissions.

- **BearmodFX**: contains main code buliding up the travel network SEIR modeling framework from [here](https://github.com/wpgp/BEARmod).
- **PreprocessData**: contains main code used to process origin-destination flows based on mobility data.
- **RunModel**: contains main code estimating transmissions for real-world COVID-19 outbreaks.
- **RunModel_sim**: contains main code estimating transmissions for simulated outbreaks.
- **RunModel_mt**: contains main code used to estimate transmissions for simulated outbreaks under multiple rounds of mass testing.

## Data availablity
### Demographics and COVID-19 data
Population data access can be requested [here](www.worldpop.org). Aggregated population were seen in the file 'CommunityAttr.xlsx'.
COVID-19 data used in the study have been detailed in Supplementary Information.

### Mobile phone signaling data
It is restricted for the origin mobile phone signaling data (June 11 to 12, 2020) access because it is purchased from the service provider (China Mobile Ltd.). The data purchase agreement with China Mobile prohibits us from sharing these data with third parties. Interested parties can contact China Mobile to make the same data purchase. However, aggregated staying population at communities based on mobile phone signaling data were detailed in 'CommunityAttr.xlsx'.

### Point-of-interest data
Publicly availability is restricted for the origin POI data owing to data restrictions from AMap Services. Readers interested in the data can contact AutoNavi Software Co., Ltd.

### Processed data
- Based on mobile phone signaling and POI data, infection risk at the community level derived from sampling approaches was computed and showed in files 'HCI.csv', 'HFI.csv', 'CFI.csv', and 'CTI.csv'.
- 'no. of estimated affected communities.csv': Number of estimated affected communities using the SEIR for the real-world outbreak.
- 'cfi&cases_simulated transmissions.csv': Infection risks in the CFI and cumulative number of cases under simulated epidemics.
- 'bj_face_mask.csv': Daily Baidu search index, using “mask” as a search term [here](https://index.baidu.com/).
