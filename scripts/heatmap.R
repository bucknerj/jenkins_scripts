#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if(length(args) != 2) {
  stop("usage: heatmap.R <input data file path> <heatmap png output path>")
}

library(data.table, warn.conflicts = FALSE, quietly = TRUE)
library(dplyr, warn.conflicts = FALSE, quietly = TRUE)
library(purrr, warn.conflicts = FALSE, quietly = TRUE)
library(tidyr, warn.conflicts = FALSE, quietly = TRUE)
library(lubridate, warn.conflicts = FALSE, quietly = TRUE)
library(ggplot2, warn.conflicts = FALSE, quietly = TRUE)
library(scales, warn.conflicts = FALSE, quietly = TRUE)
library(gridExtra, warn.conflicts = FALSE, quietly = TRUE)
library(ggthemes, warn.conflicts = FALSE, quietly = TRUE)
library(viridis, warn.conflicts = FALSE, quietly = TRUE)
library(knitr, warn.conflicts = FALSE, quietly = TRUE)

tdiff <- tbl_df(fread(args[1]))
colnames(tdiff) <- c('test', 'date.a', 'date.b', 'edit.dist')
setorder(tdiff, test, date.a)

gg <- ggplot(tdiff, aes(x=date.a, y=test, fill=edit.dist)) +
    geom_tile(color="white", size=0.1) +
    scale_fill_viridis(name="edit dist", label=comma) +
    coord_equal() +
    labs(x=NULL, y=NULL, title="testcase changes") +
    theme_tufte() +
    theme(plot.title=element_text(hjust=0)) +
    theme(axis.ticks=element_blank()) +
    theme(axis.text=element_text(size=7)) +
    theme(axis.text.x=element_text(angle=45, hjust=0.8)) +
    theme(legend.title=element_text(size=8)) +
    theme(legend.text=element_text(size=6))

ggsave(file=args[2], plot=gg)
