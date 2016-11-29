#!/usr/bin/env guile \
-e main -s
!#

(use-modules (ice-9 popen)
             (ice-9 ftw)
             (ice-9 rdelim)
             (srfi srfi-1)
             (srfi srfi-26))

(define (interleave lst-a lst-b)
  (map cons lst-a lst-b))

(define (but-last lst)
  (if (> 2 (length lst)) 
      '()
      (cons (car lst) (but-last (cdr lst)))))

(define (pair-suc lst)
  (if (null? lst)
      '() 
      (interleave (but-last lst) (cdr lst))))

(define (all-files dirs)
  (apply
   (cut lset-union string=? <...>)
   (map scandir
        (filter file-exists? dirs))))

(define (lines-in-file path)
  (if (not (file-exists? path))
      0
      (let* ((p (open-input-pipe
                 (string-append
                  "wc -l "
                  path
                  " | awk '{print $1}'")))
             (pipe-str (read-line p)))
        (close-pipe p)
        (string->number
         (string-trim-both pipe-str)))))

(define (compare-files path-a path-b)
  (let* ((exists-a (file-exists? path-a))
         (n-lines-a (lines-in-file path-a))
         (exists-b (file-exists? path-b))
         (n-lines-b (lines-in-file path-b))
         (max-lines (max n-lines-a n-lines-b))
         
         )
    (cond
     ((not (or exists-a exists-b)) "NA")
     ((not exists-a) "1")
     ((not exists-b) "1")
     (#t (let* ((diff-p (open-input-pipe
                  (string-append
                   "diff -U 0 "
                   path-a
                   " "
                   path-b
                   " | grep -c ^@")))
               (diff-str (read-line diff-p)))
           (close-pipe diff-p)
           (if (= 0 max-lines)
               "NA"
               (number->string
                (exact->inexact
                 (/  (string->number
                      (string-trim-both diff-str))
                     max-lines)))))))))

(define (display-all-diffs dir-a dir-b files)
  (if (not (null? files))
      (let ((file (car files)))
        (display
         (string-append
          file
          " "
          dir-a
          " "
          dir-b
          " "
          (compare-files
           (string-append dir-a "/" file)
           (string-append dir-b "/" file))))
        (newline)
        (display-all-diffs dir-a dir-b (cdr files)))))

(define (main args)
  (let* ((dirs (cdr args))
         (dir-pairs (pair-suc dirs))
         (files (filter
                  (lambda (fn) (not (or (string=? "." fn) (string=? ".." fn))))
                  (all-files dirs)))) 
    (map
     (lambda (dir-pair)
       (display-all-diffs (car dir-pair) (cdr dir-pair) files))
     dir-pairs)))
