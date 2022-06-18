####Model running code
library(data.table) # fread - fastly reading data
library(lubridate)

### simulation dates
startdate <- ymd("2020-06-03")  # start date of simulation
start_report <- ymd("2020-06-11") # date of the first case reported
enddate <- ymd("2020-07-05") # date of the last case reported
date_0 <- startdate -1

### travel network-based SEIR model
source("2 bearmod_fx.R")

### preprocess data
source("3 preprocess_data.R")

## epidemiological  parameters
exposepd = 5.2 # incubation period
R0 = 4.9 # basic reproduction number
onset_isolation <- 5 # high-transmissibility period after illness onset

## recovery rate variable - days from onset/being infectious to recovery/isolation under interventions e.g. testing
onset_report <- fread('infectious_period.csv', stringsAsFactors = F, encoding="UTF-8")
onset_report$date <- as.Date(onset_report$date)

## intervention one-week delay
# onset_report$date <- onset_report$date + 7

## daily probability of recovery/isolation - from onset to report (removing cases from the model)
recover_df = data.frame(date = seq(from=min(movement_data$Date),
                                   to=max(movement_data$Date),by="days"))
recover_df <- merge(recover_df, onset_report, by.x = 'date', by.y = 'date', all.x = T)
colnames(recover_df) <- c('date', 'recrate')

recover_df$recrate[which(recover_df$date < min(onset_report$date))] <- recover_df$recrate[which(recover_df$date == min(onset_report$date))]
recover_df$recrate[which(recover_df$date > max(onset_report$date))] <- recover_df$recrate[which(recover_df$date == max(onset_report$date))]
recover_df$recrate <- 1/recover_df$recrate # lower proportion, slower recovery/isolation and high transmission rate


## intervention one-week delay
# contact_drop$date <- contact_drop$date + 7

## basic exposure rate, modified by travel and contact reductions under NPIs
contact <- read.csv('baidu-based_weight.csv', stringsAsFactors = F)
contact$date <- date(contact$date)
contact <- contact[which(contact$date >= start_report & contact$date <= enddate),]
contact$drop_mean[which(contact$date < startdate)] <- 1
contact$drop_mean[which(contact$date > end_report)] <- contact$drop_mean[which(contact$date == end_report)]

exposerate_df <- recover_df
exposerate_df <- merge(exposerate_df, contact_drop[,c("date", 'drop_mean')], 
                       by.x='date', by.y='date', all.x=T)
exposerate_df$drop_mean[which(exposerate_df$date < start_report)] <- 1
exposerate_df$drop_mean[which(exposerate_df$date > max(contact_drop$date))] <- 
  exposerate_df$drop_mean[which(exposerate_df$date == max(contact_drop$date))]

exposerate_df$exposerate <- R0/onset_isolation * exposerate_df$drop_mean

## exposure rate, modified by Face covering
maskrate <- 0.733 # proportion of population with face covering before the outbreak
mask_eff <- 1/1.44 # Effectiveness of Face Mask

face_mask <- read.csv('face_mask.csv', stringsAsFactors = F) # daily changing
face_mask$date <- date(face_mask$date)

face_mask$rate <- face_mask$num / 
  max(face_mask$num[which(face_mask$date >= start_report & face_mask$date <= enddate)])

face_mask$maskrate_eff <- (1 -  face_mask$rate * maskrate * mask_eff)^2

## merge with exposerate data frame 
exposerate_df <- merge(exposerate_df, face_mask[,c("date", 'maskrate_eff')],
                       by.x='date', by.y='date', all.x=T)
exposerate_df$maskrate_eff[is.na(exposerate_df$maskrate_eff) == T] <- (1 - maskrate * mask_eff)^2
exposerate_df$exposerate <- exposerate_df$exposerate * exposerate_df$maskrate_eff
  
exposerate_df$recrate <- exposerate_df$drop_mean <- exposerate_df$maskrate_eff <- NULL

## relative mobility reduction
relative_move_data <- expand.grid(from = patNames, date = input_dates)
relative_move_data <- merge(relative_move_data, exposerate_df, by='date', all.x = T)
relative_move_data <- relative_move_data[,c('date', 'from', 'drop_mean')]
names(relative_move_data) <- c('date', 'from', 'relative_move')

## dates of simulation
input_dates = seq(startdate, enddate, by="days") # Beijing

for (i in 1:100){
  ### parameters
  ## Initial parameters
  NPat = length(patNames)
  patnInf = rep(0,NPat)
  patnExp = c(rep(0,NPat))
  
  ## start infection (initial number of cases at day 0) in one location
  patnInf[which(patNames == '144')] = 15
  
  #### Running the model --------
  HPop = InitiatePop(pat_locator,patnInf,patnExp)
  
  ## Master function
  results = list()
  n=500 # no. of simulations
  
  for (run in 1:n){
    HPop_update = runSim(HPop,pat_locator,relative_move_data,movement_data, input_dates,recover_df, exposerate_df, exposepd)
    results[[run]] = HPop_update$all_spread # daily new infections
  }
  
  save(results, file=paste0('Results_500t_',i,".RData"))
}


