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
# tdiff$test <- as.factor(tdiff$test)
# tdiff$dates <- as.factor(tdiff$dates)
tdiff <- tdiff[order(tdiff$test, tdiff$date.a)]

# kable(head(tdiffs))

png(args[2]) #,    # create PNG for the heat map

#    width = 10*300,        # 10 x 300 pixels
#    height = 10*300,
#    res = 300,            # 300 pixels per inch
#    pointsize = 8)        # smaller font size

gg <- ggplot(tdiff, aes(x=date.a, y=test, fill=edit.dist))
gg <- gg + geom_tile(color="white", size=0.1)
gg <- gg + scale_fill_viridis(name="edit dist", label=comma)
gg <- gg + coord_equal()
gg <- gg + labs(x=NULL, y=NULL, title="testcase changes")
gg <- gg + theme_tufte()
gg <- gg + theme(plot.title=element_text(hjust=0))
gg <- gg + theme(axis.ticks=element_blank())
gg <- gg + theme(axis.text=element_text(size=7))
gg <- gg + theme(axis.text.x=element_text(angle=45, hjust=0.8))
gg <- gg + theme(legend.title=element_text(size=8))
gg <- gg + theme(legend.text=element_text(size=6))
gg

dev.off()               # close the PNG device
