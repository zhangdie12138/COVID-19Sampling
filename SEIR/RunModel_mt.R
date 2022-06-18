####Model running code

library(data.table) # fread - fastly reading data
library(lubridate)

### simulation dates
startdate <- ymd("2020-06-15")
start_report <- ymd("2020-06-11")
end_report <- ymd("2020-07-05")
enddate <- ymd("2020-08-30")
date_0 <- startdate -1

### travel network-based SEIR model
source("2 bearmod_fx_mt.R")

### preprocess data
source("3 preprocess_data.R") 

exposepd = 5.2
R0 = 9.5
onset_isolation <- 5
mt_days <- 12 # duration of mass testing
input_dates <- seq(startdate, enddate, by="days")
NPat <- length(patNames)


recover_df_mt <- do.call(rbind,lapply(seq(1,mt_days),function(i){
  day <- input_dates[i]
  recrate <- 6 - floor((i+1)/2)
  if (recrate<2){
    recrate <- 2
  }
  return(data.frame(date=day, recrate= recrate))
  
}))

onset_report <- data.frame(date = seq(from=min(movement_data$Date),
                                      to=max(movement_data$Date),by="days"))
recover_df <- merge(onset_report, recover_df_mt, by.x = 'date', by.y = 'date', all.x = T)
colnames(recover_df) <- c('date', 'recrate')

recover_df$recrate[which(recover_df$date < min(recover_df_mt$date))] <- recover_df$recrate[which(recover_df$date == min(recover_df_mt$date))]
recover_df$recrate[which(recover_df$date > max(recover_df_mt$date))] <- recover_df$recrate[which(recover_df$date == max(recover_df_mt$date))]
recover_df$rec_day <- recover_df$recrate
recover_df$recrate <- 1/recover_df$recrate 


mass_n <- round(NPat * 1/mt_days) # number of daily sampled communities

contact <- read.csv('baidu-based_weight.csv', stringsAsFactors = F)
contact$date <- date(contact$date)
contact <- contact[which(contact$date >= start_report & contact$date <= enddate),]

contact$drop_mean[which(contact$date < startdate)] <- 1
contact$drop_mean[which(contact$date > end_report)] <- contact$drop_mean[which(contact$date == end_report)]


for (t in 1:30){
  patnInf = rep(0,NPat)
  patnExp = c(rep(0,NPat))

  ## initial cases
  begin.p <- fread(paste0(as.character(t),"_ini_cases.csv"), stringsAsFactors = F)
  begin.p[is.na(begin.p)] <- 0

  patnInf[which(patNames%in%begin.p$id)] = begin.p$num
  
  ## infection risks from CFI
  cfi <- read.csv(paste0('CFI_', as.character(t),".csv"), stringsAsFactors = F)
  cfi <- merge(cfi, zonecode, by ='jd_id', all.x = T)
  
  
  ## contact reductions under mass testing
  contact_drop_data <- do.call(rbind,lapply(seq(1,mt_days),function(i){
    day <- input_dates[i]
    tt <- 1/2.7 # the reciprocal of time lags from exposure to contagiousness
    c_r <- contact$drop_mean[which(contact$date == day)]
    
    drop_cfi <- cfi[sample(seq_len(nrow(cfi)),mass_n,prob=cfi$New_inf),]$jd_id
    
    c_r_n <- c_r * (tt * mass_n / (NPat-mass_n) + 1)
    
    drop_m <- data.frame(from=patNames, date=day, drop=c_r_n, drop_mean = c_r)
    drop_m$drop[which(drop_m$from%in%drop_cfi)] <- c_r * (1-tt)
    
    return(drop_m)
    
  }))
  
  contact_drop <- subset(contact_drop_data, date==input_dates[1])
  for (i in 2:mt_days){
    day <- input_dates[i]
    contact_drop_day_i <- subset(contact_drop_data, date==day)
    contact_drop_day_i_1 <- subset(contact_drop, date==day-1)
    contact_drop_day <- merge(contact_drop_day_i, contact_drop_day_i_1, by='from', all=T)
    contact_drop_day$contact_drop <- contact_drop_day$drop.x * contact_drop_day$drop.y / contact_drop_day$drop_mean.y
    contact_drop_day <- contact_drop_day[,c('from', 'date.x', 'contact_drop', 'drop_mean.x')]
    names(contact_drop_day) <- c('from', 'date', 'drop', 'drop_mean')
    contact_drop <- rbind(contact_drop, contact_drop_day)
    
  }
  
  
  mt_end <- input_dates[mt_days] # end date of mass testing
  
  exposerate_df <- expand.grid(from = patNames, date = input_dates)
  exposerate_df <- merge(exposerate_df, contact_drop[,c('from', 'date', 'drop')], by=c('from','date'), all.x=T)
  
  exposerate_df <- merge(exposerate_df, contact, by='date', all.x=T)
  exposerate_df$drop[which(exposerate_df$date > mt_end)] <-
    exposerate_df$drop_mean[which(exposerate_df$date > mt_end)]
  
  exposerate_df$drop[which(exposerate_df$date > end_report)] <-
    exposerate_df$drop[which(exposerate_df$date == end_report)]
  
  exposerate_df$exposerate <- R0/onset_isolation * exposerate_df$drop
  

  maskrate <- 0.733
  mask_eff <- 1/1.44
  
  face_mask <- read.csv('BJface_mask.csv', stringsAsFactors = F)
  face_mask$date <- date(face_mask$date)
  
  face_mask$rate <- face_mask$num / 
    max(face_mask$num[which(face_mask$date >= start_report & face_mask$date <= enddate)])
  
  face_mask$maskrate_eff <- (1 - face_mask$rate * maskrate * mask_eff)^2
  
  exposerate_df <- merge(exposerate_df, face_mask[,c("date", 'maskrate_eff')],
                         by.x='date', by.y='date', all.x=T)
  exposerate_df$maskrate_eff[is.na(exposerate_df$maskrate_eff) == T] <- (1 - maskrate * mask_eff)^2
  exposerate_df$exposerate <- exposerate_df$exposerate * exposerate_df$maskrate_eff
  
  exposerate_df$maskrate_eff <- NULL
  
  
  relative_move_data <- exposerate_df[,c('date', 'from', 'drop')]
  names(relative_move_data) <- c('date', 'from', 'relative_move')
  
  #### Running the model --------
  HPop = InitiatePop(pat_locator,patnInf,patnExp)
  ## Master function
  results = list()
  n=500 # no. of simulations
  
  for (run in 1:n){
    HPop_update = runSim(HPop,pat_locator,relative_move_data,movement_data,input_dates,recover_df,exposerate_df,exposepd)
    results[[run]] = HPop_update$all_spread
  }
  
  save(results, file=paste0(as.character(t),"_results.RData"))
  print(paste0("Run # ",t))
}

