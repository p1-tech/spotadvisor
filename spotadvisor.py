import argparse
import json
import logging
import urllib.request

spotdataurl="https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
ppofamilies = ["m3","m4","m5", "m6", "c3", "c4", "c5", "c6", "r3", "r4", "r5"]


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', default='eu-west-1', type=str.lower, help='AWS region')
    parser.add_argument('--os', default='Linux', choices={"Linux", "Windows"},
                        help='Operating System: Linux or Windows (default = Linux)s')
    parser.add_argument('--mincpus', default=48, type=int, help='Minimum vCPU count (default = 48)')
    parser.add_argument('--intelonly', default=False, action='store_true',
                        help='consider only intel CPU instances (default = False')
    parser.add_argument('--maxintcode', default=4, type=int, choices=range(0,5), metavar="[0-4]",
                        help='Maximum interruption rate to consider: 0=5%%, 1=10%%, 2=15%%, 3=20%%, 4=any (default = 1)')
    parser.add_argument('--format', default='table', choices={'table', 'csv', 'instancelist', 'json'},
                        help='Output format: table, csv, instancelist (default = table)')
    parser.add_argument('--pretty', default=False, action='store_true', help="Pretty prints output. Only usable with '--format json'")
    args = parser.parse_args()
    return args

def main():

    args = parseargs()

    with urllib.request.urlopen(spotdataurl) as url:
        data = json.loads(url.read().decode())
        ranges = data['ranges']
        instances = data['instance_types']
        rates = data['spot_advisor']

        if args.region not in rates.keys():
            logging.error("Region %s not found in AWS region list." % args.region)
            exit(1)

        instlist = []
        for inst in instances:
            fam = inst.split('.')[0]
            if args.intelonly and len(fam) > 2 and fam[2] in ['a', 'g']:
                continue
            if inst[:2] in ppofamilies:
                if inst in rates[args.region][args.os]:
                    if instances[inst]['cores'] >= args.mincpus:
                        if rates[args.region][args.os][inst]['r'] <= args.maxintcode:
                            if args.format == 'json':
                                inst_obj = instances[inst]
                                inst_obj["instance_type"] = inst
                                inst_obj["interruption_rate"] = ranges[rates[args.region][args.os][inst]['r']]['label']
                                instlist.append(instances[inst])
                            elif args.format == 'table':
                                print("%-12s\t%s" % (inst, ranges[rates[args.region][args.os][inst]['r']]['label']))
                            elif args.format == 'csv':
                                print("%s, %s" % (inst, ranges[rates[args.region][args.os][inst]['r']]['label']))
                            else:
                                print("%s" % inst)
        if args.format == 'json' and args.pretty:
            print(json.dumps(instlist, indent=2))
        else:
            print(json.dumps(instlist))


if __name__ == '__main__':
    exit(main())
