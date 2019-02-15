import argparse
import seaborn as sns

sns.set()
parser = argparse.ArgumentParser()

parser.add_argument('--karyotype', dest='karyotype', type=argparse.FileType('rU'), required=True, help='Path to the karyotype file (BED format)')
# parser.add_argument('--fb', dest='fb', help='Path to RFmix FB output')
parser.add_argument('--msp', dest='msp', type=argparse.FileType('rU'), required=True, help='Path to RFmix MSP output')
parser.add_argument('--chr', dest='chrm', help='Include only the specified chromosome')
parser.add_argument('--sample', dest='sample', help='Include only the specified sample')
parser.add_argument('--prefix', dest='prefix', default='output', help='Output prefix')
parser.add_argument('--bed', dest='bed', action='store_true', help='Output BED format [default]')
parser.add_argument('--html', dest='html', action='store_true', help='Output HTML format')
parser.add_argument('--nojs', dest='nojs', action='store_true', help='No dynamic HTML')
parser.add_argument('--R', dest='r', action='store_true', help='Output R ready format [not implemented]')
args = parser.parse_args()

karyotype = {}
group = {}
samples = []
genome = {}
maxchrm = 0

if args.html is False and args.bed is False and args.r is False:
    args.bed = True

# Read karyotype
if args.karyotype is not None and args.msp is not None:
    for line in args.karyotype:
        tabs = line[:-1].split('\t')
        if args.chrm is None or args.chrm == tabs[0]:
            karyotype[tabs[0]] = tabs
            if maxchrm < int(tabs[2]):
                maxchrm = int(tabs[2])
    args.karyotype.close()

    # Read Group names
    # #Subpopulation order/codes: AND=0	AUR=1	...
    line = args.msp.readline()
    for tmp in line[28:-1].split('\t'):
        tab = tmp.split('=')
        group[int(tab[1])] = tab[0]

    # ReadSample names
    # #chm	spos	epos	sgpos	egpos	n snps	Col340.0	Col340.1	Col341.0	Col341.1	...
    line = args.msp.readline()
    count = 0
    for tmp in line[:-1].split('\t')[6:]:
        count += 1
        if count % 2 == 0:
            samples.append(tmp[:-2])

    # Read Chromosome structures
    # NC_031974.2	10728	3669032	0.00	10.39	22	9	9	9	9	9	9	9	...
    for line in args.msp:
        if args.chrm is None or args.chrm in line:
            tabs = line[:-1].split('\t')
            if tabs[0] in karyotype:
                if tabs[0] not in genome:
                    genome[tabs[0]] = {}
                count = 0
                for tmp in tabs[6:]:
                    sampleid = (count - count % 2) / 2
                    if args.sample is None or args.sample == samples[int(sampleid)]:
                        if samples[int(sampleid)] not in genome[tabs[0]]:
                            genome[tabs[0]][samples[int(sampleid)]] = {}
                        if count % 2 not in genome[tabs[0]][samples[int(sampleid)]]:
                            genome[tabs[0]][samples[int(sampleid)]][count % 2] = {}
                        if tabs[1] not in genome[tabs[0]][samples[int(sampleid)]][count % 2]:
                            genome[tabs[0]][samples[int(sampleid)]][count % 2][(tabs[1], tabs[2])] = tmp
                    count += 1
    args.msp.close()

    # Analyse/Compact the chromosome structures
    output = {}
    for chrm in karyotype.keys():
        if chrm in genome:
            for sample in sorted(genome[chrm].keys()):
                if sample not in output:
                    output[sample] = {}
                if chrm not in output[sample]:
                    output[sample][chrm] = {}
                for strand in sorted(genome[chrm][sample].keys()):
                    output[sample][chrm][strand] = []
                    last = None
                    lastx = None
                    last2 = None
                    for pos in genome[chrm][sample][strand].keys():
                        if last2 is not None and last2 == pos[0] and genome[chrm][sample][strand][pos] == last:
                            last2 = pos[1]
                        else:
                            if last2 is not None:
                                output[sample][chrm][strand].append([int(last), int(lastx), int(last2)])
                            last2 = pos[1]
                            lastx = pos[0]
                            last = genome[chrm][sample][strand][pos]
                    if last2 is not None:
                        output[sample][chrm][strand].append([int(last), int(lastx), int(last2)])

    # Free memory
    samples = []
    genome = {}

    # output data
    colours = sns.hls_palette(len(group), s=.4)
    if args.bed:
        with open(args.prefix + '.bed', 'w') as bedout:
            for sample in output.keys():
                bedout.write('track name="' + sample + '" type=bedDetail description="Sample ' + sample + ' custom track" visibility=2 itemRgb="On"\n')
                for chrm in output[sample].keys():
                    scale = 100 / int(karyotype[chrm][2])
                    for strand in output[sample][chrm].keys():
                        for segment in output[sample][chrm][strand]:
                            bedout.write(chrm + '\t' + str(segment[1]) + '\t' + str(segment[2]) + '\t' + group[segment[0]] + '\t0\t' + ('+' if strand == 0 else '-') + '\t' + str(segment[1]) + '\t' + str(segment[2]) + '\t' + str(int(colours[segment[0]][0]*255)) + ',' + str(int(colours[segment[0]][1]*255)) + ',' + str(int(colours[segment[0]][2]*255)) + '\n')

    if args.html:
        with open(args.prefix + '.html', 'w') as htmlout:
            htmlout.write('<!DOCTYPE html>\n<html lang="en">\n<head><meta content="text/html; charset=utf-8" http-equiv="content-type"><meta content="width=device-width, initial-scale=1" name="viewport"><title>Ancestry Composition</title><style>*,::after,::before{-webkit-box-sizing:inherit;box-sizing:inherit}body{font-feature-settings:"kern","liga","pnum";-moz-osx-font-smoothing:grayscale;color:#333435;font-family:"Avenir Next",Helvetica,Roboto,Arial,sans-serif;line-height:1.5;background:#fff}html{font-size:100%;font-family:sans-serif;-webkit-text-size-adjust:100%}#navlegend{position:fixed;left:0;top:0;width:100%;height:70px;overflow:hidden;z-index:1000;background:#fff;border-bottom:1px solid #eee}#content{margin-top:75px}body .chromosome-painting{float:left;display:block;margin-left:.5%;margin-right:2.5%;width:62%}body .chromosome-painting .chromosome-container{margin-bottom:10px;display:-webkit-box;display:-webkit-flex;display:-ms-flexbox;display:flex;-webkit-box-align:center;-webkit-align-items:center;-ms-flex-align:center;align-items:center;height:30px}body .chromosome-painting .chromosome-container .number{-webkit-box-flex:0;-webkit-flex:0 0 50px;-ms-flex:0 0 50px;flex:0 0 50px;font-weight:500}body .chromosome-painting .chromosome-container .chromosome{-webkit-box-flex:1;-webkit-flex:1;-ms-flex:1;flex:1}body .chromosome-painting .chromosome-container .chrom1{margin-bottom:3px}body .chromosome-painting .chromosome-container .chrom1,body .chromosome-painting .chromosome-container .chrom2{background:#edeff0 url("data:image/svg+xml;base64,PHN2ZyBlbmFibGUtYmFja2dyb3VuZD0ibmV3IDAgMCAxMCAxMCIgdmlld0JveD0iMCAwIDEwIDEwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxnIGZpbGw9IiNjMGMxYzIiPjxwYXRoIGQ9Im0wIDB2LjZsLjYtLjZ6Ii8+PHBhdGggZD0ibTQuNCAwLTQuNCA0LjR2MS4ybDUuNi01LjZ6Ii8+PHBhdGggZD0ibTEwIDBoLS42bC05LjQgOS40di42aC42bDkuNC05LjR6Ii8+PHBhdGggZD0ibTUuNiAxMCA0LjQtNC40di0xLjJsLTUuNiA1LjZ6Ii8+PHBhdGggZD0ibTEwIDEwdi0uNmwtLjYuNnoiLz48L2c+PC9zdmc+") repeat center center;border-radius:5px;height:10px;overflow:hidden;position:relative;-webkit-transform:translate3d(0,0,0);transform:translate3d(0,0,0)}body .chromosome-painting .chromosome-container .chrom1 .segment,body .chromosome-painting .chromosome-container .chrom2 .segment{height:100%;position:absolute}body .chromosome-painting .chromosome-container .chrom1 .centromere,body .chromosome-painting .chromosome-container .chrom2 .centromere{background:transparent url("data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwIiB2aWV3Qm94PSIwIDAgMTAgMTAiIHdpZHRoPSIxMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJtMzg0IDYwaDEwYy0yLjc2MTQyNCAwLTUgMi4yMzg1NzYzLTUgNXMyLjIzODU3NiA1IDUgNWgtMTBjMi43NjE0MjQgMCA1LTIuMjM4NTc2MyA1LTVzLTIuMjM4NTc2LTUtNS01eiIgZmlsbD0iI2ZmZiIgZmlsbC1ydWxlPSJldmVub2RkIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMzg0IC02MCkiLz48L3N2Zz4=") no-repeat center center;width:10px;height:10px;margin-left:-5px;position:absolute;top:0}body .chromosome-painting .species{font-weight:500;margin-bottom:10px}.legend{margin-left:.5%;margin-right:2.5%;height:70px;overflow:hidden;position:relative;align-items:center;display:flex}.minichrm{height:10px;width:15px;-webkit-transform:translate3d(0,0,0);transform:translate3d(0,0,0);border-radius:5px}.name{padding:2px 1.5em 0 .5em;font-weight:500}</style>')
            if not args.nojs:
                htmlout.write('<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"></script><script>$(document).ready(function(){$(".minichrm").each(function(){$(this).hover(function(){var t=$(this).data("species-id");$(".segment").each(function(){$(this).data("species-id")!=t&&$(this).css({opacity:0})})},function(){$(".segment").css({opacity:1})})})});</script>')
            htmlout.write('</head><body><nav id="navlegend"><div class="legend">\n')
            for sample in group.keys():
                htmlout.write('<div class="minichrm" data-species-id="' + group[sample] + '" style="background-color: rgb(' + str(int(colours[sample][0]*255)) + ', ' + str(int(colours[sample][1]*255)) + ', ' + str(int(colours[sample][2]*255)) + ');"></div><div class="name">' + group[sample] + '</div>')
            htmlout.write('</div></nav><div id="content">')
            for sample in output.keys():
                htmlout.write('  <div class="chromosome-painting">\n    <div class="species">' + sample + '</div>\n')
                for chrm in output[sample].keys():
                    scale = 100 / int(karyotype[chrm][2])
                    htmlout.write('    <div class="' + chrm + ' chromosome-container">\n      <div class="number">' + karyotype[chrm][3] + '</div>\n      <div class="chromosome">\n')
                    for strand in output[sample][chrm].keys():
                        htmlout.write('        <div class="chrom' + str(strand + 1) + '" style="width: ' + str(round(int(karyotype[chrm][2]) * 100 / maxchrm, 4)) + '%;">\n')
                        for segment in output[sample][chrm][strand]:
                            htmlout.write('          <div class="segment" data-species-id="' + group[segment[0]] + '" style="width: ' + str(round((segment[2] - segment[1]) * scale, 4)) + '%; left: ' + str(round(segment[1] * scale, 4)) + '%; background-color: rgb(' + str(int(colours[segment[0]][0]*255)) + ', ' + str(int(colours[segment[0]][1]*255)) + ', ' + str(int(colours[segment[0]][2]*255)) + ');"></div>\n')
                        if len(karyotype[chrm]) > 5:
                            htmlout.write('<div class="centromere" style="left: ' + str(round(int(karyotype[chrm][4]) * scale, 4)) + '%;"></div>\n')
                        htmlout.write('        </div>\n')
                    htmlout.write('      </div>\n    </div>\n')
                htmlout.write('  </div>\n')
            htmlout.write('</div></body></html>\n')
    if args.r:
        pass