#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, csv, cStringIO, codecs, os
from operator import itemgetter
from nltk.metrics.distance import edit_distance
from dateutil.parser import parse as dparse

def merge_similar(items):
    # merges all the items by starting to find rare items that only
    # differ in a few chars in from the most common items
    agg={}
    for item in items:
        agg[item]=agg.get(item, 0)+1

    map={}
    for item in (k for k,v in sorted(agg.items(), key=itemgetter(1))):
        if not item or not len(item.strip()): continue
        for candidate in (k for k,v in sorted(agg.items(), key=itemgetter(1), reverse=True)):
            if not item or not len(candidate.strip()): continue
            if item==candidate: break
            if ((candidate in item and
                 len(item)-len(candidate)<len(item)/5) or
                edit_distance(candidate, item)<len(candidate)/10):
                map[item]=candidate
                break
    print >>sys.stderr, '\n'.join(sorted([str(x) for x in map.items()], key=itemgetter(1)))
    return [map.get(item,item).strip() for item in items]

frmonths={ u'juin': '6',
           u'septembre': '9',
           u'décembre': '12',
           u'mai': '5',
           u'juillet': '7',
           u'octobre': '10',
           u'novembre': '11',
           u'avril': '4',
           u'août': '8',
           }

def frenchdates(item):
    pos=item.find(u'trimestre')
    if pos>=0:
        try:
            quarter=int(item[pos-5])
        except ValueError:
            return item
        date='15/%s/2012' % ((quarter*3)-1)
    else:
        date=u'/'.join([frmonths.get(x,x) for x in item.split()])
    try:
        date=dparse(date)
    except (UnicodeEncodeError, ValueError) as e:
        return item
    except:
        print >>sys.stderr, date.encode('utf8')
        raise
    return date.isoformat()

def stripquotes(text):
    if text and text[0]==text[-1]=='"':
        return text[1:-1]
    return text

if __name__=='__main__':
    writer = csv.writer(sys.stdout)
    reader = csv.reader(sys.stdin)
    rows=list(reader)
    for row, procedure in zip(rows,
                              merge_similar([row[6].decode('utf8') for row in rows]) ):
        if len(row)<7 or len(filter(None,['x' if len(x.strip())>1 and x.strip()!='""' else None for x in row[:5]]))<5:
            print >>sys.stderr, "skipping", len(row), len(filter(None,['x' if len(x)>2 else None for x in row[:5]])), row
            continue
        res=[None] * 11
        res[0]=''.join(row[0].split()) # procedure id?
        res[1]=stripquotes(row[1]) # french name of DG -- skip
        res[2]=stripquotes(row[2]) # title -- sometimes has left protruding garbage
        res[3]='/'.join([x for x in stripquotes(row[3]).split() if x.isupper() and len(x)>1]) # DGs abbrevs -- has lots of left protruding garbage
        res[4]=frenchdates(row[4].decode('utf8')).encode('utf8') # date
        res[5]=stripquotes(row[5]) # legal base
        if len(row)==11:
            res[6]=procedure.encode('utf8') # procedure type
            res[7]=row[7] if row[7] in ['O', 'X'] else ''
            res[8]=row[8] if row[8] in ['O', 'X'] else ''
            res[9]=stripquotes(row[9]) # description
            res[10]='Y' if 'Yes' in row[10] else ''
        else:
            res[7]=row[6] if row[6] in ['O', 'X'] else ''
            res[8]=row[7] if row[7] in ['O', 'X'] else ''
            res[9]=stripquotes(row[8]) # description
            res[10]='Y' if 'Yes' in row[9] else ''
        writer.writerow(res)

