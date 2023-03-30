#' graph will have "number of mRNA therapy studies started per year" on y axis, x axis will be seperated from y and will start at 2002 til 2022 (continuous time), a dotted line to start.
#' words and lines will be used for the categories; cancer, virus, genetic disease
#' the following annotations will be added: moderna established, covid-19 gene sequenced (2019), emergency authorization of mRNA vaccine for COVID-19

#packages
library(dplyr)
library(tidyr)
library(ggplot2)
library(bbplot)
library(RColorBrewer)


#Data
mRNAtherapyhist <- read.csv("~/Documents/GitHub/mRNA-therapy-history-data/Non-covid mRNA vaccines since 01_01_2020 - Sheet1.csv")
mRNAtherapyhist <- mRNAtherapyhist[,1:9] #remove clinicaltrials.gov link

#organize data
blankdata <- data.frame(Study.start.year=seq(from=2002, to=2022, by=1),
                        Cancer=c("0"),
                        Virus=c("0"),
                        `Genetic Disease`=c("0"))
blankdata <- blankdata %>% 
  gather("Disease.Type", "n", 2:4)

countdata <- mRNAtherapyhist %>% count(Study.start.year, Disease.Type, sort=TRUE)
countdata <- rbind(countdata, blankdata)
countdata$n <- as.numeric(countdata$n)
countdata2 <- countdata %>% 
  group_by(Study.start.year, Disease.Type) %>% 
  summarise(freq=sum(n))
countdata2$Disease.Type[is.na(countdata2$Disease.Type)] <- "Genetic Disease"
countdata2 <- countdata2[-c(51,55,62,66),]
countdata2$Disease.Type <- ordered(countdata2$Disease.Type, levels=c("Cancer", "Virus", "Genetic Disease"))
countdata2$Disease.Type[is.na(countdata2$Disease.Type)] <- "Genetic Disease"
countdata3 <- countdata2 %>% group_by(Disease.Type) %>% arrange(Study.start.year) %>% mutate(cumm=cumsum(freq))

ggplot(countdata3, aes(Study.start.year, cumm, fill=Disease.Type)) +
  geom_area(alpha=0.7) +
  scale_x_continuous(breaks=seq(from=2002, to=2022, by=1))+
  scale_y_continuous(expand=c(0,0), limits=c(0,80))+
  scale_fill_brewer(palette="Dark2") +
  ggtitle("Cumulative number of \nclinical mRNA therapy trials each year (excl. COVID-19)") +
  geom_vline(xintercept=2010, linetype="dotted", size=1, color="darkgray") + annotate("text", x=2010, y=75, size=6, label="Moderna founded", hjust=1.02) + 
  geom_vline(xintercept=2019.358, linetype="dotted", size=1, color="darkgray") + annotate("text", 2019.358, 68, label="COVID-19 \ngenome \nsequenced", size=6, hjust=1.02) +
  theme(axis.text.x = element_text(angle = 270, vjust = 0.5, hjust=1), legend.position="none")+
  bbc_style()

ggplot(countdata3, aes(Study.start.year, cumm, fill=Disease.Type)) +
  geom_area(alpha=0.7) +
  scale_x_continuous(breaks=seq(from=2002, to=2022, by=1))+
  scale_y_continuous(expand=c(0,0), limits=c(0,80))+
  scale_fill_brewer(palette="Dark2") +
  #ggtitle("Cumulative number of \nclinical mRNA therapy trials each year (excl. COVID-19)") +
  #geom_vline(xintercept=2010, linetype="dotted", size=1, color="darkgray") + annotate("text", x=2010, y=75, size=6, label="Moderna founded", hjust=1.02) + 
  #geom_vline(xintercept=2019.358, linetype="dotted", size=1, color="darkgray") + annotate("text", 2019.358, 68, label="COVID-19 \ngenome \nsequenced", size=6, hjust=1.02) +
  theme(axis.text.x = element_text(angle = 270, vjust = 0.5, hjust=1), legend.position="none")+
  theme_void()

