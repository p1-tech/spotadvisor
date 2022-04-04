# spotadvisor

spotadvisor is a tool that creates candidate instance family lists using data from
the AWS Spot Advisor data feed and input from the user.

## Installation
  spotadvisor.py is a standalone Python file that can be installed anywhere.

## Requirements
  The only requirement is Python 3.6+.  All other dependencies are included 
  in the Python standard library.

## Arguments
  spotadvior accepts the following arguments.

 __--help, -h__ prints help message

 __--familylist__ A comma delimited list of the instance family prefixes to search.  'any' 
selects all families.  Regular expressions are supported within list items (i.e r5.*,c6,
 m[56])

__--os__ Operating system language to match.  Options are Linux or Windows.

__--mincpus__ The minimum number of instance vCPUs to include in the search.

__--procfamily__ The processor family to include in the search.  'any' includes all
processor families, other options are intel, amd, or graviton.

__--maxintcode__ The maximum interruption rate to consider for inclusion.  0 = < 5%,
1 = < 10%, 2 = < 15%, 3 = < 20%, 4 = no limit

__--format__ Presentation format for output date.  Options are table, CSV, JSON, or 
instancelist.  Table and CSV include interruption rate data, instancelist is a bare
list of instance types.

__--pretty__ Adds line breaks and indentation to the JSON formatted output.

__--sort__ Sort output.  Options are name, avail (interruption rate), and vcpucount.
vcpucount sorting is highest vcpu count instances first.

__--advisordata__ Overrides default URL for AWS spot advisor data

__--regionlist__ Prints AWS region list and exits.

__--instancelist__ Prints AWS instance family list and exits.

##Usage

```sh
# csv output
python3 ./spotadvisor.py --maxintcode 2 --mincpus 24  --region=us-west-2 --intelonly --format csv

# pretty-printed json
python3 ./spotadvisor.py --maxintcode 1 --mincpus 48  --region=us-west-2 --intelonly --format json --pretty

# Select all instances in the r5 family and c5 instances that have an interruption rate less than 15%
python3 ./spotadvisor.py --familylist r5.*,c5 --maxintcode 2
```
## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you 
would like to change.

## License
[GPL3](https://choosealicense.com/licenses/gpl-3.0/)