# packages
library(dplyr)
library(tidyr)
library(ggplot2)
library(RColorBrewer)

# Data
mRNAtherapyhist <- read.csv("~/Documents/GitHub/mRNA-therapy-history-data/data/mrna_trials_classified.csv", check.names=FALSE)
mRNAtherapyhist <- mRNAtherapyhist %>% filter(is_covid == "False" | is_covid == FALSE)
mRNAtherapyhist <- mRNAtherapyhist %>% filter(match_source != "official_title_only")

# Define Dark2 colors manually for the single-fill bar charts
dark2_colors <- brewer.pal(8, "Dark2")

# 1. Trials by Company (Top 10)
company_counts <- mRNAtherapyhist %>%
  filter(!is.na(lead_sponsor) & lead_sponsor != "") %>%
  count(lead_sponsor, sort = TRUE) %>%
  top_n(10, n)

p1 <- ggplot(company_counts, aes(x = reorder(lead_sponsor, n), y = n)) +
  geom_bar(stat = "identity", fill = dark2_colors[1]) + # #1B9E77
  coord_flip() +
  theme_minimal() +
  labs(title = "Top 10 Companies/Sponsors by Number of Trials",
       x = "Company/Sponsor",
       y = "Number of Trials")

ggsave("~/Documents/GitHub/mRNA-therapy-history-data/figures/trials_by_company.png", plot = p1, width = 8, height = 6)

# 2. New Trials Per Year (Non-Cumulative)
countdata <- mRNAtherapyhist %>% 
  filter(!is.na(start_year)) %>%
  count(start_year, disease_type)

countdata$disease_type[is.na(countdata$disease_type) | countdata$disease_type == ""] <- "Other"
countdata$disease_type <- factor(countdata$disease_type, levels=c("Cancer", "Virus", "Genetic Disease", "Other"))

p2 <- ggplot(countdata, aes(x = start_year, y = n, fill = disease_type)) +
  geom_bar(stat = "identity") +
  scale_x_continuous(breaks=seq(from=min(countdata$start_year, na.rm=T), to=max(countdata$start_year, na.rm=T), by=1)) +
  scale_fill_brewer(palette = "Dark2") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(title = "New mRNA Therapy Trials Per Year (excl. COVID-19)",
       x = "Study Start Year",
       y = "Number of New Trials",
       fill = "Disease Type")

ggsave("~/Documents/GitHub/mRNA-therapy-history-data/figures/new_trials_per_year.png", plot = p2, width = 8, height = 6)

# 3. Delivery Method Breakdown (Therapy Type)
therapy_counts <- mRNAtherapyhist %>%
  filter(!is.na(therapy_type) & therapy_type != "") %>%
  count(therapy_type, sort = TRUE)

p3 <- ggplot(therapy_counts, aes(x = reorder(therapy_type, n), y = n)) +
  geom_bar(stat = "identity", fill = dark2_colors[2]) + # #D95F02
  coord_flip() +
  theme_minimal() +
  labs(title = "Breakdown of Therapy Types",
       x = "Therapy Type",
       y = "Number of Trials")

ggsave("~/Documents/GitHub/mRNA-therapy-history-data/figures/therapy_type_breakdown.png", plot = p3, width = 8, height = 6)

# 4. Top Targeted Conditions (Top 10)
# conditions column might have multiple conditions separated by pipes or commas.
# We'll just take the whole string for now as it usually lists the primary condition.
conditions_counts <- mRNAtherapyhist %>%
  filter(!is.na(conditions) & conditions != "") %>%
  count(conditions, sort = TRUE) %>%
  top_n(10, n)

p4 <- ggplot(conditions_counts, aes(x = reorder(conditions, n), y = n)) +
  geom_bar(stat = "identity", fill = dark2_colors[3]) + # #7570B3
  coord_flip() +
  theme_minimal() +
  labs(title = "Top 10 Targeted Conditions",
       x = "Condition",
       y = "Number of Trials")

ggsave("~/Documents/GitHub/mRNA-therapy-history-data/figures/top_conditions.png", plot = p4, width = 8, height = 6)

# 5. Top Targeted Conditions for "Other" Category
other_conditions_counts <- mRNAtherapyhist %>%
  filter((is.na(disease_type) | disease_type == "Other") & !is.na(conditions) & conditions != "") %>%
  count(conditions, sort = TRUE) %>%
  top_n(10, n)

p5 <- ggplot(other_conditions_counts, aes(x = reorder(conditions, n), y = n)) +
  geom_bar(stat = "identity", fill = dark2_colors[4]) + # Pink for "Other"
  coord_flip() +
  theme_minimal() +
  labs(title = 'Top 10 "Other" Targeted Conditions',
       x = "Condition",
       y = "Number of Trials")

ggsave("~/Documents/GitHub/mRNA-therapy-history-data/figures/other_conditions_breakdown.png", plot = p5, width = 8, height = 6)
