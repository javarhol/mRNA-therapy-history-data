#' Cumulative mRNA clinical-trial starts per year, by disease type.
#' Reads the auto-updated CSV produced by scripts/classify.py (which in turn
#' reads scripts/fetch_trials.py output) and plots three stacked areas:
#' Cancer / Virus / Genetic Disease. COVID trials are excluded.
#'
#' The year axis, y-axis cap, and annotation positions are derived from the
#' data so the script keeps working as the CSV grows.

# packages ----------------------------------------------------------------
library(dplyr)
library(tidyr)
library(ggplot2)
library(RColorBrewer)

has_bbplot <- requireNamespace("bbplot", quietly = TRUE)

# locate repo root whether this is sourced from figures/ or run from root -
here <- tryCatch(dirname(sys.frame(1)$ofile), error = function(e) NA)
if (is.na(here) || !nzchar(here)) here <- getwd()
repo_root <- if (basename(here) == "figures") dirname(here) else here

csv_path <- file.path(repo_root, "data", "mrna_trials_classified.csv")
if (!file.exists(csv_path)) {
  stop(sprintf(
    "Classified CSV not found at %s.\nRun: python3 scripts/fetch_trials.py && python3 scripts/classify.py",
    csv_path))
}

# data --------------------------------------------------------------------
trials <- read.csv(csv_path, stringsAsFactors = FALSE)

# keep interventional, non-COVID trials in the 3 tracked disease buckets;
# treat `is_covid` as TRUE/FALSE tolerantly (csv writes Python booleans).
is_true <- function(x) tolower(as.character(x)) %in% c("true", "1", "yes")

trials <- trials %>%
  filter(!is_true(is_covid)) %>%
  filter(disease_type %in% c("Cancer", "Virus", "Genetic Disease")) %>%
  mutate(start_year = suppressWarnings(as.integer(start_year))) %>%
  filter(!is.na(start_year))

year_range <- seq(min(trials$start_year), max(trials$start_year))

counts <- trials %>%
  count(start_year, disease_type, name = "n")

# pad every (year, disease_type) combo with zeros so the area plot stays flat
# where there are no trials
grid <- expand.grid(
  start_year = year_range,
  disease_type = c("Cancer", "Virus", "Genetic Disease"),
  stringsAsFactors = FALSE
)

cumulative <- grid %>%
  left_join(counts, by = c("start_year", "disease_type")) %>%
  mutate(n = tidyr::replace_na(n, 0L)) %>%
  group_by(disease_type) %>%
  arrange(start_year, .by_group = TRUE) %>%
  mutate(cumulative = cumsum(n)) %>%
  ungroup() %>%
  mutate(disease_type = factor(disease_type,
                               levels = c("Cancer", "Virus", "Genetic Disease")))

# plot --------------------------------------------------------------------
y_cap <- ceiling(max(
  cumulative %>%
    group_by(start_year) %>%
    summarise(total = sum(cumulative), .groups = "drop") %>%
    pull(total)
) / 20) * 20  # round up to the next 20 for headroom

annotations <- tibble::tribble(
  ~year,  ~label,
  2010,   "Moderna founded",
  2020,   "COVID-19 genome sequenced"
) %>% filter(year >= min(year_range), year <= max(year_range))

p <- ggplot(cumulative, aes(start_year, cumulative, fill = disease_type)) +
  geom_area(alpha = 0.75) +
  scale_x_continuous(breaks = seq(min(year_range), max(year_range), by = 2)) +
  scale_y_continuous(expand = c(0, 0), limits = c(0, y_cap)) +
  scale_fill_brewer(palette = "Dark2", name = NULL) +
  ggtitle("Cumulative clinical mRNA therapy trials (excl. COVID-19)") +
  labs(x = NULL, y = "Cumulative trials started",
       caption = sprintf("Data: clinicaltrials.gov v2 API, fetched %s",
                         format(Sys.Date(), "%Y-%m-%d")))

for (i in seq_len(nrow(annotations))) {
  p <- p +
    geom_vline(xintercept = annotations$year[i], linetype = "dotted",
               linewidth = 0.8, color = "grey30") +
    annotate("text", x = annotations$year[i], y = y_cap * 0.95,
             label = annotations$label[i], hjust = 1.05, size = 4)
}

p <- p +
  theme(axis.text.x = element_text(angle = 270, vjust = 0.5, hjust = 0),
        legend.position = "bottom")

if (has_bbplot) {
  p <- p + bbplot::bbc_style()
}

# save --------------------------------------------------------------------
out_path <- file.path(repo_root, "figures", "mRNA therapy graph.png")
ggsave(out_path, p, width = 10, height = 6, dpi = 150)
message("Wrote ", out_path)
print(p)
