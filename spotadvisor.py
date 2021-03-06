#!/usr/bin/python3

# spotadvisor.py - Generates spot instance suggestions based on AWS interruption data
# Copyright (C) 2022  Sam Cole & Rob Jones for p1 Technologies

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import argparse
import json
import logging
import re
import urllib.error
import urllib.request
from operator import itemgetter

ppafamilies = "^(m[3456].*|c[3456].*|r[3456].*)$"

defaultadvisorurl = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"

# Define processor families here.  Intel is the catchall, and should have all suffixes not used
# by another processor family.
procfamilies = {'amd': 'a',
                'graviton': 'g',
                'intel': 'bcdefhijklmnopqrstuvwxyz'
                }


def parseargs():
    parser = argparse.ArgumentParser(
        description='Generate a list of spot instance suggestions based on user input and interruption data.'
    )
    parser.add_argument('--familylist', default='any', type=str.lower,
                        help='Comma separated list of instance families to consider.  "all" or "any" selects \
                        all instance families.  Individual entries support simple regular expression syntax.')
    parser.add_argument('--region', default='eu-west-1', type=str.lower, help='AWS region (default: eu-west-1')
    parser.add_argument('--os', default='Linux', choices={"Linux", "Windows"},
                        help='Operating System: Linux or Windows (default: Linux)s')
    parser.add_argument('--mincpus', default=0, type=int, help='Minimum vCPU count')
    parser.add_argument('--maxcpus', default=0, type=int, help='Maximum vCPU count')
    parser.add_argument('--procfamily', default='any', type=str.lower,
                        choices={'any', 'amd', 'graviton', 'intel'},
                        help='Processor family (default = any)')
    parser.add_argument('--maxintcode', default=4, type=int, choices=range(0, 5), metavar="[0-4]",
                        help='Maximum interruption rate to consider: 0=5%%, 1=10%%, 2=15%%, 3=20%%, 4=any')
    parser.add_argument('--format', default='table', choices={'table', 'csv', 'instancelist', 'json'},
                        help='Output format: table, csv, instancelist (default: table)')
    parser.add_argument('--pretty', default=False, action='store_true',
                        help="Pretty prints output. Only usable with '--format json'")
    parser.add_argument('--advisordata', default=defaultadvisorurl,
                        metavar="URL", help='URL of spot advisor data file')
    parser.add_argument('--sort', default='name', type=str.lower, choices={'name', 'avail', 'vcpucount'},
                        help='Sort order for results (default: name)')
    megroup = parser.add_mutually_exclusive_group()
    megroup.add_argument('--regionlist', default=False, action='store_true', help='Print region list and exit')
    megroup.add_argument('--instancelist', default=False, action='store_true', help='Print instance list and exit')
    args = parser.parse_args()
    return args


def listregions(data, args):
    # List regions from the advisor data set

    regionset = sorted(set(data.keys()))
    if args.format == 'json':
        print(json.dumps(regionset, indent=2)) if args.pretty else print(json.dumps(regionset))
    else:
        for region in regionset:
            print(region)
    return


def listinstances(instances, args):
    # List instance types from the advisor data set
    instanceset = sorted(set(instances.keys()))
    if args.format == 'json':
        print(json.dumps(instanceset, indent=2)) if args.pretty else print(json.dumps(instanceset))
    else:
        for instance in instanceset:
            print(instance)
    return


def print_out(data, args):
    if args.sort == 'avail':
        sortdata = sorted(data, key=itemgetter('interruption_rate'))
    elif args.sort == 'name':
        sortdata = sorted(data, key=itemgetter('instance_type'))
    elif args.sort == 'vcpucount':
        sortdata = sorted(data, key=itemgetter('cores'), reverse=True)
    else:
        sortdata = data

    if args.format == 'json':
        print(json.dumps(sortdata, indent=2)) if args.pretty else print(json.dumps(sortdata))

    elif args.format == 'table':
        for i in sortdata:
            print("%-12s\t%s" % (i['instance_type'], i['interruption_text']))

    elif args.format == 'csv':
        for i in sortdata:
            print("%s, %s" % (i['instance_type'], i['interruption_text']))

    else:
        for i in sortdata:
            print("%s" % i['instance_type'])


def main():
    args = parseargs()

    # Download the spot advisor data set from AWS.
    try:
        with urllib.request.urlopen(args.advisordata) as url:
            data = json.loads(url.read().decode())
            ranges = data['ranges']
            instances = data['instance_types']
            rates = data['spot_advisor']
    except ValueError as e:
        logging.error("unable to get advisor data: %s" % e.args[0])
        return 1
    except urllib.error.URLError as e:
        logging.error("unable to get advisor data: %s" % e.reason)
        return 1

    if args.regionlist:
        listregions(rates, args)
        return 0

    if args.instancelist:
        listinstances(instances, args)
        return 0

    # Match requested region to the advisor data set.  Abort if no match found.
    if args.region not in rates.keys():
        logging.error("Region %s not found in AWS region list." % args.region)
        exit(1)

    # Iterate over the instances in the spot advisor data structure.
    instlist = []
    if args.familylist in ['all', 'any']:
        searchstring = '^.*$'
    elif args.familylist in ['ppa', 'ppo']:
        searchstring = ppafamilies
    else:
        searchstring = "^(%s)$" % re.sub(",", "|", args.familylist)

    exp = re.compile(searchstring)

    for inst in instances:
        inst_obj = instances[inst]
        inst_obj["instance_type"] = inst
        fam = inst.split('.')[0]

        # Sort on processor family, if the current instance type doesn't match abort this iteration.
        if args.procfamily != 'any':
            if args.procfamily != 'intel':
                if len(fam) == 2 or fam[2] not in procfamilies[args.procfamily]:
                    continue
            elif len(fam) > 2 and fam[2] not in procfamilies[args.procfamily]:
                continue

        # Match against instance families in the PPO list. Add to the eligible instance list if matched.
        if re.match(exp, fam):
            if inst in rates[args.region][args.os]:
                # Compare to vCPU limits
                if (instances[inst]['cores'] >= args.mincpus) and \
                        ((not args.maxcpus) or (instances[inst]['cores'] <= args.maxcpus)):
                    if rates[args.region][args.os][inst]['r'] <= args.maxintcode:
                        inst_obj["interruption_rate"] = rates[args.region][args.os][inst]['r']
                        inst_obj["interruption_text"] = ranges[rates[args.region][args.os][inst]['r']]['label']
                        instlist.append(instances[inst])
    
    print_out(instlist, args)


if __name__ == '__main__':
    exit(main())
