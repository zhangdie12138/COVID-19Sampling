# library(lubridate)
library(data.table) # fread - fastly reading data
library(tidyverse)

### zonecode
pop <- fread("bj_pop.csv",sep=",",header=T,encoding = "UTF-8",stringsAsFactors = F)
zonecode <- pop[,c("Name","jd_id")]
### read data -------
movement_data <- fread("jd_OD_days1112.csv",sep=",", header=T, stringsAsFactors = F,encoding="UTF-8")
movement_data$day<-movement_data$day-10
colnames(movement_data)<-c("from","to","date","movers")


mind<-as.numeric(startdate-as.Date("2020-06-10"))
maxd<-as.numeric(enddate-as.Date("2020-06-10"))
movement_data<-do.call(rbind,lapply(seq(mind,maxd),function(k){
  if(k>=3){
    mm<-subset(movement_data, movement_data$date==max(movement_data$date))
    mm$date<-k
    mm$movers<-round(mm$movers*(0.95^(k-2)),0)
  }else if(k>=1){
    mm<-subset(movement_data, movement_data$date==k)
    }else{
      mm<-subset(movement_data, movement_data$date==min(movement_data$date))
      mm$date<-k}
  #mm$movers<-round(mm$movers*lrate[k-2],0)
  return(mm)}))

movement_data$movers <- movement_data$movers +1

## population data
users <- movement_data[, list(users = sum(movers, na.rm=T)/48), by='from'] 
sum(users$users)
pop <- merge(pop, users, by.x="jd_id", by.y='from')
pop$pop_users <- pop$users + pop$pop*0.7

patNames = unique(pop$jd_id)[order(unique(pop$jd_id))]  
patIDs = 1:length(patNames)
pat_locator = data.frame(patNames,patIDs)

names(pat_locator)<-c("from","fr_pat")
movement_data<-merge(movement_data, pat_locator, by="from")
names(pat_locator)<-c("to","to_pat")
movement_data<-merge(movement_data, pat_locator, by="to")

pop_users <-pop[,c("jd_id","pop_users")]
names(pop_users)<-c("from","fr_users")
movement_data<-merge(movement_data, pop_users, by="from")
names(pop_users)<-c("to","to_users")
movement_data<-merge(movement_data, pop_users, by="to")

movement_data$fr_users = as.integer(movement_data$fr_users)
movement_data$to_users = as.integer(movement_data$to_users)

movement_data$fr_pat = as.integer(movement_data$fr_pat)
movement_data$to_pat = as.integer(movement_data$to_pat)

#convert dates to format R can read
movement_data$date = movement_data$date + as.Date("2020-06-10")
colnames(movement_data)[4] <- "move" # change variable name
movement_data <- movement_data[, c('to', 'date', 'from', 'move', 'fr_pat', 'to_pat', 'fr_users', 'to_users')]
movement_data$Date = ymd(movement_data$date) # change variable name
head(movement_data)

### population by region ----
pop_data <-pop[,c("jd_id","pop")]
names(pat_locator)<-c("patNames","patIDs")
pat_locator = merge(pat_locator,pop_data,by.x="patNames",by.y="jd_id")
pat_locator$pop <- as.integer(pat_locator$pop)
